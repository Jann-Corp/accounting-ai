from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class WalletType(str, enum.Enum):
    BANK_CARD = "bank_card"
    E_WALLET = "e_wallet"
    CASH = "cash"
    OTHER = "other"


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    wallet_type = Column(SQLEnum(WalletType), default=WalletType.OTHER)
    balance = Column(Float, default=0.0)
    currency = Column(String(10), default="CNY")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="wallets")
    records = relationship("Record", back_populates="wallet")
