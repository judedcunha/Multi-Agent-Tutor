"""
logging configuration for the AI Tutor system 
Provides comprehensive logging for debugging and monitoring
"""

import logging
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""
    
    def __init__(self, enable_full_logging: bool = False):
        """
        Initialize the sensitive data filter
        
        Args:
            enable_full_logging: If True, disable redaction (for debugging only)
        """
        super().__init__()
        self.enable_full_logging = enable_full_logging
        
        # Collect API keys and secrets from environment
        self.secrets = []
        sensitive_env_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'HUGGINGFACE_API_KEY',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_ACCESS_KEY_ID',
        ]
        
        for var in sensitive_env_vars:
            value = os.getenv(var)
            if value and value not in ['', 'your_key_here', 'None']:
                self.secrets.append(value)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to redact sensitive information
        
        Args:
            record: The log record to filter
            
        Returns:
            True to allow the record through, False to block it
        """
        # If full logging is enabled, don't redact
        if self.enable_full_logging:
            return True
        
        # Redact message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for secret in self.secrets:
                if secret in record.msg:
                    record.msg = record.msg.replace(secret, '***REDACTED***')
        
        # Redact args (used in formatted messages)
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                redacted_args = {}
                for key, value in record.args.items():
                    if isinstance(value, str):
                        for secret in self.secrets:
                            if secret in value:
                                value = value.replace(secret, '***REDACTED***')
                    redacted_args[key] = value
                record.args = redacted_args
            elif isinstance(record.args, (list, tuple)):
                redacted_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        for secret in self.secrets:
                            if secret in arg:
                                arg = arg.replace(secret, '***REDACTED***')
                    redacted_args.append(arg)
                record.args = tuple(redacted_args) if isinstance(record.args, tuple) else redacted_args
        
        return True


def setup_logging(
    level: str = "INFO",
    log_dir: str = "./logs",
    enable_file_logging: bool = True,
    enable_console: bool = True,
    log_llm_requests: bool = False,
    log_api_requests: bool = False,
    enable_full_llm_logging: bool = False
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
        enable_full_llm_logging: Whether to log full unredacted LLM bodies (DEBUG ONLY)
        
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
        
        # Add sensitive data filter (redacts by default unless full logging enabled)
        sensitive_filter = SensitiveDataFilter(enable_full_logging=enable_full_llm_logging)
        llm_logger.addFilter(sensitive_filter)
        
        if enable_full_llm_logging:
            logging.warning("Full unredacted LLM logging is ENABLED - sensitive data will be logged!")
        else:
            logging.info("LLM logging configured with sensitive data redaction")
    
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
