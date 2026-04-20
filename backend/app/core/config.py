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

    # AI receipt recognition prompt (supports multiple records; response should be a JSON array)
    # Example: "[{\"amount\": 123, \"merchant_name\": \"...\", ...}, {...}]"
    AI_RECOGNITION_PROMPT: str = (
        "你是一个专业的小票/收据识别助手。请分析这张图片中的所有消费记录，提取每一条记录的信息，以JSON数组格式返回。\n"
        "每条记录包含以下字段：\n"
        "- amount: 消费金额（数字）\n"
        "- record_type: 记录类型，固定为 expense（支出）\n"
        "- merchant_name: 商家名称\n"
        "- date: 消费日期时间（格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM），图中只有时间时也要返回 HH:MM，我会自动补充当天日期\n"
        "- category_guess: 消费分类猜测（如：餐饮、交通、购物、娱乐、医疗、教育、居住、通讯、其他）\n"
        "- confidence: 识别置信度（0.0-1.0之间的浮点数，真实反映识别准确程度，不要固定为0.85）\n\n"
        "规则：\n"
        "1. 返回一个JSON数组，每项对应一条消费记录\n"
        "2. 如果图片中无法识别出有效的消费记录，返回空数组 []\n"
        "3. date 字段必须识别，图片中能找到日期就返回日期，找不到也猜一个最合理的日期\n"
        "4. 只返回JSON数组，不要有其他文字"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
