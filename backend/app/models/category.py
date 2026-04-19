from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CategoryType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    category_type = Column(SQLEnum(CategoryType), nullable=False)
    icon = Column(String(50), default="📦")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="categories")
    records = relationship("Record", back_populates="category")
