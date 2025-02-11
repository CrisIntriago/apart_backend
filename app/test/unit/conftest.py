from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import pytest
from app.db.models.common_model import Base
from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.dependencies.dependencies import get_db
import pytest_asyncio
from app.db.models.user_models import (UserModel)
import importlib

engine = create_async_engine('sqlite+aiosqlite:///:memory:',  isolation_level="AUTOCOMMIT")
TestAsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(scope="session")
async def db_session() -> AsyncSession:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        TestingSessionLocal = sessionmaker(
            expire_on_commit=False,
            class_=AsyncSession,
            bind=engine,
        )
        async with TestingSessionLocal(bind=connection) as session:
                yield session
                await session.flush()
                await session.rollback()
                await session.close()

@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> UserModel:
    user = UserModel(
        name="John",
        last_name="Doe",
        document_number="1234567890",
        phone_number="9876543210",
        email="john.doe@example.com",
        user_auth_id="auth_1234",
        accept_terms_and_conditions=True,
        accept_privacy_policy=True
    )
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.delete(user)
    await db_session.commit()

