from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.record import RecordType, RecordStatus


class RecordBase(BaseModel):
    amount: float
    record_type: RecordType
    date: datetime
    note: Optional[str] = None
    wallet_id: Optional[int] = None
    category_id: Optional[int] = None


class RecordCreate(RecordBase):
    job_id: Optional[int] = None
    is_ai_recognized: bool = False


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    record_type: Optional[RecordType] = None
    date: Optional[datetime] = None
    note: Optional[str] = None
    wallet_id: Optional[int] = None
    category_id: Optional[int] = None


class RecordResponse(RecordBase):
    id: int
    user_id: int
    original_image_url: Optional[str] = None
    ai_confidence: Optional[float] = None
    is_ai_recognized: bool = False
    is_suspected_duplicate: bool = False
    job_id: Optional[int] = None
    status: RecordStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Include related data
    wallet_name: Optional[str] = None
    category_name: Optional[str] = None
    category_icon: Optional[str] = None

    class Config:
        from_attributes = True


class RecordFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    wallet_id: Optional[int] = None
    category_id: Optional[int] = None
    record_type: Optional[RecordType] = None
    status: Optional[RecordStatus] = None
    limit: int = 50
    offset: int = 0


class AIRecognizeRecord(BaseModel):
    """Single recognized record item"""
    amount: Optional[float] = None
    merchant_name: Optional[str] = None
    date: Optional[str] = None
    category_guess: Optional[str] = None
    category_id: Optional[int] = None
    confidence: float = 0.0
    record_type: str = "expense"  # "expense" or "income" based on amount sign


class AIRecognizeResponse(BaseModel):
    amount: Optional[float] = None
    merchant_name: Optional[str] = None
    date: Optional[str] = None
    category_guess: Optional[str] = None
    category_id: Optional[int] = None
    confidence: float = 0.0
    original_image_url: str = ""
    raw_response: Optional[str] = None
    # All recognized records (new - supports multiple items)
    records: list[AIRecognizeRecord] = []
