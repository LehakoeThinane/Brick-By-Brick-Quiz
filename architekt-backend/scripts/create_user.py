"""One-time script to create a user account directly in the database."""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select

EMAIL = "lehakoe.thinane@gmail.com"
PASSWORD = "020890SL"
DISPLAY_NAME = "Lehakoe"

def main():
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == EMAIL))
        if existing:
            print(f"User {EMAIL} already exists (id={existing.id})")
            return

        user = User(
            id=uuid.uuid4(),
            email=EMAIL,
            hashed_password=hash_password(PASSWORD),
            display_name=DISPLAY_NAME,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_active_at=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.email} (id={user.id})")
    finally:
        db.close()

if __name__ == "__main__":
    main()
