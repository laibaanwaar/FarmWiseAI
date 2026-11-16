import copy
import threading
from datetime import datetime, timezone

import pytest
from bson import ObjectId
from fastapi import Header
from fastapi.testclient import TestClient

from backend.dependencies.auth import get_current_user
from backend.main import app
from backend.models.conversation import conversation_document
from backend.services.chat_service import ChatService


CITATIONS = [{
    "document_title": "Farmer's Handbook on Basic Agriculture",
    "pdf_page": 87,
    "printed_page": 79,
}]


class MemoryChatRepository:
    def __init__(self):
        self.rows = {}
        self.lock = threading.Lock()

    def create(self, owner_id, question, answer, citations, status, crop):
        row = conversation_document(owner_id, question, answer, citations, status, crop)
        row["_id"] = ObjectId()
        with self.lock:
            self.rows[str(row["_id"])] = row
        return copy.deepcopy(row)

    def append_message(self, owner_id, conversation_id, message, crop):
        with self.lock:
            row = self.rows.get(conversation_id)
            if not row or row["owner_id"] != owner_id:
                return False
            row["messages"].append(copy.deepcopy(message))
            row["updated_at"] = message["created_at"]
            row["crop"] = crop
            row["message_count"] += 1
            return True

    def list_for_user(self, owner_id, offset, limit):
        with self.lock:
            rows = [row for row in self.rows.values() if row["owner_id"] == owner_id]
            rows.sort(key=lambda row: (row["updated_at"], str(row["_id"])), reverse=True)
            return [{
                "conversation_id": str(row["_id"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"],
            } for row in rows[offset:offset + limit]]

    def get_for_user(self, owner_id, conversation_id):
        with self.lock:
            row = self.rows.get(conversation_id)
            if not row or row["owner_id"] != owner_id:
                return None
            return {
                "conversation_id": str(row["_id"]),
                "owner_id": row["owner_id"], "crop": row["crop"],
                "created_at": row["created_at"], "updated_at": row["updated_at"],
                "messages": sorted(copy.deepcopy(row["messages"]),
                                   key=lambda message: message["created_at"]),
                "message_count": row["message_count"],
            }


@pytest.fixture
def chat_api():
    repository = MemoryChatRepository()
    calls = []

    def fake_rag(question, crop):
        calls.append((question, crop))
        return {"status": "ok", "answer": f"Answer for {question}", "citations": CITATIONS}

    async def authenticated_user(x_test_user: str = Header(default="user-a")):
        return {"user": {"_id": x_test_user}}

    app.state.chat_service = ChatService(repository, fake_rag)
    app.dependency_overrides[get_current_user] = authenticated_user
    try:
        with TestClient(app) as client:
            yield client, repository, calls
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _user_header(user="user-a"):
    return {"X-Test-User": user}


def test_query_trims_question_creates_conversation_and_persists_citations(chat_api):
    client, repository, calls = chat_api
    response = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "  What are cotton wilt symptoms?  ",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"]
    assert body["answer"] == "Answer for What are cotton wilt symptoms?"
    assert body["citations"][0]["pdf_page"] == 87
    assert calls == [("What are cotton wilt symptoms?", "cotton")]
    saved = repository.get_for_user("user-a", body["conversation_id"])
    assert saved["messages"][0]["question"] == "What are cotton wilt symptoms?"
    assert saved["messages"][0]["citations"] == CITATIONS


def test_blank_question_is_rejected_without_calling_rag(chat_api):
    client, _, calls = chat_api
    response = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "   ",
    })
    assert response.status_code == 422
    assert calls == []


def test_query_continues_owned_conversation_in_chronological_order(chat_api):
    client, repository, calls = chat_api
    first = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "Symptoms in cotton?", "crop": "Cotton",
    }).json()
    second = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "And how to control it?", "conversation_id": first["conversation_id"],
    })
    detail = client.get(
        f"/api/v1/chat/history/{first['conversation_id']}", headers=_user_header()
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]
    assert calls == [("Symptoms in cotton?", "cotton"), ("And how to control it?", "cotton")]
    assert [message["question"] for message in detail.json()["messages"]] == [
        "Symptoms in cotton?", "And how to control it?",
    ]
    assert repository.get_for_user("user-a", first["conversation_id"])["message_count"] == 2


def test_history_is_paginated_and_scoped_to_authenticated_user(chat_api):
    client, _, _ = chat_api
    one = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "First question",
    }).json()
    second = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "Second question",
    }).json()
    client.post("/api/v1/chat/query", headers=_user_header("user-b"), json={
        "question": "User B question",
    })

    page = client.get("/api/v1/chat/history?offset=0&limit=1", headers=_user_header())
    user_b_list = client.get("/api/v1/chat/history", headers=_user_header("user-b"))
    assert page.status_code == 200
    assert len(page.json()["items"]) == 1
    assert page.json()["items"][0]["conversation_id"] == second["conversation_id"]
    assert len(user_b_list.json()["items"]) == 1
    assert user_b_list.json()["items"][0]["conversation_id"] != one["conversation_id"]


def test_user_b_cannot_open_or_append_to_user_a_conversation_and_rag_is_not_called(chat_api):
    client, _, calls = chat_api
    created = client.post("/api/v1/chat/query", headers=_user_header("user-a"), json={
        "question": "A private question",
    }).json()
    before = list(calls)

    detail = client.get(
        f"/api/v1/chat/history/{created['conversation_id']}", headers=_user_header("user-b")
    )
    append = client.post("/api/v1/chat/query", headers=_user_header("user-b"), json={
        "question": "Try to append", "conversation_id": created["conversation_id"],
    })

    assert detail.status_code == append.status_code == 404
    assert calls == before
    assert client.get("/api/v1/chat/history", headers=_user_header("user-b")).json()["items"] == []


def test_unauthenticated_chat_request_returns_401():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as client:
        response = client.get("/api/v1/chat/history")
    assert response.status_code == 401


def test_well_formed_missing_conversation_returns_404(chat_api):
    client, _, _ = chat_api
    response = client.get(f"/api/v1/chat/history/{ObjectId()}", headers=_user_header())
    assert response.status_code == 404


def test_pipeline_insufficient_context_response_is_preserved(chat_api):
    client, repository, _ = chat_api
    app.state.chat_service.pipeline = lambda question, crop: {
        "status": "no_passage", "answer": "INSUFFICIENT_CONTEXT", "citations": [],
    }
    response = client.post("/api/v1/chat/query", headers=_user_header(), json={
        "question": "Question with no supporting handbook context",
    })
    saved = repository.get_for_user("user-a", response.json()["conversation_id"])
    assert response.status_code == 200
    assert response.json()["answer"] == "INSUFFICIENT_CONTEXT"
    assert response.json()["citations"] == []
    assert saved["messages"][0]["status"] == "no_passage"
