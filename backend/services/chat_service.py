import asyncio
from datetime import datetime, timezone

from rag.pipeline import answer_question
from rag.urdu_demo_answers import (
    lookup_urdu_demo_answer, strip_demo_label, urdu_demo_answers_enabled,
)


class ChatServiceError(Exception):
    pass


class ConversationNotFound(Exception):
    pass


class ChatService:
    def __init__(self, repository, pipeline=answer_question):
        self.repository = repository
        self.pipeline = pipeline

    async def query(self, owner_id, request):
        conversation = None
        if request.conversation_id:
            conversation = await asyncio.to_thread(
                self.repository.get_for_user, owner_id, request.conversation_id
            )
            if conversation is None:
                raise ConversationNotFound
            crop = request.crop or conversation["crop"]
        else:
            crop = request.crop or "cotton"

        demo_answer = (
            lookup_urdu_demo_answer(request.question)
            if urdu_demo_answers_enabled() else None
        )
        if demo_answer is not None:
            result = {
                "status": "urdu_demo",
                "answer": demo_answer["answer"],
                "citations": demo_answer["citations"],
            }
        else:
            try:
                result = await asyncio.to_thread(
                    self.pipeline, request.question, crop
                )
            except Exception as exc:
                raise ChatServiceError from exc

        if (not isinstance(result, dict) or not isinstance(result.get("answer"), str)
                or not isinstance(result.get("citations"), list)):
            raise ChatServiceError

        status = result.get("status", "ok")
        timestamp = datetime.now(timezone.utc)
        message = {
            "question": request.question,
            "answer": result["answer"],
            "citations": result["citations"],
            "status": status,
            "created_at": timestamp,
        }
        if conversation is None:
            saved = await asyncio.to_thread(
                self.repository.create, owner_id, request.question, result["answer"],
                result["citations"], status, crop,
            )
            conversation_id = str(saved["_id"])
        else:
            appended = await asyncio.to_thread(
                self.repository.append_message, owner_id,
                request.conversation_id, message, crop,
            )
            if not appended:
                raise ConversationNotFound
            conversation_id = request.conversation_id

        return {
            "conversation_id": conversation_id,
            "answer": result["answer"],
            "citations": result["citations"],
        }

    async def history(self, owner_id, offset, limit):
        return await asyncio.to_thread(self.repository.list_for_user, owner_id, offset, limit)

    async def conversation(self, owner_id, conversation_id, offset, limit):
        result = await asyncio.to_thread(
            self.repository.get_for_user, owner_id, conversation_id
        )
        if result is None:
            raise ConversationNotFound
        messages = [dict(message) for message in result["messages"][offset:offset + limit]]
        for message in messages:
            if message.get("status") == "urdu_demo":
                message["answer"] = strip_demo_label(message["answer"])
        return {
            "conversation_id": result["conversation_id"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
            "messages": messages,
            "total_messages": result["message_count"],
            "offset": offset,
            "limit": limit,
        }
