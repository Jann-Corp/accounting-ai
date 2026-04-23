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
    is_ai_recognized = Column(Integer, default=0, nullable=False)  # 0=manual, 1=AI recognized
    job_id = Column(Integer, ForeignKey("ai_recognition_jobs.id", ondelete="SET NULL"), nullable=True)  # AI 识别任务 ID
    is_suspected_duplicate = Column(Integer, default=0, nullable=False)  # 0=正常, 1=疑似重复
    status = Column(SQLEnum(RecordStatus), default=RecordStatus.CONFIRMED)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="records")
    wallet = relationship("Wallet", back_populates="records")
    category = relationship("Category", back_populates="records")
    job = relationship("AIRecognitionJob", foreign_keys=[job_id], lazy="selectin")
