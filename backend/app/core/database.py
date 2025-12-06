# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from app.config.setting import settings
import asyncpg


# -----------------------------
# 1) Auto-create database
# -----------------------------

async def create_database_if_not_exists():
    sqlalchemy_url = settings.database_url

    # Convert "postgresql+asyncpg://" → "postgresql://"
    admin_url = sqlalchemy_url.replace("+asyncpg", "")

    # Extract database name
    db_name = sqlalchemy_url.rsplit("/", 1)[-1]

    # Connect to postgres default DB (admin)
    admin_url = admin_url.rsplit("/", 1)[0] + "/postgres"

    try:
        conn = await asyncpg.connect(admin_url)

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_name
        )

        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"[INFO] Database '{db_name}' created successfully!")
        else:
            print(f"[INFO] Database '{db_name}' already exists.")

        await conn.close()

    except Exception as e:
        print(f"[ERROR] Could not create database: {e}")
        raise


# -----------------------------
# 2) Create engine AFTER DB exists
# -----------------------------
engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# FastAPI dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
