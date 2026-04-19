from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator, Optional
from datetime import datetime
import hashlib

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.apikey import ApiKey

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Standard Bearer JWT authentication."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_current_user_or_api_key(
    x_api_key: Optional[str] = None,
    db: Session = None,
) -> User:
    """
    Synchronous auth helper for export endpoints.
    Accepts X-API-Key header value and a SQLAlchemy Session.
    Supports both API keys and JWT Bearer tokens.
    Returns the authenticated User.
    Raises HTTPException on auth failure.
    """
    print(f"DEBUG get_current_user_or_api_key: x_api_key={x_api_key!r}", flush=True)
    if x_api_key is None:
        print("DEBUG: x_api_key is None -> 401", flush=True)

    # First try JWT Bearer token (looks like a JWT if it has dots and is long)
    if "." in x_api_key and len(x_api_key) > 32:
        payload = decode_token(x_api_key)
        if payload is not None:
            user_id = int(payload.get("sub"))
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user

    # Try API key lookup (SHA-256 hash comparison)
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,
    ).first()

    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check expiry
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last_used_at
    api_key_record.last_used_at = datetime.utcnow()
    db.commit()

    return api_key_record.user
