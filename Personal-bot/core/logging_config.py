import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import sys
import warnings

# Suppress specific deprecation warnings from third-party libraries
warnings.filterwarnings('ignore', message=r'.*timeout.*parameter is deprecated.*', category=DeprecationWarning)
warnings.filterwarnings('ignore', message=r'.*verify.*parameter is deprecated.*', category=DeprecationWarning)
warnings.filterwarnings('ignore', message=r'.*datetime.datetime.utcnow\(\) is deprecated.*', category=DeprecationWarning)

# Structured logging formatter
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get the default formatted message
        message = record.getMessage()
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, '_structured_data'):
            log_entry.update(getattr(record, '_structured_data', {}))
            
        return json.dumps(log_entry)

def setup_structured_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/cryptopulse.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup structured logging with file rotation and console output
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for console only)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured root logger
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_structured_data(logger: logging.Logger, level: int, message: str, **kwargs):
    """
    Log structured data with additional fields
    
    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        **kwargs: Additional structured data
    """
    # Create a log record with structured data
    extra = {'_structured_data': kwargs}
    logger.log(level, message, extra=extra)

# Default configuration
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "()": StructuredFormatter,
        },
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "structured",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "structured",
            "filename": "logs/cryptopulse.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}