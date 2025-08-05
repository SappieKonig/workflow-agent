#!/usr/bin/env python3
import uuid
import bcrypt
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DB_PATH = Path(__file__).parent / "auth_tokens.db"
Base = declarative_base()


class AuthToken(Base):
    __tablename__ = 'auth_tokens'
    
    id = Column(Integer, primary_key=True)
    token_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)
    
    @property
    def is_active(self) -> bool:
        """Check if token is active (not revoked)."""
        return self.revoked_at is None
    
    def revoke(self) -> None:
        """Mark this token as revoked."""
        self.revoked_at = datetime.utcnow()


def get_engine():
    """Get SQLAlchemy engine."""
    return create_engine(f"sqlite:///{DB_PATH}")


def get_session() -> Session:
    """Get SQLAlchemy session."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def init_db():
    """Initialize the database with the auth_tokens table."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def add_token(description: Optional[str] = None) -> Tuple[str, int]:
    """Generate a new token, store its hash, and return the plaintext token."""
    # Generate a new UUID token
    token = str(uuid.uuid4())
    
    # Hash the token
    token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt())
    
    # Store in database
    with get_session() as session:
        auth_token = AuthToken(
            token_hash=token_hash.decode('utf-8'),
            description=description
        )
        session.add(auth_token)
        session.commit()
        session.refresh(auth_token)
        
        return token, auth_token.id


def list_tokens():
    """List all tokens with their metadata."""
    with get_session() as session:
        tokens = session.query(AuthToken).order_by(AuthToken.created_at.desc()).all()
        return [(t.id, t.created_at, t.description, t.revoked_at) for t in tokens]


def revoke_token(token_id: int) -> bool:
    """Revoke a token by ID."""
    with get_session() as session:
        token = session.query(AuthToken).filter(
            AuthToken.id == token_id,
            AuthToken.revoked_at.is_(None)
        ).first()
        
        if token:
            token.revoke()
            session.commit()
            return True
        return False


def check_token(token: str) -> bool:
    """Check if a token is valid."""
    with get_session() as session:
        active_tokens = session.query(AuthToken).filter(
            AuthToken.revoked_at.is_(None)
        ).all()
        
        for auth_token in active_tokens:
            if bcrypt.checkpw(token.encode('utf-8'), auth_token.token_hash.encode('utf-8')):
                return True
        
        return False


def main():
    # Initialize database
    init_db()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  uv run auth_cli.py add [description]    - Generate new token")
        print("  uv run auth_cli.py list                 - List all tokens")
        print("  uv run auth_cli.py revoke <token_id>    - Revoke a token")
        print("  uv run auth_cli.py check <token>        - Check if token is valid")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add":
        description = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        token, token_id = add_token(description)
        
        print("Generated new auth token:")
        print(f"Token: {token}")
        if description:
            print(f"Description: {description}")
        print(f"Token ID: {token_id}")
        print("\nToken saved. Share the token above with the user.")
        print("This is the only time the token will be shown.")
    
    elif command == "list":
        tokens = list_tokens()
        
        if not tokens:
            print("No tokens found.")
            return
        
        print(f"{'ID':<4} | {'Created At':<20} | {'Description':<30} | {'Status':<8}")
        print("-" * 70)
        
        for token_id, created_at, description, revoked_at in tokens:
            status = "Revoked" if revoked_at else "Active"
            desc = description or ""
            created = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{token_id:<4} | {created:<20} | {desc:<30} | {status:<8}")
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("Error: Please provide token ID to revoke")
            sys.exit(1)
        
        try:
            token_id = int(sys.argv[2])
        except ValueError:
            print("Error: Token ID must be a number")
            sys.exit(1)
        
        if revoke_token(token_id):
            print(f"Token {token_id} has been revoked.")
        else:
            print(f"Token {token_id} not found or already revoked.")
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Error: Please provide token to check")
            sys.exit(1)
        
        token = sys.argv[2]
        if check_token(token):
            print("Token is valid and active.")
        else:
            print("Token is invalid or revoked.")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()