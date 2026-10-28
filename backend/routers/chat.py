"""Chat endpoints backed by the Gemini AI agent."""

from fastapi import APIRouter, HTTPException

from agent import ask_agent
from conversation_store import conversation_store
from schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreateResponse,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "/session",
    response_model=SessionCreateResponse,
    summary="Create a new chat session",
)
def create_chat_session():
    session_id = conversation_store.create_session()
    return SessionCreateResponse(session_id=session_id)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message to the GovScheme AI agent",
)
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        session_id, chat_session = conversation_store.get_or_create(
            request.session_id
        )
        reply, chat_session = ask_agent(chat_session, message)
        conversation_store.replace_chat(session_id, chat_session)
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Agent request failed: {error}",
        ) from error

    return ChatResponse(
        session_id=session_id,
        message=message,
        reply=reply,
    )


@router.delete(
    "/session/{session_id}",
    summary="Delete a chat session",
)
def delete_chat_session(session_id: str):
    deleted = conversation_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "session_id": session_id}
