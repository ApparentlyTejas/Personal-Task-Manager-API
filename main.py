from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import init_db, get_session
from models import TaskDB, TaskCreate, TaskUpdate, TaskResponse

# Create the FastAPI app with startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    print("📦 Initializing database...")
    await init_db()
    print("✅ Database initialized!")
    yield
    # Shutdown: Cleanup happens here if needed
    print("👋 Shutting down...")

app = FastAPI(
    title="Task Manager API",
    description="A simple CRUD API for managing tasks",
    version="1.0.0",
    lifespan=lifespan
)

# ===== ENDPOINTS =====

@app.get("/")
async def read_root():
    """Health check endpoint"""
    return {"message": "Task Manager API is running! 🚀"}

# ===== CREATE: POST /tasks =====
@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    """
    Create a new task.

    Example request body:
    {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "status": "pending"
    }
    """
    # Create a new TaskDB object
    db_task = TaskDB(
        title=task.title,
        description=task.description,
        status=task.status
    )

    # Add to session and commit
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)

    return db_task

# ===== READ: GET /tasks =====
@app.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks(session: AsyncSession = Depends(get_session)):
    """
    Get all tasks.

    Returns a list of all tasks in the database.
    """
    result = await session.execute(select(TaskDB))
    tasks = result.scalars().all()
    return tasks

# ===== READ: GET /tasks/{task_id} =====
@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """
    Get a specific task by ID.
    """
    result = await session.execute(select(TaskDB).where(TaskDB.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return task

# ===== UPDATE: PATCH /tasks/{task_id} =====
@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, session: AsyncSession = Depends(get_session)):
    """
    Update a task. Only provide the fields you want to change.

    Example request body:
    {
        "status": "completed"
    }
    """
    # Fetch the task
    result = await session.execute(select(TaskDB).where(TaskDB.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Update only the fields that were provided
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    # Save changes
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)

    return db_task

# ===== DELETE: DELETE /tasks/{task_id} =====
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """
    Delete a task by ID.
    """
    # Fetch the task
    result = await session.execute(select(TaskDB).where(TaskDB.id == task_id))
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Delete it
    await session.delete(db_task)
    await session.commit()

    return {"message": f"Task {task_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
