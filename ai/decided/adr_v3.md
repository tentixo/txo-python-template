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

**Status:** DEPRECATED in v3.0  
**Date:** 2025-01-01  
**Deprecated:** 2025-01-16  

### Context
Logs need context about which environment/resource is being accessed.

### Decision
URL builders return `(url, context)` tuple.

### v3.0 Update
Pattern still supported but less emphasized. Context extraction now internal to API clients.

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

**Status:** MANDATORY - ENHANCED in v3.0  
**Date:** 2025-01-01  
**Updated:** 2025-01-16  

### Context
Path construction errors cause cross-platform issues.

### Decision (v1-v2)
Always use `get_path()` from path_helpers.

### Decision (v3.0)
Use type-safe Categories constants instead of string literals.

### Implementation
```python
from utils.path_helpers import Categories

# v3.0 - Type-safe
get_path(Categories.CONFIG, 'settings.json')

# v1-v2 - String-based (deprecated)
get_path('config', 'settings.json')
```

### Consequences
- Positive: Type safety, IDE autocomplete, no typos
- Positive: Cross-platform compatibility
- Negative: Must import Categories
- Mitigation: Clear error messages for invalid categories

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
# Creates: txo-prod-report_2025-01-16T1430Z.xlsx
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

## ADR-019: Type-Safe Categories for Path Management

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
String literals for directory names ('config', 'output') cause typos and lack IDE support. No compile-time or development-time checking.

### Decision
Implement Categories class with type-safe constants and CategoryType literal.

### Implementation
```python
class Categories:
    CONFIG: CategoryType = 'config'
    OUTPUT: CategoryType = 'output'
    # ... etc

# Usage
from utils.path_helpers import Categories
data_handler.save(data, Categories.OUTPUT, 'file.json')
```

### Consequences
- Positive: IDE autocomplete and type checking
- Positive: No typos possible
- Positive: Better refactoring support
- Negative: Must import Categories
- Mitigation: Clear error messages guide to correct usage

---

## ADR-020: Token Optional by Default

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Most scripts don't need authentication. Requiring OAuth setup for simple local scripts creates unnecessary friction for users.

### Decision
Change `require_token` default from True to False in parse_args_and_load_config().

### Implementation
```python
# Local scripts (most common)
config = parse_args_and_load_config("My script")  # No token

# API scripts (explicit)
config = parse_args_and_load_config("API script", require_token=True)
```

### Consequences
- Positive: Easier onboarding for new users
- Positive: Simpler config for local scripts
- Positive: Clear distinction between script types
- Negative: Breaking change from v2.x
- Mitigation: Clear documentation and examples

---

## ADR-021: Mandatory Configuration Files

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Optional configurations with defaults hide misconfigurations and create inconsistent behavior across environments. Security patterns must always be active.

### Decision
Three configuration files are mandatory - script exits if any are missing:
1. `{org}-{env}-config.json` - Main configuration
2. `logging-config.json` - Logging setup
3. `log-redaction-patterns.json` - Security patterns

### Implementation
Logger will call `sys.exit(1)` if configuration files are missing or invalid. No defaults, no fallbacks.

### Consequences
- Positive: Consistent behavior across all environments
- Positive: Security patterns always active
- Positive: Fail fast on misconfiguration
- Negative: Cannot run without config files
- Mitigation: Provide templates for easy setup

---

## ADR-022: Smart Save/Load with Auto-Detection

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Multiple save methods (save_json, save_text, save_excel) create confusion. Users must remember which method for which type.

### Decision
Implement smart `save()` and `load()` methods that auto-detect format from file extension and data type.

### Implementation
```python
# All use the same method
data_handler.save(dict_data, Categories.OUTPUT, "data.json")
data_handler.save(dataframe, Categories.OUTPUT, "data.csv")
data_handler.save("text", Categories.OUTPUT, "report.txt")

# Load also auto-detects
data = data_handler.load(Categories.DATA, "input.xlsx")
```

### Consequences
- Positive: Single method to remember
- Positive: Cleaner, more intuitive API
- Positive: Type validation prevents mistakes
- Negative: Less explicit about operation
- Mitigation: Clear error messages for mismatches

---

## ADR-023: Thread-Safe Lazy Loading

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Heavy dependencies (pandas, yaml, openpyxl) slow startup even when not used. Concurrent access without synchronization causes race conditions.

### Decision
Implement thread-safe lazy loading with double-checked locking pattern.

### Implementation
```python
class TxoDataHandler:
    _modules: Dict[str, Any] = {}
    _import_lock = threading.Lock()
    
    @classmethod
    def _lazy_import(cls, module_name: str) -> Any:
        if module_name not in cls._modules:
            with cls._import_lock:
                # Double-check pattern
                if module_name not in cls._modules:
                    import module
                    cls._modules[module_name] = module
```

### Consequences
- Positive: Fast startup for scripts not using heavy modules
- Positive: Thread-safe for concurrent operations
- Positive: Memory efficient
- Negative: First use has import delay
- Mitigation: Clear logging of lazy loads

---

## ADR-024: Nested Configuration Structure

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Flat configuration with prefixed keys (enable-rate-limiting, rate-limit-per-second) creates verbose, hard-to-read configs.

### Decision
Use nested objects for related configuration.

### Implementation
```json
{
  "rate-limiting": {
    "enabled": true,
    "calls-per-second": 10,
    "burst-size": 1
  },
  "circuit-breaker": {
    "enabled": false,
    "failure-threshold": 5,
    "timeout-seconds": 60
  }
}
```

### Consequences
- Positive: Cleaner, more organized configuration
- Positive: Easier to understand relationships
- Positive: Better for complex configs
- Negative: Breaking change from v2.x
- Mitigation: Clear migration guide

---

## ADR-025: Project Structure Reorganization

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Scripts in src/ directory unclear if examples or production. Need clear separation of examples, tests, and utilities.

### Decision
Reorganize directory structure:
- `examples/` - Example scripts and demos
- `tests/` - Test scripts
- `utils/` - Core framework (unchanged)

### Implementation
```
txo-python-template/
├── examples/       # Example scripts
├── tests/         # Test scripts  
├── utils/         # Framework
```

### Consequences
- Positive: Clear purpose for each directory
- Positive: Examples easy to find
- Positive: Tests separate from examples
- Negative: Scripts must be moved
- Mitigation: Clear migration instructions

---

## ADR-026: Security-First Logging Configuration

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Accidental token/password logging creates security vulnerabilities. Optional redaction patterns allow security bypasses.

### Decision
Mandatory `log-redaction-patterns.json` file. Logger exits if missing or invalid. No default patterns.

### Implementation
```json
{
  "redaction-patterns": {
    "patterns": [
      {
        "name": "bearer-token",
        "pattern": "Bearer\\s+[A-Za-z0-9\\-._~+/]+=*",
        "replacement": "Bearer [REDACTED]"
      }
    ]
  }
}
```

### Consequences
- Positive: Security patterns always active
- Positive: No accidental token exposure
- Positive: Customizable per environment
- Negative: Cannot run without redaction config
- Mitigation: Template provided

---

## ADR-027: Hard-Fail Configuration Access

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Soft-failing with defaults for missing configuration masks errors and creates inconsistent behavior.

### Decision
Always use hard-fail (KeyError) for required configuration. No `.get()` with defaults for config keys.

### Implementation
```python
# Required config - let it fail
api_url = config['global']['api-base-url']  # KeyError if missing

# Nested required config
rate_config = config['script-behavior']['rate-limiting']
enabled = rate_config['enabled']  # Hard fail if structure wrong

# Only API responses can soft-fail
email = api_response.get('email')  # None is OK for external data
```

### Consequences
- Positive: Fail fast on misconfiguration
- Positive: No silent errors
- Positive: Clear error messages
- Negative: Must have complete configs
- Mitigation: Provide complete templates

---

## ADR-028: Elimination of Module-Level Defaults

**Status:** MANDATORY  
**Date:** 2025-01-16  

### Context
Defaults in modules hide configuration problems and create inconsistent behavior across deployments.

### Decision
Remove all default values from utility modules. Configuration must come from config files.

### Implementation
```python
# Old (v2.x) - defaults in module
class ApiClient:
    def __init__(self, timeout=30):  # Default

# New (v3.0) - no defaults
class ApiClient:
    def __init__(self, timeout):  # Required from config
```

### Consequences
- Positive: All behavior configured explicitly
- Positive: No hidden defaults
- Positive: Consistent across environments
- Negative: More configuration required
- Mitigation: Complete config templates

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