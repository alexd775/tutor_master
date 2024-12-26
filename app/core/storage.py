from typing import Optional, BinaryIO
from pathlib import Path
import boto3
import os
from fastapi import UploadFile
from botocore.exceptions import ClientError
from app.core.config import settings
import aiofiles
import mimetypes
import uuid

class FileStorage:
    """Abstract base class for file storage."""
    
    async def upload_file(self, file: UploadFile, folder: str) -> str:
        """Upload a file and return its URL."""
        raise NotImplementedError
    
    async def get_file(self, file_path: str) -> Optional[tuple[BinaryIO, str]]:
        """Get file and its mime type."""
        raise NotImplementedError
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        raise NotImplementedError

class LocalFileStorage(FileStorage):
    """Local file storage implementation."""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile, folder: str) -> str:
        """Save file to local storage."""
        ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        folder_path = self.upload_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return str(Path(folder) / filename)
    
    async def get_file(self, file_path: str) -> Optional[tuple[BinaryIO, str]]:
        """Get file from local storage."""
        full_path = self.upload_dir / file_path
        if not full_path.exists():
            return None
        
        mime_type, _ = mimetypes.guess_type(str(full_path))
        return (open(full_path, 'rb'), mime_type or 'application/octet-stream')
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        full_path = self.upload_dir / file_path
        try:
            full_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False

class S3FileStorage(FileStorage):
    """S3 file storage implementation."""
    
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET
    
    async def upload_file(self, file: UploadFile, folder: str) -> str:
        """Upload file to S3."""
        ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        s3_path = f"{folder}/{filename}"
        
        content = await file.read()
        self.s3.put_object(
            Bucket=self.bucket,
            Key=s3_path,
            Body=content,
            ContentType=file.content_type
        )
        
        return s3_path
    
    async def get_file(self, file_path: str) -> Optional[tuple[BinaryIO, str]]:
        """Get file from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=file_path)
            return (response['Body'], response.get('ContentType', 'application/octet-stream'))
        except ClientError:
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError:
            return False

# Factory function to get the appropriate storage backend
def get_storage() -> FileStorage:
    """Get storage backend based on configuration."""
    if settings.STORAGE_BACKEND == "s3":
        return S3FileStorage()
    return LocalFileStorage() 