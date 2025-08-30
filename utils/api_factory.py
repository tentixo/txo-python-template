# utils/api_factory.py
"""
API client factory with enhanced configuration support.

Handles creation of REST API clients with:
- Rate limiting and circuit breaker support
- Automatic configuration from config dict
- Optional API instance caching
- Context manager support
"""

import threading
from typing import Dict, Any, Optional
from weakref import WeakValueDictionary

from utils.logger import setup_logger
from utils.rest_api_helpers import MinimalRestAPI
from utils.api_common import RateLimiter, CircuitBreaker

logger = setup_logger()

# Thread-safe cache for API instances (optional)
_api_cache: WeakValueDictionary = WeakValueDictionary()
_cache_lock = threading.Lock()


def _get_rate_limiter(config: Dict[str, Any]) -> Optional[RateLimiter]:
    """Create rate limiter from configuration if enabled."""
    script_behavior = config.get("script-behavior", {})

    if not script_behavior.get("enable-rate-limiting", False):
        return None

    calls_per_second = script_behavior.get("rate-limit-per-second", 10)
    logger.debug(f"Creating rate limiter: {calls_per_second} calls/second")

    return RateLimiter(calls_per_second=calls_per_second)


def _get_circuit_breaker(config: Dict[str, Any]) -> Optional[CircuitBreaker]:
    """Create circuit breaker from configuration if enabled."""
    script_behavior = config.get("script-behavior", {})

    if not script_behavior.get("enable-circuit-breaker", False):
        return None

    failure_threshold = script_behavior.get("circuit-breaker-threshold", 5)
    timeout = script_behavior.get("circuit-breaker-timeout", 60)
    logger.debug(f"Creating circuit breaker: threshold={failure_threshold}, timeout={timeout}s")

    return CircuitBreaker(failure_threshold=failure_threshold, timeout=timeout)


def create_rest_api(config: Dict[str, Any],
                    use_cache: bool = False,
                    cache_key: Optional[str] = None,
                    rate_limiter: Optional[RateLimiter] = None,
                    circuit_breaker: Optional[CircuitBreaker] = None) -> MinimalRestAPI:
    """
    Create configured REST API client with enhanced features.

    Args:
        config: Configuration dictionary
        use_cache: Whether to cache and reuse API instances
        cache_key: Optional custom cache key
        rate_limiter: Optional rate limiter
        circuit_breaker: Optional circuit breaker

    Returns:
        Configured MinimalRestAPI instance
    """
    # Generate cache key if caching is enabled
    if use_cache:
        if not cache_key:
            org_id = config.get("_org_id", "default")
            env_type = config.get("_env_type", "default")
            cache_key = f"rest_{org_id}_{env_type}"

        # Check cache
        with _cache_lock:
            if cache_key in _api_cache:
                logger.debug(f"Returning cached REST API for {cache_key}")
                return _api_cache[cache_key]

    # Extract configuration
    token = config["_token"]
    script_behavior = config.get("script-behavior", {})
    timeout_config = script_behavior.get("api-timeouts", {})
    jitter_config = script_behavior.get("jitter", {})

    # Create rate limiter and circuit breaker from config if not provided
    if rate_limiter is None:
        rate_limiter = _get_rate_limiter(config)

    if circuit_breaker is None:
        circuit_breaker = _get_circuit_breaker(config)

    # Create API instance with all features
    api = MinimalRestAPI(
        token=token,
        timeout_config=timeout_config,
        jitter_config=jitter_config,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker
    )

    # Cache if requested
    if use_cache and cache_key:
        with _cache_lock:
            _api_cache[cache_key] = api
            logger.debug(f"Cached REST API instance for {cache_key}")

    logger.debug(f"Created REST API client for {config.get('_org_id', 'unknown')}-"
                 f"{config.get('_env_type', 'unknown')} "
                 f"(rate_limit={rate_limiter is not None}, "
                 f"circuit_breaker={circuit_breaker is not None})")

    return api


def clear_api_cache() -> None:
    """Clear all cached API instances."""
    with _cache_lock:
        count = len(_api_cache)
        _api_cache.clear()
        if count > 0:
            logger.debug(f"Cleared {count} cached API instances")


class ApiManager:
    """
    Context manager for API lifecycle management.

    Example:
       # >>> with ApiManager(config) as manager:
       # ...     rest_api = manager.get_rest_api()
       # ...     # API is automatically cleaned up on exit
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize API manager."""
        self.config = config
        self._rest_api: Optional[MinimalRestAPI] = None

    def get_rest_api(self, **kwargs) -> MinimalRestAPI:
        """Get or create REST API instance."""
        if self._rest_api is None:
            self._rest_api = create_rest_api(self.config, **kwargs)
        return self._rest_api

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self._rest_api and hasattr(self._rest_api, 'close'):
            self._rest_api.close()
            logger.debug("Closed REST API connection")


# Backward compatibility alias
def create_minimal_rest_api(config: Dict[str, Any]) -> MinimalRestAPI:
    """
    Legacy function name for backward compatibility.

    Deprecated: Use create_rest_api() instead.
    """
    logger.warning("create_minimal_rest_api is deprecated. Use create_rest_api() instead.")
    return create_rest_api(config)