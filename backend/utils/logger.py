import logging
import os
import sys
from sys import stdout

# Ensure stdout uses UTF-8 where supported on Windows
if hasattr(stdout, "reconfigure"):
    try:
        stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "satquery.log")

def setup_logger(name: str = "satquery_backend") -> logging.Logger:
    """
    Configures and returns a structured logger writing to both console and satquery.log
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Stream Handler (Console)
        console_handler = logging.StreamHandler(stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler (logs/satquery.log) with UTF-8 encoding
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()
