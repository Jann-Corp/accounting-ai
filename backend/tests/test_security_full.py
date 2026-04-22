"""
Comprehensive tests for security module.
"""
import pytest
from datetime import datetime, timedelta


def test_create_access_token():
    """Test creating JWT access token."""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": "123"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_valid_token():
    """Test decoding a valid JWT token."""
    from app.core.security import create_access_token, decode_token
    
    token = create_access_token(data={"sub": "123", "exp": datetime.utcnow() + timedelta(hours=1)})
    payload = decode_token(token)
    
    assert payload is not None
    assert payload["sub"] == "123"


def test_decode_expired_token():
    """Test decoding an expired JWT token."""
    from jose import jwt
    from app.core.security import decode_token
    from app.core.config import settings
    
    # Create an already-expired token directly using jose
    expire = datetime.utcnow() - timedelta(hours=1)
    payload = {"sub": "123", "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    result = decode_token(token)
    assert result is None


def test_decode_invalid_token():
    """Test decoding an invalid JWT token."""
    from app.core.security import decode_token
    
    result = decode_token("invalid.token.here")
    assert result is None


def test_decode_token_missing_sub():
    """Test decoding token without 'sub' claim returns payload but without sub."""
    from jose import jwt
    from app.core.security import decode_token
    from app.core.config import settings
    
    # Token with no 'sub' claim
    expire = datetime.utcnow() + timedelta(hours=1)
    payload = {"no_sub": "123", "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    result = decode_token(token)
    # decode_token returns the payload (doesn't check for sub)
    # The sub validation happens in get_current_user
    assert result is not None
    assert result.get("no_sub") == "123"
    assert result.get("sub") is None


def test_hash_and_verify_password():
    """Test password hashing and verification."""
    from app.core.security import get_password_hash, verify_password
    
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_different_passwords_different_hashes():
    """Test that different passwords produce different hashes."""
    from app.core.security import get_password_hash
    
    hash1 = get_password_hash("password1")
    hash2 = get_password_hash("password2")
    
    assert hash1 != hash2


def test_same_password_different_hashes():
    """Test that same password produces different hashes (due to salt)."""
    from app.core.security import get_password_hash
    
    hash1 = get_password_hash("same_password")
    hash2 = get_password_hash("same_password")
    
    # Hashes should be different due to random salt
    assert hash1 != hash2
    # But both should verify correctly
    from app.core.security import verify_password
    assert verify_password("same_password", hash1) is True
    assert verify_password("same_password", hash2) is True
