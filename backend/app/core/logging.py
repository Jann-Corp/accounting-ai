"""
Logging configuration for the application.
"""
import logging
import sys
from app.core.config import settings


def setup_logging():
    """Setup application logging based on LOG_LEVEL setting."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('app').setLevel(log_level)
    
    return logging.getLogger(__name__)


# Create module logger
logger = setup_logging()
