from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.models import Topic, Session as DBSession, User, Agent, ChatMessage
from app.schemas.topic import TopicCreate, TopicUpdate, TopicResponse
from app.schemas.session import SessionResponse
from app.services.ai import AIService
import uuid

router = APIRouter()

@router.post("", response_model=TopicResponse)
async def create_topic(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    topic_in: TopicCreate
) -> Topic:
    """Create new topic (admin only)."""
    if topic_in.parent_id:
        parent = db.query(Topic).filter(Topic.id == topic_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent topic not found")
    
    agent = db.query(Agent).filter(Agent.id == topic_in.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not agent.is_active:
        raise HTTPException(status_code=400, detail="Agent is not active")
    
    db_topic = Topic(
        id=str(uuid.uuid4()),
        **topic_in.model_dump()
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.get("", response_model=List[TopicResponse])
async def list_topics(
    db: Annotated[Session, Depends(deps.get_db)],
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    parent_id: Optional[str] = None
) -> List[Topic]:
    """List topics with optional parent filter."""
    query = db.query(Topic)
    
    if parent_id is not None:
        query = query.filter(Topic.parent_id == parent_id)
    else:
        # Root topics only
        query = query.filter(Topic.parent_id.is_(None))
    
    topics = query.offset(skip).limit(limit).all()
    
    # Attach computed stats
    for topic in topics:
        # Get subtopic count
        subtopic_count = db.query(func.count(Topic.id))\
            .filter(Topic.parent_id == topic.id)\
            .scalar()
        
        # Get session stats
        session_stats = db.query(
            func.count(DBSession.id),
            func.avg(DBSession.completion_rate)
        ).filter(DBSession.topic_id == topic.id, DBSession.is_active == True).first()
        
        setattr(topic, 'subtopic_count', subtopic_count or 0)
        setattr(topic, 'total_sessions', session_stats[0] or 0)
        setattr(topic, 'average_completion_rate', float(session_stats[1] or 0))
    
    return topics

@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: str,
    db: Annotated[Session, Depends(deps.get_db)]
) -> Topic:
    """Get topic by ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Attach computed stats
    subtopic_count = db.query(func.count(Topic.id))\
        .filter(Topic.parent_id == topic.id)\
        .scalar()
    
    session_stats = db.query(
        func.count(DBSession.id),
        func.avg(DBSession.completion_rate)
    ).filter(DBSession.topic_id == topic.id, DBSession.is_active == True).first()
    
    setattr(topic, 'subtopic_count', subtopic_count or 0)
    setattr(topic, 'total_sessions', session_stats[0] or 0)
    setattr(topic, 'average_completion_rate', float(session_stats[1] or 0))
    
    return topic

@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    topic_id: str,
    topic_in: TopicUpdate
) -> Topic:
    """Update topic (admin only)."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for key, value in topic_in.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    
    db.commit()
    db.refresh(topic)
    return topic

@router.delete("/{topic_id}")
async def delete_topic(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    topic_id: str
):
    """Delete topic and all related data (admin only)."""
    try:
        # Start a nested transaction
        with db.begin_nested():
            # Get the topic and all its subtopics
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")
            
            # Get all subtopic IDs recursively
            def get_subtopic_ids(topic_id: str, ids=None) -> set:
                if ids is None:
                    ids = set()
                ids.add(topic_id)
                subtopics = db.query(Topic).filter(Topic.parent_id == topic_id).all()
                for subtopic in subtopics:
                    get_subtopic_ids(subtopic.id, ids)
                return ids
            
            topic_ids = get_subtopic_ids(topic_id)
            
            # Get all session IDs for these topics
            session_ids = [
                id[0] for id in 
                db.query(DBSession.id)
                .filter(DBSession.topic_id.in_(topic_ids))
                .all()
            ]
            
            if not session_ids:
                session_ids = []  # Ensure it's an empty list for the IN clause
            
            # Delete all chat messages for these sessions
            deleted_messages = db.query(ChatMessage)\
                .filter(ChatMessage.session_id.in_(session_ids))\
                .delete(synchronize_session=False)
            
            # Delete all sessions
            deleted_sessions = db.query(DBSession)\
                .filter(DBSession.topic_id.in_(topic_ids))\
                .delete(synchronize_session=False)
            
            # Delete all topics
            deleted_topics = db.query(Topic)\
                .filter(Topic.id.in_(topic_ids))\
                .delete(synchronize_session=False)
            
            result = {
                "message": "Topic deleted",
                "deleted_topics": deleted_topics,
                "deleted_sessions": deleted_sessions,
                "deleted_messages": deleted_messages
            }
            
        # If we get here, the nested transaction was successful
        # Commit the outer transaction
        db.commit()
        return result
        
    except Exception as e:
        # Rollback in case of any error
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete topic: {str(e)}"
        )

@router.get("/{topic_id}/session", response_model=SessionResponse)
async def get_or_create_session(
    *,
    topic_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> DBSession:
    """Get latest session for topic or create new one."""
    # First check if topic exists
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check for existing session
    existing_session = db.query(DBSession)\
        .filter(
            DBSession.user_id == current_user.id,
            DBSession.topic_id == topic_id,
            DBSession.is_active == True
        )\
        .order_by(DBSession.created_at.desc())\
        .first()
    
    if existing_session:
        # Add topic title for response
        setattr(existing_session, 'topic_title', topic.title)
        return existing_session
    
    # Create new session
    new_session = DBSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        topic_id=topic_id,
        agent_id=topic.agent_id,
        completion_rate=0.0,
        duration=0,
        interaction_data={}
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # Initialize AI chat for new session
    ai_service = AIService(db)
    await ai_service.initialize_session(new_session)
    
    # Add topic title for response
    setattr(new_session, 'topic_title', topic.title)
    return new_session 