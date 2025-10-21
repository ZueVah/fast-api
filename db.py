#db.py for FastAPI application
# This file sets up the database connection and session management using SQLAlchemy.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus  # for safely encoding special characters in the password
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables (only for local development)
# In production, Render will provide DATABASE_URL directly
if os.path.exists('config.env'):
    load_dotenv('config.env')

# Use environment variables for production, fallback to local config for development
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local development configuration
    DB_CONFIG = {
        "dbname": "postgres",
        "user": "postgres",
        "password": quote_plus("0000"),  # safely encode '@' to %40
        "host": "localhost",
        "port": "5432"
    }
    
    DATABASE_URL = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "connect_timeout": 10,
        "application_name": "smart_license_api",
        "sslmode": "require"
    }
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ✅ Add this function to allow FastAPI to access DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
