# TXO Python Template v2.1 - In-Depth Guide

## Overview

The TXO Python Template v2.1 is a production-ready framework that enforces consistent patterns across all Python scripts interacting with REST/OData APIs. It includes enterprise-grade features like automatic token redaction, rate limiting, circuit breakers, and async operation support.

**Version**: 2.1.0  
**Python**: 3.10+ required, 3.13+ recommended  
**Philosophy**: Hard-fail on configuration, fail-fast on errors, clear guidance for users

## Table of Contents
1. [Core Patterns](#core-patterns)
2. [V2.1 Features](#v21-features)
3. [Security Patterns](#security-patterns)
4. [API Resilience Patterns](#api-resilience-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Performance Patterns](#performance-patterns)
7. [Configuration Management](#configuration-management)
8. [Helper Modules Reference](#helper-modules-reference)
9. [Script Development Guide](#script-development-guide)
10. [Best Practices](#best-practices)
11. [Common Pitfalls](#common-pitfalls)
12. [Troubleshooting](#troubleshooting)

## Core Patterns

### 1. Mandatory Parameters Pattern

Every script MUST have `org_id` and `env_type` as first two arguments:

```python
# Always required
python script.py <org_id> <env_type>

# Examples
python script.py acme prod
python script.py demo test
python script.py mycompany dev
```

This creates predictable naming:
- Config: `acme-prod-config.json`
- Secrets: `acme-prod-config-secrets.json`
- Output: `acme-prod-report_2025-01-15T1430Z.xlsx`

### 2. Hard-Fail Configuration Pattern

**V2.1 Philosophy**: Configuration errors should fail immediately, not silently.

```python
# ✅ CORRECT - Hard fail on missing config
api_url = config['global']['api-base-url']  # KeyError if missing
tenant = config['global']['tenant-id']      # Immediate failure

# ❌ WRONG - Soft fail with defaults
api_url = config.get('global', {}).get('api-base-url', 'default')  # Silent bugs!

# ✅ CORRECT - Optional API response data
email = response.get('email')  # None if missing is OK for API data
```

### 3. Configuration Injection Pattern

All configuration and derived values in a single dict:

```python
config = parse_args_and_load_config("Script description")

# Automatically injected:
# config['_org_id']      - from command line
# config['_env_type']    - from command line  
# config['_token']       - from OAuth or secrets
# config['_client_secret'] - from secrets file (if exists)
```

Pass the entire config dict:

```python
# ✅ CORRECT
def process_data(config: Dict[str, Any]) -> None:
    org_id = config['_org_id']
    api = create_rest_api(config)

# ❌ WRONG
def process_data(org_id: str, env_type: str, token: str) -> None:
    pass  # Don't pass individual parameters
```

### 4. Logger-First Pattern

Every module starts with logger:

```python
# src/any_script.py  ← Path comment ALWAYS first line
from utils.logger import setup_logger

logger = setup_logger()  # Before any other code

# Then use throughout
logger.info("Starting process")
logger.debug("Detailed information")
logger.error("Error occurred", exc_info=True)

# NEVER use print()
print("Don't do this")  # ❌ WRONG
```

### 5. HelpfulError Pattern

User-friendly errors with actionable solutions:

```python
from utils.exceptions import HelpfulError

if not Path(config_file).exists():
    raise HelpfulError(
        what_went_wrong=f"Configuration file '{config_file}' not found",
        how_to_fix="Create the file in the config/ directory",
        example=f"Copy config/example.json to config/{org_id}-{env_type}-config.json"
    )
```

Output format:
```
❌ Problem: Configuration file 'acme-prod-config.json' not found

✅ Solution: Create the file in the config/ directory

📝 Example:
Copy config/example.json to config/acme-prod-config.json
```

### 6. Path Centralization Pattern

Never construct paths manually:

```python
# ✅ CORRECT
from utils.path_helpers import get_path
config_file = get_path('config', 'settings.json')
output_file = get_path('output', 'report.xlsx')

# ❌ WRONG
config_file = Path('config/settings.json')
config_file = 'config/settings.json'
config_file = os.path.join('config', 'settings.json')
```

### 7. Output Naming Pattern

Include organization, environment, and UTC timestamp:

```python
from datetime import datetime, timezone

utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
filename = f"{config['_org_id']}-{config['_env_type']}-report_{utc}.xlsx"
# Creates: acme-prod-report_2025-01-15T1430Z.xlsx
```

### 8. Intelligent Save Pattern

The `save()` method auto-detects type from data and extension:

```python
from utils.load_n_save import TxoDataHandler

data_handler = TxoDataHandler()

# All use the same method - just change extension!
data_handler.save(dict_data, "output", "data.json")    # JSON
data_handler.save(dataframe, "output", "data.csv")     # CSV
data_handler.save(dataframe, "output", "data.xlsx")    # Excel
data_handler.save("text", "output", "report.txt")      # Text

# Handles Decimal automatically for JSON
from decimal import Decimal
data = {"amount": Decimal("99.99"), "count": 100}
data_handler.save(data, "output", "amounts.json")  # Works!
```

## V2.1 Features

### Automatic Token Redaction

Logger automatically redacts sensitive patterns to prevent exposure:

```python
# These are automatically redacted in logs:
logger.info(f"Token: {token}")  
# Logs: "Token: Bearer [REDACTED]"

logger.debug(f"Config: {json.dumps({'password': 'secret'})}")  
# Logs: "Config: {"password": "[REDACTED]"}"

logger.error(f"JWT: {jwt_token}")  
# Logs: "JWT: [REDACTED_JWT]"
```

Redacted patterns:
- Bearer tokens → `[REDACTED]`
- JWT tokens (eyJ...) → `[REDACTED_JWT]`
- Passwords in JSON → `[REDACTED]`
- API keys (40+ chars) → `[REDACTED_TOKEN]`
- Client secrets → `[REDACTED]`

### Rate Limiting

Prevent API bans with automatic throttling:

```json
{
  "script-behavior": {
    "rate-limiting": {
      "enabled": true,
      "calls-per-second": 10,
      "burst-size": 1
    }
  }
}
```

Usage is automatic:
```python
api = create_rest_api(config)  # Rate limiting applied
response = api.get(url)  # Automatically throttled
```

### Circuit Breaker

Stop cascade failures when APIs are down:

```json
{
  "script-behavior": {
    "circuit-breaker": {
      "enabled": true,
      "failure-threshold": 5,
      "timeout-seconds": 60
    }
  }
}
```

Behavior:
1. After 5 consecutive failures → circuit opens
2. All requests fail immediately for 60 seconds
3. After timeout → circuit attempts to close
4. One success → circuit fully closes

### Async Operations (202 Accepted)

Handle long-running operations transparently:

```python
# This handles 202 responses automatically
result = api.post("/long-operation", data)

# Behind the scenes:
# 1. Detects 202 Accepted response
# 2. Extracts Location header
# 3. Polls Location URL
# 4. Respects Retry-After header
# 5. Returns final result when ready
# 6. Times out after 5 minutes (configurable)
```

Configuration:
```json
{
  "script-behavior": {
    "api-timeouts": {
      "async-max-wait": 300,
      "async-poll-interval": 5
    }
  }
}
```

### Connection Pooling

Sessions are automatically pooled and reused:

- Maximum 50 sessions cached
- LRU eviction when full
- Thread-safe implementation
- Automatic cleanup on exit

### Exponential Backoff with Jitter

All API calls include intelligent retry:

```json
{
  "script-behavior": {
    "retry-strategy": {
      "max-retries": 3,
      "backoff-factor": 2.0
    },
    "jitter": {
      "min-factor": 0.8,
      "max-factor": 1.2
    }
  }
}
```

## Security Patterns

### Configuration Separation

Keep secrets separate from configuration:

```
config/
├── acme-prod-config.json         # Can be committed to git
└── acme-prod-config-secrets.json # GITIGNORED - never commit!
```

Main config (`acme-prod-config.json`):
```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "client-id": "public-client-id"
  }
}
```

Secrets file (`acme-prod-config-secrets.json`):
```json
{
  "client-secret": "oauth-secret-value",
  "az-token": "Bearer eyJ...",
  "api-key": "sk-..."
}
```

Secrets are injected with underscore prefix:
- `client-secret` → `config['_client_secret']`
- `az-token` → `config['_az_token']`
- `api-key` → `config['_api_key']`

### OAuth Token Management

Tokens are cached and refreshed automatically:

```python
# Token acquisition with fallback
config = parse_args_and_load_config("Script")
# Tries in order:
# 1. OAuth client credentials flow
# 2. Cached token if still valid
# 3. Fallback token from secrets (_az_token)
```

## API Resilience Patterns

### Handling Different Response Codes

```python
from utils.exceptions import *

try:
    result = api.get(url)
except ApiAuthenticationError:
    # 401 - Authentication failed
    logger.error("Token expired or invalid")
except ApiRateLimitError as e:
    # 429 - Rate limited
    if e.retry_after:
        time.sleep(e.retry_after)
except ApiTimeoutError:
    # 408 or timeout - Request timed out
    logger.error("API request timed out")
except EntityNotFoundError:
    # 404 - Resource not found
    logger.warning("Entity does not exist")
except ApiValidationError:
    # 400/422 - Validation failed
    logger.error("Invalid request data")
```

### Batch Processing with Rate Limiting

```python
from utils.concurrency import rate_limited_parallel

# Process items with rate limiting
results = rate_limited_parallel(
    api_call_function,
    items,
    calls_per_second=5,
    max_workers=10
)

logger.info(f"Success rate: {results.success_rate:.1%}")
```

### OData Pagination

Automatic pagination for large datasets:

```python
# Fetches ALL pages automatically
entities = api.get_odata_entities(
    base_url="https://api.example.com/odata",
    entity_name="Customers",
    odata_filter="Country eq 'USA'",
    select_fields=["Name", "Email", "Phone"],
    page_size=100  # Per page
)

logger.info(f"Retrieved {len(entities)} total customers")
```

## Error Handling Patterns

### Exception Hierarchy

```
TxoBaseError
├── ApiError
│   ├── ApiOperationError
│   ├── ApiTimeoutError
│   ├── ApiAuthenticationError
│   ├── ApiRateLimitError (has retry_after)
│   ├── ApiValidationError
│   └── EntityNotFoundError
├── ConfigurationError
├── ValidationError
├── FileOperationError
└── HelpfulError (user-friendly messages)
```

### Error Handling Strategy

```python
def main():
    try:
        config = parse_args_and_load_config("Script")
        process_data(config)
        
    except HelpfulError:
        # Already formatted nicely, just re-raise
        raise
        
    except ApiRateLimitError as e:
        # Handle rate limiting
        logger.warning(f"Rate limited, retry after {e.retry_after}s")
        raise HelpfulError(
            what_went_wrong="API rate limit exceeded",
            how_to_fix=f"Wait {e.retry_after} seconds and retry",
            example="Consider enabling rate limiting in config"
        )
        
    except Exception as e:
        # Unexpected error - provide guidance
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HelpfulError(
            what_went_wrong=f"Script failed: {str(e)}",
            how_to_fix="Check the logs for details",
            example="Run with --debug flag for more information"
        )
```

## Performance Patterns

### Lazy Loading

Heavy dependencies are imported only when needed:

```python
def process_excel(config: Dict[str, Any]):
    import pandas as pd  # Only loaded if function is called
    return pd.read_excel(...)

# Not at module level
import pandas as pd  # Would load even if not used
```

### Parallel Processing

```python
from utils.concurrency import parallel_map, batch_process

# Process items in parallel
result = parallel_map(
    process_item,
    items,
    max_workers=10,
    show_progress=True  # Optional progress bar
)

# Process in batches for memory efficiency
result = batch_process(
    process_batch,
    large_dataset,
    batch_size=1000
)
```

### Context Managers

Ensure proper resource cleanup:

```python
from utils.api_factory import ApiManager

# Automatic cleanup
with ApiManager(config) as manager:
    api = manager.get_rest_api()
    data = api.get("/endpoint")
    # API sessions closed automatically on exit
```

## Configuration Management

### ⚠️ Critical Rule: Schema Must Match Config

**EVERY configuration change requires updating the JSON schema!**

When you modify configuration:
1. Update `config/{org}-{env}-config.json`
2. **IMMEDIATELY** update `schemas/org-env-config-schema.json`
3. Use kebab-case: `"my-new-setting"` not `"my_new_setting"`
4. Document purpose in schema description
5. Set reasonable defaults and constraints

### Configuration Structure (v2.1)

```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "api-version": "v2",
    "tenant-id": "your-tenant-id",
    "client-id": "your-client-id",
    "oauth-scope": "https://api.example.com/.default"
  },
  "script-behavior": {
    "api-delay-seconds": 1,
    "api-timeouts": {
      "rest-timeout-seconds": 60,
      "soap-timeout-seconds": 120,
      "wsdl-timeout-seconds": 60,
      "async-max-wait": 300,
      "async-poll-interval": 5
    },
    "retry-strategy": {
      "max-retries": 3,
      "backoff-factor": 2.0
    },
    "jitter": {
      "min-factor": 0.8,
      "max-factor": 1.2
    },
    "rate-limiting": {
      "enabled": true,
      "calls-per-second": 10,
      "burst-size": 1
    },
    "circuit-breaker": {
      "enabled": true,
      "failure-threshold": 5,
      "timeout-seconds": 60
    },
    "batch-handling": {
      "read-batch-size": 100,
      "update-batch-size": 50,
      "vat-batch-size": 10
    }
  },
  "environments": {
    "test": {
      "api-endpoint": "https://test-api.example.com"
    },
    "prod": {
      "api-endpoint": "https://api.example.com"
    }
  }
}
```

### Custom Configuration Sections

Add your own sections for script-specific config:

```json
{
  "global": { ... },
  "script-behavior": { ... },
  "my-feature": {
    "enabled": true,
    "custom-endpoint": "https://my-api.com",
    "processing-options": {
      "skip-validation": false,
      "output-format": "excel"
    }
  }
}
```

Remember to update the schema!

## Helper Modules Reference

### Core Modules

#### utils.script_runner
```python
# Standard initialization
config = parse_args_and_load_config(
    "Script description",
    require_token=True,     # Get OAuth token
    validate_config=True    # Validate against schema
)

# With custom arguments
from utils.script_runner import ArgumentDefinition

extra_args = [
    ArgumentDefinition("batch_size", int, "Batch size", default=100),
    ArgumentDefinition("dry_run", bool, "Dry run mode", action="store_true")
]
config = parse_custom_args_and_load_config("Script", extra_args)
```

#### utils.logger
```python
logger = setup_logger(org_id="myorg")  # Optional context

logger.debug("Detailed info")     # File only
logger.info("Important event")    # Console + file
logger.warning("Potential issue") # Console + file
logger.error("Error occurred")    # Console + file
```

#### utils.load_n_save
```python
data_handler = TxoDataHandler()

# Load operations
data = data_handler.load_json("config", "settings.json")
df = data_handler.load_excel("data", "input.xlsx", sheet_name="Sheet1")
df = data_handler.load_csv("data", "input.csv")

# Save operations (auto-detects type!)
path = data_handler.save(data, "output", "data.json", indent=2)
path = data_handler.save(df, "output", "report.csv", index=False)
path = data_handler.save(df, "output", "report.xlsx", sheet_name="Results")
path = data_handler.save("text", "output", "report.txt")

# File operations
exists = data_handler.exists("config", "settings.json")
data_handler.delete("tmp", "temp_file.json")
size = data_handler.get_size("output", "report.xlsx")
```

#### utils.api_factory
```python
# Create REST API with all features
api = create_rest_api(config)  # Rate limiting, circuit breaker included

# For public APIs (no auth)
api = create_rest_api(config, require_auth=False)

# With context manager
with ApiManager(config) as manager:
    api = manager.get_rest_api()
    # Automatic cleanup
```

#### utils.exceptions
```python
# User-friendly errors
raise HelpfulError(
    what_went_wrong="Database connection failed",
    how_to_fix="Check your connection string",
    example="postgres://user:pass@localhost/db"
)

# API-specific exceptions
raise ApiAuthenticationError("Invalid token")
raise ApiRateLimitError("Rate limit exceeded", retry_after=60)
raise ApiTimeoutError("Request timed out", timeout_seconds=30)
raise EntityNotFoundError("Customer", entity_id="12345")
```

### Advanced Modules

#### utils.concurrency
```python
# Parallel processing
result = parallel_map(process_func, items, max_workers=10)

# Rate-limited parallel
result = rate_limited_parallel(
    api_call, items, 
    calls_per_second=5
)

# Batch processing
result = batch_process(
    process_batch, data,
    batch_size=1000
)

# Check results
if result.success_rate < 90:
    logger.warning(f"High failure rate: {result.failure_count} failed")
```

#### utils.url_helpers
```python
# Build URLs
url = build_url(
    "https://api.example.com",
    "v2", "customers", customer_id,
    query_params={"include": "orders", "limit": 10}
)

# Build OData filters
filter_str = build_odata_filter({
    "status": "eq 'active'",
    "created": "gt 2024-01-01",
    "amount": "ge 100"
})
```

## Script Development Guide

### Standard Script Template

```python
# src/my_script.py
"""
Script description and purpose.

Usage:
    python my_script.py <org_id> <env_type>

Example:
    python my_script.py acme prod
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.api_factory import create_rest_api
from utils.exceptions import HelpfulError, ApiOperationError

logger = setup_logger()
data_handler = TxoDataHandler()


def validate_config(config: Dict[str, Any]) -> None:
    """Validate required configuration exists."""
    # Hard-fail on missing required config
    required_keys = ['global', 'script-behavior']
    for key in required_keys:
        if key not in config:
            raise HelpfulError(
                what_went_wrong=f"Missing '{key}' section in configuration",
                how_to_fix=f"Add '{key}' section to your config file",
                example="See config/example.json for structure"
            )
    
    # Check specific required values
    if 'api-base-url' not in config['global']:
        raise HelpfulError(
            what_went_wrong="Missing 'api-base-url' in global config",
            how_to_fix="Add 'api-base-url' to the 'global' section",
            example='"global": {"api-base-url": "https://api.example.com"}'
        )


def process_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main processing logic.
    
    Args:
        config: Configuration dictionary with injected fields
        
    Returns:
        List of processed records
        
    Raises:
        ApiOperationError: If API calls fail
    """
    api = create_rest_api(config)
    
    try:
        # Your processing logic here
        endpoint = f"{config['global']['api-base-url']}/data"
        response = api.get(endpoint)
        
        records = response.get('items', [])
        logger.info(f"Retrieved {len(records)} records")
        
        # Process records
        processed = []
        for record in records:
            # Transform data
            processed.append({
                'id': record['id'],
                'name': record['name'],
                'processed_at': datetime.now(timezone.utc).isoformat()
            })
        
        return processed
        
    except ApiOperationError as e:
        logger.error(f"API operation failed: {e}")
        raise HelpfulError(
            what_went_wrong=f"Failed to fetch data: {e}",
            how_to_fix="Check API endpoint and authentication",
            example="Verify the API URL and token are correct"
        )


def save_results(config: Dict[str, Any], data: List[Dict[str, Any]]) -> None:
    """Save processed results."""
    if not data:
        logger.warning("No data to save")
        return
    
    # Generate filename with TXO pattern
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    filename = f"{config['_org_id']}-{config['_env_type']}-results_{utc}.json"
    
    # Save using intelligent save
    output_path = data_handler.save(data, "output", filename, indent=2)
    logger.info(f"✅ Saved {len(data)} records to: {output_path}")


def main():
    """Main entry point."""
    # Load configuration
    config = parse_args_and_load_config(
        "My Data Processing Script",
        require_token=True,
        validate_config=True
    )
    
    org_id = config['_org_id']
    env_type = config['_env_type']
    
    logger.info(f"Starting process for {org_id}-{env_type}")
    
    try:
        # Validate
        validate_config(config)
        
        # Process
        data = process_data(config)
        
        # Save
        save_results(config, data)
        
        logger.info(f"✅ Process completed successfully for {org_id}-{env_type}")
        
    except HelpfulError:
        # Re-raise helpful errors for display
        raise
        
    except Exception as e:
        # Convert unexpected errors to helpful format
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HelpfulError(
            what_went_wrong=f"Process failed unexpectedly: {str(e)}",
            how_to_fix="Check the logs for details",
            example="Run with --debug flag for more information"
        )


if __name__ == "__main__":
    import sys
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except HelpfulError:
        # HelpfulError already logged nicely
        sys.exit(1)
    except Exception:
        # Unexpected errors already logged
        sys.exit(1)
```

## Best Practices

### 1. Configuration Management
- **ALWAYS** update schema when changing config structure
- Use hard-fail for required configuration
- Keep secrets separate from main config
- Use kebab-case for all config keys

### 2. Error Handling
- Use HelpfulError for user-facing errors
- Handle specific exceptions appropriately
- Log errors with context
- Never show raw stack traces to users

### 3. Logging
- Use logger for ALL output (never print)
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages
- Don't log sensitive data (but it's auto-redacted anyway)

### 4. Code Structure
- Path comment as first line of every file
- Include docstrings with type hints
- Pass entire config dict, not individual params
- Use context managers for resource cleanup

### 5. File Operations
- Use path_helpers for all paths
- Include UTC timestamp in output files
- Use intelligent save() method
- Handle file errors gracefully

### 6. API Interactions
- Enable rate limiting and circuit breakers
- Handle all response codes appropriately
- Use pagination for large datasets
- Implement proper retry logic

## Common Pitfalls

### 1. Using Soft-Fail on Config
```python
# ❌ WRONG - Silent failures
url = config.get('global', {}).get('api-url', 'default')

# ✅ CORRECT - Fail fast
url = config['global']['api-url']
```

### 2. Not Updating Schema
```python
# ❌ WRONG - Add to config only

# ✅ CORRECT - Update both
# 1. config/{org}-{env}-config.json
# 2. schemas/org-env-config-schema.json
```

### 3. Using Print Instead of Logger
```python
# ❌ WRONG
print("Processing started")

# ✅ CORRECT
logger.info("Processing started")
```

### 4. Building Paths Manually
```python
# ❌ WRONG
path = "config/settings.json"
path = Path("config") / "settings.json"

# ✅ CORRECT
path = get_path("config", "settings.json")
```

### 5. Missing UTC Timestamp
```python
# ❌ WRONG
filename = f"{org_id}-{env_type}-report.xlsx"

# ✅ CORRECT
utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
filename = f"{org_id}-{env_type}-report_{utc}.xlsx"
```

### 6. Wrong Save Method
```python
# ❌ WRONG - These methods don't exist
data_handler.save_json(data, "output", "file.json")
data_handler.save_excel(df, "output", "file.xlsx")

# ✅ CORRECT - Just use save()
data_handler.save(data, "output", "file.json")
data_handler.save(df, "output", "file.xlsx")
```

## Troubleshooting

### Config File Not Found
```
❌ Problem: Configuration file 'acme-prod-config.json' not found
✅ Solution: Create the file in config/ directory
📝 Example: Copy config/example.json to config/acme-prod-config.json
```

**Fix**: Create the config file with required structure

### Schema Validation Failed
```
❌ Problem: Configuration doesn't match schema
✅ Solution: Check schemas/org-env-config-schema.json
```

**Fix**: Ensure config structure matches schema exactly

### KeyError on Config Access
```
KeyError: 'api-base-url'
```

**Fix**: Add missing key to config (v2.1 uses hard-fail)

### Rate Limit Errors
```
ApiRateLimitError: Rate limit exceeded
```

**Fix**: Enable rate limiting in config:
```json
"rate-limiting": {
  "enabled": true,
  "calls-per-second": 5
}
```

### Circuit Breaker Open
```
ApiOperationError: Circuit breaker open
```

**Fix**: Wait for timeout or fix the underlying API issue

### Import Errors
```
ImportError: cannot import name 'X' from 'utils.Y'
```

**Fix**: Check you're using v2.1 class names (TxoRestAPI not MinimalRestAPI)

### Token Not Found
```
❌ Problem: Failed to acquire authentication token
✅ Solution: Check OAuth config or add fallback token
```

**Fix**: Either fix OAuth config or add `az-token` to secrets file

## Advanced Patterns

### Custom Retry Logic
```python
from utils.api_common import manual_retry

@manual_retry(max_retries=5, backoff=3.0)
def unstable_operation():
    # Operation that might fail
    pass
```

### Progress Tracking
```python
from utils.concurrency import parallel_map

result = parallel_map(
    process_item,
    items,
    show_progress=True,  # Shows progress bar
    max_workers=10
)
```

### Complex OData Queries
```python
entities = api.get_odata_entities_filtered(
    base_url=url,
    entity_name="Orders",
    filter_conditions={
        "Status": "eq 'Active'",
        "Amount": "gt 1000",
        "Created": f"gt {start_date}"
    },
    select_fields=["OrderId", "Customer", "Amount", "Status"],
    page_size=200
)
```

### Batch Updates with Tracking
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class UpdateResults:
    successful: List[str] = field(default_factory=list)
    failed: List[tuple] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        total = len(self.successful) + len(self.failed)
        return (len(self.successful) / total * 100) if total > 0 else 0

results = UpdateResults()

for item in items:
    try:
        api.patch(f"/items/{item['id']}", item)
        results.successful.append(item['id'])
    except Exception as e:
        results.failed.append((item['id'], str(e)))

logger.info(f"Update complete: {results.success_rate:.1f}% success rate")
```

## Module Dependency Order

When refactoring or updating helpers, follow this order:

1. **exceptions.py** (no dependencies)
2. **path_helpers.py** (no dependencies)
3. **logger.py** (depends on path_helpers)
4. **api_common.py** (depends on logger)
5. **load_n_save.py** (depends on exceptions, logger, path_helpers)
6. **oauth_helpers.py** (depends on logger, exceptions)
7. **rest_api_helpers.py** (depends on api_common, exceptions, logger)
8. **config_loader.py** (depends on logger, path_helpers, load_n_save)
9. **api_factory.py** (depends on rest_api_helpers, api_common)
10. **script_runner.py** (top level orchestration)

## Version History

### v2.1.0 (Current)
- Nested configuration structure for rate-limiting and circuit-breaker
- Hard-fail philosophy for all configuration access
- TxoRestAPI class (renamed from MinimalRestAPI)
- Intelligent save() with automatic type detection
- Enhanced error messages with HelpfulError

### v2.0.0
- Added automatic token redaction
- Added rate limiting support
- Added circuit breaker pattern
- Added async operation support (202 Accepted)
- Added connection pooling

### v1.x
- Basic template structure
- Simple retry logic
- Manual save methods (save_json, save_excel)
- Soft-fail configuration access

## For More Information

- **Architecture Decisions**: See [ADR Records](ai/decided/adr-records.md)
- **Visual Architecture**: See [Module Dependency Diagram](module-dependency-diagram.md)
- **AI Assistance**: Upload `ai/prompts/txo-xml-prompt-v3.1.xml` to Claude
- **Migration Guide**: Use `ai/prompts/refactoring-prompt-v2.xml` for upgrades

## Support

- Create an issue on GitHub for bugs
- Check existing issues for solutions
- Review logs in `logs/` directory for debugging
- Use `--debug` flag for detailed logging