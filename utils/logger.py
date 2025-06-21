# utils/logger.py
import logging
import logging.config
import json
import threading
from datetime import datetime, timezone
from typing import Optional

from utils.path_helpers import get_path


class ContextFilter(logging.Filter):
    """
    A logging filter that ensures every log record contains an org_id and elapsed_ms.
    """

    def __init__(self, org_id: Optional[str] = None):
        super().__init__()
        self.org_id = org_id or "n/a"
        self.start_time = datetime.now(timezone.utc)

    def filter(self, record: logging.LogRecord) -> bool:
        record.org_id = self.org_id
        record.elapsed_ms = (datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000
        return True


class SafeFormatter(logging.Formatter):
    """
    A custom formatter that ensures the 'org_id' and 'elapsed_ms' attributes
    are present in every log record. If missing, they default to 'N/A' and 0.0, respectively.
    """

    def format(self, record):
        if not hasattr(record, 'org_id'):
            record.org_id = "N/A"
        if not hasattr(record, 'elapsed_ms'):
            record.elapsed_ms = 0.0
        return super().format(record)


class TxoDefaultLogger:
    """
    Thread-safe singleton logger for the application.

    This class provides a centralized logging facility with context-aware
    logging capabilities. It reads configuration from a JSON file and
    falls back to sensible defaults if the configuration is unavailable.
    """
    _instance = None
    _lock = threading.Lock()

    # Default configuration file path
    DEFAULT_CONFIG_PATH = 'config/logging-config.json'

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self.logger = logging.getLogger('DmarcParser')
                self.context_filter = None
                self._setup_logger()
                self._initialized = True

    def _setup_logger(self) -> None:
        """
        Set up the logger using configuration from a JSON file.
        Falls back to basic configuration if the file is not found or invalid.
        """
        config_path = get_path('config', 'logging-config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Set the log file path dynamically based on current date
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_filename = f"bc_config_{date_str}.log"
            log_path = str(get_path('log', log_filename))

            # Update the file handler with the dynamic path
            if 'handlers' in config and 'file' in config['handlers']:
                config['handlers']['file']['filename'] = log_path

            # Apply the configuration
            logging.config.dictConfig(config)
            self.logger.debug(f"Logger configured with config from {config_path}")
            self.logger.debug(f"Log file: {log_path}")

        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError) as e:
            # Set up basic configuration if the config file is missing or invalid
            default_log_file = str(get_path('logs', f"txo_log_{datetime.now().strftime('%Y-%m-%d')}.log"))
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(default_log_file, encoding='utf-8')
                ]
            )
            self.logger.error(f"Failed to load logging config from {config_path}: {e}")
            self.logger.info(f"Using default logging configuration. Log file: {default_log_file}")

    def set_context(self, org_id: Optional[str] = None) -> None:
        """
        Set the organizational context for the logger.
        This adds org_id and elapsed_ms to all log records.

        Args:
            org_id: The organization identifier for the current context.
        """
        with self._lock:
            if self.context_filter:
                self.logger.removeFilter(self.context_filter)
            self.context_filter = ContextFilter(org_id)
            self.logger.addFilter(self.context_filter)
            self.logger.debug(f"Logger context set to org_id: {org_id or 'n/a'}")

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(msg, *args, **kwargs)


def setup_logger(org_id: Optional[str] = None) -> TxoDefaultLogger:
    """
    Get a configured logger instance with the specified organizational context.

    Args:
        org_id: Optional organization identifier for context.

    Returns:
        A configured TxoDefaultLogger instance.
    """
    logger_instance = TxoDefaultLogger()
    logger_instance.set_context(org_id)
    return logger_instance