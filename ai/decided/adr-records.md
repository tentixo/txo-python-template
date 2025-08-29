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