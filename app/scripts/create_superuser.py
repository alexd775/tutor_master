import sys
import os
from pathlib import Path
# Add the parent directory to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import uuid

def create_superuser(db: Session) -> None:
    """Create a superuser if it doesn't exist."""
    
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    
    # Check if admin already exists
    admin = db.query(User).filter(
        User.email == email
    ).first()
    
    if admin:
        print("⚠️  Superuser already exists, skipping creation.")
        return
    
    # Create superuser
    admin_user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=get_password_hash(password),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    try:
        db.add(admin_user)
        db.commit()
        print("✅ Superuser created successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("\n⚠️  Please change the password after first login!")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        db.rollback()

def main() -> None:
    """Main function to create superuser."""
    db = SessionLocal()
    try:
        create_superuser(db)
    finally:
        db.close()

if __name__ == "__main__":
    main() 