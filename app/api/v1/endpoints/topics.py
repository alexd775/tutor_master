from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.models import Topic, Session as DBSession, User, Agent
from app.schemas.topic import TopicCreate, TopicUpdate, TopicResponse
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
        ).filter(DBSession.topic_id == topic.id).first()
        
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
    ).filter(DBSession.topic_id == topic.id).first()
    
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
    """Delete topic and its subtopics (admin only)."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)  # This will cascade delete subtopics
    db.commit()
    return {"message": "Topic deleted"} 