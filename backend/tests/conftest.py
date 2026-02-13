import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User, UserRole


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def coach_user(db_session: AsyncSession) -> User:
    user = User(
        email="coach@test.com",
        hashed_password=get_password_hash("coachpass123"),
        full_name="Test Coach",
        role=UserRole.COACH,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def athlete_user(db_session: AsyncSession) -> User:
    user = User(
        email="athlete@test.com",
        hashed_password=get_password_hash("athletepass123"),
        full_name="Test Athlete",
        role=UserRole.ATHLETE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def coach_token(client: AsyncClient, coach_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def athlete_token(client: AsyncClient, athlete_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    return resp.json()["access_token"]
