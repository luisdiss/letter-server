from fastapi import FastAPI, Response, HTTPException, Depends, Path, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import Annotated, Protocol
from pathlib import Path
from pydantic import BaseModel
import json
import hashlib
import uvicorn
import ssl
from database import get_db
from argon2 import PasswordHasher, exceptions
import secrets
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with open("config.json", "r") as file:
            app.state.config = json.load(file)
    except Exception as e:
        raise RuntimeError(f"Preprocessing failed: {e}")
    yield

app = FastAPI(lifespan=lifespan)
api_key_header = APIKeyHeader(name="Authorization", scheme_name="Authorization")
hasher = PasswordHasher(hash_len=16)

# --------------------------- protocols ---------------------------

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
    username:str
    password:str

# --------------------------- route functions ---------------------------

#route function for checking if a user with given username exists
@app.head("/users/{username}")
async def check_username(username: Annotated[str, Path(pattern = "^[a-zA-Z0-9]+$")], db: Session = Depends(get_db)):
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
    return Response(status_code=status.HTTP_200_OK, content=json.dumps({"auth_token":auth_token}))

#route function to handle the retrieval of all messages for a given user
@app.get("/messages")
async def get_messages(auth_token: str = Security(api_key_header), db: Session = Depends(get_db)):
    sender_id = authorise(auth_token, db)
    if sender_id == None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,)
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

#route function to handle storing of user messages ready for retrieval
@app.post("/messages")
async def send_message(message: SendMessageData, auth_token: str = Security(api_key_header), db: Session = Depends(get_db)):
    sender_id = authorise(auth_token, db)
    if sender_id == None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
    
    #check that recipient exists
    recipient_user_id = select_user_id(db, message.recipient_username)
    if recipient_user_id == None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )

    #create conversation_id if not sent and return it
    dt_str = timestamp_to_datetime_str(message.sent_at)
    if message.conversation_id == None:
        conversation_id = create_1to1_coversation_id(sender_id, recipient_user_id)
        exists = conversation_exists(db, conversation_id)
        if not exists:
            insert_conversation(db, conversation_id)
        return_data = json.dumps({"conversation_id":conversation_id})
    else:
        conversation_id = message.conversation_id
        return_data = json.dumps({})

    message_id = insert_message(db, conversation_id, sender_id, message.content, dt_str, message.expiration)
    insert_message_recipient(db, message_id, recipient_user_id)
    return Response(status_code=status.HTTP_200_OK, content = return_data)

# --------------------------- db interactions ---------------------------

def insert_message_recipient(db: Session, message_id: int, recipient_user_id: int):
        db.execute(text("INSERT INTO message_recipients VALUES (:message_id, :recipient_id, :is_read)"), {"message_id":message_id, "recipient_id":recipient_user_id, "is_read":"FALSE"})
        db.commit()

def insert_message(db: Session, conversation_id: int, sender_id: int, content: str, sent_at: str, expiration: int | None) -> int:
        return db.execute(text("INSERT INTO messages (conversation_id, sender_id, content, sent_at, expiration) VALUES (:conversation_id, :sender_id, :content, :sent_at, :expiration) RETURNING message_id"), {"conversation_id":conversation_id, "sender_id":sender_id, "content":content, "sent_at":sent_at, "expiration":expiration}).scalar()

def insert_conversation(db: Session, conversation_id):            
    db.execute(text("INSERT INTO conversations VALUES (:conversation_id, :subject, :created_at)"), {"conversation_id":conversation_id, "subject":"NULL", "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    db.commit()

def conversation_exists(db: Session, conversation_id: int) -> bool:
        if db.execute(text(f"SELECT conversation_id FROM conversations WHERE conversation_id = {conversation_id}")).scalar() == None:
            return False
        return True

def select_user_id(db: Session, username: str) -> int | None:
    return db.execute(text("SELECT user_id FROM users WHERE username = :username"), {"username":username}).scalar()

def select_username(db: Session, user_id: int) -> str | None:
    return db.execute(text("SELECT username FROM users WHERE user_id = :user_id"), {"user_id":user_id}).scalar()

def select_message(db: Session, message_id: int) -> Message | None:
    return db.execute(text("SELECT * FROM messages WHERE message_id = :message_id"), {"message_id":message_id}).fetchall()[0]

def select_message_receipts(db: Session, sender_id) -> list:
    receipts = db.execute(text("UPDATE message_recipients SET is_read = TRUE WHERE recipient_id = :sender_id AND is_read = FALSE RETURNING *"), {"sender_id":sender_id}).fetchall()
    db.commit()
    return receipts

def select_password_hash(db: Session, user_id) -> str:
    return db.execute(text("SELECT password_hash FROM users WHERE user_id = :user_id"), {"user_id":user_id}).scalar()

# --------------------------- utils ---------------------------

# takes a token of the form 'Token token' and returns the id of the user if the authentication token is valid
def authorise(auth_token: str, db: Session) -> int | None:
     return db.execute(text(f"SELECT user_id FROM sessions WHERE session_token = '{auth_token.split(" ")[1]}'")).scalar()

def create_session(user_id: int, db: Session) -> str:
    token = secrets.token_hex(16)
    db.execute(text("INSERT INTO sessions VALUES (:session_token, :user_id) ON CONFLICT (user_id) DO UPDATE SET session_token = :session_token"), {"session_token":token, "user_id":user_id})  
    db.commit()
    return token

#size of returned int compatible with postgres BIGINT
def create_1to1_coversation_id(user_id1: int, user_id2: int) -> int:
    a, b = sorted([user_id1, user_id2])
    combined = f"{a}:{b}".encode('utf-8')
    digest = hashlib.sha256(combined).digest()
    return int.from_bytes(digest[:8], 'big') & 0x7FFFFFFFFFFFFFFF 

def timestamp_to_datetime_str(timestamp: int) -> str:
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')

def datetime_obj_to_timestamp(dt_object) -> int:
    return int(dt_object.timestamp())

if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("./cert.pem", keyfile="./key.pem")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        ssl=context
    )