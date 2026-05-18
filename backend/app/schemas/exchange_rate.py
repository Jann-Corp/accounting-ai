from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ExchangeRateBase(BaseModel):
    currency: str = Field(..., max_length=10, description="货币代码，如 USD, EUR, JPY")
    rate: float = Field(..., gt=0, description="汇率（1 外币 = xxx CNY）")


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRateUpdate(BaseModel):
    rate: float = Field(..., gt=0)


class ExchangeRateResponse(ExchangeRateBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True
