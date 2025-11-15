"""
Database session management for SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    # connect_args={"check_same_thread": False} # Only needed for SQLite
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for ORM models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """
    FastAPI dependency that provides a database session.
    Ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
