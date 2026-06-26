"""Chat-related Pydantic schemas."""

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a chat message sender."""

    USER = "user"
    ASSISTANT = "assistant"


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""

    message: str = Field(..., min_length=1, description="The user's message text")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Session identifier for conversation continuity",
    )
    token: str | None = Field(
        default=None,
        description="Optional authentication token for logged-in sessions",
    )


class ChatResponse(BaseModel):
    """Chat response from the agent."""

    message: str = Field(..., description="The agent's response text")
    session_id: str = Field(..., description="Session identifier")
    role: MessageRole = MessageRole.ASSISTANT
