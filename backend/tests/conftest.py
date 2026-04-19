"""Pytest configuration and fixtures for backend tests."""
import pytest, sys, os, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

_test_db_file = tempfile.mktemp(suffix=".db", prefix="test_acc_")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_file}"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

_engine = create_engine(
    f"sqlite:///{_test_db_file}",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base = declarative_base()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_counter = [0]

def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def db():
    db = TestingSessionLocal()
    yield db
    # Clean up all rows after test
    for table in reversed(Base.metadata.sorted_tables):
        try:
            db.execute(table.delete())
            db.commit()
        except Exception:
            db.rollback()
    db.close()

@pytest.fixture(scope="function")
def client(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from app.models.user import User
    from app.models.wallet import Wallet
    from app.models.category import Category
    from app.models.record import Record
    Base.metadata.create_all(bind=_engine)
    yield
    try:
        os.unlink(_test_db_file)
    except OSError:
        pass

@pytest.fixture
def test_user(db):
    from app.models.user import User
    from app.core.security import get_password_hash
    _counter[0] += 1
    user = User(
        username=f"testuser_{_counter[0]}",
        email=f"test{_counter[0]}@example.com",
        hashed_password=get_password_hash("testpass123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_wallet(db, test_user):
    from app.models.wallet import Wallet, WalletType
    wallet = Wallet(
        user_id=test_user.id,
        name="测试钱包",
        wallet_type=WalletType.CASH,
        balance=1000.00,
        currency="CNY",
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

@pytest.fixture
def test_category(db, test_user):
    from app.models.category import Category, CategoryType
    category = Category(
        user_id=test_user.id,
        name="餐饮",
        category_type=CategoryType.EXPENSE,
        icon="🍜",
        is_default=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
