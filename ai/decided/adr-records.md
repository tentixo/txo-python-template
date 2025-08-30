# Architecture Decision Records

## ADR-001: Mandatory org_id and env_type Parameters

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Scripts need to handle multiple organizations and environments without data mixing.

### Decision
All scripts require `org_id` and `env_type` as first two command-line arguments.

### Consequences
- Positive: Clear data separation, predictable file naming
- Negative: No defaults can confuse beginners
- Mitigation: Helpful error messages guide users

### Example
```bash
python script.py txo prod
# Creates: txo-prod-config.json
```

---

## ADR-002: Configuration Injection Pattern

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Functions need access to configuration, tokens, and metadata.

### Decision
Pass single `config` dictionary with underscore-prefixed injected fields.

### Consequences
- Positive: Cleaner function signatures, easier testing
- Negative: Less explicit about dependencies
- Mitigation: Document injected fields clearly

### Example
```python
config["_org_id"] = args.org_id
config["_token"] = token
process_data(config)  # Not process_data(org_id, token, ...)
```

---

## ADR-003: Logger-First Development

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Debugging production issues requires comprehensive logging.

### Decision
Setup logger before any other code in every module.

### Consequences
- Positive: Consistent logging, better debugging
- Negative: Slight performance overhead
- Mitigation: Use appropriate log levels

### Example
```python
from utils.logger import setup_logger
logger = setup_logger()
```

---

## ADR-004: Tuple Context Pattern for URLs

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Logs need context about which environment/resource is being accessed.

### Decision
URL builders return `(url, context)` tuple.

### Consequences
- Positive: Consistent log context
- Negative: Must unpack tuples
- Mitigation: Clear naming convention

### Example
```python
url, ctx = build_url(...)
logger.info(f"{ctx} Processing started")
```

---

## ADR-005: Error Philosophy

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Different data sources have different reliability guarantees.

### Decision
- Hard fail (dict['key']) for configuration data
- Soft fail (dict.get('key')) for external data

### Consequences
- Positive: Fail fast for configuration errors
- Negative: Must understand data source
- Mitigation: Document expectations

---

## ADR-006: Centralized Path Management

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Path construction errors cause cross-platform issues.

### Decision
Always use `get_path()` from path_helpers.

### Consequences
- Positive: Cross-platform compatibility
- Negative: Extra import required
- Mitigation: Automatic directory creation

---

## ADR-007: Output File Naming Convention

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Output files need clear identification and timestamp.

### Decision
Pattern: `{org_id}-{env_type}-{purpose}_{UTC}.{ext}`

### Consequences
- Positive: No overwrites, clear lineage
- Negative: Long filenames
- Mitigation: Use purpose abbreviations

### Example
```python
filename = f"{org_id}-{env_type}-report_{utc}.xlsx"
# Creates: txo-prod-report_2025-01-15T1430Z.xlsx
```

---

## ADR-008: No Print Statements

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Print statements don't appear in log files.

### Decision
Never use print(), always use logger.

### Consequences
- Positive: All output captured in logs
- Negative: Requires logger setup
- Mitigation: Logger setup is mandatory anyway

---

## ADR-009: Type Hints Required

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Type hints improve code clarity and IDE support.

### Decision
All functions must have type hints.

### Consequences
- Positive: Better IDE support, clearer code
- Negative: More verbose signatures
- Mitigation: Use typing module imports

---

## ADR-010: JSON Configuration Only

**Status:** MANDATORY  
**Date:** 2025-01-01  

### Context
Multiple configuration formats cause confusion.

### Decision
Use JSON exclusively for configuration.

### Consequences
- Positive: Single parser, schema validation
- Negative: No comments in JSON
- Mitigation: Use descriptive keys

---

## ADR-011: Automatic Token Redaction in Logs

**Status:** MANDATORY  
**Date:** 2025-01-15  

### Context
Sensitive tokens, API keys, and secrets accidentally logged create serious security risks. Even experienced developers can accidentally log sensitive data during debugging.

### Decision
Implement automatic TokenRedactionFilter that redacts sensitive patterns before logging.

### Implementation
The filter automatically redacts:
- Bearer tokens
- JWT tokens (eyJ...)
- API keys (40+ character strings)
- Password fields in JSON
- Client secrets
- OAuth tokens

### Consequences
- Positive: Prevents accidental token exposure in logs
- Positive: Works transparently without code changes
- Negative: Slight performance overhead for regex matching
- Mitigation: Optimized regex patterns, compiled once

### Example
```python
logger.info(f"Using token: {token}")
# Actually logs: "Using token: Bearer [REDACTED]"

logger.debug(f"Response: {json.dumps({'password': 'secret123'})}")
# Actually logs: "Response: {"password": "[REDACTED]"}"
```

---

## ADR-012: Rate Limiting and Circuit Breaker Patterns

**Status:** RECOMMENDED  
**Date:** 2025-01-15  

### Context
External APIs have rate limits that cause 429 errors. Failures can cascade when services are down, overwhelming systems with retries.

### Decision
Provide optional RateLimiter and CircuitBreaker classes configurable via script-behavior.

### Implementation
```json
{
  "script-behavior": {
    "enable-rate-limiting": true,
    "rate-limit-per-second": 10,
    "enable-circuit-breaker": true,
    "circuit-breaker-threshold": 5,
    "circuit-breaker-timeout": 60
  }
}
```

### Consequences
- Positive: Prevents API bans from rate limit violations
- Positive: Stops cascade failures quickly
- Positive: Configurable per environment
- Negative: Adds complexity to API calls
- Mitigation: Disabled by default, opt-in only

---

## ADR-013: Async Operation Support (202 Accepted)

**Status:** AUTOMATIC  
**Date:** 2025-01-15  

### Context
Modern REST APIs return 202 Accepted for long-running operations, requiring polling for completion.

### Decision
Automatically handle 202 responses by polling the Location header until operation completes.

### Implementation
- Check for 202 status code
- Extract Location header
- Poll with exponential backoff
- Respect Retry-After header
- Configurable max wait time (default 5 minutes)

### Consequences
- Positive: Transparent handling of async operations
- Positive: No special code needed for 202 responses
- Negative: May wait up to 5 minutes
- Mitigation: Configurable timeouts and intervals

### Example
```python
# This automatically handles 202 and polls for completion
result = api.post("/long-operation", data)
# May take several minutes but returns final result
```

---

## ADR-014: Session Pool Management

**Status:** AUTOMATIC  
**Date:** 2025-01-15  

### Context
Creating unlimited HTTP sessions causes memory leaks and connection exhaustion.

### Decision
Implement SessionManager with LRU cache limiting to 50 concurrent sessions.

### Implementation
- Thread-safe session cache
- LRU eviction when limit reached
- Automatic cleanup on eviction
- Per-thread session storage for performance

### Consequences
- Positive: Prevents memory leaks
- Positive: Limits connection pool size
- Positive: Thread-safe operation
- Negative: May evict active sessions under heavy load
- Mitigation: Reasonable default of 50 sessions

---

## ADR-015: HelpfulError Pattern

**Status:** MANDATORY  
**Date:** 2025-01-15  

### Context
Stack traces and technical error messages confuse non-technical users and don't provide actionable guidance.

### Decision
Use HelpfulError exception for all user-facing errors with three components:
1. What went wrong (problem description)
2. How to fix it (solution)
3. Example (optional but recommended)

### Implementation
```python
raise HelpfulError(
    what_went_wrong="Configuration file not found",
    how_to_fix="Create the file in config/ directory",
    example="Copy config/example.json and modify"
)
```

### Consequences
- Positive: Clear, actionable error messages
- Positive: Consistent error format
- Positive: Reduces support requests
- Negative: Requires thoughtful error handling
- Mitigation: Provide examples in codebase

### Output Format
```
❌ Problem: Configuration file not found

✅ Solution: Create the file in config/ directory

📝 Example:
Copy config/example.json and modify
```

---

## ADR-016: Memory Optimization with __slots__

**Status:** RECOMMENDED  
**Date:** 2025-01-15  

### Context
Dataclasses without __slots__ use dictionaries for attribute storage, consuming significant memory with many instances.

### Decision
Add __slots__ to frequently instantiated dataclasses like ErrorContext, RestOperationResult, and ProcessingResults.

### Implementation
```python
@dataclass
class ErrorContext:
    __slots__ = ['operation', 'resource', 'details']
    operation: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

### Consequences
- Positive: ~40% memory reduction per instance
- Positive: Slightly faster attribute access
- Negative: Can't add attributes dynamically
- Negative: Inheritance becomes more complex
- Mitigation: Only use for high-volume dataclasses

---

## ADR-017: Python 3.13+ Feature Adoption

**Status:** OPTIONAL  
**Date:** 2025-01-15  

### Context
Python 3.13 introduces new features that can improve code quality and performance, but not all environments support it.

### Decision
Adopt Python 3.13+ features where beneficial, but maintain backwards compatibility to Python 3.10.

### Features to Adopt (When Available)
- PEP 695 type parameters (3.12+)
- Pattern matching with match/case (3.10+)
- Exception groups and notes (3.11+)
- Better error messages (3.11+)

### Consequences
- Positive: Cleaner, more modern code
- Positive: Better performance
- Negative: Requires version checking
- Mitigation: Feature detection and fallbacks

---

## ADR-018: Context Manager Pattern for Resources

**Status:** RECOMMENDED  
**Date:** 2025-01-15  

### Context
API clients and resources need proper cleanup to prevent connection leaks.

### Decision
Implement context manager support for all resource-holding classes.

### Implementation
```python
with ApiManager(config) as manager:
    api = manager.get_rest_api()
    # Automatically cleaned up on exit
```

### Consequences
- Positive: Guaranteed resource cleanup
- Positive: Cleaner code structure
- Positive: Exception-safe
- Negative: Extra indentation level
- Mitigation: Also support manual cleanup

---

## Template for New ADRs

## ADR-XXX: Title

**Status:** MANDATORY | RECOMMENDED | OPTIONAL | DEPRECATED  
**Date:** YYYY-MM-DD  

### Context
Why is this decision needed?

### Decision
What is the decision?

### Implementation
How is it implemented? (if applicable)

### Consequences
- Positive: Benefits
- Negative: Drawbacks
- Mitigation: How to address drawbacks

### Example
Code or usage example