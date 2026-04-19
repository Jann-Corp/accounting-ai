"""
Unit tests for core security functions.
Since bcrypt is mocked in test environment, we test the interface.
"""
import pytest
from app.core.security import create_access_token, decode_token


def test_password_hash_and_verify():
    """Test that SHA-256 password hashing and verification work correctly."""
    from app.core.security import get_password_hash, verify_password
    hashed = get_password_hash("testpass123")
    assert verify_password("testpass123", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    token = create_access_token(data={"sub": "user123"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token():
    """Test JWT token decoding."""
    token = create_access_token(data={"sub": "user123"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"


def test_decode_invalid_token():
    """Test decoding invalid token returns None."""
    payload = decode_token("invalid.token.here")
    assert payload is None
