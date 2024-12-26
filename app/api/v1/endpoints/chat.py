from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.models import User, Session as DBSession, ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatHistoryResponse
from app.services.ai import AIService
from app.services.analytics import update_session_analytics

router = APIRouter()

@router.post("/sessions/{session_id}/chat", response_model=ChatMessageResponse)
async def send_message(
    *,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    session_id: str,
    message: ChatMessageCreate,
    background_tasks: BackgroundTasks
) -> ChatMessageResponse:
    """Send a message to the AI agent."""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    ai_service = AIService(db)
    response = await ai_service.process_message(session, message.content)
    
    # Update analytics in background
    background_tasks.add_task(update_session_analytics, db, session.id)
    
    return response

@router.get("/sessions/{session_id}/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    skip: int = 0,
    limit: int = 50
) -> dict:
    """Get chat history for a session."""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    total = db.query(func.count(ChatMessage.id))\
        .filter(ChatMessage.session_id == session_id)\
        .scalar()
    
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.session_id == session_id)\
        .order_by(ChatMessage.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return {
        "messages": list(reversed(messages)),
        "has_more": total > skip + limit,
        "total_messages": total
    } 