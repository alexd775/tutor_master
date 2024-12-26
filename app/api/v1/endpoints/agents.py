from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import User, Agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
import uuid

router = APIRouter()

@router.post("", response_model=AgentResponse)
async def create_agent(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    agent_in: AgentCreate
) -> Agent:
    """Create new AI agent (admin only)."""
    db_agent = Agent(
        id=str(uuid.uuid4()),
        **agent_in.model_dump()
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("", response_model=List[AgentResponse])
async def list_agents(
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    skip: int = 0,
    limit: int = 100
) -> List[Agent]:
    """List all AI agents (admin only)."""
    agents = db.query(Agent)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> Agent:
    """Get specific AI agent by ID (admin only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    agent_id: str,
    agent_in: AgentUpdate
) -> Agent:
    """Update AI agent (admin only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for key, value in agent_in.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
async def delete_agent(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    agent_id: str
):
    """Delete AI agent (admin only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted"} 