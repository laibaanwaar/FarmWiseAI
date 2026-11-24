from __future__ import annotations

import asyncio
import sys
import types
import unittest
from unittest.mock import patch

from rag import urdu_demo_answers as demo


_pipeline_stub = types.ModuleType("rag.pipeline")
_pipeline_stub.answer_question = lambda question, crop: {
    "status": "ok", "answer": f"Normal answer: {question}", "citations": [],
}
with patch.dict(sys.modules, {"rag.pipeline": _pipeline_stub}):
    from backend.serializers.chat_serializer import ChatQueryRequest
    from backend.services.chat_service import ChatService


class MemoryRepository:
    def __init__(self):
        self.rows = {}

    def create(self, owner_id, question, answer, citations, status, crop):
        row = {
            "_id": "conversation-1", "owner_id": owner_id, "crop": crop,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "messages": [{
                "question": question, "answer": answer, "citations": citations,
                "status": status,
            }],
            "message_count": 1,
        }
        self.rows[row["_id"]] = row
        return row

    def get_for_user(self, owner_id, conversation_id):
        row = self.rows.get(conversation_id)
        if not row or row["owner_id"] != owner_id:
            return None
        return {**row, "conversation_id": row["_id"]}

    def append_message(self, owner_id, conversation_id, message, crop):
        row = self.get_for_user(owner_id, conversation_id)
        if not row:
            return False
        row["messages"].append(message)
        row["message_count"] += 1
        return True

    def list_for_user(self, owner_id, offset, limit):
        rows = [row for row in self.rows.values() if row["owner_id"] == owner_id]
        return [{"conversation_id": row["_id"], "message_count": row["message_count"]}
                for row in rows[offset:offset + limit]]


class UrduDemoAnswerTests(unittest.TestCase):
    def setUp(self):
        self.repo = MemoryRepository()
        self.pipeline_calls = []

        def pipeline(question, crop):
            self.pipeline_calls.append((question, crop))
            return {"status": "ok", "answer": f"Normal answer: {question}", "citations": []}

        self.service = ChatService(self.repo, pipeline)

    def test_all_eight_questions_have_curated_answers_and_real_citations(self):
        requested_questions = [
            "کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟",
            "کپاس کے پتے پیلے ہونے کی کیا وجوہات ہیں؟",
            "کپاس میں سفید مکھی کو کیسے کنٹرول کیا جا سکتا ہے؟",
            "کپاس کی گلابی سنڈی سے بچاؤ کیسے کیا جائے؟",
            "کپاس کی کاشت کے لیے کون سی مٹی موزوں ہے؟",
            "کپاس کو پانی کب اور کتنی بار دینا چاہیے؟",
            "کپاس میں کھاد کب اور کتنی مقدار میں ڈالنی چاہیے؟",
            "کپاس کے پھول اور ٹینڈے گرنے کی کیا وجوہات ہیں؟",
        ]
        self.assertEqual(len(demo._ANSWER_ROWS), len(requested_questions))
        for question in requested_questions:
            with self.subTest(question=question):
                result = demo.lookup_urdu_demo_answer(question)
                self.assertIsNotNone(result)
                self.assertFalse(result["answer"].startswith(demo.DEMO_LABEL))
                self.assertTrue(result["citations"])
                for citation in result["citations"]:
                    self.assertEqual(
                        citation["document_title"], "Farmer’s Handbook on Basic Agriculture"
                    )
                    self.assertIsInstance(citation["pdf_page"], int)
                    self.assertIsInstance(citation["printed_page"], int)

    def test_unicode_marks_whitespace_and_trailing_punctuation_normalize_exactly(self):
        variant = "  کَپاس   میں فیوزیریم وِلٹ کی کیا علامات ہیں؟؟؟  "
        self.assertEqual(
            demo.lookup_urdu_demo_answer(variant),
            demo.lookup_urdu_demo_answer("کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟"),
        )

    def test_unmatched_urdu_and_english_do_not_get_demo_answers(self):
        self.assertIsNone(demo.lookup_urdu_demo_answer("کپاس میں وائرس کا علاج کیا ہے؟"))
        self.assertIsNone(demo.lookup_urdu_demo_answer("What are cotton wilt symptoms?"))

    def test_enable_flag_is_opt_in(self):
        with patch.dict("os.environ", {"URDU_DEMO_ANSWERS_ENABLED": "false"}):
            self.assertFalse(demo.urdu_demo_answers_enabled())
        with patch.dict("os.environ", {"URDU_DEMO_ANSWERS_ENABLED": " TRUE "}):
            self.assertTrue(demo.urdu_demo_answers_enabled())

    def test_flag_disabled_and_unmatched_or_english_questions_use_normal_pipeline(self):
        questions = [
            "کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟",
            "کپاس میں وائرس کا علاج کیا ہے؟",
            "What are the symptoms of Fusarium wilt in cotton?",
        ]
        with patch.dict("os.environ", {"URDU_DEMO_ANSWERS_ENABLED": "false"}):
            for question in questions:
                result = asyncio.run(self.service.query(
                    "user-a", ChatQueryRequest(question=question)
                ))
                self.assertTrue(result["answer"].startswith("Normal answer:"))
        self.assertEqual([row[0] for row in self.pipeline_calls], questions)

    def test_enabled_demo_skips_rag_and_is_saved_in_conversation_history(self):
        question = "کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟"
        with patch.dict("os.environ", {"URDU_DEMO_ANSWERS_ENABLED": "true"}):
            result = asyncio.run(self.service.query(
                "user-a", ChatQueryRequest(question=question)
            ))
            history = asyncio.run(self.service.history("user-a", 0, 20))
            detail = asyncio.run(self.service.conversation(
                "user-a", result["conversation_id"], 0, 20
            ))
        self.assertEqual(self.pipeline_calls, [])
        self.assertEqual(result["answer"], detail["messages"][0]["answer"])
        self.assertNotIn(demo.DEMO_LABEL, result["answer"])
        self.assertNotIn(demo.DEMO_LABEL, detail["messages"][0]["answer"])
        saved = self.repo.get_for_user("user-a", result["conversation_id"])
        self.assertEqual(saved["messages"][0]["status"], "urdu_demo")
        self.assertEqual(saved["messages"][0]["citations"], result["citations"])
        self.assertEqual(history[0]["message_count"], 1)

    def test_old_saved_demo_marker_is_hidden_from_conversation_detail(self):
        question = "کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟"
        old = f"{demo.DEMO_LABEL}\n\nCurated response."
        self.repo.rows["conversation-1"] = {
            "_id": "conversation-1", "owner_id": "user-a", "crop": "cotton",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00", "message_count": 1,
            "messages": [{"question": question, "answer": old, "status": "urdu_demo",
                          "citations": []}],
        }
        detail = asyncio.run(self.service.conversation("user-a", "conversation-1", 0, 20))
        self.assertEqual(detail["messages"][0]["answer"], "Curated response.")


if __name__ == "__main__":
    unittest.main()
