# utils/rate_limit_manager.py
from typing import Dict, Optional
from dataclasses import dataclass
import threading
import time
from urllib.parse import urlparse

from utils.api_common import RateLimiter
from utils.logger import setup_logger

logger = setup_logger()


@dataclass
class EndpointLimits:
    """Rate limit configuration for an endpoint."""
    calls_per_second: float
    burst_size: float = 1.0
    shared_pool: Optional[str] = None  # Share limits with other endpoints


class RateLimitManager:
    """
    Manages rate limiters for multiple API endpoints.

    Supports:
    - Per-endpoint limits
    - Shared limit pools
    - Dynamic limit updates from response headers
    """

    def __init__(self, default_cps: float = 10, default_burst: float = 1.0):
        self.default_cps = default_cps
        self.default_burst = default_burst
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()

        # Endpoint-specific configurations
        self._endpoint_configs: Dict[str, EndpointLimits] = {}

    def configure_endpoint(self, pattern: str,
                           calls_per_second: float,
                           burst_size: float = 1.0,
                           shared_pool: Optional[str] = None):
        """
        Configure limits for an endpoint pattern.

        Args:
            pattern: URL pattern (e.g., "api.github.com", "*/users/*")
            calls_per_second: Rate limit for this endpoint
            burst_size: Burst capacity
            shared_pool: Name of shared limit pool
        """
        self._endpoint_configs[pattern] = EndpointLimits(
            calls_per_second, burst_size, shared_pool
        )

    def get_limiter(self, url: str) -> RateLimiter:
        """Get or create rate limiter for URL."""
        # Extract domain as default key
        parsed = urlparse(url)
        domain = parsed.netloc

        # Find matching configuration
        config = self._find_config(url, domain)

        # Use shared pool name if configured, else use domain
        key = config.shared_pool if config.shared_pool else domain

        with self._lock:
            if key not in self._limiters:
                self._limiters[key] = RateLimiter(
                    config.calls_per_second,
                    config.burst_size
                )
                logger.debug(f"Created rate limiter for {key}: "
                             f"{config.calls_per_second} cps, "
                             f"burst={config.burst_size}")

            return self._limiters[key]

    def _find_config(self, url: str, domain: str) -> EndpointLimits:
        """Find best matching configuration for URL."""
        # Check exact domain match
        if domain in self._endpoint_configs:
            return self._endpoint_configs[domain]

        # Check patterns (simplified - could use fnmatch)
        for pattern, config in self._endpoint_configs.items():
            if pattern in url:
                return config

        # Return defaults
        return EndpointLimits(self.default_cps, self.default_burst)

    def update_from_headers(self, url: str, headers: Dict[str, str]):
        """
        Update rate limits from API response headers with adaptive adjustment.

        Implements 4-tier adaptive rate adjustment:
        - <5% remaining: Emergency slow down (30% of current rate)
        - <10% remaining: Aggressive slow down (50% of current rate)
        - <25% remaining: Moderate slow down (75% of current rate)
        - >75% remaining: Speed up (125% of current rate, max original)

        Handles:
        - X-RateLimit-Limit: requests per window
        - X-RateLimit-Remaining: requests remaining
        - X-RateLimit-Reset: window reset time (Unix timestamp)
        - Retry-After: seconds to wait (429 responses)

        Args:
            url: API endpoint URL
            headers: HTTP response headers
        """
        limit = headers.get('X-RateLimit-Limit')
        remaining = headers.get('X-RateLimit-Remaining')
        reset = headers.get('X-RateLimit-Reset')
        retry_after = headers.get('Retry-After')

        # No rate limit headers - nothing to do
        if not (limit and remaining):
            return

        limiter = self.get_limiter(url)

        try:
            limit_int = int(limit)
            remaining_int = int(remaining)

            # Calculate remaining percentage
            remaining_pct = remaining_int / limit_int if limit_int > 0 else 1.0

            # Store original rate for recovery (if not already stored)
            if not hasattr(limiter, '_original_rate'):
                limiter._original_rate = limiter.rate

            # Adaptive rate adjustment based on remaining percentage
            if remaining_pct < 0.05:  # Less than 5% remaining - EMERGENCY
                new_rate = limiter.rate * 0.3
                logger.warning(
                    f"Rate limit CRITICAL for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}) - "
                    f"Emergency slow down from {limiter.rate:.2f} to {new_rate:.2f} cps"
                )
                limiter.rate = max(0.1, new_rate)  # Don't go below 0.1 cps

            elif remaining_pct < 0.1:  # Less than 10% remaining - AGGRESSIVE
                new_rate = limiter.rate * 0.5
                logger.warning(
                    f"Rate limit LOW for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}) - "
                    f"Aggressive slow down from {limiter.rate:.2f} to {new_rate:.2f} cps"
                )
                limiter.rate = max(0.5, new_rate)  # Don't go below 0.5 cps

            elif remaining_pct < 0.25:  # Less than 25% remaining - MODERATE
                new_rate = limiter.rate * 0.75
                logger.info(
                    f"Rate limit depleting for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}) - "
                    f"Moderate slow down from {limiter.rate:.2f} to {new_rate:.2f} cps"
                )
                limiter.rate = max(1.0, new_rate)  # Don't go below 1.0 cps

            elif remaining_pct > 0.75:  # More than 75% remaining - CAN SPEED UP
                original_rate = limiter._original_rate
                if limiter.rate < original_rate:
                    new_rate = min(original_rate, limiter.rate * 1.25)
                    logger.debug(
                        f"Rate limit healthy for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}) - "
                        f"Speeding up from {limiter.rate:.2f} to {new_rate:.2f} cps"
                    )
                    limiter.rate = new_rate
                else:
                    # Already at or above original rate - just log status
                    logger.debug(
                        f"Rate limit healthy for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}), "
                        f"current rate: {limiter.rate:.2f} cps"
                    )
            else:
                # Between 25% and 75% - stable zone, just log
                logger.debug(
                    f"Rate limit stable for {url}: {remaining}/{limit} remaining ({remaining_pct:.1%}), "
                    f"current rate: {limiter.rate:.2f} cps"
                )

            # Handle reset time
            if reset:
                try:
                    reset_time = int(reset)
                    time_until_reset = reset_time - time.time()
                    if time_until_reset > 0:
                        logger.debug(
                            f"Rate limit for {url} resets in {time_until_reset:.0f}s "
                            f"(at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(reset_time))})"
                        )
                    else:
                        # Reset time has passed - can recover to original rate
                        if hasattr(limiter, '_original_rate') and limiter.rate < limiter._original_rate:
                            logger.info(
                                f"Rate limit window reset for {url} - "
                                f"Recovering to original rate {limiter._original_rate:.2f} cps"
                            )
                            limiter.rate = limiter._original_rate
                except (ValueError, OSError) as e:
                    logger.debug(f"Could not parse reset time '{reset}': {e}")

            # Handle retry-after (typically from 429 responses)
            if retry_after:
                try:
                    retry_seconds = int(retry_after)
                    logger.warning(
                        f"Retry-After header for {url}: wait {retry_seconds}s before next request"
                    )
                    # Could implement actual waiting here or let caller handle it
                except ValueError as e:
                    logger.debug(f"Could not parse Retry-After '{retry_after}': {e}")

        except ValueError as e:
            logger.warning(f"Invalid rate limit headers for {url}: {e}")