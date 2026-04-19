from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Accounting"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/accounting"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Qwen API (for AI vision)
    QWEN_API_KEY: Optional[str] = None
    QWEN_API_BASE: str = "https://coding.dashscope.aliyuncs.com/v1"
    QWEN_MODEL: str = "qwen3.5-plus"  # or qwen-vl-max

    # File upload
    UPLOAD_DIR: str = "/tmp/accounting-uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # AI Confidence threshold
    AI_CONFIDENCE_THRESHOLD: float = 0.85

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
