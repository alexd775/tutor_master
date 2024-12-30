import uuid
from typing import Annotated, List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api import deps
from app.models import Session as DBSession, Topic, User
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse
from app.services.ai import AIService


router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(
    *,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    session_in: SessionCreate
) -> DBSession:
    """Create a new learning session."""
    # Check for existing incomplete session
    existing_session = db.query(DBSession).filter(
        DBSession.user_id == current_user.id,
        DBSession.topic_id == session_in.topic_id,
        DBSession.completion_rate < 1.0  # Consider sessions with < 100% completion as active
    ).first()
    
    if existing_session:
            detail={
                "message": "Active session already exists for this topic",
                "session_id": existing_session.id,
                "completion_rate": existing_session.completion_rate
            }
            raise HTTPException(status_code=400, detail=detail)
    
    # Get topic and its agent
    topic = db.query(Topic).filter(Topic.id == session_in.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if not topic.agent_id:
        raise HTTPException(
            status_code=400,
            detail="Topic has no associated AI agent"
        )
    
    # Create session with topic's agent
    db_session = DBSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        agent_id=topic.agent_id,  # Set agent from topic
        **session_in.model_dump()
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Initialize AI chat
    ai_service = AIService(db)
    await ai_service.initialize_session(db_session)
    
    return db_session

@router.get("/me", response_model=List[SessionResponse])
async def list_user_sessions(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    topic_id: Optional[str] = None
) -> List[DBSession]:
    """List current user's learning sessions."""
    query = db.query(DBSession)
    query = query.filter(DBSession.user_id == current_user.id)
    query = query.filter(DBSession.is_active == True)

    if topic_id:
        query = query.filter(DBSession.topic_id == topic_id)
    
    sessions = query.order_by(desc(DBSession.created_at)).offset(skip).limit(limit).all()
    
    # Add topic titles
    topic_ids = [s.topic_id for s in sessions]
    topics = {t.id: t.title for t in db.query(Topic).filter(Topic.id.in_(topic_ids))}
    
    for session in sessions:
        setattr(session, 'topic_title', topics.get(session.topic_id, ""))
    
    return sessions

@router.get("/all", response_model=List[SessionResponse])
async def list_all_sessions(
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    user_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100)
) -> List[DBSession]:
    """
    List all sessions with optional filters (admin only).
    Sessions are ordered by creation date (newest first).
    """
    query = db.query(DBSession)
    
    # Apply filters
    if user_id:
        query = query.filter(DBSession.user_id == user_id)
    if topic_id:
        query = query.filter(DBSession.topic_id == topic_id)
    
    # Add topic titles and user names
    query = query\
        .join(Topic)\
        .join(User, DBSession.user_id == User.id)\
        .add_columns(
            Topic.title.label('topic_title'),
            User.full_name.label('user_full_name')
        )\
        .order_by(DBSession.created_at.desc())\
        .offset(skip)\
        .limit(limit)
    
    sessions = []
    for session, topic_title, user_full_name in query.all():
        setattr(session, 'topic_title', topic_title)
        setattr(session, 'user_full_name', user_full_name)
        sessions.append(session)
    
    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> DBSession:
    """Get specific session by ID."""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id,
        DBSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add topic title
    topic = db.query(Topic).filter(Topic.id == session.topic_id).first()
    setattr(session, 'topic_title', topic.title if topic else "")
    
    return session

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    *,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    session_id: str,
    session_in: SessionUpdate
) -> DBSession:
    """Update session progress and feedback."""
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id,
        DBSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session fields
    for key, value in session_in.model_dump(exclude_unset=True).items():
        if key == "interaction_data" and value and session.interaction_data:
            # Merge interaction data instead of replacing
            session.interaction_data.update(value)
        else:
            setattr(session, key, value)
    
    db.commit()
    db.refresh(session)
    
    # Add topic title
    topic = db.query(Topic).filter(Topic.id == session.topic_id).first()
    setattr(session, 'topic_title', topic.title if topic else "")
    
    return session

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_session_stats(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> dict:
    """Get user's session statistics summary."""
    from sqlalchemy import func
    
    # Get total time spent
    total_duration = db.query(func.sum(DBSession.duration))\
        .filter(DBSession.user_id == current_user.id)\
        .scalar() or 0
    
    # Get average completion rate
    avg_completion = db.query(func.avg(DBSession.completion_rate))\
        .filter(DBSession.user_id == current_user.id)\
        .scalar() or 0
    
    # Get topics completed
    completed_topics = db.query(func.count(DBSession.topic_id.distinct()))\
        .filter(
            DBSession.user_id == current_user.id,
            DBSession.completion_rate >= 0.8
        ).scalar() or 0
    
    # Get recent activity
    recent_sessions = db.query(
        DBSession.created_at,
        Topic.title,
        DBSession.completion_rate
    ).join(Topic)\
        .filter(DBSession.user_id == current_user.id)\
        .order_by(desc(DBSession.created_at))\
        .limit(5)\
        .all()
    
    return {
        "total_duration_minutes": total_duration,
        "average_completion_rate": float(avg_completion),
        "completed_topics": completed_topics,
        "recent_activity": [
            {
                "date": session.created_at,
                "topic": session.title,
                "completion": session.completion_rate
            }
            for session in recent_sessions
        ]
    } 

@router.post("/{session_id}/disable", response_model=SessionResponse)
async def disable_and_create_session(
    *,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    session_id: str
) -> DBSession:
    """
    Disable current session and create a new one with the same settings.
    Useful when user wants to restart a session.
    """
    # Get current session
    current_session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id,
        DBSession.is_active == True
    ).first()
    
    if not current_session:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    try:
        # Disable current session
        current_session.is_active = False
        db.add(current_session)
        
        # Create new session with same settings
        new_session = DBSession(
            id=str(uuid.uuid4()),
            user_id=current_session.user_id,
            topic_id=current_session.topic_id,
            agent_id=current_session.agent_id,
            completion_rate=0.0,  # Reset progress
            duration=0,  # Reset duration
            interaction_data={},  # Fresh interaction data
            is_active=True
        )
        
        db.add(new_session)
        db.flush()  # Ensure new session is created before initializing AI
        
        # Initialize AI chat for new session
        ai_service = AIService(db)
        await ai_service.initialize_session(new_session)
        
        # Add topic title for response
        topic = db.query(Topic).filter(Topic.id == new_session.topic_id).first()
        setattr(new_session, 'topic_title', topic.title if topic else "")
        
        # Commit the transaction
        db.commit()
        return new_session
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable and create session: {str(e)}"
        ) 
