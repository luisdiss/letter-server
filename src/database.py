from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv() 

try:
    creds = {
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }
except KeyError as e:
    raise RuntimeError(f"Missing environment variable: {e}")

sqlalchemy_database_url = f"postgresql://{creds['user']}:{creds['password']}@localhost/letter"
engine = create_engine(sqlalchemy_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
