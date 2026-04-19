from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class RecordType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class RecordStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    REJECTED = "rejected"


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    record_type = Column(SQLEnum(RecordType), nullable=False)
    note = Column(String(500), nullable=True)
    date = Column(DateTime, nullable=False)
    original_image_url = Column(String(500), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    status = Column(SQLEnum(RecordStatus), default=RecordStatus.CONFIRMED)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="records")
    wallet = relationship("Wallet", back_populates="records")
    category = relationship("Category", back_populates="records")
