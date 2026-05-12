import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/treasury_hub_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["DEBUG"] = "false"

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/treasury_hub_test",
)

test_engine = None
TestSessionLocal = async_sessionmaker(expire_on_commit=False)


def _get_test_engine():
    global test_engine, TestSessionLocal
    if test_engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine

        test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    return test_engine


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    from app.database import Base

    engine = _get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_test_db):
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_client(db_session: AsyncSession):
    from app.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
