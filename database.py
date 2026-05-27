"""
Database connection and initialization
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://taskuser:taskpass@localhost:5432/taskdb")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Print SQL statements (helpful for learning!)
    future=True
)

# Create session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    """Dependency to get a database session"""
    async with async_session() as session:
        yield session
