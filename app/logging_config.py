"""
Centralized logging configuration for the Home Equipment Manuals Corpus.
"""

import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)

# Pre-configured loggers for common use
crawler_logger = get_logger("crawler")
api_logger = get_logger("api") 
ingest_logger = get_logger("ingest")
db_logger = get_logger("database")
