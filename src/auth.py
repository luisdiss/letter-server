import secrets
from sqlalchemy.orm import Session
from sqlalchemy import text


def authorise(auth_token: str, db: Session) -> int | None:
    """Takes a token and returns the user_id if the authentication token is valid"""
    return db.execute(text(f"SELECT user_id FROM sessions WHERE session_token = :auth_token"), {"auth_token": auth_token.split(" ")[1]}).scalar()


def create_session(user_id: int, db: Session) -> str:
    """Creates a new session token for the user"""
    token = secrets.token_hex(16)
    db.execute(text("INSERT INTO sessions VALUES (:session_token, :user_id) ON CONFLICT (user_id) DO UPDATE SET session_token = :session_token"), {"session_token": token, "user_id": user_id})  
    db.commit()
    return token
