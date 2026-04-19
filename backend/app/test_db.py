"""
Test database utilities - creates a shared in-memory SQLite engine
for use in tests. Import this BEFORE importing app.database.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Create a single shared in-memory engine
# WARNING: This only works with StaticPool + SQLite in-memory
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

Base = declarative_base()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def get_test_db():
    """Yield the shared test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
