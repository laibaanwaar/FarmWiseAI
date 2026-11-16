from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    crop: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if not isinstance(value, str) or not value:
            raise ValueError("Question cannot be blank.")
        return value

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, value):
        if value is not None:
            from bson import ObjectId
            value = value.strip()
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid conversation ID.")
        return value

    @field_validator("crop")
    @classmethod
    def normalize_crop(cls, value):
        if value is None:
            return None
        value = value.strip().lower()
        if not value:
            raise ValueError("Crop cannot be blank.")
        return value


class CitationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_title: str
    pdf_page: int
    printed_page: int | None = None


class ChatQueryResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[CitationResponse]


class ConversationSummary(BaseModel):
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    items: list[ConversationSummary]
    offset: int
    limit: int


class ConversationMessage(BaseModel):
    question: str
    answer: str
    status: str
    citations: list[CitationResponse]
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessage]
    total_messages: int
    offset: int
    limit: int
