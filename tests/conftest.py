"""
Shared pytest fixtures for backend test suite.

Provides:
- In-memory SQLite database session (no production DB side effects)
- User/wallet factory fixtures
- FastAPI TestClient using test database overrides
- Mock for yfinance stock price calls
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force test database URL before any app imports
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory

from sqlalchemy.pool import StaticPool

from api.models import Base
from api.db_utils import create_user, add_to_wallet, get_wallet


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine():
    """Create a fresh in-memory SQLite engine for each test.
    
    Uses StaticPool so all sessions share the same in-memory database
    (SQLite in-memory DBs are per-connection by default).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """Provide a transactional database session that rolls back after each test."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# User/wallet factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_user(db_session):
    """Create a test user with email test@example.com and return the ORM object."""
    user = create_user(db_session, "test@example.com", "TestPassword123!")
    db_session.commit()
    return user


@pytest.fixture()
def funded_user(db_session, test_user):
    """Create a test user with ₹100,000 in wallet."""
    add_to_wallet(db_session, test_user.id, 100_000.0)
    db_session.commit()
    return test_user


# ---------------------------------------------------------------------------
# Mock stock price — avoids real yfinance network calls
# ---------------------------------------------------------------------------

MOCK_PRICE_DATA = {
    "price": 1500.0,
    "change": 25.0,
    "changePercent": 1.69,
    "volume": 5_000_000,
    "name": "Test Stock",
}


@pytest.fixture(autouse=True)
def mock_stock_price():
    """Globally mock get_stock_price in app_fixed to avoid yfinance calls."""
    with patch("api.app_fixed.get_stock_price", return_value=MOCK_PRICE_DATA):
        yield


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db_engine):
    """
    Provide a FastAPI TestClient that uses the test in-memory database.
    
    Overrides the get_db dependency so all endpoints use our test session
    instead of the production database.
    """
    from api.app_fixed import app, get_db

    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    from starlette.testclient import TestClient
    c = TestClient(app)
    yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helper — signup and get token for authenticated requests
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client):
    """Sign up a test user via API and return auth headers dict."""
    import time
    email = f"testuser_{int(time.time() * 1000)}@example.com"
    resp = client.post("/api/auth/signup", json={
        "email": email,
        "password": "TestPassword123!",
        "name": "Test User",
    })
    assert resp.status_code == 200, f"Signup failed: {resp.text}"
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}
