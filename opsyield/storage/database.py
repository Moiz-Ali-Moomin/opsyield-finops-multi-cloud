import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# Default to SQLite memory for development if not provided, though Postgres is expected in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# PostgreSQL Example: "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True,
    # connection pool settings can be configured here based on DATABASE_URL
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints to get a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        # Avoid creating tables if using alembic migrations,
        # but useful for local testing.
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized.")
