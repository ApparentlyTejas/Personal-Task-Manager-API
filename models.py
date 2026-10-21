"""
Database models and Pydantic schemas for the Task Manager API
"""
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()

# ===== DATABASE MODELS (SQLAlchemy) =====
# These define the actual database tables

class TaskDB(Base):  # type: ignore[misc,valid-type]  # declarative_base() returns Any; see mypy#2477
    """
    The Task table in PostgreSQL.

    Columns:
    - id: Unique identifier (primary key)
    - title: Short title of the task
    - description: Longer description
    - status: Either 'pending', 'in_progress', or 'completed'
    - created_at: When the task was created
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===== PYDANTIC SCHEMAS =====
# These define the structure of data sent/received via the API

class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str
    description: str | None = None
    status: str = "pending"

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: str | None = None
    description: str | None = None
    status: str | None = None

class TaskResponse(BaseModel):
    """Schema for returning a task in API responses"""
    id: int
    title: str
    description: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from ORM objects
