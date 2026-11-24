from __future__ import annotations

import unittest
from unittest.mock import patch

from farmwise import chat_api
from farmwise import auth_api
from farmwise.api_client import APIError


class ChatAPITests(unittest.TestCase):
    def test_new_query_omits_conversation_id_and_keeps_citations(self):
        response = {
            "conversation_id": "0123456789abcdef01234567",
            "answer": "Use clean seed and rotate crops.",
            "citations": [{"document_title": "Cotton Guide", "pdf_page": 9,
                           "printed_page": 6}],
        }
        with patch.object(chat_api, "authenticated_request", return_value=response) as send:
            result = chat_api.query({"auth_access_token": "token"}, "Cotton wilt?")
        self.assertEqual(send.call_args.args[:3], (
            {"auth_access_token": "token"}, "POST", "/api/v1/chat/query"
        ))
        self.assertEqual(send.call_args.kwargs["payload"], {"question": "Cotton wilt?"})
        self.assertNotIn("conversation_id", send.call_args.kwargs["payload"])
        self.assertEqual(result["citations"][0]["pdf_page"], 9)

    def test_follow_up_includes_current_conversation_id(self):
        response = {"conversation_id": "0123456789abcdef01234567", "answer": "Next answer.", "citations": []}
        with patch.object(chat_api, "authenticated_request", return_value=response) as send:
            chat_api.query({}, "And next?", "0123456789abcdef01234567")
        self.assertEqual(send.call_args.kwargs["payload"], {
            "question": "And next?", "conversation_id": "0123456789abcdef01234567"
        })

    def test_query_rejects_malformed_response(self):
        with patch.object(chat_api, "authenticated_request", return_value={"answer": "missing id"}):
            with self.assertRaises(APIError):
                chat_api.query({}, "Question")

    def test_history_and_detail_send_pagination(self):
        history = {"items": [], "offset": 100, "limit": 100}
        detail = {
            "conversation_id": "0123456789abcdef01234567", "messages": [],
            "offset": 100, "limit": 100, "total_messages": 101,
        }
        with patch.object(chat_api, "authenticated_request", side_effect=[history, detail]) as send:
            self.assertEqual(chat_api.list_conversations({}, offset=100)["items"], [])
            self.assertEqual(chat_api.conversation_messages(
                {}, "0123456789abcdef01234567", offset=100
            )["total_messages"], 101)
        self.assertEqual(send.call_args_list[0].kwargs["params"], {"offset": 100, "limit": 100})
        self.assertEqual(send.call_args_list[1].kwargs["params"], {"offset": 100, "limit": 100})

    def test_empty_history_is_valid_and_api_failures_propagate(self):
        with patch.object(chat_api, "authenticated_request", return_value={
            "items": [], "offset": 0, "limit": 100
        }):
            self.assertEqual(chat_api.list_conversations({})["items"], [])
        error = APIError("Chat service temporarily unavailable.", status_code=503, retryable=True)
        with patch.object(chat_api, "authenticated_request", side_effect=error):
            with self.assertRaisesRegex(APIError, "temporarily unavailable"):
                chat_api.query({}, "Question")

    def test_ambiguous_query_failure_is_not_retried(self):
        failure = APIError("The API request timed out.", retryable=True)
        with patch.object(auth_api, "post_authenticated", side_effect=failure) as send, patch.object(
            auth_api, "_refresh"
        ) as refresh:
            with self.assertRaisesRegex(APIError, "timed out"):
                auth_api.authenticated_request(
                    {"auth_access_token": "access", "auth_refresh_token": "refresh"},
                    "POST", "/api/v1/chat/query", payload={"question": "Question"},
                    timeout=(3.05, 120),
                )
        send.assert_called_once()
        refresh.assert_not_called()

    def test_history_pagination_and_empty_history(self):
        first = [{"conversation_id": f"{index:024x}", "message_count": 1}
                 for index in range(100)]
        last = [{"conversation_id": f"{100:024x}", "message_count": 2}]
        with patch.object(chat_api, "list_conversations", side_effect=[
            {"items": first}, {"items": last}
        ]) as load:
            self.assertEqual(len(chat_api.all_conversations({})), 101)
        self.assertEqual([call.kwargs["offset"] for call in load.call_args_list], [0, 100])

        with patch.object(chat_api, "list_conversations", return_value={"items": []}):
            self.assertEqual(chat_api.all_conversations({}), [])

    def test_user_change_clears_private_conversation_state(self):
        state = {
            "chat_active_conversation": "private-id", "chat_messages": [{"answer": "private"}],
            "chat_history": [{"conversation_id": "private-id"}],
        }
        auth_api.clear_user_data(state)
        self.assertIsNone(state["chat_active_conversation"])
        self.assertEqual(state["chat_messages"], [])
        self.assertEqual(state["chat_history"], [])

    def test_detail_pagination_preserves_chronological_order(self):
        cid = "0123456789abcdef01234567"
        later = {"question": "second", "answer": "b", "status": "ok",
                 "citations": [], "created_at": "2026-01-02T00:00:00Z"}
        earlier = {"question": "first", "answer": "a", "status": "ok",
                   "citations": [], "created_at": "2026-01-01T00:00:00Z"}
        pages = [
            {"conversation_id": cid, "messages": [later], "total_messages": 2},
            {"conversation_id": cid, "messages": [earlier], "total_messages": 2},
        ]
        with patch.object(chat_api, "conversation_messages", side_effect=pages) as load:
            messages = chat_api.all_conversation_messages({}, cid)
        self.assertEqual([message["question"] for message in messages], ["first", "second"])
        self.assertEqual([call.kwargs["offset"] for call in load.call_args_list], [0, 1])


if __name__ == "__main__":
    unittest.main()
