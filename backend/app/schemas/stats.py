from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MonthlyStats(BaseModel):
    year: int
    month: int
    total_expense: float
    total_income: float
    balance: float
    record_count: int


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    category_icon: str
    total_amount: float
    percentage: float
    record_count: int


class CategoryBreakdownResponse(BaseModel):
    year: int
    month: int
    breakdown: List[CategoryBreakdown]


class TrendPoint(BaseModel):
    year: int
    month: int
    total_expense: float
    total_income: float


class TrendResponse(BaseModel):
    trend: List[TrendPoint]
