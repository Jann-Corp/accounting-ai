from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.ai_recognition_job import RecognitionStatus


class AIRecognitionJobBase(BaseModel):
    original_image_url: Optional[str] = None


class AIRecognitionJobCreate(AIRecognitionJobBase):
    pass


class AIRecognitionRecordItem(BaseModel):
    """单条识别结果中的子记录"""
    amount: Optional[float] = None
    record_type: Optional[str] = None
    merchant_name: Optional[str] = None
    date: Optional[str] = None
    category_guess: Optional[str] = None
    category_id: Optional[int] = None
    confidence: Optional[float] = None


class AIRecognitionJobResponse(AIRecognitionJobBase):
    id: int
    user_id: int
    status: RecognitionStatus
    result_json: Optional[str] = None  # JSON 字符串，前端自行解析
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIRecognitionJobDetailResponse(AIRecognitionJobResponse):
    """带解析后 records 列表的详情"""
    records: List[AIRecognitionRecordItem] = []


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
