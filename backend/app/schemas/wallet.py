from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.wallet import WalletType


class WalletBase(BaseModel):
    name: str
    wallet_type: WalletType
    balance: float = 0.0
    currency: str = "CNY"


class WalletCreate(WalletBase):
    pass


class WalletUpdate(BaseModel):
    name: Optional[str] = None
    wallet_type: Optional[WalletType] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class WalletResponse(WalletBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float
    note: Optional[str] = None
