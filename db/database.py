"""Database connection and session management"""
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database file path
DATABASE_URL = "sqlite:///./data/app.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """Initialize database and create all tables"""
    # Import models to register them with SQLModel metadata
    from db.models import Course, Theme, Lesson
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

