from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
print( "Aws access key", os.getenv('AWS_ACCESS_KEY'))
print( "Aws secret key", os.getenv('AWS_SECRET_KEY'))
DATABASE_URL = os.getenv("DATABASE_URL")

print(DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_timeout=30)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
