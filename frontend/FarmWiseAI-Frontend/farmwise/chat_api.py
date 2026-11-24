"""Authenticated wrappers for the chat query and history endpoints."""

from __future__ import annotations

import os
import re
from typing import Any, MutableMapping

from farmwise.api_client import APIError
from farmwise.auth_api import authenticated_request

PAGE_SIZE = 100
_CONVERSATION_ID = re.compile(r"^[0-9a-fA-F]{24}$")


def _timeout() -> tuple[float, float]:
    try:
        read_timeout = float(os.getenv("CHAT_QUERY_TIMEOUT", "120"))
    except ValueError:
        read_timeout = 120.0
    return 3.05, max(1.0, read_timeout)


def _object(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise APIError(message, retryable=True)
    return value


def _citations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise APIError("The chat service returned malformed citations.", retryable=True)
    citations = []
    for item in value:
        citation = _object(item, "The chat service returned a malformed citation.")
        title, page = citation.get("document_title"), citation.get("pdf_page")
        printed_page = citation.get("printed_page")
        if (not isinstance(title, str) or not title.strip()
                or isinstance(page, bool) or not isinstance(page, int)
                or (printed_page is not None and
                    (isinstance(printed_page, bool) or not isinstance(printed_page, int)))):
            raise APIError("The chat service returned a malformed citation.", retryable=True)
        citations.append({"document_title": title, "pdf_page": page,
                          "printed_page": printed_page})
    return citations


def query(session_state: MutableMapping[str, Any], question: str,
          conversation_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"question": question}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    response = _object(authenticated_request(
        session_state, "POST", "/api/v1/chat/query", payload=payload,
        timeout=_timeout(),
    ), "The chat service returned an unexpected response.")
    conversation = response.get("conversation_id")
    answer = response.get("answer")
    if (not isinstance(conversation, str) or not _CONVERSATION_ID.fullmatch(conversation)
            or not isinstance(answer, str)):
        raise APIError("The chat service returned an incomplete answer.", retryable=True)
    return {"conversation_id": conversation, "answer": answer,
            "citations": _citations(response.get("citations"))}


def list_conversations(session_state: MutableMapping[str, Any], *,
                       offset: int = 0, limit: int = 100) -> dict[str, Any]:
    response = _object(authenticated_request(
        session_state, "GET", "/api/v1/chat/history",
        params={"offset": offset, "limit": limit},
    ), "The history service returned an unexpected response.")
    items = response.get("items")
    if (not isinstance(items, list) or response.get("offset") != offset
            or response.get("limit") != limit):
        raise APIError("The history service returned malformed conversation history.", retryable=True)
    checked = []
    for item in items:
        row = _object(item, "The history service returned a malformed conversation.")
        if (not isinstance(row.get("conversation_id"), str)
                or not _CONVERSATION_ID.fullmatch(row["conversation_id"])
                or isinstance(row.get("message_count"), bool)
                or not isinstance(row.get("message_count"), int)
                or not isinstance(row.get("created_at"), str)
                or not isinstance(row.get("updated_at"), str)):
            raise APIError("The history service returned a malformed conversation.", retryable=True)
        checked.append(row)
    return {"items": checked, "offset": offset, "limit": limit}


def conversation_messages(session_state: MutableMapping[str, Any], conversation_id: str,
                          *, offset: int = 0, limit: int = 100) -> dict[str, Any]:
    if not _CONVERSATION_ID.fullmatch(conversation_id):
        raise APIError("The conversation ID is invalid.", status_code=422)
    response = _object(authenticated_request(
        session_state, "GET", f"/api/v1/chat/history/{conversation_id}",
        params={"offset": offset, "limit": limit},
    ), "The history service returned an unexpected response.")
    messages = response.get("messages")
    total_messages = response.get("total_messages")
    if (not isinstance(messages, list) or response.get("offset") != offset
            or response.get("limit") != limit
            or isinstance(total_messages, bool) or not isinstance(total_messages, int)
            or total_messages < 0):
        raise APIError("The history service returned malformed messages.", retryable=True)
    checked = []
    for message in messages:
        row = _object(message, "The history service returned a malformed message.")
        if not isinstance(row.get("question"), str) or not isinstance(row.get("answer"), str):
            raise APIError("The history service returned a malformed message.", retryable=True)
        checked.append({**row, "citations": _citations(row.get("citations"))})
    if response.get("conversation_id") != conversation_id:
        raise APIError("The history service returned the wrong conversation.", retryable=True)
    return {**response, "messages": checked}


def all_conversations(session_state: MutableMapping[str, Any]) -> list[dict[str, Any]]:
    offset = 0
    conversations: list[dict[str, Any]] = []
    while True:
        page = list_conversations(session_state, offset=offset, limit=PAGE_SIZE)
        rows = page["items"]
        conversations.extend(rows)
        if len(rows) < PAGE_SIZE:
            return conversations
        offset += len(rows)


def all_conversation_messages(session_state: MutableMapping[str, Any],
                              conversation_id: str) -> list[dict[str, Any]]:
    offset = 0
    total = None
    messages: list[dict[str, Any]] = []
    while total is None or offset < total:
        page = conversation_messages(
            session_state, conversation_id, offset=offset, limit=PAGE_SIZE
        )
        rows = page["messages"]
        messages.extend(rows)
        total = page.get("total_messages", len(messages))
        if not rows:
            break
        offset += len(rows)
    return sorted(messages, key=lambda row: str(row.get("created_at", "")))
