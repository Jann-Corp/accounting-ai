from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
import enum
from app.database import Base


class RecognitionStatus(str, enum.Enum):
    PENDING = "PENDING"      # 等待处理
    PROCESSING = "PROCESSING"  # AI 识别中
    DONE = "DONE"           # 完成，已生成记录
    FAILED = "FAILED"       # 识别失败


class AIRecognitionJob(Base):
    """AI 识别任务记录（不可变日志）。

    每次上传图片产生一条 Job 记录，追踪识别状态和结果。
    关联的 Record 由用户在 UI 确认/编辑后保存，Job 本身不可修改。
    """

    __tablename__ = "ai_recognition_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_image_url = Column(String(500), nullable=True)   # 图片路径
    _status = Column("status", String(20), default="pending")

    # AI 识别结果 JSON（识别完成后写入，永久保存）
    # 包含: amount, merchant_name, date, category_guess, confidence, raw_response, records[]
    result_json = Column(Text, nullable=True)

    # 错误信息（识别失败时保存）
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)   # 识别完成时间

    # === Case-insensitive hybrid property for backward compat ===

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
                return func.upper(self.expression.cast(String)) == str(other).upper()

            def __ne__(self, other):
                if isinstance(other, enum.Enum):
                    other = other.value
                return func.upper(self.expression.cast(String)) != str(other).upper()
        return UpperComparator(cls._status)

    # Relationships
    user = relationship("User", back_populates="ai_recognition_jobs")
