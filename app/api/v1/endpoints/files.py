from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api import deps
from app.core.storage import get_storage
from app.models import File as DBFile, User
from app.schemas.file import FileResponse, FileUpdate
from app.core.config import settings
import uuid
import os

router = APIRouter()
storage = get_storage()

def validate_file(file: UploadFile) -> None:
    """Validate file size and type."""
    # Check file size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/1024/1024}MB"
        )
    
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    topic_id: Optional[str] = None
) -> DBFile:
    """Upload a file with metadata (admin only)."""
    validate_file(file)
    
    # Upload file
    file_path = await storage.upload_file(file, "topics")
    
    # Create file record
    db_file = DBFile(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
        size=file.size,
        topic_id=topic_id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/{file_id}", response_class=StreamingResponse)
async def get_file(
    file_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)]
):
    """Get file content."""
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = await storage.get_file(db_file.file_path)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    return StreamingResponse(
        file_data[0],
        media_type=file_data[1],
        headers={
            "Content-Disposition": f'attachment; filename="{db_file.filename}"'
        }
    )

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)]
):
    """Delete file (admin only)."""
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from storage
    if not await storage.delete_file(db_file.file_path):
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")
    
    # Delete from database
    db.delete(db_file)
    db.commit()
    
    return {"message": "File deleted successfully"}

@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    *,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)],
    file_id: str,
    file_update: FileUpdate
) -> DBFile:
    """Update file metadata (admin only)."""
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update metadata
    for key, value in file_update.model_dump(exclude_unset=True).items():
        setattr(db_file, key, value)
    
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("", response_model=List[FileResponse])
async def list_files(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    topic_id: str,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100)
) -> List[DBFile]:
    """List files with optional filtering."""
    query = db.query(DBFile).filter(DBFile.topic_id == topic_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DBFile.title.ilike(search_term),
                DBFile.description.ilike(search_term),
                DBFile.filename.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all() 