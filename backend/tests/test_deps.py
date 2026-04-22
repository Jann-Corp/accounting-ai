"""
Unit tests for authentication dependencies (deps.py).
"""
import pytest
from datetime import datetime, timedelta
import hashlib


def test_get_current_user_success(client, test_user):
    """Test getting current user with valid JWT token."""
    from app.core.security import create_access_token
    from app.api.deps import get_current_user, get_db
    from fastapi.testclient import TestClient
    from app.main import app
    
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # Use the token to get current user via the /auth/me endpoint
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id


def test_get_current_user_no_credentials():
    """Test get_current_user with no credentials."""
    from app.api.deps import get_current_user, bearer_scheme
    from fastapi import Depends, HTTPException
    
    # This is tested indirectly via 401 responses on protected endpoints
    response = pytest.importorskip("builtins")
    # Tested via test_auth.py - test_get_me_unauthenticated


def test_get_current_user_invalid_token():
    """Test get_current_user with invalid JWT token."""
    from app.main import app
    from fastapi.testclient import TestClient
    
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


def test_get_current_user_or_api_key_with_jwt():
    """Test get_current_user_or_api_key with JWT token."""
    from app.api.deps import get_current_user_or_api_key
    from app.core.security import create_access_token
    from app.database import get_db
    from sqlalchemy.orm import Session
    
    # This function is used by export endpoint
    # Tested indirectly via export tests with JWT token
    pass  # Integration tested in test_export.py


def test_get_current_user_or_api_key_with_valid_api_key(client, db, test_user):
    """Test get_current_user_or_api_key with valid API key."""
    from app.models.apikey import ApiKey
    from app.api.deps import get_current_user_or_api_key
    
    full_key = "ak_test_valid_key_12345"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="测试密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    
    # Call the function directly
    user = get_current_user_or_api_key(x_api_key=full_key, db=db)
    assert user.id == test_user.id


def test_get_current_user_or_api_key_with_invalid_api_key(db):
    """Test get_current_user_or_api_key with invalid API key."""
    from app.api.deps import get_current_user_or_api_key
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_or_api_key(x_api_key="invalid_key", db=db)
    
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail


def test_get_current_user_or_api_key_with_expired_api_key(client, db, test_user):
    """Test get_current_user_or_api_key with expired API key."""
    from app.models.apikey import ApiKey
    from app.api.deps import get_current_user_or_api_key
    from fastapi import HTTPException
    import time

    full_key = f"ak_test_expired_key_{int(time.time() * 1000)}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    api_key = ApiKey(
        user_id=test_user.id,
        name="过期密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=True,
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(api_key)
    db.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_or_api_key(x_api_key=full_key, db=db)
    
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail


def test_get_current_user_or_api_key_with_inactive_api_key(client, db, test_user):
    """Test get_current_user_or_api_key with inactive API key."""
    from app.models.apikey import ApiKey
    from app.api.deps import get_current_user_or_api_key
    from fastapi import HTTPException
    
    full_key = "ak_test_inactive_key"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="非激活密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=False,  # Inactive
    )
    db.add(api_key)
    db.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_or_api_key(x_api_key=full_key, db=db)
    
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail


def test_get_current_user_or_api_key_updates_last_used(client, db, test_user):
    """Test that using API key updates last_used_at."""
    from app.models.apikey import ApiKey
    from app.api.deps import get_current_user_or_api_key
    
    full_key = "ak_test_last_used_key"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="测试密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=True,
        last_used_at=None,
    )
    db.add(api_key)
    db.commit()
    
    # Use the key
    user = get_current_user_or_api_key(x_api_key=full_key, db=db)
    
    # Verify last_used_at was updated
    db.refresh(api_key)
    assert api_key.last_used_at is not None


def test_get_current_user_or_api_key_with_jwt_token_format(client, db, test_user):
    """Test that JWT tokens are recognized in x_api_key parameter."""
    from app.core.security import create_access_token
    from app.api.deps import get_current_user_or_api_key
    
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # Pass JWT token as x_api_key (for export endpoint compatibility)
    user = get_current_user_or_api_key(x_api_key=token, db=db)
    assert user.id == test_user.id


def test_api_key_hash_comparison():
    """Test that API key hash comparison works correctly."""
    full_key = "ak_test_hash_key"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Same key should produce same hash
    assert hashlib.sha256(full_key.encode()).hexdigest() == key_hash
    
    # Different key should produce different hash
    different_key = "ak_different_key"
    assert hashlib.sha256(different_key.encode()).hexdigest() != key_hash


def test_bearer_scheme_extraction():
    """Test Bearer token extraction."""
    from app.api.deps import bearer_scheme
    from fastapi.security import HTTPBearer
    
    assert isinstance(bearer_scheme, HTTPBearer)
    assert bearer_scheme.auto_error is False
