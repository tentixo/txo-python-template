# utils/logger.py
"""
Thread-safe singleton logger with automatic token redaction.

This module provides centralized logging with:
- Automatic token/secret redaction for security
- Context injection (org_id, elapsed time)
- Console (INFO+) and file (DEBUG+) output
- Thread-safe singleton pattern
"""

import logging
import logging.config
import json
import re
import threading
from datetime import datetime, timezone
from typing import Optional

from utils.path_helpers import get_path


class TokenRedactionFilter(logging.Filter):
    """
    Filter that redacts tokens and secrets from log messages.

    Prevents accidental exposure of sensitive data in logs.
    """

    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = [
        (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
        (r'"api[_-]?token":\s*"[^"]*"', '"api_token": "[REDACTED]"'),
        (r'"client[_-]?secret":\s*"[^"]*"', '"client_secret": "[REDACTED]"'),
        (r'"password":\s*"[^"]*"', '"password": "[REDACTED]"'),
        (r'\b[A-Za-z0-9]{40,}\b', '[REDACTED_TOKEN]'),  # Long tokens
        (r'ey[A-Za-z0-9\-_]+\.ey[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', '[REDACTED_JWT]'),  # JWT tokens
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log record."""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
            record.msg = msg

        # Also check args if present
        if hasattr(record, 'args') and record.args:
            cleaned_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.SENSITIVE_PATTERNS:
                    arg_str = re.sub(pattern, replacement, arg_str, flags=re.IGNORECASE)
                cleaned_args.append(arg_str)
            record.args = tuple(cleaned_args)

        return True


class ContextFilter(logging.Filter):
    """
    Add context information to all log records.

    Adds org_id and elapsed time since logger creation.
    """

    def __init__(self, org_id: Optional[str] = None):
        super().__init__()
        self.org_id = org_id or "default"
        self.start_time = datetime.now(timezone.utc)

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context fields to record."""
        record.org_id = self.org_id
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        record.elapsed_ms = elapsed * 1000
        return True


class SafeFormatter(logging.Formatter):
    """
    Safe formatter that handles missing attributes gracefully.

    Prevents errors when format string references attributes that may not exist.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record, adding default values for missing attributes.

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        # Ensure custom attributes exist with defaults
        if not hasattr(record, 'org_id'):
            record.org_id = 'default'
        if not hasattr(record, 'elapsed_ms'):
            record.elapsed_ms = 0.0

        # Call parent formatter
        return super().format(record)


class TxoLogger:
    """
    Thread-safe singleton logger for the application.

    Features:
    - Automatic token redaction
    - Context-aware logging (org_id, elapsed time)
    - Configurable via JSON or falls back to defaults
    - Thread-safe singleton pattern
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize logger if not already initialized."""
        with self._lock:
            if not self._initialized:
                self.logger = logging.getLogger('TxoApp')
                self.context_filter = None
                self.token_filter = TokenRedactionFilter()
                self._setup_logger()
                self._initialized = True

    def _setup_logger(self) -> None:
        """
        Set up logger with configuration file or defaults.

        Tries to load logging-config.json, falls back to sensible defaults.
        """
        config_path = get_path('config', 'logging-config.json')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Set dynamic log file path
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_filename = f"app_{date_str}.log"
            log_path = str(get_path('logs', log_filename))

            # Update file handler path
            if 'handlers' in config and 'file' in config['handlers']:
                config['handlers']['file']['filename'] = log_path

            # Apply configuration
            logging.config.dictConfig(config)
            self.logger.debug(f"Logger configured from {config_path}")

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # Use default configuration
            self._setup_default_logging()
            self.logger.info(f"Using default logging config: {e}")

        # Always add token redaction filter
        self.logger.addFilter(self.token_filter)

    def _setup_default_logging(self) -> None:
        """Set up default logging configuration."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = str(get_path('logs', f"app_{date_str}.log"))

        # Create formatters (using SafeFormatter for file handler)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_formatter = SafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(org_id)s] [%(elapsed_ms).0fms] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # File handler (DEBUG and above)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # Configure logger
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear any existing handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def set_context(self, org_id: Optional[str] = None) -> None:
        """
        Set organizational context for logging.

        Args:
            org_id: Organization identifier for context
        """
        with self._lock:
            if self.context_filter:
                self.logger.removeFilter(self.context_filter)
            self.context_filter = ContextFilter(org_id)
            self.logger.addFilter(self.context_filter)
            self.logger.debug(f"Logger context set to org_id: {org_id or 'default'}")

    # Logging methods
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)


def setup_logger(org_id: Optional[str] = None) -> TxoLogger:
    """
    Get configured logger instance.

    Args:
        org_id: Optional organization identifier for context

    Returns:
        Configured TxoLogger instance

    Example:
        >>> logger = setup_logger("myorg")
        >>> logger.info("Processing started")
    """
    logger_instance = TxoLogger()
    if org_id:
        logger_instance.set_context(org_id)
    return logger_instance