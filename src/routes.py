from fastapi import HTTPException, Depends, Path, Security, status, Response
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Annotated
import json

from database import get_db
from models import SendMessageData, LoginCreds
from auth import authorise, create_session
from dal import (
    select_user_id, select_password_hash, select_message_receipts,
    select_message, select_username, insert_message, insert_message_recipient,
    conversation_exists, insert_conversation, insert_user
)
from utils import (
    create_1to1_coversation_id, timestamp_to_datetime_str, datetime_obj_to_timestamp
)
from argon2 import PasswordHasher, exceptions

api_key_header = APIKeyHeader(name="Authorization", scheme_name="Authorization")
hasher = PasswordHasher(hash_len=16)


def get_routes(app):
    """Register routes with the FastAPI app"""
    
    @app.head("/users/{username}")
    async def check_username(username: Annotated[str, Path(pattern="^[a-zA-Z0-9]+$")], db: Session = Depends(get_db)):
        username = username.lower()
        user_id = select_user_id(db, username)   
        if user_id != None:
            return Response(status_code=status.HTTP_200_OK)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    @app.post("/login")
    async def login(creds: LoginCreds, db: Session = Depends(get_db)):
        username, password = creds.username, creds.password
        if len(username) > app.state.config["un_max_len"] or len(username) < app.state.config["un_min_len"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        elif len(password) > app.state.config["pw_max_len"] or len(password) < app.state.config["pw_min_len"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        user_id = select_user_id(db, username)
        if user_id == None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        stored_hash = select_password_hash(db, user_id)
        try:
            hasher.verify(stored_hash, password)
        except exceptions.VerifyMismatchError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        auth_token = create_session(user_id, db)
        return Response(status_code=status.HTTP_200_OK, content=json.dumps({"auth_token": auth_token}))

    @app.post("/users", status_code=status.HTTP_201_CREATED)
    async def register(creds: LoginCreds, db: Session = Depends(get_db)):
        username, password = creds.username, creds.password
        if len(username) > app.state.config["un_max_len"] or len(username) < app.state.config["un_min_len"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        if len(password) > app.state.config["pw_max_len"] or len(password) < app.state.config["pw_min_len"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        if select_user_id(db, username) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        insert_user(db, username, hasher.hash(password))
        return Response(status_code=status.HTTP_201_CREATED)

    @app.get("/messages")
    async def get_messages(auth_token: str = Security(api_key_header), db: Session = Depends(get_db)):
        sender_id = authorise(auth_token, db)
        if sender_id == None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        receipts = select_message_receipts(db, sender_id)

        messages = []
        for receipt in receipts:
            message = select_message(db, receipt.message_id)
            sender_username = select_username(db, message.sender_id)
            messages.append({"conversation_id": message.conversation_id, 
                             "author": sender_username, 
                             "content": message.content,
                             "sent_at": datetime_obj_to_timestamp(message.sent_at), 
                             "expiration": message.expiration}
                        )

        return Response(content=json.dumps(messages), status_code=status.HTTP_200_OK)

    @app.post("/messages")
    async def send_message(message: SendMessageData, auth_token: str = Security(api_key_header), db: Session = Depends(get_db)):
        sender_id = authorise(auth_token, db)
        if sender_id == None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        recipient_user_id = select_user_id(db, message.recipient_username)
        if recipient_user_id == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        dt_str = timestamp_to_datetime_str(message.sent_at)
        if message.conversation_id == None:
            conversation_id = create_1to1_coversation_id(sender_id, recipient_user_id)
            exists = conversation_exists(db, conversation_id)
            if not exists:
                insert_conversation(db, conversation_id)
            return_data = json.dumps({"conversation_id": conversation_id})
        else:
            conversation_id = message.conversation_id
            return_data = json.dumps({})

        message_id = insert_message(db, conversation_id, sender_id, message.content, dt_str, message.expiration)
        insert_message_recipient(db, message_id, recipient_user_id)
        return Response(status_code=status.HTTP_200_OK, content=return_data)
