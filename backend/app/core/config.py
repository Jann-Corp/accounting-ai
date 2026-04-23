from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Accounting"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/accounting"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Provider: "qwen" or "minimax"
    AI_PROVIDER: str = "qwen"
    
    # Qwen API (for AI vision)
    QWEN_API_KEY: Optional[str] = None
    QWEN_API_BASE: str = "https://coding.dashscope.aliyuncs.com/v1"
    QWEN_MODEL: str = "qwen-vl-max"
    
    # Minimax API (for AI vision)
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_API_BASE: str = "https://api.minimax.chat/v1"
    MINIMAX_MODEL: str = "MiniMax-VL-01"
    MINIMAX_GROUP_ID: Optional[str] = None

    # File upload
    UPLOAD_DIR: str = "/tmp/accounting-uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # AI Confidence threshold
    AI_CONFIDENCE_THRESHOLD: float = 0.85

    # AI receipt recognition prompt (supports multiple records; response should be a JSON array)
    # Example: "[{\"amount\": 123, \"record_type\": \"expense\", ...}, {\"amount\": 50, \"record_type\": \"income\", ...}]"
    AI_RECOGNITION_PROMPT: str = (
        "你是一个专业的小票/收据识别助手。请分析这张图片中的所有交易记录，提取每一条记录的信息，以 JSON 数组格式返回。\n"
        "每条记录包含以下字段：\n"
        "- amount: 交易金额（数字，正数）\n"
        "- record_type: 记录类型，必填。expense=支出，income=收入\n"
        "- merchant_name: 商家名称（支出填商家，收入填资金来源，如：工资入账、退款、转账收入）\n"
        "- date: 交易日期时间（格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM），图中只有时间时也要返回 HH:MM，我会自动补充当天日期\n"
        "- category_guess: 分类猜测\n"
        "  支出分类：餐饮、交通、购物、娱乐、医疗、教育、居住、通讯、水电煤、其他\n"
        "  收入分类：工资、奖金、投资、退款、转账、佣金、理财、其他\n"
        "- confidence: 识别置信度（0.0-1.0 之间的浮点数，真实反映识别准确程度）\n\n"
        "输出 JSON Demo（必须严格按照此格式返回，不要有额外文字）：\n"
        "[\n"
        "  {\"amount\": 85.5, \"record_type\": \"expense\", \"merchant_name\": \"麦当劳\", \"date\": \"2024-01-15\", \"category_guess\": \"餐饮\", \"confidence\": 0.92},\n"
        "  {\"amount\": 2000, \"record_type\": \"income\", \"merchant_name\": \"工资入账\", \"date\": \"2024-01-15\", \"category_guess\": \"工资\", \"confidence\": 0.95}\n"
        "]\n\n"
        "规则：\n"
        "1. 返回一个 JSON 数组，每项对应一条交易记录\n"
        "2. 如果图片中无法识别出有效的交易记录，返回空数组 []\n"
        "3. date 字段必须识别，图片中能找到日期就返回日期，找不到也猜一个最合理的日期\n"
        "4. 只返回 JSON 数组，不要有其他文字\n"
        "5. amount 必须是正数，record_type 必须为 expense 或 income（字符串）"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
