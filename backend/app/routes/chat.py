"""Chat API endpoints for the CarePlus agent."""

import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.core import create_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return the agent's response.

    Parameters
    ----------
    request : ChatRequest
        The incoming chat message with session_id.

    Returns
    -------
    ChatResponse
        The agent's response message.
    """
    agent = create_agent(session_id=request.session_id)
    response = agent.run(request.message)

    response_text = response.content if response and response.content else "I'm sorry, I couldn't process that request. How can I help you?"

    return ChatResponse(
        message=response_text,
        session_id=request.session_id,
    )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Process a chat message and stream the agent's response.

    Parameters
    ----------
    request : ChatRequest
        The incoming chat message with session_id.

    Returns
    -------
    StreamingResponse
        Server-sent events stream of the agent's response.
    """
    agent = create_agent(session_id=request.session_id)

    def generate():
        response = agent.run(request.message, stream=True)
        for chunk in response:
            if chunk and chunk.content:
                yield f"data: {chunk.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chat/session")
def new_session() -> dict:
    """Generate a new session ID for starting a fresh conversation.

    Returns
    -------
    dict
        A new unique session identifier.
    """
    return {"session_id": str(uuid.uuid4())}
