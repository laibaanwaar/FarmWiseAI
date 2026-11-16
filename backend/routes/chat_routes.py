from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import StringConstraints

from backend.controllers.chat_controller import (
    conversation_controller, history_controller, query_controller,
)
from backend.dependencies.auth import get_current_user
from backend.serializers.chat_serializer import (
    ChatQueryRequest, ChatQueryResponse, ConversationDetailResponse,
    ConversationListResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])
ConversationId = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{24}$")]


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(
    request: Request,
    payload: ChatQueryRequest,
    current_user=Depends(get_current_user),
):
    return await query_controller(request, payload, current_user)


@router.get("/history", response_model=ConversationListResponse)
async def chat_history(
    request: Request,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user=Depends(get_current_user),
):
    return await history_controller(request, current_user, offset, limit)


@router.get("/history/{conversation_id}", response_model=ConversationDetailResponse)
async def chat_history_detail(
    request: Request,
    conversation_id: ConversationId = Path(),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user=Depends(get_current_user),
):
    return await conversation_controller(
        request, current_user, conversation_id, offset, limit
    )
