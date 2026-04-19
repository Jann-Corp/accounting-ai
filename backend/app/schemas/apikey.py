from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApiKeyBase(BaseModel):
    name: str
    expires_at: Optional[datetime] = None


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str          # e.g. "ak_abc1..."
    key_full: Optional[str]  # Only returned ONCE at creation time
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
