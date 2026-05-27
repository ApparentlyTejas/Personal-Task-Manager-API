"""
Database models and Pydantic schemas for the Task Manager API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()

# ===== DATABASE MODELS (SQLAlchemy) =====
# These define the actual database tables

class TaskDB(Base):
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
    description: Optional[str] = None
    status: str = "pending"

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class TaskResponse(BaseModel):
    """Schema for returning a task in API responses"""
    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from ORM objects
