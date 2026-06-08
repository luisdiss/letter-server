from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    creds = {
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }
except KeyError as e:
    raise RuntimeError(f"Missing environment variable: {e}")

DB_HOST = os.environ.get("DB_HOST", "localhost")
sqlalchemy_database_url = f"postgresql://{creds['user']}:{creds['password']}@{DB_HOST}/letter"
engine = create_engine(sqlalchemy_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
