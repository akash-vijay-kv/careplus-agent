"""Chat API endpoints for the CarePlus agent."""

import asyncio
import uuid
from functools import partial

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.core import create_agent
from app.database import SessionLocal
from app.routes.auth import decode_token
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

FALLBACK_RESPONSE = (
    "I'm sorry, I couldn't process that request. How can I help you?"
)


def _extract_user_id(token: str | None) -> int | None:
    """Extract user_id from an authentication token.

    Parameters
    ----------
    token : str | None
        The base64-encoded auth token, or None for guest sessions.

    Returns
    -------
    int | None
        The user_id if token is valid, None otherwise.
    """
    if not token:
        return None
    payload = decode_token(token)
    if payload and "user_id" in payload:
        return payload["user_id"]
    return None


def _run_agent_sync(message: str, session_id: str, user_id: int | None) -> str:
    """Run the agent synchronously inside a dedicated DB session.

    Opens and closes its own ``SessionLocal`` so the connection is
    returned to the pool as soon as the agent finishes.

    Parameters
    ----------
    message : str
        The user's chat message.
    session_id : str
        Conversation session identifier.
    user_id : int | None
        Authenticated user ID or None for guests.

    Returns
    -------
    str
        The agent's response text.
    """
    db_session = SessionLocal()
    try:
        agent = create_agent(
            db_session=db_session,
            session_id=session_id,
            user_id=user_id,
        )
        response = agent.run(message)
        if response and response.content:
            return response.content
        return FALLBACK_RESPONSE
    finally:
        db_session.close()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return the agent's response.

    Runs the blocking agent call in a thread-pool executor so the
    async event loop stays free for other requests.

    Parameters
    ----------
    request : ChatRequest
        The incoming chat message with session_id and optional token.

    Returns
    -------
    ChatResponse
        The agent's response message.
    """
    user_id = _extract_user_id(request.token)

    loop = asyncio.get_running_loop()
    response_text = await loop.run_in_executor(
        None,
        partial(_run_agent_sync, request.message, request.session_id, user_id),
    )

    return ChatResponse(
        message=response_text,
        session_id=request.session_id,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Process a chat message and stream the agent's response.

    Parameters
    ----------
    request : ChatRequest
        The incoming chat message with session_id and optional token.

    Returns
    -------
    StreamingResponse
        Server-sent events stream of the agent's response.
    """
    user_id = _extract_user_id(request.token)

    def generate():
        db_session = SessionLocal()
        try:
            agent = create_agent(
                db_session=db_session,
                session_id=request.session_id,
                user_id=user_id,
            )
            response = agent.run(request.message, stream=True)
            for chunk in response:
                if chunk and chunk.content:
                    yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            db_session.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chat/session")
async def new_session() -> dict:
    """Generate a new session ID for starting a fresh conversation.

    Returns
    -------
    dict
        A new unique session identifier.
    """
    return {"session_id": str(uuid.uuid4())}
