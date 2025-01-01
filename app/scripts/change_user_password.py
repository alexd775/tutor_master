import sys
import os
from pathlib import Path
# Add the parent directory to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def change_user_password(db: Session) -> None:
    """Change the password for a user."""
    email = os.getenv("USER_EMAIL", "admin@example.com")
    password = os.getenv("USER_PASSWORD", "admin")
    if not email or not password:
        print("⚠️  USER_EMAIL and USER_PASSWORD must be set in the environment.")
        return
    
    user = db.query(User).filter(User.email == email).first()
    user.hashed_password = get_password_hash(password)
    db.commit()
    db.close()
    print(f"Password for user {email} has been changed to {password}")

if __name__ == "__main__":
    db = SessionLocal()
    change_user_password(db)
    db.close()

