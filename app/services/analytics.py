from datetime import datetime, UTC
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Session as DBSession, ChatMessage

async def update_session_analytics(db: Session, session_id: str) -> None:
    """Update session analytics in background."""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        messages_count = db.query(func.count(ChatMessage.id))\
            .filter(ChatMessage.session_id == session_id)\
            .scalar()
        
        session.interaction_data = {
            **(session.interaction_data or {}),
            "total_messages": messages_count,
            "last_updated": datetime.now(UTC).isoformat()
        }
        db.commit() 