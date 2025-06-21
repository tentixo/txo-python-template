# utils/api_helpers.py - All PyCharm warnings fixed

import json
import time
import re
import xml.etree.ElementTree as ElT  # Fixed: lowercase alias
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import quote, urlsplit, urlunsplit

import requests
from zeep import Client
from zeep.cache import SqliteCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport
from platformdirs import user_cache_dir
from pathlib import Path

# Fixed: Removed unused SOAPError import
from utils.exceptions import (
    APIError, BusinessCentralError, DuplicateEntityError,
    BCValidationError, ConcurrencyError, BCPermissionError, EntityNotFoundError,
    AuthenticationError, APITimeoutError, ErrorContext, SOAPFaultInfo
)
from utils.logger import setup_logger

logger = setup_logger()

# Default timeouts for REST and SOAP calls (in seconds)
REST_API_TIMEOUT_SECONDS = 30
SOAP_API_TIMEOUT_SECONDS = 60  # Increased from previous values
WSDL_API_TIMEOUT_SECONDS = 30


@dataclass
class APIResponse:
    """Enhanced API response with better error context"""

    def __init__(self, status_code: int,
                 error: Optional[str] = None,
                 data: Any = None,
                 request: Any = None,
                 context: Optional[ErrorContext] = None):
        """
        Initialize API response.

        Args:
            status_code: HTTP status code
            error: Error message if the request failed
            data: Response data if the request succeeded
            request: Original request information for debugging
            context: Structured error context
        """
        self.status_code = status_code
        self.error = error
        self.data = data
        self.request = request
        self.context = context or ErrorContext()

    @property
    def success(self) -> bool:
        """Check if response indicates success"""
        return self.error is None and 200 <= self.status_code < 300

    def to_exception(self) -> Optional[Exception]:
        """Convert failed response to appropriate exception"""
        if self.success:
            return None

        if self.status_code == 401:
            return AuthenticationError(self.error or "Authentication failed",
                                       status_code=self.status_code,
                                       context=self.context)

        return APIError(self.error or f"Request failed with status {self.status_code}",
                        status_code=self.status_code,
                        context=self.context)


class SOAPFaultDetector:
    """Centralized SOAP fault detection and parsing"""

    @staticmethod
    def detect_fault_in_response(response) -> Optional[SOAPFaultInfo]:
        """
        Detect and parse SOAP fault from various response types.

        Args:
            response: Response object (could be string, bytes, requests.Response, etc.)

        Returns:
            SOAPFaultInfo if fault detected, None otherwise
        """
        try:
            xml_content = SOAPFaultDetector._extract_xml_content(response)
            if not xml_content:
                return None

            # Quick check for SOAP fault indicators
            if not SOAPFaultDetector._contains_soap_fault(xml_content):
                return None

            return SOAPFaultDetector._parse_soap_fault_xml(xml_content)

        except Exception as e:
            logger.debug(f"Error detecting SOAP fault: {e}")
            return None

    @staticmethod
    def _extract_xml_content(response) -> Optional[str]:
        """Extract XML content from various response types"""
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'content'):
            content = response.content
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return str(content)
        elif isinstance(response, (str, bytes)):
            if isinstance(response, bytes):
                return response.decode('utf-8', errors='ignore')
            return response
        else:
            return str(response)

    @staticmethod
    def _contains_soap_fault(xml_content: str) -> bool:
        """Quick check if content contains SOAP fault indicators"""
        fault_indicators = [
            '<s:Fault>', '<soap:Fault>', '<Fault>',
            '<faultcode>', '<faultstring>'
        ]
        return any(indicator in xml_content for indicator in fault_indicators)

    @staticmethod
    def _parse_soap_fault_xml(xml_content: str) -> Optional[SOAPFaultInfo]:
        """Parse SOAP fault details from XML"""
        try:
            # Clean namespaces for easier parsing
            cleaned_xml = re.sub(r'xmlns[^=]*="[^"]*"', '', xml_content)

            root = ElT.fromstring(cleaned_xml)

            # Find fault element
            for fault_path in ['.//Fault', './/s:Fault', './/soap:Fault']:
                fault_element = root.find(fault_path)
                if fault_element is not None:
                    break

            if fault_element is None:
                return None

            fault_info = SOAPFaultInfo()

            # Extract fault components
            fault_info.fault_code = SOAPFaultDetector._get_element_text(fault_element, './/faultcode')
            fault_info.fault_string = SOAPFaultDetector._get_element_text(fault_element, './/faultstring')
            fault_info.fault_actor = SOAPFaultDetector._get_element_text(fault_element, './/faultactor')

            # Extract detail (may be nested) - FIX: Proper None check
            detail_elem = fault_element.find('.//detail')
            if detail_elem is not None:
                fault_info.detail = SOAPFaultDetector._extract_detail_text(detail_elem)

            return fault_info if fault_info.is_valid else None

        except ElT.ParseError as e:
            logger.debug(f"XML parse error in SOAP fault detection: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error parsing SOAP fault: {e}")
            return None

    @staticmethod
    def _get_element_text(parent, xpath: str) -> Optional[str]:
        """Safely extract text from XML element"""
        elem = parent.find(xpath)
        return elem.text.strip() if elem is not None and elem.text else None

    @staticmethod
    def _extract_detail_text(detail_elem) -> str:
        """Extract text from detail element, handling nested content"""
        texts = []
        if detail_elem.text:
            texts.append(detail_elem.text.strip())

        for child in detail_elem:
            if child.text:
                texts.append(child.text.strip())

        return " ".join(filter(None, texts))


class BusinessCentralErrorClassifier:
    """Classify Business Central specific errors"""

    ERROR_PATTERNS = {
        'duplicate_entity': [
            r'already exists',
            r'already has.*contact business relation',
            r'duplicate.*key',
            r'record.*already.*exists',
            r'entity.*already.*exists'
        ],
        'not_found': [
            r'not found',
            r'does not exist',
            r'cannot find',
            r'no.*record.*found',
            r'record.*not.*found'
        ],
        'validation_error': [
            r'validation.*failed',
            r'invalid.*value',
            r'required.*field',
            r'constraint.*violation',
            r'business.*rule.*violation'
        ],
        'permission_error': [
            r'access.*denied',
            r'permission.*denied',
            r'unauthorized',
            r'insufficient.*privileges',
            r'not.*allowed'
        ],
        'concurrency_error': [
            r'other user has modified',
            r'concurrency.*conflict',
            r'record.*changed.*another.*user',
            r'modified.*by.*another.*user'
        ],
        'timeout_error': [
            r'timeout',
            r'timed out',
            r'request.*timeout',
            r'operation.*timeout'
        ]
    }

    @classmethod
    def classify_error(cls, error_message: str, fault_code: str = None) -> str:
        """
        Classify error message and fault code into categories.

        Args:
            error_message: Error message to classify
            fault_code: Optional SOAP fault code

        Returns:
            Error category string
        """
        if not error_message:
            return 'unknown_error'

        error_lower = error_message.lower()

        # Check fault code first (more reliable)
        if fault_code:
            fault_category = cls._classify_by_fault_code(fault_code)
            if fault_category != 'unknown_error':
                return fault_category

        # Check message patterns
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return category

        return 'unknown_error'

    @classmethod
    def _classify_by_fault_code(cls, fault_code: str) -> str:
        """Classify by SOAP fault code"""
        if not fault_code:
            return 'unknown_error'

        fault_lower = fault_code.lower()

        if 'duplicate' in fault_lower or 'exists' in fault_lower:
            return 'duplicate_entity'
        elif 'notfound' in fault_lower or 'missing' in fault_lower:
            return 'not_found'
        elif 'validation' in fault_lower or 'invalid' in fault_lower:
            return 'validation_error'
        elif 'unauthorized' in fault_lower or 'permission' in fault_lower:
            return 'permission_error'
        elif 'concurrency' in fault_lower or 'modified' in fault_lower:
            return 'concurrency_error'
        elif 'timeout' in fault_lower:
            return 'timeout_error'

        return 'unknown_error'

    @classmethod
    def create_business_exception(cls, error_message: str,
                                  fault_info: Optional[SOAPFaultInfo] = None,
                                  context: Optional[ErrorContext] = None,
                                  **kwargs) -> BusinessCentralError:
        """
        Create appropriate Business Central exception based on error classification.

        Args:
            error_message: Error message
            fault_info: SOAP fault information
            context: Error context
            **kwargs: Additional arguments for exception

        Returns:
            Appropriate BusinessCentralError subclass
        """
        category = cls.classify_error(error_message,
                                      fault_info.fault_code if fault_info else None)

        common_args = {
            'fault_info': fault_info,
            'context': context,
            **kwargs
        }

        if category == 'duplicate_entity':
            entity_type = context.service_name if context and context.service_name else "Entity"
            entity_id = "unknown"
            # Try to extract entity ID from message
            match = re.search(r"(\w+)\s+['\"]?([^'\"\s]+)['\"]?\s+already", error_message, re.IGNORECASE)
            if match:
                entity_type, entity_id = match.groups()

            return DuplicateEntityError(entity_type, entity_id, **common_args)

        elif category == 'not_found':
            entity_type = context.service_name if context and context.service_name else "Entity"
            entity_id = "unknown"
            # Try to extract entity info from message
            match = re.search(r"(\w+)\s+['\"]?([^'\"\s]+)['\"]?\s+(?:not found|does not exist)",
                              error_message, re.IGNORECASE)
            if match:
                entity_type, entity_id = match.groups()

            return EntityNotFoundError(entity_type, entity_id, **common_args)

        elif category == 'validation_error':
            return BCValidationError(error_message, **common_args)

        elif category == 'permission_error':
            return BCPermissionError(**common_args)

        elif category == 'concurrency_error':
            return ConcurrencyError(**common_args)

        else:
            # Generic BusinessCentralError
            return BusinessCentralError(
                error_message,
                error_category=category,
                is_retryable=(category == 'concurrency_error'),
                is_ignorable=(category == 'duplicate_entity'),
                **common_args
            )


def soap_error_handler(operation_name: str):
    """
    Decorator for centralized SOAP error handling.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, url: str, service_name: str, *args, **kwargs):
            context = ErrorContext(
                operation=operation_name,
                service_name=service_name,
                url=url,
                timestamp=datetime.now().isoformat()
            )

            try:
                return func(self, url, service_name, *args, context=context, **kwargs)

            except Fault as fault:
                # Handle Zeep Fault exceptions - FIX: Proper fault.detail handling
                detail_text = None
                if fault.detail is not None:
                    if hasattr(fault.detail, 'text') and fault.detail.text:
                        detail_text = fault.detail.text
                    else:
                        detail_text = str(fault.detail)

                fault_info = SOAPFaultInfo(
                    fault_code=getattr(fault, 'code', None) or getattr(fault, 'faultcode', None),
                    fault_string=fault.message,
                    detail=detail_text
                )

                # Create appropriate business exception
                bc_error = BusinessCentralErrorClassifier.create_business_exception(
                    fault.message, fault_info, context, response=fault
                )

                logger.error(f"SOAP {operation_name} fault for {service_name}: {bc_error}",
                             extra=bc_error.get_logging_context())

                raise_for_status = kwargs.get('raise_for_status', True)
                if raise_for_status:
                    raise bc_error

                return APIResponse(500, error=str(bc_error), context=context)

            except Exception as e:
                logger.error(f"Unexpected error in SOAP {operation_name} for {service_name}: {e}",
                             extra=context.to_dict())

                raise_for_status = kwargs.get('raise_for_status', True)
                if raise_for_status:
                    raise APIError(f"Unexpected error in SOAP {operation_name}: {e}", context=context)

                return APIResponse(500, error=str(e), context=context)

        return wrapper
    return decorator


def _normalize_url(url: str) -> str:
    """Normalize URL for consistent caching"""
    parts = urlsplit(url)
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        quote(parts.path),
        quote(parts.query, safe="=&"),
        quote(parts.fragment)
    ))


def _detect_and_handle_soap_fault(response, operation: str, service_name: str,
                                  context: ErrorContext, raise_for_status: bool) -> Optional[APIResponse]:
    """
    Detect SOAP fault in response and handle appropriately.

    Returns:
        APIResponse if fault detected, None if no fault
    """
    fault_info = SOAPFaultDetector.detect_fault_in_response(response)
    if not fault_info:
        return None

    # Create appropriate business exception
    bc_error = BusinessCentralErrorClassifier.create_business_exception(
        fault_info.fault_string or "SOAP Fault occurred",
        fault_info,
        context,
        response=response
    )

    logger.error(f"SOAP {operation} fault for {service_name}: {bc_error}",
                 extra=bc_error.get_logging_context())

    if raise_for_status:
        raise bc_error

    return APIResponse(500, error=str(bc_error), context=context)


def _find_matching_record(data, payload: Dict[str, Any], filter_fields: List[str]):
    """Find record that matches all filter fields"""
    if not isinstance(data, list):
        return data

    for record in data:
        if all(record.get(field) == payload.get(field) for field in filter_fields):
            return record
    return None


def _create_payload_summary(payload: Dict[str, Any]) -> str:
    """Create sanitized payload summary for logging"""
    sensitive_fields = {'Key', 'Password', 'Token', 'Secret'}
    summary = {}

    for key, value in payload.items():
        if key in sensitive_fields:
            summary[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 50:
            summary[key] = f"{value[:47]}..."
        else:
            summary[key] = value

    return str(summary)


def _is_duplicate_error(error_message: str) -> bool:
    """
    Check if error message indicates a duplicate/existing record.

    Args:
        error_message: Error message to check

    Returns:
        True if error indicates duplicate record
    """
    if not error_message:
        return False

    error_lower = error_message.lower()

    # BC-specific duplicate indicators
    duplicate_patterns = [
        "already exists",
        "already has a contact business relation",
        "duplicate",
        "record already exists",
        "entity already exists",
        "violates unique constraint",
        "primary key constraint",
        "unique key constraint"
    ]

    return any(pattern in error_lower for pattern in duplicate_patterns)


def _handle_soap_response(response, operation: str, service_name: str,
                          context: ErrorContext, raise_for_status: bool,
                          request_xml: str = None, response_xml: str = None) -> APIResponse:
    """
    Common error handling for SOAP responses across create/update operations.

    Args:
        response: SOAP response object
        operation: Operation name (Create, Update, etc.)
        service_name: BC service name
        context: Error context
        raise_for_status: Whether to raise exceptions
        request_xml: Request XML for debugging
        response_xml: Response XML for debugging

    Returns:
        APIResponse or raises exception
    """
    # Check for SOAP faults in response
    fault_response = _detect_and_handle_soap_fault(
        response, operation, service_name, context, raise_for_status
    )
    if fault_response:
        # Add debug info to fault response
        if context:
            context.request_id = f"{operation.lower()}_{service_name}_{int(time.time())}"
        logger.debug(f"SOAP {operation} fault - Request XML: {request_xml}")
        logger.debug(f"SOAP {operation} fault - Response XML: {response_xml}")
        return fault_response

    # Check HTTP status
    status_code = getattr(response, 'status_code', 200)
    if status_code >= 400:
        error_msg = f"SOAP {operation} operation failed with status {status_code}"
        logger.error(f"{error_msg} for {service_name}")
        logger.debug(f"SOAP {operation} error - Request XML: {request_xml}")
        logger.debug(f"SOAP {operation} error - Response XML: {response_xml}")

        if raise_for_status:
            raise APIError(error_msg, status_code=status_code, response=response, context=context)
        return APIResponse(status_code, error=error_msg, context=context)

    logger.debug(f"SOAP {operation} successful for {service_name}")
    return APIResponse(status_code, data=response, context=context, request=request_xml)


class SoapAPI:
    """Enhanced SOAP API client with comprehensive error handling"""

    def __init__(
            self,
            token: str,
            timeout: int = SOAP_API_TIMEOUT_SECONDS,
            wsdl_timeout: int = WSDL_API_TIMEOUT_SECONDS,
            additional_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the SOAP API client.

        Args:
            token: Azure Bearer token
            timeout: Per‐operation timeout in seconds
            wsdl_timeout: Timeout for loading WSDL/XSD in seconds
            additional_headers: Optional extra headers
        """
        self.headers = {"Authorization": f"Bearer {token}"}
        if additional_headers:
            self.headers.update(additional_headers)

        self.session = self._create_session_with_fallback()
        self.transport = self._create_transport(wsdl_timeout, timeout)
        self.timeout = timeout
        self._client_cache: Dict[str, Client] = {}
        self.history = HistoryPlugin()

        logger.debug(
            f"Initialized SOAP API (op_timeout={timeout}s, wsdl_timeout={wsdl_timeout}s)"
        )

    @classmethod
    def from_headers(cls, headers: Dict[str, str],
                     timeout: int = SOAP_API_TIMEOUT_SECONDS,
                     wsdl_timeout: int = WSDL_API_TIMEOUT_SECONDS) -> 'SoapAPI':
        """Alternative constructor using pre‐built headers."""
        instance = cls.__new__(cls)
        instance.headers = headers
        instance.timeout = timeout
        instance.session = instance._create_session_with_fallback()
        instance.transport = instance._create_transport(wsdl_timeout, timeout)
        instance._client_cache = {}
        logger.debug(f"Initialized SOAP API from headers (op timeout={timeout}s, WSDL timeout={wsdl_timeout}s)")
        return instance

    def _create_session_with_fallback(self) -> requests.Session:
        """Create requests session with proper timeout configuration"""
        session = requests.Session()
        session.headers.update(self.headers)

        # Configure adapters with retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        return session

    def _get_request_response_xml(self):
        """Helper method to extract request/response XML from history"""
        request_xml = None
        response_xml = None

        if self.history.last_sent:
            envelope = self.history.last_sent.get('envelope')
            if envelope:
                request_xml = envelope.decode('utf-8') if isinstance(envelope, bytes) else str(envelope)

        if self.history.last_received:
            envelope = self.history.last_received.get('envelope')
            if envelope:
                response_xml = envelope.decode('utf-8') if isinstance(envelope, bytes) else str(envelope)

        return request_xml, response_xml

    def _create_transport(self, wsdl_timeout: int, operation_timeout: int) -> Transport:
        """Create Zeep transport with proper timeout configuration"""
        cache_dir = Path(user_cache_dir("tentixo-bc-rapid"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "wsdl_cache.sqlite"

        cache = SqliteCache(path=str(cache_path), timeout=3600)
        return Transport(
            session=self.session,
            cache=cache,
            timeout=wsdl_timeout,  # For WSDL/XSD loading
            operation_timeout=operation_timeout  # For SOAP operations
        )

    def reinitialize(self, new_token: str, timeout: Optional[int] = None):
        """Reinitialize with new token and proper timeout handling"""
        self.headers = {"Authorization": f"Bearer {new_token}"}

        if timeout is not None:
            self.timeout = timeout

        self.session = self._create_session_with_fallback()
        self.transport = self._create_transport(WSDL_API_TIMEOUT_SECONDS, self.timeout)
        self._client_cache = {}  # Clear cache

        logger.debug(f"Reinitialized SOAP API with new token and operation_timeout {self.timeout}s")

    def get_client(self, url: str) -> Client:
        """Get cached SOAP client for URL"""
        normalized_url = _normalize_url(url)

        if normalized_url not in self._client_cache:
            try:
                logger.debug(f"Creating SOAP client for {normalized_url}")
                # Add the history plugin to capture requests/responses
                client = Client(normalized_url, transport=self.transport, plugins=[self.history])
                self._client_cache[normalized_url] = client
            except Exception as e:
                logger.error(f"Failed to create SOAP client for {normalized_url}: {e}")
                raise APIError(f"SOAP client initialization failed: {e}")

        return self._client_cache[normalized_url]

    @soap_error_handler("Read")
    def read(self, url: str, service_name: str, params: Dict[str, Any],
            context: ErrorContext = None) -> APIResponse:
        """
        Perform a SOAP Read operation.
        """
        client = self.get_client(url)

        logger.debug(f"SOAP Read: {service_name} at {url} with params {params}")

        response = client.service.Read(**params)

        data = serialize_object(response) if response else {}
        return APIResponse(200, data=data, context=context)

    @soap_error_handler("ReadMultiple")
    def read_multiple(self, url: str, service_name: str,
                      filters: Optional[List[Dict[str, str]]] = None,
                      set_size: int = 200,
                      context: ErrorContext = None) -> APIResponse:
        """
        Perform a SOAP ReadMultiple operation.
        """
        client = self.get_client(url)

        logger.debug(f"SOAP ReadMultiple: {service_name} at {url}")

        filter_list = filters if filters else [{'Field': 'Name', 'Criteria': '*'}]

        response = client.service.ReadMultiple(filter=filter_list, setSize=set_size)

        data = [serialize_object(r) for r in response] if response else []
        return APIResponse(200, data=data, context=context)

    @soap_error_handler("Create")
    def create(self, url: str, service_name: str, payload: Dict[str, Any],
               raise_for_status: bool = True, context: ErrorContext = None) -> APIResponse:
        """
        Perform a SOAP Create operation with enhanced error handling.
        """
        client = self.get_client(url)
        factory = client.type_factory('ns0')

        # Add payload summary to context (sanitized)
        if context:
            context.payload_summary = _create_payload_summary(payload)

        logger.debug(f"SOAP Create: {service_name} at {url}")

        try:
            soap_obj = getattr(factory, service_name)(**payload)
            response = client.service.Create(soap_obj)

            # Capture request/response XML for debugging
            request_xml, response_xml = self._get_request_response_xml()

            # Use common error handling
            return _handle_soap_response(
                response, "Create", service_name, context, raise_for_status,
                request_xml, response_xml
            )

        except Exception as e:
            # Log request/response for debugging on error
            request_xml, response_xml = self._get_request_response_xml()
            logger.debug(f"SOAP Create error - Request XML: {request_xml}: {e}")
            logger.debug(f"SOAP Create error - Response XML: {response_xml}: {e}")
            raise

    @soap_error_handler("Update")
    def update(self, url: str, service_name: str, payload: Dict[str, Any],
               raise_for_status: bool = True, context: ErrorContext = None) -> APIResponse:
        """
        Perform a SOAP Update operation with enhanced error handling.
        """
        if not isinstance(payload, dict) or "Key" not in payload:
            error_msg = "Invalid payload for Update: Must be a dict with Key"
            logger.error(f"{error_msg}, got {payload}")

            if raise_for_status:
                raise APIError(error_msg, status_code=400, context=context)
            return APIResponse(400, error=error_msg, context=context)

        client = self.get_client(url)
        factory = client.type_factory('ns0')

        # Add payload summary to context
        if context:
            context.payload_summary = _create_payload_summary(payload)

        logger.debug(f"SOAP Update: {service_name} at {url}")

        try:
            soap_obj = getattr(factory, service_name)(**payload)
            response = client.service.Update(soap_obj)

            # Capture request/response XML for debugging
            request_xml, response_xml = self._get_request_response_xml()

            # Use common error handling
            return _handle_soap_response(
                response, "Update", service_name, context, raise_for_status,
                request_xml, response_xml
            )

        except Exception as e:
            # Log request/response for debugging on error
            request_xml, response_xml = self._get_request_response_xml()
            logger.debug(f"SOAP Update error - Request XML: {request_xml}: {e}")
            logger.debug(f"SOAP Update error - Response XML: {response_xml}: {e}")
            raise

    def create_or_update(self, url: str, service_name: str, payload: Dict[str, Any],
                         filter_fields: List[str], company_id: str = None,
                         raise_for_status: bool = True) -> APIResponse:
        """
        Idempotent operation: Try Create first, fallback to Update if record exists.

        Args:
            url: SOAP endpoint URL
            service_name: BC service name (CustomerCard, VendorCard, etc.)
            payload: Data to create/update
            filter_fields: Fields to use for finding existing record (for Update)
            company_id: Company ID (for logging context)
            raise_for_status: Whether to raise exceptions on errors

        Returns:
            APIResponse with operation result
        """
        # Remove Key from payload for Create operation
        create_payload = {k: v for k, v in payload.items() if k != "Key"}

        try:
            # Phase 1: Try Create
            logger.debug(f"Attempting Create for {service_name} in {company_id or 'unknown company'}")

            # Don't pass context explicitly - let the decorator handle it
            create_response = self.create(url, service_name, create_payload, raise_for_status=False)

            if create_response.success:
                logger.info(f"Successfully created {service_name} in {company_id or 'unknown company'}")
                return create_response

            # Phase 2: Check if failure is due to existing record
            if not _is_duplicate_error(create_response.error):
                # Non-duplicate error - don't attempt update
                logger.error(f"Create failed with non-duplicate error for {service_name}: {create_response.error}")
                if raise_for_status:
                    if hasattr(create_response, 'to_exception') and create_response.to_exception():
                        raise create_response.to_exception()
                    raise APIError(f"Create operation failed: {create_response.error}")
                return create_response

            # Phase 3: Record exists, try Update
            logger.info(f"Record exists for {service_name}, attempting Update in {company_id or 'unknown company'}")

            try:
                # Fetch the Key for existing record
                key = self.fetch_key_for_api(url, service_name, company_id or "",
                                             create_payload, filter_fields, raise_for_status=False)
                if not key:
                    error_msg = f"Could not fetch Key for existing {service_name} record"
                    logger.error(error_msg)
                    if raise_for_status:
                        raise EntityNotFoundError(service_name, str(create_payload))
                    return APIResponse(404, error=error_msg)

                # Perform Update with Key
                update_payload = payload.copy()
                update_payload["Key"] = key

                # Don't pass context explicitly - let the decorator handle it
                update_response = self.update(url, service_name, update_payload, raise_for_status=raise_for_status)

                if update_response.success:
                    logger.info(f"Successfully updated existing {service_name} in {company_id or 'unknown company'}")

                return update_response

            except Exception as update_error:
                error_msg = f"Update fallback failed for {service_name}: {update_error}"
                logger.error(error_msg)
                if raise_for_status:
                    raise APIError(error_msg)
                return APIResponse(500, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error in create_or_update for {service_name}: {e}"
            logger.error(error_msg)
            if raise_for_status:
                raise APIError(error_msg)
            return APIResponse(500, error=error_msg)

    @soap_error_handler("Delete")
    def delete(self, url: str, service_name: str, payload: Dict[str, Any],
               raise_for_status: bool = True, context: ErrorContext = None) -> APIResponse:
        """
        Perform a SOAP Delete operation.

        Note: raise_for_status is handled by the @soap_error_handler decorator
        """
        key = payload.get("Key")
        if not key:
            error_msg = f"No Key provided for Delete operation in {service_name}"
            logger.error(error_msg)

            if raise_for_status:
                raise APIError(error_msg, status_code=400, context=context)
            return APIResponse(400, error=error_msg, context=context)

        client = self.get_client(url)

        logger.debug(f"SOAP Delete: {service_name} at {url}")

        with client.settings(timeout=self.timeout):
            response = client.service.Delete(key)

        if response:
            return APIResponse(200, context=context)
        else:
            error_msg = f"Delete failed for {service_name} - record not found or already deleted"
            logger.error(error_msg)

            if raise_for_status:
                raise EntityNotFoundError(service_name, key, context=context)
            return APIResponse(404, error=error_msg, context=context)

    def update_multiple(self, url: str, service_name: str, payload_list: Dict[str, list],
                        raise_for_status: bool = True) -> APIResponse:
        """
        Perform a SOAP UpdateMultiple operation for batch updates.
        """
        client = self.get_client(url)
        factory = client.type_factory('ns0')

        wrapper = f"{service_name}_List"
        entries = payload_list.get(wrapper, [])

        context = ErrorContext(
            operation="UpdateMultiple",
            service_name=service_name,
            url=url,
            timestamp=datetime.now().isoformat()
        )

        logger.debug(f"SOAP UpdateMultiple: {service_name} at {url} with {len(entries)} entries")

        if not entries:
            msg = f"Empty {wrapper}"
            logger.warning(f"{msg} sent for {service_name} in {url}")
            if raise_for_status:
                raise APIError(msg, context=context)
            return APIResponse(400, error=msg, context=context)

        # Build Zeep objects
        soap_objects = []
        for entry in entries:
            if not isinstance(entry, dict):
                logger.error(f"Invalid entry in {wrapper}: {entry!r}")
                continue
            soap_objects.append(getattr(factory, service_name)(**entry))

        # Call UpdateMultiple
        try:
            response = client.service.UpdateMultiple(**{wrapper: soap_objects})

            # Capture request/response XML for debugging
            request_xml, response_xml = self._get_request_response_xml()

            # Use common error handling
            return _handle_soap_response(
                response, "UpdateMultiple", service_name, context, raise_for_status,
                request_xml, response_xml
            )

        except Fault as fault:
            faultstr = str(fault)
            # Concurrency conflict—treat as non-fatal
            if "Other user has modified" in faultstr:
                logger.warning(f"[Concurrency] {service_name} batch conflict: {faultstr}")
                return APIResponse(200, data=None, context=context)

            # Handle as regular fault
            fault_info = SOAPFaultInfo(
                fault_code=getattr(fault, 'code', None),
                fault_string=fault.message
            )
            if fault.detail is not None:
                if hasattr(fault.detail, 'text') and fault.detail.text:
                    fault_info.detail = fault.detail.text
                else:
                    fault_info.detail = str(fault.detail)

            bc_error = BusinessCentralErrorClassifier.create_business_exception(
                fault.message, fault_info, context, response=fault
            )

            if raise_for_status:
                raise bc_error
            return APIResponse(500, error=str(bc_error), context=context)

        except Exception as e:
            # Log request/response for debugging on error
            request_xml, response_xml = self._get_request_response_xml()
            logger.debug(f"SOAP UpdateMultiple error - Request XML: {request_xml}: {e}")
            logger.debug(f"SOAP UpdateMultiple error - Response XML: {response_xml}: {e}")
            raise

    def fetch_key_for_api(self, url: str, service_name: str, company_id: str,
                          payload: Dict[str, Any], filter_fields: List[str],
                          raise_for_status: bool = True) -> str:
        """Fetch the Key (eTag) for a specific API with enhanced error handling"""
        if not filter_fields:
            error_msg = f"'filter_fields' must be provided and non-empty for {service_name}"
            if raise_for_status:
                raise ValueError(error_msg)
            return ""

        # Build filters from payload
        filters = []
        for field in filter_fields:
            value = payload.get(field)
            if value is None:
                error_msg = f"Missing required field '{field}' in payload for {service_name} in {company_id}"
                if raise_for_status:
                    raise ValueError(error_msg)
                return ""
            filters.append({"Field": field, "Criteria": value})

        context = ErrorContext(
            operation="FetchKey",
            service_name=service_name,
            company_id=company_id,
            url=url
        )

        logger.debug(f"Fetching Key for {service_name} using filters {filters} in {company_id}")

        try:
            read_resp = self.read_multiple(url, service_name, filters=filters,
                                           raise_for_status=raise_for_status)
        except Exception as e:
            error_msg = f"Error fetching key for {service_name} in {company_id}: {e}"
            logger.error(error_msg)
            if raise_for_status:
                raise APIError(error_msg, context=context)
            return ""

        if read_resp.error:
            error_msg = f"Error fetching key for {service_name} in {company_id}: {read_resp.error}"
            logger.error(error_msg)
            if raise_for_status:
                raise APIError(error_msg, response=read_resp, context=context)
            return ""

        # Handle empty results with fallback
        if not read_resp.data:
            return self._fetch_key_with_fallback(url, service_name, company_id,
                                                 payload, filter_fields, raise_for_status, context)

        # Find matching record
        matching_record = _find_matching_record(read_resp.data, payload, filter_fields)
        if not matching_record:
            matching_record = read_resp.data[0] if isinstance(read_resp.data, list) else read_resp.data

        key = matching_record.get("Key")
        if not key:
            error_msg = f"No Key found for {service_name} in {company_id} using filters {filters}"
            if raise_for_status:
                raise APIError(error_msg, context=context)
            return ""

        logger.debug(f"Found Key for {service_name} in {company_id}: {key}")
        return key

    def _fetch_key_with_fallback(self, url: str, service_name: str, company_id: str,
                                 payload: Dict[str, Any], filter_fields: List[str],
                                 raise_for_status: bool, context: ErrorContext) -> str:
        """Fallback key fetching with wildcard filters"""
        fallback_filters = [{"Field": field, "Criteria": "*"} for field in filter_fields]
        logger.debug(f"No records found, trying fallback filters {fallback_filters}")

        try:
            read_resp = self.read_multiple(url, service_name, filters=fallback_filters,
                                           raise_for_status=raise_for_status)
        except Exception as e:
            logger.error(f"Error with fallback filters: {e}")
            if raise_for_status:
                raise APIError(f"Error fetching key with fallback filters for {company_id}: {e}", context=context)
            return ""

        if read_resp.error or not read_resp.data:
            if raise_for_status:
                raise EntityNotFoundError(service_name, str(payload), context=context)
            return ""

        # Use first available record as fallback
        first_record = read_resp.data[0] if isinstance(read_resp.data, list) else read_resp.data
        return first_record.get("Key", "")


def _handle_rest_response(response: requests.Response, identifier: Optional[str] = None,
                          raw: bool = False, context: ErrorContext = None) -> APIResponse:
    """Process HTTP response with enhanced error context and debugging"""
    try:
        # Log response details for debugging
        logger.debug(f"Response status: {response.status_code}, "
                     f"headers: {dict(response.headers)}, "
                     f"content-length: {len(response.content)}")

        if raw:
            data = response.text
        elif response.status_code in (202, 204):
            data = None
        else:
            try:
                data = response.json()

                # Log OData-specific information if present
                if isinstance(data, dict):
                    if "@odata.count" in data:
                        logger.debug(f"OData count: {data['@odata.count']}")
                    if "value" in data and isinstance(data["value"], list):
                        logger.debug(f"OData value array length: {len(data['value'])}")

            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract useful info from text
                text_content = response.text[:500] if response.text else "No content"
                logger.debug(f"JSON decode failed, response text: {text_content}")
                data = {"error": "Invalid JSON response", "raw_content": response.text}

        if response.status_code >= 400:
            # Enhanced error message extraction
            error_msg = _extract_rest_error_message(response, data)
            logger.error(f"HTTP {response.status_code}{f' ({identifier})' if identifier else ''}: {error_msg}")
            return APIResponse(response.status_code, error=error_msg, context=context)

        logger.debug(f"Request successful{f' ({identifier})' if identifier else ''}: status {response.status_code}")
        return APIResponse(response.status_code, data=data, context=context)

    except Exception as e:
        error_msg = f"Error processing response: {e}"
        logger.error(f"{error_msg}{f' ({identifier})' if identifier else ''}")
        return APIResponse(response.status_code if hasattr(response, 'status_code') else 500,
                           error=error_msg, context=context)

def _extract_rest_error_message(response: requests.Response, data: Any) -> str:
    """Extract meaningful error message from REST response"""
    # Try to get error from JSON data first
    if isinstance(data, dict):
        # OData error format
        if "error" in data:
            error_obj = data["error"]
            if isinstance(error_obj, dict):
                message = error_obj.get("message", {})
                if isinstance(message, dict):
                    return message.get("value", str(error_obj))
                return str(message) if message else str(error_obj)
            return str(error_obj)

        # Other error formats
        for key in ["message", "Message", "detail", "Detail"]:
            if key in data:
                return str(data[key])

    # Fallback to response text
    if response.text:
        return response.text[:1000]  # Limit error message length

    return f"HTTP {response.status_code} - No error details available"


def _should_retry_rest_request(status_code: int, attempt: int, max_retries: int) -> bool:
    """Determine if REST request should be retried based on status code and attempt number"""
    if attempt >= max_retries:
        return False

    # Retry on server errors and rate limiting
    retryable_codes = {429, 500, 502, 503, 504}
    return status_code in retryable_codes


def _calculate_rest_backoff_delay(attempt: int, retry_after: Optional[str] = None,
                                  backoff_factor: float = 1.5) -> float:
    """Calculate delay before retry with exponential backoff"""
    if retry_after:
        try:
            return float(retry_after)
        except (ValueError, TypeError):
            pass

    # Exponential backoff with jitter
    base_delay = backoff_factor ** attempt
    return min(base_delay, 30)  # Cap at 30 seconds


class RestAPI:
    """Enhanced REST API client with comprehensive error handling and retry logic"""

    def __init__(self, token: str, timeout: int = REST_API_TIMEOUT_SECONDS,
                 additional_headers: Optional[Dict[str, str]] = None):
        """Initialize the REST API client with enhanced configuration"""
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        if additional_headers:
            self.headers.update(additional_headers)
        self.timeout = timeout
        self.max_retries = 3
        self.backoff_factor = 1.5
        logger.debug(f"Initialized REST API with timeout {timeout}s and max_retries {self.max_retries}")

    @classmethod
    def from_headers(cls, headers: Dict[str, str], timeout: int = REST_API_TIMEOUT_SECONDS) -> 'RestAPI':
        """Alternative constructor from headers"""
        instance = cls.__new__(cls)
        instance.headers = headers
        instance.timeout = timeout
        instance.max_retries = 3
        instance.backoff_factor = 1.5
        logger.debug(f"Initialized REST API from headers with timeout {timeout}s")
        return instance

    def _execute_request(self, method: str, url: str,
                         identifier: Optional[str] = None,
                         timeout: Optional[int] = None,
                         headers: Optional[Dict[str, str]] = None,
                         raw: bool = False,
                         raise_for_status: bool = True,
                         **kwargs) -> APIResponse:
        """Execute REST API request with enhanced error handling and retry logic"""
        request_headers = {**self.headers, **(headers or {})}
        request_method = getattr(requests, method.lower())
        actual_timeout = timeout if timeout is not None else self.timeout

        context = ErrorContext(
            operation=method.upper(),
            url=url,
            timestamp=datetime.now().isoformat()
        )

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.debug(f"Retry attempt {attempt}/{self.max_retries} for {method.upper()} {url}")

                response = request_method(url, headers=request_headers, timeout=actual_timeout, **kwargs)
                api_response = _handle_rest_response(response, identifier, raw, context)

                # Check if we should retry
                if (api_response.status_code >= 400 and
                        _should_retry_rest_request(api_response.status_code, attempt, self.max_retries) and
                        attempt < self.max_retries):
                    retry_after = response.headers.get('Retry-After')
                    delay = _calculate_rest_backoff_delay(attempt, retry_after, self.backoff_factor)

                    logger.warning(f"Request failed with status {api_response.status_code}, "
                                   f"retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue

                # Handle final errors
                if raise_for_status and api_response.status_code >= 400:
                    correlation_id = response.headers.get('x-ms-correlation-request-id')

                    if api_response.status_code == 401:
                        raise AuthenticationError(
                            f"Authentication failed: {api_response.error}",
                            status_code=api_response.status_code,
                            correlation_id=correlation_id,
                            context=context
                        )
                    elif api_response.status_code == 403:
                        raise APIError(
                            f"Access forbidden: {api_response.error}",
                            status_code=api_response.status_code,
                            correlation_id=correlation_id,
                            context=context
                        )
                    elif api_response.status_code == 404:
                        raise APIError(
                            f"Resource not found: {api_response.error}",
                            status_code=api_response.status_code,
                            correlation_id=correlation_id,
                            context=context
                        )
                    elif api_response.status_code == 429:
                        raise APIError(
                            f"Rate limit exceeded: {api_response.error}",
                            status_code=api_response.status_code,
                            correlation_id=correlation_id,
                            context=context
                        )
                    else:
                        raise APIError(
                            f"API call failed: {api_response.error}",
                            status_code=api_response.status_code,
                            response=response,
                            correlation_id=correlation_id,
                            context=context
                        )

                return api_response

            except requests.Timeout as e:
                if attempt < self.max_retries:
                    delay = _calculate_rest_backoff_delay(attempt, backoff_factor=self.backoff_factor)
                    logger.warning(
                        f"Request timeout, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Final timeout on {method.upper()} {url}: {e}")
                    if raise_for_status:
                        raise APITimeoutError(actual_timeout, context=context)
                    return APIResponse(408, error=f"Request timed out: {e}", context=context)

            except requests.ConnectionError as e:
                if attempt < self.max_retries:
                    delay = _calculate_rest_backoff_delay(attempt, backoff_factor=self.backoff_factor)
                    logger.warning(
                        f"Connection error, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Final connection error on {method.upper()} {url}: {e}")
                    if raise_for_status:
                        raise APIError(f"Connection failed: {e}", context=context)
                    return APIResponse(500, error=f"Connection failed: {e}", context=context)

            except requests.RequestException as e:
                logger.error(f"Request exception on {method.upper()} {url}: {e}")
                if raise_for_status:
                    raise APIError(f"Request failed: {e}", context=context)
                return APIResponse(500, error=f"Request failed: {e}", context=context)

        # This should never be reached, but just in case
        return APIResponse(500, error="Maximum retries exceeded", context=context)

    def get(self, url: str, identifier: Optional[str] = None, **kwargs) -> APIResponse:
        """Execute a GET request with enhanced error handling"""
        return self._execute_request("get", url, identifier, **kwargs)

    def post(self, url: str, payload: Dict[str, Any], identifier: Optional[str] = None, **kwargs) -> APIResponse:
        """Execute a POST request with enhanced error handling"""
        return self._execute_request("post", url, identifier, json=payload, **kwargs)

    def patch(self, url: str, payload: Any, identifier: Optional[str] = None, **kwargs) -> APIResponse:
        """Execute a PATCH request with enhanced error handling"""
        request_kwargs = {"json": payload} if isinstance(payload, (dict, list)) else {"data": payload}
        return self._execute_request("patch", url, identifier, **request_kwargs, **kwargs)

    def delete(self, url: str, identifier: Optional[str] = None, **kwargs) -> APIResponse:
        """Execute a DELETE request with enhanced error handling"""
        return self._execute_request("delete", url, identifier, **kwargs)

    def put(self, url: str, payload: Dict[str, Any], identifier: Optional[str] = None, **kwargs) -> APIResponse:
        """Execute a PUT request with enhanced error handling"""
        return self._execute_request("put", url, identifier, json=payload, **kwargs)


# Enhanced retry logic with business-aware retry strategies
def retry_api_call(api_func, *args, max_retries=3, backoff=2, **kwargs) -> APIResponse:
    """
    Enhanced retry logic with business-aware retry strategies.
    """
    attempt = 0
    response = APIResponse(500, error="API call failed before attempts could be made")
    last_error = None
    success_codes = (200, 201, 202, 204)

    while attempt < max_retries:
        try:
            if 'raise_for_status' not in kwargs:
                kwargs['raise_for_status'] = False

            response = api_func(*args, **kwargs)

            # Check for authentication errors - don't retry
            if response.status_code == 401:
                logger.error(f"401 Unauthorized encountered: {response.error}")
                raise AuthenticationError("Unauthorized access", status_code=401)

            # Success - return immediately
            if not response.error and response.status_code in success_codes:
                return response

            # Check if error is retryable using business logic
            if response.error and not _should_retry_error(response.error):
                logger.info(f"Non-retryable error detected: {response.error}")
                return response

            attempt += 1
            last_error = response.error
            logger.warning(f"API call failed on attempt {attempt}/{max_retries}: {last_error}")

            if attempt < max_retries:
                time.sleep(backoff ** attempt)

        except AuthenticationError:
            raise
        except BusinessCentralError as e:
            if e.is_retryable and attempt < max_retries:
                attempt += 1
                logger.warning(f"Retryable BC error on attempt {attempt}/{max_retries}: {e}")
                time.sleep(backoff ** attempt)
                continue
            else:
                logger.info(f"Non-retryable BC error: {e}")
                raise
        except Exception as e:
            attempt += 1
            last_error = str(e)
            logger.warning(f"API call failed on attempt {attempt}/{max_retries}: {last_error}")

            if attempt >= max_retries:
                raise
            time.sleep(backoff ** attempt)

    logger.error(f"API call failed after {max_retries} retries. Last error: {last_error}")
    raise APIError(f"API call failed after {max_retries} retries. Last error: {last_error}",
                   response=response)


def _should_retry_error(error_message: str) -> bool:
    """Determine if error should be retried based on business logic"""
    category = BusinessCentralErrorClassifier.classify_error(error_message)

    # Only retry concurrency errors and timeouts
    retryable_categories = {'concurrency_error', 'timeout_error'}
    return category in retryable_categories