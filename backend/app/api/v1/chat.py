"""Chat with Characters API endpoints (M17)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.models.ai import CharacterListResponse, CharacterPublic
from app.models.chat import (
    ChatMessageRequest,
    ChatSessionCreate,
    ChatSessionListItem,
    ChatSessionPublic,
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _require_vip_max(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: require VIP Max tier."""
    if current_user.get("vip_tier") != "max":
        raise HTTPException(status_code=403, detail="VIP Max required")
    return current_user


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


@router.get("/novels/{novel_id}/characters", response_model=CharacterListResponse)
async def list_characters(novel_id: str) -> CharacterListResponse:
    """List all characters for a novel (public)."""
    characters = chat_service.get_characters(novel_id)
    return CharacterListResponse(
        items=[CharacterPublic(**c) for c in characters]
    )


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=ChatSessionPublic, status_code=201)
async def create_session(
    data: ChatSessionCreate,
    current_user: dict = Depends(_require_vip_max),
) -> ChatSessionPublic:
    """Create a new chat session for a character in a novel. VIP Max only."""
    session = chat_service.create_session(
        user_id=current_user["id"],
        novel_id=data.novel_id,
        character_id=data.character_id,
    )
    return ChatSessionPublic(**session)


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_sessions(
    novel_id: str = Query(..., description="Filter sessions by novel"),
    current_user: dict = Depends(get_current_user),
) -> list[ChatSessionListItem]:
    """List the current user's sessions for a given novel."""
    sessions = chat_service.list_sessions(
        user_id=current_user["id"],
        novel_id=novel_id,
    )
    return [ChatSessionListItem(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionPublic)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> ChatSessionPublic:
    """Fetch a chat session with full message history."""
    session = chat_service.get_session(
        session_id=session_id,
        user_id=current_user["id"],
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSessionPublic(**session)


# ---------------------------------------------------------------------------
# Messaging (streaming)
# ---------------------------------------------------------------------------


@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: str,
    data: ChatMessageRequest,
    current_user: dict = Depends(_require_vip_max),
) -> StreamingResponse:
    """Send a message and stream back the character's RAG-powered response.

    Returns a text/event-stream response with SSE chunks.
    Each chunk is "data: <token>\\n\\n".
    The final event is "data: [DONE]\\n\\n".
    On error: "data: [ERROR] <message>\\n\\n".
    """
    return StreamingResponse(
        chat_service.stream_message(
            session_id=session_id,
            user_id=current_user["id"],
            content=data.content,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering for streaming
        },
    )
