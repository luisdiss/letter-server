from pydantic import BaseModel
from typing import Protocol


class SendMessageData(BaseModel):
    conversation_id: int | None
    recipient_username: str
    content: str
    sent_at: int
    expiration: int | None


class Message(Protocol):
    message_id: int 
    conversation_id: int
    sender_id: int
    content: str     
    sent_at: str    
    expiration: int | None


class LoginCreds(BaseModel):
    username: str
    password: str
