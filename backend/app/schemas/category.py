from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.category import CategoryType


class CategoryBase(BaseModel):
    name: str
    category_type: CategoryType
    icon: str = "📦"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
