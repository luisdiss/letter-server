from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from models import Message


def insert_message_recipient(db: Session, message_id: int, recipient_user_id: int):
    """Insert a message recipient record"""
    db.execute(text("INSERT INTO message_recipients VALUES (:message_id, :recipient_id, :is_read)"), {"message_id": message_id, "recipient_id": recipient_user_id, "is_read": "FALSE"})
    db.commit()


def insert_message(db: Session, conversation_id: int, sender_id: int, content: str, sent_at: str, expiration: int | None) -> int:
    """Insert a message and return the message_id"""
    return db.execute(text("INSERT INTO messages (conversation_id, sender_id, content, sent_at, expiration) VALUES (:conversation_id, :sender_id, :content, :sent_at, :expiration) RETURNING message_id"), {"conversation_id": conversation_id, "sender_id": sender_id, "content": content, "sent_at": sent_at, "expiration": expiration}).scalar()


def insert_conversation(db: Session, conversation_id):
    """Insert a new conversation"""
    db.execute(text("INSERT INTO conversations VALUES (:conversation_id, :subject, :created_at)"), {"conversation_id": conversation_id, "subject": "NULL", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    db.commit()


def conversation_exists(db: Session, conversation_id: int) -> bool:
    """Check if a conversation exists"""
    if db.execute(text(f"SELECT conversation_id FROM conversations WHERE conversation_id = {conversation_id}")).scalar() == None:
        return False
    return True


def select_user_id(db: Session, username: str) -> int | None:
    """Get user_id by username"""
    return db.execute(text("SELECT user_id FROM users WHERE username = :username"), {"username": username}).scalar()


def select_username(db: Session, user_id: int) -> str | None:
    """Get username by user_id"""
    return db.execute(text("SELECT username FROM users WHERE user_id = :user_id"), {"user_id": user_id}).scalar()


def select_message(db: Session, message_id: int) -> Message | None:
    """Get message by message_id"""
    return db.execute(text("SELECT * FROM messages WHERE message_id = :message_id"), {"message_id": message_id}).fetchall()[0]


def select_message_receipts(db: Session, sender_id) -> list:
    """Get and mark message receipts as read"""
    receipts = db.execute(text("UPDATE message_recipients SET is_read = TRUE WHERE recipient_id = :sender_id AND is_read = FALSE RETURNING *"), {"sender_id": sender_id}).fetchall()
    db.commit()
    return receipts


def select_password_hash(db: Session, user_id) -> str:
    """Get password hash by user_id"""
    return db.execute(text("SELECT password_hash FROM users WHERE user_id = :user_id"), {"user_id": user_id}).scalar()


def insert_user(db: Session, username: str, password_hash: str) -> None:
    db.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"), {"username": username, "password_hash": password_hash})
    db.commit()
