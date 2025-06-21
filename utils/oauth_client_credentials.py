# utils/oauth_client_credentials.py
"""
OAuth 2.0 Client Credentials Flow implementation using ConfigLoader methods.

This module provides token acquisition for server-to-server authentication
with proper separation of concerns and modern datetime handling.
"""
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional
from dataclasses import dataclass

import requests

from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from utils.exceptions import AuthenticationError, APIError, ErrorContext

logger = setup_logger()


@dataclass
class TokenResponse:
    """Represents an OAuth token response"""
    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None

    # Calculated fields
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """Calculate expiration time"""
        if self.expires_in:
            # Use timezone-aware UTC datetime (Python 3.13+ best practice)
            self.expires_at = datetime.now(UTC) + timedelta(seconds=self.expires_in - 300)  # 5 min buffer

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 minute buffer)"""
        if not self.expires_at:
            return False
        return datetime.now(UTC) >= self.expires_at

    @property
    def bearer_token(self) -> str:
        """Get properly formatted bearer token"""
        return f"Bearer {self.access_token}"

    def to_headers(self) -> Dict[str, str]:
        """Get headers dictionary for API requests"""
        return {
            "Authorization": self.bearer_token,
            "Content-Type": "application/json"
        }


def _parse_token_response(response_data: Dict[str, Any]) -> TokenResponse:
    """Parse successful token response"""
    try:
        return TokenResponse(
            access_token=response_data['access_token'],
            token_type=response_data.get('token_type', 'Bearer'),
            expires_in=response_data.get('expires_in', 3600),
            scope=response_data.get('scope'),
            refresh_token=response_data.get('refresh_token'),
            id_token=response_data.get('id_token')
        )
    except KeyError as e:
        raise AuthenticationError(f"Invalid token response: missing {e}")


def _parse_error_response(response: requests.Response) -> str:
    """Parse error response from OAuth endpoint"""
    try:
        error_data = response.json()
        error_code = error_data.get('error', 'unknown_error')
        error_description = error_data.get('error_description', 'No description provided')
        error_uri = error_data.get('error_uri', '')

        error_msg = f"{error_code}: {error_description}"
        if error_uri:
            error_msg += f" (See: {error_uri})"

        return error_msg

    except (json.JSONDecodeError, ValueError):
        # Fallback to raw response text
        return f"HTTP {response.status_code}: {response.text[:500]}"


class OAuthClientCredentials:
    """
    OAuth 2.0 Client Credentials Flow implementation.

    This class handles server-to-server authentication using client credentials
    and uses ConfigLoader methods for configuration access.
    """

    def __init__(self,
                 tenant_id: str,
                 client_id: str,
                 client_secret: str,
                 scope: str = "https://api.businesscentral.dynamics.com/.default",
                 authority: str = "https://login.microsoftonline.com",
                 timeout: int = 30):
        """
        Initialize OAuth client credentials authenticator.

        Args:
            tenant_id: Azure tenant ID or domain
            client_id: Application (client) ID from Azure app registration
            client_secret: Client secret from Azure app registration
            scope: OAuth scope (default for Business Central)
            authority: OAuth authority URL (default Microsoft)
            timeout: Request timeout in seconds
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.authority = authority.rstrip('/')
        self.timeout = timeout

        # Token caching
        self._cached_token: Optional[TokenResponse] = None

        # Build token endpoint URL
        self.token_endpoint = f"{self.authority}/{self.tenant_id}/oauth2/v2.0/token"

        logger.debug(f"Initialized OAuth client for tenant {tenant_id}")

    @classmethod
    def from_config_loader(cls, config_loader: ConfigLoader,
                           authority: str = "https://login.microsoftonline.com",
                           timeout: int = 30) -> 'OAuthClientCredentials':
        """
        Create OAuth client from ConfigLoader instance using dedicated methods.

        Args:
            config_loader: ConfigLoader instance with OAuth methods
            authority: OAuth authority URL (default Microsoft)
            timeout: Request timeout in seconds

        Returns:
            OAuthClientCredentials: Configured OAuth client

        Raises:
            KeyError: If required config values are missing
        """
        # Use dedicated ConfigLoader methods for each OAuth parameter
        tenant_id = config_loader.get_oauth_tenant_id()
        client_id = config_loader.get_oauth_client_id()
        client_secret = config_loader.get_oauth_client_secret()
        scope = config_loader.get_oauth_scope()

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            authority=authority,
            timeout=timeout
        )

    @classmethod
    def from_org_env(cls, org_id: str, env_type: str,
                     authority: str = "https://login.microsoftonline.com",
                     timeout: int = 30) -> 'OAuthClientCredentials':
        """
        Create OAuth client directly from org_id and env_type.

        Args:
            org_id: Organization ID (e.g., 'txo')
            env_type: Environment type (e.g., 'test', 'prod')
            authority: OAuth authority URL
            timeout: Request timeout in seconds

        Returns:
            OAuthClientCredentials: Configured OAuth client
        """
        config_loader = ConfigLoader(org_id, env_type)
        return cls.from_config_loader(config_loader, authority, timeout)

    def get_token(self, force_refresh: bool = False) -> TokenResponse:
        """
        Get access token, using cache if available and not expired.

        Args:
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            TokenResponse: Valid access token response

        Raises:
            AuthenticationError: If token acquisition fails
            APIError: If there are network/HTTP issues
        """
        # Return cached token if valid and not forcing refresh
        if not force_refresh and self._cached_token and not self._cached_token.is_expired:
            logger.debug("Using cached token")
            return self._cached_token

        logger.debug("Acquiring new access token")

        # Prepare request data
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        context = ErrorContext(
            operation="OAuth_ClientCredentials",
            url=self.token_endpoint,
            timestamp=datetime.now(UTC).isoformat()  # Fixed: Use timezone-aware UTC
        )

        try:
            # Make token request
            response = requests.post(
                self.token_endpoint,
                data=token_data,
                headers=headers,
                timeout=self.timeout
            )

            # Handle response
            if response.status_code == 200:
                token_response = _parse_token_response(response.json())
                self._cached_token = token_response
                logger.info(f"Successfully acquired token (expires in {token_response.expires_in}s)")
                return token_response

            else:
                # Handle error response
                error_details = _parse_error_response(response)
                raise AuthenticationError(
                    f"Token acquisition failed: {error_details}",
                    status_code=response.status_code,
                    context=context
                )

        except requests.exceptions.Timeout:
            raise APIError(f"Token request timed out after {self.timeout}s", context=context)

        except requests.exceptions.ConnectionError as e:
            raise APIError(f"Connection failed to {self.token_endpoint}: {e}", context=context)

        except requests.exceptions.RequestException as e:
            raise APIError(f"Token request failed: {e}", context=context)

    def get_access_token_string(self, force_refresh: bool = False) -> str:
        """
        Get just the access token string (for backwards compatibility).

        Args:
            force_refresh: Force token refresh

        Returns:
            str: Access token string
        """
        token_response = self.get_token(force_refresh)
        return token_response.access_token

    def get_headers(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get headers dictionary ready for API requests.

        Args:
            force_refresh: Force token refresh

        Returns:
            Dict[str, str]: Headers with Authorization and Content-Type
        """
        token_response = self.get_token(force_refresh)
        return token_response.to_headers()

    def invalidate_cache(self):
        """Invalidate cached token to force refresh on next request"""
        self._cached_token = None
        logger.debug("Token cache invalidated")

    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about current cached token.

        Returns:
            Optional[Dict]: Token info or None if no cached token
        """
        if not self._cached_token:
            return None

        return {
            "token_type": self._cached_token.token_type,
            "scope": self._cached_token.scope,
            "expires_at": self._cached_token.expires_at.isoformat() if self._cached_token.expires_at else None,
            "is_expired": self._cached_token.is_expired,
            "expires_in_seconds": int((self._cached_token.expires_at - datetime.now(
                UTC)).total_seconds()) if self._cached_token.expires_at else None
        }