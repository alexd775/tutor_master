from typing import Annotated, List
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import User, Invite
from app.schemas.invite import InviteCreate, InviteResponse, InviteList
from app.core.config import settings

router = APIRouter()

def generate_invite_code() -> str:
    """Generate a random invite code."""
    return secrets.token_urlsafe(8)

@router.post("", response_model=List[InviteResponse])
async def create_invites(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    invite_in: InviteCreate
) -> List[Invite]:
    """Generate new invite codes (admin only)."""
    if not settings.REQUIRE_INVITE:
        raise HTTPException(
            status_code=400,
            detail="Invite system is disabled"
        )
        
    invites = []
    for _ in range(invite_in.count):
        invite = Invite(
            id=str(uuid.uuid4()),
            code=generate_invite_code(),
            created_by_id=current_user.id
        )
        invites.append(invite)
    
    db.add_all(invites)
    db.commit()
    for invite in invites:
        db.refresh(invite)
    
    return invites

@router.get("", response_model=InviteList)
async def list_invites(
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    unused: bool = False,
    skip: int = 0,
    limit: int = 100
) -> dict:
    """List all invite codes (admin only)."""
    if not settings.REQUIRE_INVITE:
        raise HTTPException(
            status_code=400,
            detail="Invite system is disabled"
        )
        
    # Base query
    query = db.query(Invite)
    if unused:
        query = query.filter(Invite.used_by_id == None)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    invites = query.order_by(Invite.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
        
    return {
        "items": invites,
        "total": total
    } 
