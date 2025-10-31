# utils/api_common.py
"""
Common API utilities shared across different API types.

Provides:
- Rate limiting
- Circuit breaker pattern
- Retry logic with jitter
- Common API patterns
"""

import time
import random
from typing import Dict, Any, Optional, Callable

from utils.logger import setup_logger

logger = setup_logger()


class RateLimiter:
    """
    Simple rate limiter using token bucket algorithm.

    Limits the rate of API calls to prevent hitting rate limits.
    """
    def __init__(self,
                 calls_per_second: float = 10,
                 burst_size: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Sustained rate limit
            burst_size: Max tokens that can accumulate (1.0 = no burst)
        """
        self.rate = calls_per_second
        self.burst_size = max(1.0, burst_size)
        self.allowance = min(1.0, self.burst_size)
        self.last_check = time.time()

    def wait_if_needed(self) -> None:
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current

        self.allowance += time_passed * self.rate

        # Cap at burst_size instead of rate
        if self.allowance > self.burst_size:
            self.allowance = self.burst_size

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) / self.rate
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation with enhanced observability.

    Prevents cascading failures by stopping calls to a failing service
    after a threshold of failures is reached. Tracks state transitions
    and provides statistics for monitoring.

    States:
    - closed: Normal operation, all calls allowed
    - open: Too many failures, calls blocked
    - half-open: Testing recovery, one call allowed
    """
    __slots__ = ['failure_threshold', 'timeout', '_failures', '_last_failure', '_state',
                 '_state_changed_at', '_total_requests', '_total_failures']

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker with statistics tracking.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self._failures = 0
        self._last_failure = 0.0
        self._state = "closed"
        self._state_changed_at = time.time()
        self._total_requests = 0
        self._total_failures = 0

    def _change_state(self, new_state: str, reason: str = "") -> None:
        """
        Change circuit breaker state with logging.

        Args:
            new_state: Target state (closed, open, half-open)
            reason: Reason for state change
        """
        if new_state != self._state:
            old_state = self._state
            time_in_state = time.time() - self._state_changed_at

            logger.info(
                f"Circuit breaker state: {old_state} → {new_state} "
                f"(was in {old_state} for {time_in_state:.1f}s) - {reason}"
            )

            self._state = new_state
            self._state_changed_at = time.time()

    def record_success(self) -> None:
        """Record a successful operation with state transition logging."""
        self._total_requests += 1
        self._failures = 0

        if self._state != "closed":
            self._change_state("closed", "Success after failure")
        else:
            logger.debug("Circuit breaker: success recorded")

    def record_failure(self) -> None:
        """Record a failed operation with state transition logging."""
        self._total_requests += 1
        self._total_failures += 1
        self._failures += 1
        self._last_failure = time.time()

        if self._failures >= self.failure_threshold and self._state != "open":
            self._change_state(
                "open",
                f"{self._failures} consecutive failures (threshold: {self.failure_threshold})"
            )
        elif self._state != "open":
            logger.debug(f"Circuit breaker: failure {self._failures}/{self.failure_threshold}")

    def is_open(self) -> bool:
        """
        Check if circuit breaker is open (blocking calls).

        Returns:
            True if circuit is open and calls should be blocked
        """
        if self._state == "closed":
            return False

        # Check if timeout has passed
        if self._state == "open":
            if time.time() - self._last_failure >= self.timeout:
                self._change_state(
                    "half-open",
                    f"Timeout expired ({self.timeout}s since last failure)"
                )
                return False  # Allow one attempt

        return self._state == "open"

    def reset(self) -> None:
        """Reset the circuit breaker with state logging."""
        self._failures = 0
        self._change_state("closed", "Manual reset")

    @property
    def stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics for monitoring.

        Returns:
            Dictionary with current state, failure counts, and metrics

        Example:
            > breaker = CircuitBreaker(failure_threshold=5, timeout=60)
            > # ... after some requests ...
            > stats = breaker.stats
            > print(f"State: {stats['state']}, Failure rate: {stats['failure_rate']:.1%}")
        """
        return {
            'state': self._state,
            'consecutive_failures': self._failures,
            'failure_threshold': self.failure_threshold,
            'total_requests': self._total_requests,
            'total_failures': self._total_failures,
            'failure_rate': self._total_failures / max(1, self._total_requests),
            'time_in_current_state': time.time() - self._state_changed_at,
            'timeout_seconds': self.timeout,
            'last_failure_ago': time.time() - self._last_failure if self._last_failure > 0 else None
        }


def apply_jitter(delay: float, jitter_config: Optional[Dict[str, Any]] = None) -> float:
    """
    Apply jitter to a delay value to prevent thundering herd.

    Args:
        delay: Base delay in seconds
        jitter_config: Configuration with min-factor and max-factor

    Returns:
        Jittered delay value
    """
    if not jitter_config:
        jitter_config = {"min-factor": 0.8, "max-factor": 1.2}

    min_factor = jitter_config["min-factor"]  # Hard-fail if missing
    max_factor = jitter_config["max-factor"]  # Hard-fail if missing

    # Apply random jitter within the factor range
    jitter_factor = random.uniform(min_factor, max_factor)
    jittered = delay * jitter_factor

    logger.debug(f"Applied jitter: {delay:.2f}s -> {jittered:.2f}s")
    return jittered


def manual_retry(func: Callable, *args,
                 max_retries: int = 3,
                 backoff: float = 2.0,
                 jitter_config: Optional[Dict[str, Any]] = None,
                 **kwargs) -> Any:
    """
    Generic retry logic for any function.

    Args:
        func: Function to retry
        *args: Positional arguments for function
        max_retries: Maximum number of retry attempts
        backoff: Exponential backoff factor
        jitter_config: Jitter configuration
        **kwargs: Keyword arguments for function

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < max_retries - 1:
                delay = backoff ** attempt
                jittered_delay = apply_jitter(delay, jitter_config)

                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                logger.debug(f"Retrying in {jittered_delay:.2f}s")
                time.sleep(jittered_delay)
            else:
                logger.error(f"All {max_retries} attempts failed")

    raise last_exception


class APIMetrics:
    """
    Simple metrics collector for API operations.

    Tracks success/failure rates and response times.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0.0
        self._start_times: Dict[str, float] = {}

    def start_operation(self, operation_id: str) -> None:
        """Mark the start of an operation."""
        self._start_times[operation_id] = time.time()
        self.total_calls += 1

    def end_operation(self, operation_id: str, success: bool = True) -> float:
        """
        Mark the end of an operation.

        Args:
            operation_id: Unique operation identifier
            success: Whether operation was successful

        Returns:
            Operation duration in seconds
        """
        if operation_id not in self._start_times:
            logger.warning(f"No start time for operation {operation_id}")
            return 0.0

        duration = time.time() - self._start_times.pop(operation_id)
        self.total_response_time += duration

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        return duration

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def average_response_time(self) -> float:
        """Calculate average response time in seconds."""
        if self.total_calls == 0:
            return 0.0
        return self.total_response_time / self.total_calls

    def reset(self) -> None:
        """Reset all metrics."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0.0
        self._start_times.clear()

    def __str__(self) -> str:
        """String representation of metrics."""
        return (
            f"API Metrics: "
            f"Total={self.total_calls}, "
            f"Success={self.successful_calls}, "
            f"Failed={self.failed_calls}, "
            f"Success Rate={self.success_rate:.1f}%, "
            f"Avg Response={self.average_response_time:.3f}s"
        )