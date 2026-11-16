from fastapi import HTTPException, Request
from pymongo.errors import PyMongoError

from backend.services.chat_service import ChatServiceError, ConversationNotFound


async def query_controller(request: Request, payload, current_user):
    try:
        return await request.app.state.chat_service.query(
            current_user["user"]["_id"], payload
        )
    except ConversationNotFound:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    except (ChatServiceError, PyMongoError):
        raise HTTPException(status_code=503, detail="Chat service temporarily unavailable.")


async def history_controller(request: Request, current_user, offset, limit):
    try:
        items = await request.app.state.chat_service.history(
            current_user["user"]["_id"], offset, limit
        )
        return {"items": items, "offset": offset, "limit": limit}
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Chat service temporarily unavailable.")


async def conversation_controller(request: Request, current_user, conversation_id, offset, limit):
    try:
        return await request.app.state.chat_service.conversation(
            current_user["user"]["_id"], conversation_id, offset, limit
        )
    except ConversationNotFound:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Chat service temporarily unavailable.")
