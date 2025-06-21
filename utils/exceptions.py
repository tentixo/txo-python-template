# utils/exceptions.py - Fixed built-in name shadowing

from typing import Optional, Any, Dict
from dataclasses import dataclass


@dataclass
class ErrorContext:
    """Structured error context for better debugging"""
    operation: Optional[str] = None
    service_name: Optional[str] = None
    company_id: Optional[str] = None
    environment: Optional[str] = None
    url: Optional[str] = None
    payload_summary: Optional[str] = None  # Sanitized payload info
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class SOAPFaultInfo:
    """Structured SOAP fault information"""
    fault_code: Optional[str] = None
    fault_string: Optional[str] = None
    detail: Optional[str] = None
    fault_actor: Optional[str] = None

    def to_message(self) -> str:
        """Convert to human-readable error message"""
        parts = []
        if self.fault_string:
            parts.append(self.fault_string)
        if self.fault_code:
            parts.append(f"(Code: {self.fault_code})")
        if self.detail and self.detail != self.fault_string:
            parts.append(f"Detail: {self.detail}")
        return " | ".join(parts) if parts else "Unknown SOAP fault"

    @property
    def is_valid(self) -> bool:
        """Check if fault info contains meaningful data"""
        return bool(self.fault_string or self.fault_code)


class AzureBaseError(Exception):
    """Enhanced base exception for Azure operations"""

    def __init__(self, message: str,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize the base exception.

        Args:
            message: The error message
            correlation_id: Optional correlation ID for tracking the request
            context: Optional structured context information
        """
        self.correlation_id = correlation_id
        # Fix PyCharm warning by ensuring type is always ErrorContext
        self.context: ErrorContext = context or ErrorContext()
        super().__init__(message)

    def __str__(self) -> str:
        """Format the exception message with context"""
        base_message = super().__str__()

        parts = [f"{self.__class__.__name__}: {base_message}"]

        if self.correlation_id:
            parts.append(f"Correlation ID: {self.correlation_id}")

        if self.context.operation:
            parts.append(f"Operation: {self.context.operation}")

        return " | ".join(parts)

    def __repr__(self) -> str:
        return self.__str__()

    def get_logging_context(self) -> Dict[str, Any]:
        """Get structured context for logging"""
        context = {"exception_type": self.__class__.__name__}
        if self.correlation_id:
            context["correlation_id"] = self.correlation_id
        # Now PyCharm knows self.context is definitely ErrorContext
        context.update(self.context.to_dict())
        return context


class APIError(AzureBaseError):
    """Base API error - parent for REST and SOAP errors"""

    def __init__(self, message: str,
                 status_code: Optional[int] = None,
                 response: Optional[Any] = None,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize API error.

        Args:
            message: The error message
            status_code: HTTP status code
            response: Raw response object
            correlation_id: Optional correlation ID
            context: Optional structured context
        """
        self.status_code = status_code
        self.response = response

        # Build enhanced message with status
        enhanced_message = message
        if status_code:
            enhanced_message += f" (Status: {status_code})"

        super().__init__(enhanced_message, correlation_id, context)


class SOAPError(APIError):
    """SOAP-specific errors with fault information"""

    def __init__(self, message: str,
                 fault_info: Optional[SOAPFaultInfo] = None,
                 status_code: Optional[int] = None,
                 response: Optional[Any] = None,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize SOAP error with fault details.

        Args:
            message: Base error message
            fault_info: Structured SOAP fault information
            status_code: HTTP status code
            response: Raw response object
            correlation_id: Optional correlation ID
            context: Optional structured context
        """
        self.fault_info = fault_info

        # Build enhanced message with fault details
        enhanced_message = message
        if fault_info and fault_info.is_valid:
            enhanced_message += f": {fault_info.to_message()}"

        super().__init__(enhanced_message, status_code, response, correlation_id, context)

    @property
    def fault_code(self) -> Optional[str]:
        """Get fault code if available"""
        return self.fault_info.fault_code if self.fault_info else None

    @property
    def fault_string(self) -> Optional[str]:
        """Get fault string if available"""
        return self.fault_info.fault_string if self.fault_info else None


class BusinessCentralError(SOAPError):
    """Business Central specific business logic errors"""

    def __init__(self, message: str,
                 error_category: Optional[str] = None,
                 is_retryable: bool = False,
                 is_ignorable: bool = False,
                 fault_info: Optional[SOAPFaultInfo] = None,
                 status_code: Optional[int] = None,
                 response: Optional[Any] = None,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize Business Central error.

        Args:
            message: Error message
            error_category: Classification of error type
            is_retryable: Whether this error might succeed on retry
            is_ignorable: Whether this error can be safely ignored
            fault_info: SOAP fault details
            status_code: HTTP status code
            response: Raw response
            correlation_id: Correlation ID
            context: Error context
        """
        self.error_category = error_category
        self.is_retryable = is_retryable
        self.is_ignorable = is_ignorable

        super().__init__(message, fault_info, status_code, response, correlation_id, context)


class DuplicateEntityError(BusinessCentralError):
    """Entity already exists - usually ignorable"""

    def __init__(self, entity_type: str, entity_id: str, **kwargs):
        self.entity_type = entity_type
        self.entity_id = entity_id

        message = f"{entity_type} '{entity_id}' already exists"
        super().__init__(
            message,
            error_category="duplicate_entity",
            is_retryable=False,
            is_ignorable=True,
            **kwargs
        )


class BCValidationError(BusinessCentralError):
    """Business Central business rule validation failed"""

    def __init__(self, validation_rule: str, **kwargs):
        self.validation_rule = validation_rule

        super().__init__(
            f"Validation failed: {validation_rule}",
            error_category="validation_error",
            is_retryable=False,
            is_ignorable=False,
            **kwargs
        )


class ConcurrencyError(BusinessCentralError):
    """Record modified by another user - retryable"""

    def __init__(self, **kwargs):
        super().__init__(
            "Record was modified by another user",
            error_category="concurrency_error",
            is_retryable=True,
            is_ignorable=False,
            **kwargs
        )


class BCPermissionError(BusinessCentralError):
    """Business Central insufficient permissions - not retryable"""

    def __init__(self, required_permission: str = None, **kwargs):
        self.required_permission = required_permission

        message = "Access denied"
        if required_permission:
            message += f": requires {required_permission}"

        super().__init__(
            message,
            error_category="permission_error",
            is_retryable=False,
            is_ignorable=False,
            **kwargs
        )


class EntityNotFoundError(BusinessCentralError):
    """Referenced entity not found"""

    def __init__(self, entity_type: str, entity_id: str, **kwargs):
        self.entity_type = entity_type
        self.entity_id = entity_id

        super().__init__(
            f"{entity_type} '{entity_id}' not found",
            error_category="not_found",
            is_retryable=False,
            is_ignorable=False,
            **kwargs
        )


class AuthenticationError(AzureBaseError):
    """Authentication and authorization failures"""

    def __init__(self, message: str,
                 status_code: Optional[int] = None,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize authentication error.

        Args:
            message: The error message
            status_code: HTTP status code (typically 401 or 403)
            correlation_id: Optional correlation ID
            context: Optional error context
        """
        self.status_code = status_code
        status_detail = f" (Status: {status_code})" if status_code else ""
        super().__init__(f"{message}{status_detail}", correlation_id, context)


class ConfigError(AzureBaseError):
    """Configuration loading/validation failures"""

    def __init__(self, message: str,
                 config_path: Optional[str] = None,
                 correlation_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize configuration error.

        Args:
            message: The error message
            config_path: Path to the configuration file or section
            correlation_id: Optional correlation ID
            context: Optional error context
        """
        self.config_path = config_path
        path_detail = f" (Config: {config_path})" if config_path else ""
        super().__init__(f"{message}{path_detail}", correlation_id, context)


class APITimeoutError(APIError):
    """API request timeout errors"""

    def __init__(self, timeout_seconds: int, **kwargs):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Request timed out after {timeout_seconds} seconds",
            status_code=408,
            **kwargs
        )