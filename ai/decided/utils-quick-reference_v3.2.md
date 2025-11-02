# TXO Utils Quick Reference v3.2

> **🚨 DO NOT INVENT THESE FUNCTIONS - THEY ALREADY EXIST**
>
> Use this reference to see what's available in `utils/` before writing new code.
> All functions follow TXO Business ADRs and Technical Standards.
> **v3.2 NEW**: Logger strict mode, AsyncOperationResult, CircuitBreaker.stats, Adaptive rate limiting

---

## 🏗️ Script Setup & Configuration

### Script Initialization (`utils.script_runner`)

```python
from utils.script_runner import parse_args_and_load_config

# Most common pattern (no authentication needed)
config = parse_args_and_load_config("Process local data")

# API scripts (explicit token requirement)
config = parse_args_and_load_config("BC sync script", require_token=True)

# Returns config with injected fields:
# config["_org_id"] = "txo"
# config["_env_type"] = "prod"
# config["_token"] = "abc123..." (if require_token=True)
```

### Configuration Loading (`utils.config_loader`)

```python
from utils.config_loader import ConfigLoader, ConfigContext

# Direct usage
loader = ConfigLoader("txo", "prod")
config = loader.load_config(validate=True, include_secrets=True)

# Context manager pattern
with ConfigContext("txo", "prod") as config:
    api_url = config['global']['api-base-url']  # Hard-fail access
    token = config['_client-secret']  # Injected secret (kebab-case preserved)
```

### Logging (`utils.logger`)

```python
from utils.logger import setup_logger

# v3.2: Logger with strict mode for testing
# Normal usage - exits on error (infrastructure exception per ADR-T012)
logger = setup_logger()  # Default: strict=False, exits if config missing

# Testing usage - raises exceptions instead of exit
logger = setup_logger(strict=True)  # For unit tests, raises LoggerConfigurationError/LoggerSecurityError

# Hierarchical context logging
context = f"[{env_type.title()}/{company_name}/{api_name}]"
logger.info(f"{context} Processing started")
logger.debug(f"{context} Request payload: {payload}")  # Tokens auto-redacted
```

---

## 💾 Data Operations

### Universal Data Handler (`utils.load_n_save`)

```python
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir

data_handler = TxoDataHandler()

# Universal save - auto-detects format from data type + extension
data_handler.save(dict_data, Dir.OUTPUT, "report.json") -> Path  # JSON
data_handler.save(dataframe, Dir.OUTPUT, "data.xlsx") -> Path  # Excel single sheet "Sheet1"
data_handler.save(dataframe, Dir.OUTPUT, "data.csv") -> Path  # CSV
data_handler.save("text", Dir.OUTPUT, "log.txt") -> Path  # Text

# Multi-sheet Excel (v3.1.1) - Dict of DataFrames auto-detected
sheets = {"Summary": summary_df, "Details": details_df, "Errors": errors_df}
data_handler.save(sheets, Dir.OUTPUT, "report.xlsx") -> Path  # Multi-sheet Excel
data_handler.save_with_timestamp(sheets, Dir.OUTPUT, "report.xlsx", add_timestamp=True) -> Path  # report_2025-09-28T123456Z.xlsx

# UTC Timestamp saving (v3.1) - TXO standard format: 2025-01-25T143045Z
timestamp = data_handler.get_utc_timestamp() -> str  # "2025-01-25T143045Z"
data_handler.save_with_timestamp(data, Dir.OUTPUT, "report.json") -> Path  # report.json
data_handler.save_with_timestamp(data, Dir.OUTPUT, "report.json", add_timestamp=True) -> Path  # report_2025-01-25T143045Z.json

# Universal load - auto-detects format from extension
data = data_handler.load(Dir.DATA, "input.csv") -> DataFrame  # Returns pandas DataFrame
data = data_handler.load(Dir.CONFIG, "settings.json") -> dict  # Returns dict
data = data_handler.load(Dir.DATA, "document.txt") -> str  # Returns string

# Utility methods
exists = data_handler.exists(Dir.DATA, "file.csv", check_empty=True) -> bool
size = data_handler.get_size(Dir.OUTPUT, "report.xlsx") -> int  # bytes
data_handler.delete(Dir.TMP, "temp.json", safe=True) -> bool
```

### Path Management (`utils.path_helpers`)

```python
from utils.path_helpers import Dir, get_path, ProjectPaths

# Type-safe directory constants (ALWAYS use these)
Dir.CONFIG  # 'config'
Dir.DATA  # 'data'
Dir.OUTPUT  # 'output'
Dir.LOGS  # 'logs'
Dir.TMP  # 'tmp'
Dir.SCHEMAS  # 'schemas'
Dir.WSDL  # 'wsdl'

# Path construction with automatic parent creation
path = get_path(Dir.CONFIG, "settings.json") -> Path
path = get_path(Dir.OUTPUT, "report.xlsx", ensure_parent=True) -> Path

# Project paths access
paths = ProjectPaths.init()
print(f"Root: {paths.root}")
print(f"Config dir: {paths.config}")

# Cleanup utilities
deleted_count = cleanup_tmp(max_age_hours=24) -> int
size_str = get_dir_size(Dir.LOGS, human_readable=True) -> str  # "1.2 MB"
```

---

## 🌐 API Integration

### API Factory (`utils.api_factory`)

```python
from utils.api_factory import create_rest_api, ApiManager

# Create configured REST API client
api = create_rest_api(config, require_auth=True) -> TxoRestAPI
api_no_auth = create_rest_api(config, require_auth=False) -> TxoRestAPI

# With caching (optional)
api = create_rest_api(config, use_cache=True, cache_key="custom_key")

# Context manager for automatic cleanup
with ApiManager(config) as manager:
    rest_api = manager.get_rest_api(require_auth=True)
    # API automatically cleaned up on exit
```

### REST API Operations (`utils.rest_api_helpers`)

```python
# Created via api_factory - don't instantiate directly!
# api = create_rest_api(config)  # Use this instead

# Standard operations
response = api.get(url, **kwargs) -> Any
response = api.post(url, json=data, **kwargs) -> Any
response = api.put(url, json=data, **kwargs) -> Any
response = api.delete(url, **kwargs) -> Any

# Handles automatically:
# - Rate limiting (if configured) - v3.2: Adaptive adjustment from API headers
# - Circuit breaker (if configured) - v3.2: With statistics
# - Retries with exponential backoff
# - Token redaction in logs
# - Async operations (202 polling) - v3.2: Returns AsyncOperationResult
```

### AsyncOperationResult (`utils.rest_api_helpers`)
**v3.2 NEW**: Type-safe wrapper for completed async operations

```python
from utils.rest_api_helpers import AsyncOperationResult

# Returned by _execute_request() for 202 Accepted responses
# Provides Response-compatible interface without mutation

# Public API methods (get, post, etc.) handle both Response and AsyncOperationResult
result = api.post(url, json=data)  # May return AsyncOperationResult for async ops
data = result.json() if result.content else {}  # Works for both types

# Properties available:
# - .json() → Dict: Data payload
# - .ok → bool: Success check (200-299)
# - .content → bytes: JSON as bytes
# - .text → str: JSON as string
# - .status_code → int: HTTP status
# - .data → Dict: Actual data
# - .original_response → Response: Original 202 (if async)

# Type-aware code can distinguish:
if isinstance(result, AsyncOperationResult):
    print(f"Async operation completed: {result.data}")
```

**Purpose**: Eliminates response._content mutation (ADR-T004 anti-pattern)
**Compatibility**: Fully backward compatible with existing code

### OAuth Authentication (`utils.oauth_helpers`)

```python
from utils.oauth_helpers import OAuthClient

# Usually handled by script_runner - use only for custom auth flows
oauth_client = OAuthClient(tenant_id="your-tenant", cache_tokens=True)

token = oauth_client.get_client_credentials_token(
    client_id="your-client-id",
    client_secret="your-secret",
    scope="https://api.businesscentral.dynamics.com/.default",
    tenant_id="your-tenant"
) -> str
```

---

## ⚡ Performance & Reliability

### Rate Limiting & Circuit Breaker (`utils.api_common`)

```python
from utils.api_common import RateLimiter, CircuitBreaker

# Usually created by api_factory - manual usage for custom scenarios
limiter = RateLimiter(calls_per_second=10, burst_size=1.0)
limiter.wait_if_needed()  # Call before each API request

breaker = CircuitBreaker(failure_threshold=5, timeout=60)
if breaker.is_open():
    logger.warning("Circuit breaker is open, skipping request")
    return None

# After successful API call
breaker.record_success()

# After failed API call
breaker.record_failure()

# v3.2 NEW: Get circuit breaker statistics
stats = breaker.stats  # Returns dict with metrics
logger.info(f"Circuit state: {stats['state']}, failure rate: {stats['failure_rate']:.1%}")

# Available stats (9 metrics):
# - state: Current state (closed/open/half-open)
# - consecutive_failures: Sequential failures
# - total_requests: Lifetime request count
# - total_failures: Lifetime failure count
# - failure_rate: Percentage (total_failures / total_requests)
# - time_in_current_state: Seconds in current state
# - timeout_seconds: Configured timeout
# - last_failure_ago: Seconds since last failure (or None)
# - failure_threshold: Configured threshold
```

**v3.2 Enhancement**: State transition logging and statistics for observability

### Retry Logic (`utils.api_common`)

```python
from utils.api_common import manual_retry, apply_jitter

# Manual retry for any function
result = manual_retry(
    my_function, arg1, arg2,
    max_retries=3,
    backoff=2.0,
    jitter_config={"min-factor": 0.8, "max-factor": 1.2},
    kwarg1="value"
) -> Any

# Jitter calculation
jittered_delay = apply_jitter(delay=5.0, jitter_config=config) -> float
```

---

## 🛠️ Error Handling

### Custom Exceptions (`utils.exceptions`)

```python
from utils.exceptions import (
    TxoBaseError, HelpfulError, ErrorContext,
    ApiError, ApiAuthenticationError, ApiTimeoutError,
    ConfigurationError, ValidationError, FileOperationError
)

# User-friendly errors with solutions
raise HelpfulError(
    what_went_wrong="Config file missing",
    how_to_fix="Copy from templates/ directory",
    example="cp config/templates/example.json config/txo-prod-config.json"
)

# API-specific errors
raise ApiAuthenticationError("Token expired")
raise ApiTimeoutError("Request timed out", timeout_seconds=30)

# With error context
context = ErrorContext(operation="data_processing", resource="customers.csv")
raise ValidationError("Invalid CSV format", context=context)
```

---

## 📊 Operation Results Tracking

### ProcessingResults Pattern (Business Requirement)

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class ProcessingResults:
    """Standard pattern for tracking bulk operations - USE THIS!"""
    created: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    expected_errors: int = 0

    def add_result(self, api_name: str, company_id: str, result: OperationResult):

    # Implementation in your code

    def summary(self) -> str:
        """Generate ✅/❌ user-friendly summary"""
        # Returns: "✅ All 150 operations successful: 75 created, 75 updated"
        # Or: "❌ Completed with 5 failures: 70 created, 75 updated, 5 failed"


# Usage pattern
results = ProcessingResults()
for record in data:
    try:
        if create_customer(record):
            results.created.append(f"CustomerAPI/{company_id}/{record.id}")
        else:
            results.failed.append(f"CustomerAPI/{company_id}/{record.id}: creation failed")
    except Exception as e:
        results.failed.append(f"CustomerAPI/{company_id}/{record.id}: {str(e)}")

logger.info(results.summary())  # Always show final summary
```

---

## 🔄 Import Patterns

### Standard Import Block

```python
# Standard TXO script imports (copy this pattern)
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir
from utils.api_factory import create_rest_api
from utils.exceptions import HelpfulError

# Initialize
logger = setup_logger()
data_handler = TxoDataHandler()
```

---

## ⚠️ What NOT to Do

### ❌ Don't Invent These (They Already Exist!)

```python
# ❌ DON'T CREATE - Use TxoDataHandler.save() instead
def save_json(data, filename): ...
def save_excel(df, filename): ...

# ❌ DON'T CREATE - Use create_rest_api() instead
import requests
session = requests.Session()  # Use create_rest_api(config, require_auth=False)
class CustomAPIClient: ...
class RateLimitedClient: ...

# ❌ DON'T CREATE - Use save_with_timestamp() instead
utc_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")  # Use save_with_timestamp()
filename = f"report_{timestamp}.xlsx"  # Use save_with_timestamp(data, Dir.OUTPUT, "report.xlsx", add_timestamp=True)

# ❌ DON'T CREATE - Use Dir constants instead
DIRECTORIES = {"config": "config", "output": "output"}

# ❌ DON'T CREATE - Use setup_logger() instead
def create_logger(): ...
def configure_logging(): ...

# ❌ DON'T ADD - Avoid unnecessary complexity
file_size = output_path.stat().st_size  # Focus on core functionality
start_time = time.time(); elapsed = time.time() - start_time  # Not needed
```

### ❌ Anti-Patterns

```python
# ❌ String literals for directories
data_handler.save(df, "output", "file.xlsx")

# ❌ Direct instantiation of complex objects
api = TxoRestAPI(token, timeout=30)  # Use api_factory instead

# ❌ Print statements
print("Processing complete")  # Use logger.info() instead

# ❌ Soft-fail for configuration
timeout = config.get("timeout", 30)  # Use config["timeout"] instead

# ❌ OUTPUT without UTC timestamp (ADR-B017 violation)
filename = f"{config['_org_id']}-{config['_env_type']}-report.json"
data_handler.save(data, Dir.OUTPUT, filename)  # MUST use save_with_timestamp!

# ❌ TMP without org-env pattern
data_handler.save(cache, Dir.TMP, "temp-data.json")  # Missing org and env!

# ❌ Filename missing env_type
filename = f"results-{config['_org_id']}.json"  # MUST include env_type!

# ❌ Generated payload WITH UTC timestamp
filename = f"{config['_org_id']}-{config['_env_type']}-request.json"
data_handler.save_with_timestamp(payload, Dir.GENERATED_PAYLOADS, filename, add_timestamp=True)
# Why wrong: Payloads MUST be deterministic for human validation workflow

# ❌ Manual UTC formatting
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
filename = f"data_{timestamp}.json"
# Why wrong: Use framework's save_with_timestamp() method instead
```

---

## 🔍 **AI Code Review Checklist**

**Before writing ANY code, check:**

1. **API Calls**: Am I using `create_rest_api()` instead of manual `requests`?
2. **Timestamps**: Am I using `get_utc_timestamp()` instead of manual datetime formatting?
3. **File Operations**: Am I using `TxoDataHandler.save()` instead of manual file I/O?
4. **Directories**: Am I using `Dir.*` constants instead of string literals?
5. **Logging**: Am I using `setup_logger()` instead of print statements?
6. **Complexity**: Am I adding unnecessary timing, file size, or performance metrics?

**Red Flags** (immediately refactor):
- `import requests` → Use `create_rest_api()`
- `datetime.now()` for timestamps → Use `get_utc_timestamp()`
- `'output'` or `'config'` strings → Use `Dir.OUTPUT`, `Dir.CONFIG`
- Performance timing code → Remove unless specifically requested
- Manual session management → Use TXO framework

---

## 🎯 Usage Examples

### Complete Script Pattern

```python
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir
from utils.api_factory import create_rest_api

logger = setup_logger()
data_handler = TxoDataHandler()


def main():
    # 1. Initialize
    config = parse_args_and_load_config("Customer sync script", require_token=True)

    # 2. Load data
    customers = data_handler.load(Dir.DATA, "customers.csv")

    # 3. Create API client
    api = create_rest_api(config)

    # 4. Process with results tracking
    results = ProcessingResults()
    for customer in customers:
        try:
            response = api.post("/customers", json=customer.to_dict())
            results.created.append(f"CustomerAPI/{config['_org_id']}/{customer.id}")
        except Exception as e:
            results.failed.append(f"CustomerAPI/{config['_org_id']}/{customer.id}: {e}")

    # 5. Save results with org-env pattern and UTC timestamp (ADR-B017)
    filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
    output_path = data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
    logger.info(f"Results saved: {output_path}")
    logger.info(results.summary())
    # Produces: output/txo-lab-sync-results_2025-11-01T143022Z.json


if __name__ == "__main__":
    main()
```

---

## 🔗 Integration with ADRs

This reference implements:

- **Business ADRs**: Hard-fail config, logging context, ProcessingResults, directory structure
- **Technical Standards**: Thread safety, lazy loading, exception hierarchy, type safety

**Token Usage Strategy:**

```
Your Prompt + Business ADRs + Technical Standards + This Quick Reference
→ AI generates code using EXISTING functions
→ Consistent patterns, fewer tokens, working code
```

---

## 📂 Directory-Specific Save Patterns (ADR-B017)

### Quick Reference Table

| Directory                | UTC Timestamp? | Org-Env Pattern? | Method                                         | RFC 2119     |
|--------------------------|----------------|------------------|------------------------------------------------|--------------|
| `Dir.OUTPUT`             | ✅ YES          | ✅ YES            | `save_with_timestamp(..., add_timestamp=True)` | **MUST**     |
| `Dir.TMP`                | ✅ YES          | ✅ YES            | `save_with_timestamp(..., add_timestamp=True)` | **SHOULD**   |
| `Dir.GENERATED_PAYLOADS` | ❌ NO           | ✅ YES            | `save()`                                       | **MUST NOT** |
| `Dir.PAYLOADS`           | ❌ NO           | ✅ YES            | Manual move                                    | **MUST NOT** |
| `Dir.WSDL`               | ❌ NO           | ❌ NO             | `save()`                                       | **MUST NOT** |

### Complete Examples by Directory

#### Output Files (MUST use UTC)
```python
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir

data_handler = TxoDataHandler()

# JSON output
filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
path = data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
# → output/txo-lab-sync-results_2025-11-01T143022Z.json

# Excel output with multiple sheets
sheets = {"Summary": summary_df, "Details": details_df}
filename = f"{config['_org_id']}-{config['_env_type']}-analysis-report.xlsx"
path = data_handler.save_with_timestamp(sheets, Dir.OUTPUT, filename, add_timestamp=True)
# → output/txo-lab-analysis-report_2025-11-01T143022Z.xlsx
```

#### Tmp Files (SHOULD use UTC)
```python
# Processing cache (recommended pattern)
filename = f"{config['_org_id']}-{config['_env_type']}-processing-cache.json"
path = data_handler.save_with_timestamp(cache, Dir.TMP, filename, add_timestamp=True)
# → tmp/txo-lab-processing-cache_2025-11-01T143022Z.json

# Acceptable: Ephemeral data without UTC (flexible)
path = data_handler.save(quick_cache, Dir.TMP, "ephemeral-cache.json")
# → tmp/ephemeral-cache.json
```

#### Generated Payloads (MUST NOT use UTC)
```python
# JSON payloads for human validation
filename = f"{config['_org_id']}-{config['_env_type']}-create-user-request.json"
path = data_handler.save(request_payload, Dir.GENERATED_PAYLOADS, filename)
# → generated_payloads/txo-lab-create-user-request.json (deterministic, no timestamp)

# Workflow:
# 1. Code generates → generated_payloads/txo-lab-create-user-request.json
# 2. Human validates → checks JSON structure, field values
# 3. Human moves → cp to payloads/txo-lab-create-user-request.json
# 4. Code reads and sends → from payloads/ directory
```

#### Payloads Directory (Manual Workflow)
```python
# Code READS from payloads/, does NOT write to it
# Files are manually moved from generated_payloads/ after human validation

# Reading validated payloads
from utils.path_helpers import get_path, Dir
import json

payload_file = f"{config['_org_id']}-{config['_env_type']}-create-user-request.json"
payload_path = get_path(Dir.PAYLOADS, payload_file)

with open(payload_path, 'r') as f:
    validated_payload = json.load(f)

# Send via API...
```

#### WSDL Files (MUST NOT use UTC)
```python
# Service definitions (versioned by service, not time)
filename = "UserService_v2.1.wsdl"
path = data_handler.save(wsdl_content, Dir.WSDL, filename)
# → wsdl/UserService_v2.1.wsdl (service version, not timestamp)
```

### Why Different Rules?

**Output (MUST use UTC):**
- Each run creates unique file → No overwrites
- Audit trail and debugging require time tracking
- Example: "Upload your output from yesterday's 2pm run"

**Tmp (SHOULD use UTC):**
- Multi-run debugging benefits from timestamps
- But MAY be relaxed for truly ephemeral data

**Generated Payloads (MUST NOT use UTC):**
- Human validation workflow requires stable filenames
- Always overwrites with latest version
- Easier to reference: "Check the txo-lab-create-user-request.json file"

**Payloads (MUST NOT use UTC):**
- Manually curated by humans
- Stable references in code and documentation

**WSDL (MUST NOT use UTC):**
- Service version controls naming (e.g., v2.1, v3.0)
- Not time-based versioning

---

## Version History

### v3.2 (Current)

- **Logger**: Added strict parameter (setup_logger(strict=False) for testing)
- **AsyncOperationResult**: New class for type-safe async operation handling
- **CircuitBreaker**: Added .stats property with 9 metrics for monitoring
- **Rate Limiting**: Adaptive adjustment from API headers (automatic)
- **Patterns**: @staticmethod for helper methods that don't use self
- **Infrastructure Exception**: Logger may call sys.exit() (ADR-T012)
- Updated all features to reflect v3.2 refactoring improvements

### v3.1.1

- Added multi-sheet Excel support with dict of DataFrames auto-detection
- Enhanced smart format validation for Excel multi-sheet patterns
- Single DataFrame auto-names sheet as "Sheet1" (DEFAULT_SHEET_NAME constant)

### v3.1

- Organized by use case to prevent AI hallucination
- Added anti-patterns and complete script examples
- Added UTC timestamp utilities (get_utc_timestamp, save_with_timestamp)

### v1.0

- Initial comprehensive function reference
- Established DO NOT INVENT approach

---

**Version:** v3.1.1
**Last Updated:** 2025-09-28
**Domain:** TXO Utils Reference
**Purpose:** Prevent AI hallucination by showing existing functions