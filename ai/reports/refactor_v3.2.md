# TXO Python Template - Refactoring Plan v3.2

**Date:** 2025-09-29
**Scope:** utils/ directory code improvements
**Status:** Proposed
**Priority:** High → Low (ordered by impact)

---

## Executive Summary

This refactoring plan addresses code quality and robustness issues identified during the utils/ directory code review. The codebase is production-ready but has opportunities for improvement in error handling, rate limiting implementation, and memory optimization.

**Overall Health:** 8.5/10
**Security Posture:** 9.5/10 (Excellent)
**Recommended Timeline:** 2-3 sprints

---

## High-Priority Refactors

### 1. Exception Handling: Logger Module Hard Exit Refactor

**Files Affected:**
- `utils/logger.py`

**Issue:**
The logger module uses `sys.exit(1)` directly throughout initialization, making the code difficult to test and causing abrupt application terminations. This violates best practices for library code.

**Current Behavior:**
```python
# logger.py:71-72, 394-395, multiple locations
if not config_path.exists():
    error_msg = (...)
    print(error_msg, file=sys.stderr)
    sys.exit(1)
```

**Proposed Solution:**
Create custom exceptions and let calling code decide termination strategy:

```python
# Add to utils/exceptions.py
class LoggerConfigurationError(TxoBaseError):
    """Raised when logger configuration is missing or invalid."""
    pass 

class LoggerSecurityError(TxoBaseError):
    """Raised when security patterns cannot be loaded."""
    pass

# Refactor logger.py
def _fail(self, message: str) -> None:
    """Raise configuration error instead of exiting."""
    error_msg = (
        f"\n{'=' * 60}\n"
        f"CRITICAL SECURITY ERROR\n"
        f"{message}\n"
        f"File: {self.config_path}\n"
        f"{'=' * 60}"
    )
    raise LoggerSecurityError(error_msg)

# Update setup_logger()
def setup_logger() -> TxoLogger:
    """
    Get configured logger instance.

    Raises:
        LoggerConfigurationError: If configuration is missing/invalid
        LoggerSecurityError: If security patterns cannot be loaded
    """
    return TxoLogger()

# Calling code can then decide to exit:
if __name__ == "__main__":
    try:
        logger = setup_logger()
    except (LoggerConfigurationError, LoggerSecurityError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
```

**Benefits:**
- Testable logger initialization
- Better error propagation
- Allows graceful handling in tests
- Maintains hard-fail philosophy

**Estimated Effort:** 3-4 hours
**Breaking Change:** Minimal (calling code needs try/except)
**Testing Required:** Unit tests for all error paths

---

### 2. Rate Limiter: Complete Header Update Implementation

**Files Affected:**
- `utils/rate_limit_manager.py`

**Issue:**
The `update_from_headers()` method logs rate limit information but doesn't actually adjust the limiter behavior based on API responses.

**Current Code:**
```python
# rate_limit_manager.py:95-111
def update_from_headers(self, url: str, headers: Dict[str, str]):
    limit = headers.get('X-RateLimit-Limit')
    remaining = headers.get('X-RateLimit-Remaining')

    if limit and remaining:
        limiter = self.get_limiter(url)
        # Implementation depends on your needs
        logger.debug(f"Rate limit for {url}: {remaining}/{limit} remaining")
```

**Proposed Implementation:**
```python
def update_from_headers(self, url: str, headers: Dict[str, str]):
    """
    Update rate limits from API response headers.

    Handles:
    - X-RateLimit-Limit: requests per window
    - X-RateLimit-Remaining: requests remaining
    - X-RateLimit-Reset: window reset time
    - Retry-After: seconds to wait (429 responses)
    """
    limit = headers.get('X-RateLimit-Limit')
    remaining = headers.get('X-RateLimit-Remaining')
    reset = headers.get('X-RateLimit-Reset')
    retry_after = headers.get('Retry-After')

    if not (limit and remaining):
        return

    limiter = self.get_limiter(url)

    try:
        limit_int = int(limit)
        remaining_int = int(remaining)

        # Calculate remaining percentage
        remaining_pct = remaining_int / limit_int if limit_int > 0 else 1.0

        # Adaptive rate adjustment
        if remaining_pct < 0.05:  # Less than 5% remaining - emergency slow down
            new_rate = limiter.rate * 0.3
            logger.warning(f"Rate limit critical for {url}: {remaining}/{limit} - "
                          f"Reducing rate from {limiter.rate:.2f} to {new_rate:.2f} cps")
            limiter.rate = max(0.1, new_rate)  # Don't go below 0.1 cps

        elif remaining_pct < 0.1:  # Less than 10% remaining - aggressive slow down
            new_rate = limiter.rate * 0.5
            logger.warning(f"Rate limit low for {url}: {remaining}/{limit} - "
                          f"Reducing rate from {limiter.rate:.2f} to {new_rate:.2f} cps")
            limiter.rate = max(0.5, new_rate)

        elif remaining_pct < 0.25:  # Less than 25% remaining - moderate slow down
            new_rate = limiter.rate * 0.75
            logger.info(f"Rate limit depleting for {url}: {remaining}/{limit} - "
                       f"Reducing rate from {limiter.rate:.2f} to {new_rate:.2f} cps")
            limiter.rate = max(1.0, new_rate)

        elif remaining_pct > 0.75:  # More than 75% remaining - can speed up
            original_rate = self.default_cps
            if limiter.rate < original_rate:
                new_rate = min(original_rate, limiter.rate * 1.25)
                logger.debug(f"Rate limit healthy for {url}: {remaining}/{limit} - "
                           f"Increasing rate from {limiter.rate:.2f} to {new_rate:.2f} cps")
                limiter.rate = new_rate

        # Log current status
        logger.debug(f"Rate limit for {url}: {remaining}/{limit} remaining "
                    f"({remaining_pct:.1%}), current rate: {limiter.rate:.2f} cps")

        # Handle reset time
        if reset:
            try:
                reset_time = int(reset)
                time_until_reset = reset_time - time.time()
                if time_until_reset > 0:
                    logger.debug(f"Rate limit resets in {time_until_reset:.0f}s")
            except ValueError:
                pass

    except ValueError as e:
        logger.warning(f"Invalid rate limit headers for {url}: {e}")
```

**Benefits:**
- Adaptive rate limiting based on actual API usage
- Prevents hitting rate limits
- Automatic recovery when limits reset
- Better API citizenship

**Estimated Effort:** 2-3 hours
**Breaking Change:** No (additive enhancement)
**Testing Required:** Integration tests with mocked headers

---

### 3. REST API Helpers: Response Content Mutation

**Files Affected:**
- `utils/rest_api_helpers.py`

**Issue:**
Direct mutation of `response._content` violates encapsulation and is fragile.

**Current Code:**
```python
# rest_api_helpers.py:447-448
if response.status_code == 202 and not skip_async_check:
    result = self._handle_async_operation(response, context)
    # Mutating internal state - fragile!
    response._content = json.dumps(result).encode('utf-8') if result else b''
    response.status_code = 200
    return response
```

**Proposed Solution:**
Create a custom response wrapper:

```python
@dataclass
class AsyncOperationResult:
    """Result wrapper for completed async operations."""
    data: Dict[str, Any]
    status_code: int = 200
    original_response: Optional[requests.Response] = None

    def json(self) -> Dict[str, Any]:
        """Return the data payload."""
        return self.data

    @property
    def ok(self) -> bool:
        """Check if operation was successful."""
        return 200 <= self.status_code < 300

    @property
    def content(self) -> bytes:
        """Return content as bytes."""
        return json.dumps(self.data).encode('utf-8') if self.data else b''

# Update _execute_request
def _execute_request(self, method: str, url: str,
                     skip_async_check: bool = False,
                     **kwargs) -> Union[requests.Response, AsyncOperationResult]:
    """
    Execute HTTP request with retry logic, rate limiting, and circuit breaker.

    Returns:
        Response object or AsyncOperationResult for completed async operations
    """
    # ... existing code ...

    if response.ok or response.status_code == 202:
        if self.circuit_breaker:
            self.circuit_breaker.record_success()

        # Handle async operations
        if response.status_code == 202 and not skip_async_check:
            result = self._handle_async_operation(response, context)
            return AsyncOperationResult(
                data=result,
                status_code=200,
                original_response=response
            )

        return response
```

**Alternative (simpler):**
Just return the dict directly and update method signatures:

```python
def get(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute GET request with authentication and retry logic."""
    response = self._execute_request("GET", url, params=params)

    # Handle both Response and AsyncOperationResult
    if isinstance(response, AsyncOperationResult):
        return response.json()
    return response.json() if response.content else {}
```

**Benefits:**
- Type-safe response handling
- No internal attribute mutation
- Clear separation of async vs sync responses
- Better testability

**Estimated Effort:** 4-5 hours
**Breaking Change:** No (return type compatible)
**Testing Required:** Unit tests for async operations

---

### 4. OAuth Helpers: Exception Handling Specificity

**Files Affected:**
- `utils/oauth_helpers.py`

**Issue:**
Broad exception catch masks potential bugs.

**Current Code:**
```python
# oauth_helpers.py:314
except (json.JSONDecodeError, ValueError, AttributeError):
    error_msg = f"{error_msg}: {response.text[:200]}"
```

**Proposed Solution:**
```python
except json.JSONDecodeError as e:
    error_msg = f"{error_msg}: Invalid JSON response - {e}"
except KeyError as e:
    error_msg = f"{error_msg}: Missing field in response - {e}"
except (ValueError, AttributeError) as e:
    error_msg = f"{error_msg}: Unexpected response format - {e}"
```

**Benefits:**
- Better error diagnostics
- Won't hide unexpected errors
- More actionable error messages

**Estimated Effort:** 1 hour
**Breaking Change:** No
**Testing Required:** Unit tests for error cases

---

## Medium-Priority Refactors

### 5. Memory Optimization: Consistent __slots__ Strategy

**Files Affected:**
- `utils/exceptions.py`
- `utils/url_helpers.py`
- `utils/rest_api_helpers.py`
- `utils/oauth_helpers.py`
- `utils/concurrency.py`
- `utils/load_n_save.py`

**Issue:**
Inconsistent `__slots__` usage across dataclasses. Some use `__slots__` with manual `__init__`, others removed `__slots__` due to dataclass default value conflicts.

**Current Situation:**
```python
# Removed __slots__ due to conflict with defaults
@dataclass
class ErrorContext:
    # NOTE: Removed __slots__ because it conflicts with default values
    operation: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Using __slots__ with manual init
class CircuitBreaker:
    __slots__ = ['failure_threshold', 'timeout', '_failures', '_last_failure', '_state']

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        # ... etc
```

**Decision Required:**
Choose one consistent approach across the codebase.

**Option A: Prioritize Developer Experience (Current Mix)**
- Use dataclasses with defaults where convenient
- Accept 20-30% memory overhead for small objects
- Use `__slots__` only for high-volume classes
- **Recommendation:** Document this in ADR

**Option B: Prioritize Memory Efficiency**
- Refactor all dataclasses to use `__slots__` with manual `__init__`
- More verbose but consistent
- Better for high-scale deployments

**Proposed ADR Update:**
```markdown
# ADR: Memory Optimization Strategy

## Decision
Use `__slots__` optimization selectively based on object volume:

### Use __slots__ for:
- High-volume objects (>1000 instances expected)
- Network request/response objects
- Cache entries
- Objects in tight loops

### Use dataclasses without __slots__ for:
- Configuration objects (low volume)
- One-off result containers
- Objects prioritizing readability

### Implementation
When using __slots__ with defaults, use manual __init__:

```python
class HighVolumeClass:
    __slots__ = ['field1', 'field2', '_private']

    def __init__(self, field1: str, field2: int = 0):
        self.field1 = field1
        self.field2 = field2
        self._private = None
```

## Rationale
- Balances memory efficiency with developer productivity
- Optimizes where it matters most
- Maintains code readability
```

**Estimated Effort:** 6-8 hours (if refactoring all)
**Breaking Change:** No (internal implementation)
**Testing Required:** Performance benchmarks

---

### 6. API Common: Rate Limiter Edge Case Handling

**Files Affected:**
- `utils/api_common.py`

**Issue:**
Token bucket algorithm allows allowance to go negative, potentially causing incorrect wait calculations.

**Current Code:**
```python
# api_common.py:42-59
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
        self.allowance = 0.0  # Could be negative after sleep
    else:
        self.allowance -= 1.0
```

**Proposed Solution:**
```python
def wait_if_needed(self) -> None:
    """
    Wait if needed to stay within rate limit using token bucket algorithm.

    Ensures allowance never goes negative to prevent calculation errors.
    """
    current = time.time()
    time_passed = current - self.last_check
    self.last_check = current

    # Add tokens based on elapsed time
    self.allowance += time_passed * self.rate

    # Cap at burst size (max tokens that can accumulate)
    self.allowance = min(self.allowance, self.burst_size)

    # Check if we have enough tokens
    if self.allowance < 1.0:
        # Calculate wait time needed to accumulate 1 token
        tokens_needed = 1.0 - self.allowance
        sleep_time = tokens_needed / self.rate

        logger.debug(f"Rate limiting: need {tokens_needed:.3f} tokens, "
                    f"sleeping {sleep_time:.3f}s")
        time.sleep(sleep_time)

        # After sleeping, we should have exactly 1 token
        # Add time-based tokens for the sleep period
        self.allowance += sleep_time * self.rate

        # Ensure we don't go negative after consuming the token
        self.allowance = max(0.0, self.allowance - 1.0)
    else:
        # Have enough tokens, consume one
        self.allowance -= 1.0
```

**Benefits:**
- Prevents negative allowance values
- More accurate rate limiting
- Better handling of burst scenarios
- Clearer algorithm intent

**Estimated Effort:** 2 hours
**Breaking Change:** No (bug fix)
**Testing Required:** Unit tests with edge cases

---

### 7. Circuit Breaker: State Transition Logging

**Files Affected:**
- `utils/api_common.py`

**Issue:**
Circuit breaker could benefit from more detailed state transition logging for debugging.

**Enhancement:**
```python
class CircuitBreaker:
    """Circuit breaker with enhanced state tracking."""

    __slots__ = ['failure_threshold', 'timeout', '_failures', '_last_failure',
                 '_state', '_state_changed_at', '_total_requests', '_total_failures']

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self._failures = 0
        self._last_failure = 0.0
        self._state = "closed"
        self._state_changed_at = time.time()
        self._total_requests = 0
        self._total_failures = 0

    def _change_state(self, new_state: str, reason: str = "") -> None:
        """Log state transitions."""
        if new_state != self._state:
            old_state = self._state
            time_in_state = time.time() - self._state_changed_at

            logger.info(
                f"Circuit breaker state: {old_state} -> {new_state} "
                f"(was in {old_state} for {time_in_state:.1f}s) - {reason}"
            )

            self._state = new_state
            self._state_changed_at = time.time()

    def record_success(self) -> None:
        """Record a successful operation."""
        self._total_requests += 1
        self._failures = 0

        if self._state != "closed":
            self._change_state("closed", "Success after failure")
        else:
            logger.debug("Circuit breaker: success recorded")

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._total_requests += 1
        self._total_failures += 1
        self._failures += 1
        self._last_failure = time.time()

        if self._failures >= self.failure_threshold and self._state != "open":
            self._change_state(
                "open",
                f"{self._failures} consecutive failures (threshold: {self.failure_threshold})"
            )

    @property
    def stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            'state': self._state,
            'consecutive_failures': self._failures,
            'total_requests': self._total_requests,
            'total_failures': self._total_failures,
            'failure_rate': self._total_failures / max(1, self._total_requests),
            'time_in_current_state': time.time() - self._state_changed_at
        }
```

**Benefits:**
- Better observability
- Easier debugging of intermittent failures
- Useful metrics for monitoring

**Estimated Effort:** 2-3 hours
**Breaking Change:** No (additive)
**Testing Required:** Unit tests for state transitions

---

## Low-Priority Refactors

### 8. Path Helpers: Exception Handling Clarity

**Files Affected:**
- `utils/path_helpers.py`

**Issue:**
Silent exception swallowing in cleanup operations could hide legitimate errors.

**Current Code:**
```python
# path_helpers.py:350-352
try:
    file_path.unlink()
except OSError as e:
    # Continue processing other files
    pass
```

**Proposed Solution:**
```python
try:
    file_path.unlink()
    deleted_files.append(file_path)
except PermissionError as e:
    logger.error(f"Permission denied deleting {file_path}: {e}")
    # Don't add to deleted list but continue
except OSError as e:
    logger.warning(f"Could not delete {file_path}: {e}")
    # Don't add to deleted list but continue
```

**Benefits:**
- Distinguishes permission errors from other issues
- Provides actionable error messages
- Maintains cleanup functionality

**Estimated Effort:** 1 hour
**Breaking Change:** No
**Testing Required:** Unit tests for error cases

---

### 9. OAuth Helpers: Unused Parameter Marking

**Files Affected:**
- `utils/oauth_helpers.py`

**Issue:**
Parameters marked as intentionally unused for API compatibility could be more explicit.

**Current Code:**
```python
# oauth_helpers.py:348-349
def revoke_token(self, token: str, client_id: str,
                 client_secret: str, tenant_id: Optional[str] = None) -> bool:
    # Mark parameters as intentionally unused for API compatibility
    _ = token  # Unused - Microsoft doesn't support token revocation
    _ = client_secret  # Unused - kept for API consistency
```

**Proposed Solution:**
```python
def revoke_token(
    self,
    _token: str,  # Prefix with _ to indicate intentionally unused
    client_id: str,
    _client_secret: str,  # Prefix with _ to indicate intentionally unused
    tenant_id: Optional[str] = None
) -> bool:
    """
    Clear token from cache (Microsoft doesn't support revocation endpoint).

    Args:
        _token: Unused (kept for API compatibility)
        client_id: Application ID to clear tokens for
        _client_secret: Unused (kept for API compatibility)
        tenant_id: Azure tenant ID

    Returns:
        True (always succeeds for cache clearing)
    """
    tenant = tenant_id or self.tenant_id
    if not tenant:
        raise ValueError("tenant_id must be provided")

    # Clear from cache
    if self.cache_tokens:
        cache_key = f"{tenant}:{client_id}:*"
        _token_cache.clear(cache_key)
        logger.info(f"Cleared cached tokens for client {client_id[:8]}...")

    return True
```

**Benefits:**
- More Pythonic unused parameter handling
- Clear intent in function signature
- Consistent with Python conventions

**Estimated Effort:** 30 minutes
**Breaking Change:** No
**Testing Required:** None (cosmetic)

---

### 10. Concurrency: Type Hint Improvements

**Files Affected:**
- `utils/concurrency.py`

**Issue:**
Some return types could be more specific.

**Enhancement:**
```python
from typing import List, Any, Callable, Optional, Dict, Tuple, TypeVar, Generic, Iterator

def batch_process(
    func: Callable[[List[Any]], List[T]],
    items: List[Any],
    batch_size: int = 100,
    show_progress: bool = True,
    max_workers: Optional[int] = None
) -> ProcessingResult[T]:
    """
    Process items in batches for memory efficiency.

    Type-safe batch processing with generic return types.
    """
    # ... existing implementation ...

# Add iterator type hints
def load_csv(
    directory: CategoryType,
    filename: str,
    chunksize: Optional[int] = None,
    **kwargs
) -> Union['pd.DataFrame', Iterator['pd.DataFrame']]:
    """
    Load CSV with proper iterator type when chunksize specified.
    """
    # ... existing implementation ...
```

**Benefits:**
- Better IDE autocomplete
- Clearer API contracts
- Type checker satisfaction

**Estimated Effort:** 1-2 hours
**Breaking Change:** No
**Testing Required:** Type checking with mypy

---

## Testing Requirements

### Unit Tests to Add

1. **Logger Module:**
   - Test exception raising instead of sys.exit
   - Test all error paths (missing config, invalid JSON, etc.)
   - Test token redaction with edge cases

2. **Rate Limiter:**
   - Test header-based rate adjustment
   - Test adaptive rate changes
   - Test recovery to default rate

3. **Circuit Breaker:**
   - Test all state transitions
   - Test timeout-based recovery
   - Test half-open state behavior

4. **OAuth Client:**
   - Test token caching and expiration
   - Test refresh token flow
   - Test error handling for all failure modes

5. **REST API Client:**
   - Test async operation handling
   - Test response wrapper compatibility
   - Test retry logic with circuit breaker

### Integration Tests to Add

1. **Rate Limiting Integration:**
   - Mock API with rate limit headers
   - Test adaptive rate adjustment in real scenario
   - Test burst handling

2. **Circuit Breaker + Retry:**
   - Test interaction between circuit breaker and retry logic
   - Test recovery after service degradation

---

## Performance Benchmarks

Run before and after refactoring:

```python
# Benchmark script template
import time
from utils.api_common import RateLimiter

def benchmark_rate_limiter(iterations=10000):
    """Benchmark rate limiter performance."""
    limiter = RateLimiter(calls_per_second=1000, burst_size=10)

    start = time.time()
    for _ in range(iterations):
        limiter.wait_if_needed()
    elapsed = time.time() - start

    print(f"Rate limiter: {iterations} calls in {elapsed:.2f}s")
    print(f"Average: {elapsed/iterations*1000:.3f}ms per call")

def benchmark_logger_init():
    """Benchmark logger initialization."""
    start = time.time()
    for _ in range(100):
        setup_logger()  # Should use cached instance
    elapsed = time.time() - start

    print(f"Logger init: 100 calls in {elapsed:.2f}s")
```

**Expected Results:**
- Rate limiter: < 0.001ms per call
- Logger init (cached): < 0.01ms per call
- Circuit breaker: < 0.001ms overhead

---

## Migration Guide

### For Script Authors

#### Logger Initialization (Breaking Change)

**Before:**
```python
from utils.logger import setup_logger

logger = setup_logger()  # Could call sys.exit(1)
```

**After:**
```python
from utils.logger import setup_logger
from utils.exceptions import LoggerConfigurationError, LoggerSecurityError

try:
    logger = setup_logger()
except (LoggerConfigurationError, LoggerSecurityError) as e:
    print(f"Logger initialization failed: {e}", file=sys.stderr)
    sys.exit(1)
```

#### REST API Async Operations (Compatible)

**Before:**
```python
api = create_rest_api(config)
response = api.get(url)
data = response.json()
```

**After (still works):**
```python
api = create_rest_api(config)
response = api.get(url)  # Returns dict directly
# Response could be AsyncOperationResult, but .json() still works
data = response if isinstance(response, dict) else response.json()
```

---

## Rollout Plan

### Phase 1: High Priority (Sprint 1)
**Week 1:**
- Logger module exception refactor
- Add comprehensive tests for logger

**Week 2:**
- Rate limiter header implementation
- REST API response wrapper
- OAuth exception specificity

### Phase 2: Medium Priority (Sprint 2)
**Week 3:**
- Memory optimization ADR decision
- Circuit breaker enhancements
- Rate limiter edge case fixes

**Week 4:**
- Integration testing
- Performance benchmarking
- Documentation updates

### Phase 3: Low Priority (Sprint 3)
**Week 5:**
- Path helpers exception clarity
- OAuth parameter cleanup
- Type hint improvements

**Week 6:**
- Final testing
- Release notes
- Version bump to v3.2

---

## Success Criteria

### Functional Requirements
- ✅ All existing tests pass
- ✅ New tests achieve >90% coverage for changed code
- ✅ No performance regression (benchmarks within 5%)

### Code Quality
- ✅ All high-priority issues resolved
- ✅ Consistent error handling patterns
- ✅ No breaking changes for existing scripts

### Documentation
- ✅ ADRs updated for memory optimization strategy
- ✅ Migration guide provided
- ✅ Release notes completed

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Logger refactor breaks scripts | Medium | High | Provide compatibility wrapper |
| Performance regression | Low | Medium | Benchmark before/after |
| Rate limiter too aggressive | Low | Medium | Make thresholds configurable |
| Memory optimization complex | Medium | Low | Document decision, phase gradually |

---

## Appendix: Code Metrics

### Current State
- **Total Lines (utils/):** ~7,500
- **Number of Classes:** 28
- **Number of Functions:** 156
- **Test Coverage:** ~75%
- **Type Hint Coverage:** ~95%

### Target State (v3.2)
- **Test Coverage:** >85%
- **High Priority Issues:** 0
- **Medium Priority Issues:** <3
- **Performance:** No regression

---

## Questions & Decisions Needed

1. **Logger Exception Strategy:**
   - Should we provide a compatibility mode that still calls sys.exit?
   - **Decision:** Yes, add `setup_logger(strict=False)` that swallows exceptions

2. **Rate Limiter Aggressiveness:**
   - Should adaptive rate adjustment be opt-in or opt-out?
   - **Decision:** Opt-out (enabled by default, configurable)

3. **Memory Optimization:**
   - Prioritize memory or developer experience?
   - **Decision:** Document strategy (see ADR above)

4. **Async Response Wrapper:**
   - Return custom type or keep mutating response?
   - **Decision:** Custom type for clarity and type safety

---

## References

- TXO Business ADR: `ai/decided/txo-business-adr_v3.1.md`
- Technical Standards: `ai/decided/txo-technical-standards_v3.1.md`
- Utils Reference: `ai/decided/utils-quick-reference_v3.1.md`
- Original Code Review: Code review conducted 2025-09-29

---

**Version:** 3.2
**Status:** Draft - Awaiting Approval
**Next Review:** After Phase 1 completion