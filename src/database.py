from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import json

try:
    with open("dbcred.json") as file:
        creds = json.load(file)
except Exception:
    print('could not get db creds')

sqlalchemy_database_url = f"postgresql://{creds['username']}:{creds['password']}@localhost/letter"
engine = create_engine(sqlalchemy_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
