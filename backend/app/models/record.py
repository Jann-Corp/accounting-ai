from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
import enum
from app.database import Base


class RecordType(str, enum.Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"


class RecordStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    _record_type = Column("record_type", String(20), nullable=False)
    note = Column(String(500), nullable=True)
    date = Column(DateTime, nullable=False)
    original_image_url = Column(String(500), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    is_ai_recognized = Column(Integer, default=0, nullable=False)  # 0=manual, 1=AI recognized
    job_id = Column(Integer, ForeignKey("ai_recognition_jobs.id", ondelete="SET NULL"), nullable=True)  # AI 识别任务 ID
    is_suspected_duplicate = Column(Integer, default=0, nullable=False)  # 0=正常, 1=疑似重复
    _status = Column("status", String(20), default="CONFIRMED")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # === Case-insensitive hybrid properties for backward compat with existing DB data ===

    @hybrid_property
    def record_type(self):
        return self._record_type

    @record_type.setter
    def record_type(self, value):
        if isinstance(value, enum.Enum):
            value = value.value
        self._record_type = str(value).upper()

    @record_type.comparator
    def record_type(cls):
        class UpperComparator(Comparator):
            def __init__(self, expression):
                super().__init__(expression)

            def __eq__(self, other):
                if isinstance(other, enum.Enum):
                    other = other.value
                return func.upper(self.expression) == str(other).upper()

            def __ne__(self, other):
                if isinstance(other, enum.Enum):
                    other = other.value
                return func.upper(self.expression) != str(other).upper()
        return UpperComparator(cls._record_type)

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if isinstance(value, enum.Enum):
            value = value.value
        self._status = str(value).upper()

    @status.comparator
    def status(cls):
        class UpperComparator(Comparator):
            def __init__(self, expression):
                super().__init__(expression)

            def __eq__(self, other):
                if isinstance(other, enum.Enum):
                    other = other.value
                return func.upper(self.expression) == str(other).upper()

            def __ne__(self, other):
                if isinstance(other, enum.Enum):
                    other = other.value
                return func.upper(self.expression) != str(other).upper()
        return UpperComparator(cls._status)

    # Relationships
    user = relationship("User", back_populates="records")
    wallet = relationship("Wallet", back_populates="records")
    category = relationship("Category", back_populates="records")
    job = relationship("AIRecognitionJob", foreign_keys=[job_id], lazy="selectin")
