"""
logging configuration for the AI Tutor system 
Provides comprehensive logging for debugging and monitoring
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_dir: str = "./logs",
    enable_file_logging: bool = True,
    enable_console: bool = True,
    log_llm_requests: bool = False,
    log_api_requests: bool = False
) -> logging.Logger:
    """
    Setup comprehensive logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        enable_file_logging: Whether to log to files
        enable_console: Whether to log to console
        log_llm_requests: Whether to log full LLM requests/responses
        log_api_requests: Whether to log API requests
        
    Returns:
        Configured logger instance
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"tutor_{timestamp}.log"
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (detailed)
    if enable_file_logging:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # LLM request logger (separate file)
    if log_llm_requests:
        llm_logger = logging.getLogger('llm_requests')
        llm_file = log_path / f"llm_requests_{timestamp}.log"
        llm_handler = logging.FileHandler(llm_file)
        llm_handler.setFormatter(detailed_formatter)
        llm_logger.addHandler(llm_handler)
        llm_logger.setLevel(logging.DEBUG)
        llm_logger.propagate = False  # Don't propagate to root
    
    # API request logger
    if log_api_requests:
        api_logger = logging.getLogger('api_requests')
        api_file = log_path / f"api_requests_{timestamp}.log"
        api_handler = logging.FileHandler(api_file)
        api_handler.setFormatter(detailed_formatter)
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.DEBUG)
        api_logger.propagate = False  # Don't propagate to root
    
    logging.info(f"Logging initialized - Level: {level}, File: {log_file}")
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


if __name__ == "__main__":
    # Test logging setup
    setup_logging(level="DEBUG", log_llm_requests=True, log_api_requests=True)
    
    logger = logging.getLogger(__name__)
    logger.info("Test info message")
    logger.debug("Test debug message")
    logger.warning("Test warning message")
    
    llm_logger = logging.getLogger('llm_requests')
    llm_logger.info("Test LLM request log")
    
    api_logger = logging.getLogger('api_requests')
    api_logger.info("Test API request log")
    
    print("\nLogging test complete! Check the logs directory.")
