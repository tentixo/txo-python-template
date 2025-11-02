# TXO Python Template - In-Depth Guide v3.3

> **⚠️ TEMPLATE DOCUMENT - For Refactoring Workflow**
>
> **Purpose**: Pattern for root in-depth-readme.md during framework refactoring
> **Usage**: Content for framework maintainers and contributors
> **Audience**: Developers who want to understand or extend the TXO framework
> **Workflow**: Refactoring (ai/prompts/refactoring-ai-prompt_v3.3.md)
>
> **AI Instructions**:
> - This template IS for the framework repository itself
> - Update during done-done phase when adding framework features
> - Focus on framework INTERNALS, not script usage
> - Add new ADR explanations as they're created
> - Keep version numbers synchronized (v3.3.0)

---

# TXO Python Template v3.3.0 - In-Depth Guide

> **Audience**: Framework maintainers, experienced developers, and contributors
> **Purpose**: Deep understanding of framework architecture, rationale, and extension points
> **Prerequisite**: Read [README.md](README.md) for basic understanding
> **Time Investment**: 60-90 minutes to comprehensive understanding

## Table of Contents

1. [Architecture & Design Philosophy](#architecture--design-philosophy)
2. [ADR Deep Dives](#adr-deep-dives)
3. [Framework Components](#framework-components)
4. [Configuration System Internals](#configuration-system-internals)
5. [Path Management Architecture](#path-management-architecture)
6. [API Factory Design](#api-factory-design)
7. [Logging System Architecture](#logging-system-architecture)
8. [Data Handler Internals](#data-handler-internals)
9. [Compliance Validation System](#compliance-validation-system)
10. [Extending the Framework](#extending-the-framework)
11. [Document Archival Workflow](#document-archival-workflow)
12. [Contributing Guidelines](#contributing-guidelines)

---

## Architecture & Design Philosophy

### The TXO Way: Fail Fast, Consistent, Secure

TXO Template is built on three core principles:

**1. Fail Fast (ADR-B003)**

**Problem**: Traditional scripts use defaults that mask configuration errors

**Solution**: Hard-fail immediately on missing configuration

```python
# TXO Way - Fails immediately if misconfigured
api_url = config['global']['api-base-url']  # KeyError if missing

# Traditional Way - Silent failure, hard to debug
api_url = config.get('global', {}).get('api-base-url', 'https://default.com')
```

**Benefit**: Production errors surface during development, no hidden dependencies

**Trade-off**: More explicit configuration required (but this is a feature, not a bug)

---

**2. Consistency (ADR-B010, ADR-B017)**

**Problem**: Scripts generate files with inconsistent naming

**Solution**: Mandatory patterns for all file operations

```python
# All output files MUST follow org-env-description_timestamp pattern
filename = f"{config['_org_id']}-{config['_env_type']}-results.json"
data_handler.save_with_timestamp(data, Dir.OUTPUT, filename, add_timestamp=True)
# Produces: mycompany-prod-results_2025-11-01T143022Z.json
```

**Benefit**: Easy to trace files to specific org/env/time

---

**3. Security (ADR-B005, ADR-B006)**

**Problem**: Secrets accidentally committed or logged

**Solution**: Framework-enforced separation and redaction

```python
# Secrets MUST be in separate gitignored file
config-secrets.json  # Gitignored by default

# Logging automatically redacts credentials
logger.info("API call to {url}", extra={'api_key': secret})
# Logged as: "API call to https://api.example.com" (api_key redacted)
```

**Benefit**: Impossible to leak secrets through normal framework usage

---

### Layered Architecture (No Circular Dependencies)

```
┌─────────────────────────────────────┐
│  Layer 5: User Scripts              │  (src/, tests/)
│  - Business logic                   │
│  - Script-specific code             │
└─────────────────────────────────────┘
              ↓ imports
┌─────────────────────────────────────┐
│  Layer 4: Orchestration             │  (script_runner, api_factory, config_loader)
│  - Workflow coordination            │
│  - High-level abstractions          │
└─────────────────────────────────────┘
              ↓ imports
┌─────────────────────────────────────┐
│  Layer 3: API & Data                │  (rest_api_helpers, oauth_helpers, load_n_save)
│  - API integration                  │
│  - Data transformation              │
└─────────────────────────────────────┘
              ↓ imports
┌─────────────────────────────────────┐
│  Layer 2: Core Services             │  (logger, api_common)
│  - Cross-cutting concerns           │
│  - Shared services                  │
└─────────────────────────────────────┘
              ↓ imports
┌─────────────────────────────────────┐
│  Layer 1: Foundation                │  (path_helpers, exceptions)
│  - Zero dependencies                │
│  - Pure Python utilities            │
└─────────────────────────────────────┘
```

**Dependency Rules**:
- Higher layers can import lower layers
- Lower layers NEVER import higher layers
- Foundation layer has zero dependencies

**Why**: Prevents circular imports, enables testing, clear responsibility separation

---

## ADR Deep Dives

### ADR-B003: Hard-Fail Configuration

**Decision**: Use `config['key']` not `config.get('key', default)`

**Rationale**:
1. **Explicit > Implicit**: Required config should fail if missing
2. **Fail Early**: Catch misconfiguration before API calls
3. **No Hidden Dependencies**: Clear what config is required

**Implementation**: `config_loader.py` returns dict with no `.get()` wrapper

**Exception**: Framework may use `.get()` for truly optional features

---

### ADR-B005: Secrets Separation

**Decision**: Secrets in separate `*-config-secrets.json` file

**Rationale**:
1. **Git Safety**: Main config checked in, secrets gitignored
2. **Flat Structure**: Secrets file is flat dict (easy to scan)
3. **Audit Trail**: Easy to see what secrets are required

**Implementation**:
```python
# config_loader.py merges both files
config = {**main_config, **secrets_config}

# User accesses normally
api_key = config['api-key']  # Could be from either file
```

**Security**: Even if user manually logs config, redaction patterns catch secrets

---

### ADR-B006: Smart Logging Context Strategy

**Decision**: Automatic context (org_id, env_type) in every log

**Rationale**:
1. **Traceability**: Know which org/env generated each log line
2. **AI-Friendly**: JSON structured logs for parsing
3. **Security**: Automatic redaction of sensitive patterns

**Implementation**:
```python
# logger.py adds context automatically
logger = setup_logger()  # Reads config['_org_id'], config['_env_type']

logger.info("Processing started")
# Logged as:
# {"timestamp": "2025-11-01T14:30:22Z", "level": "INFO",
#  "org_id": "mycompany", "env_type": "prod",
#  "message": "Processing started"}
```

**Redaction**: Configured in `config/log-redaction-patterns.json`

---

### ADR-B007: API Factory Pattern

**Decision**: Single function `create_rest_api()` creates configured clients

**Rationale**:
1. **Consistent Behavior**: All APIs use same retry/timeout/logging
2. **Easy to Mock**: Single factory function for testing
3. **Credential Management**: Framework loads credentials, not user

**Implementation**:
```python
# api_factory.py
def create_rest_api(config, api_name):
    """
    Creates authenticated API client with:
    - Credentials from config
    - Retry logic (exponential backoff)
    - Structured logging
    - Timeout handling
    """
    return AuthenticatedAPIClient(config, api_name)
```

**Usage**:
```python
api_client = create_rest_api(config, "my-api")
response = api_client.get("/endpoint")  # Automatic retry, logging, etc.
```

---

### ADR-B010: Directory Structure and Path Management

**Decision**: Type-safe `Dir` constants, not string literals

**Rationale**:
1. **Typo Prevention**: IDE autocomplete for directory names
2. **Type Safety**: Literal types catch errors at development time
3. **Centralized**: Single source of truth for paths

**Implementation**:
```python
# path_helpers.py
class Dir:
    CONFIG: CategoryType = 'config'
    DATA: CategoryType = 'data'
    OUTPUT: CategoryType = 'output'
    TMP: CategoryType = 'tmp'
    # ...

# Usage (IDE autocomplete!)
data_handler.save(data, Dir.OUTPUT, "file.json")  # ✅
data_handler.save(data, "output", "file.json")    # ❌ No autocomplete
```

---

### ADR-B017: Directory-Specific UTC Timestamp Rules

**Decision**: Different timestamp rules for different directories

**Rationale**: Different directories serve different purposes

| Directory             | UTC?     | Rationale                                  |
|-----------------------|----------|--------------------------------------------|
| `output/`             | MUST     | Audit trail, non-destructive, traceability |
| `tmp/`                | SHOULD   | Multi-run debugging (flexible)             |
| `generated_payloads/` | MUST NOT | Human validation workflow (stable names)   |
| `payloads/`           | MUST NOT | Manual curation (stable references)        |
| `wsdl/`               | MUST NOT | Service versioning (not time-based)        |

**Implementation**:
```python
# For output (MUST use UTC)
data_handler.save_with_timestamp(data, Dir.OUTPUT, filename, add_timestamp=True)

# For generated payloads (MUST NOT use UTC)
data_handler.save(payload, Dir.GENERATED_PAYLOADS, filename)
```

**Validation**: `validate_tko_compliance.py` checks correct usage

**Human Workflow** (payloads):
```bash
# 1. Code generates (no timestamp)
generated_payloads/mycompany-prod-create-user.json

# 2. Human validates
cat generated_payloads/mycompany-prod-create-user.json
# Check fields, values, structure

# 3. Human approves
cp generated_payloads/mycompany-prod-create-user.json payloads/

# 4. Code reads and sends
# (reads from payloads/ directory)
```

---

## Framework Components

### script_runner.py - Orchestration Layer

**Purpose**: Single entry point for all scripts

**Key Function**: `parse_args_and_load_config()`

**What It Does**:
1. Parse command-line args (org_id, env_type)
2. Load main config: `config/{org}-{env}-config.json`
3. Load secrets: `config/{org}-{env}-config-secrets.json`
4. Merge both dicts
5. Add special keys: `_org_id`, `_env_type`
6. Initialize logger with context
7. Return unified config dict

**Usage**:
```python
def main():
    config = parse_args_and_load_config("My script description")
    # config now has everything: main config + secrets + _org_id + _env_type
```

**Benefits**: Zero boilerplate in user scripts

---

### load_n_save.py - Data Handler

**Purpose**: Type-safe file operations with automatic patterns

**Key Class**: `TxoDataHandler`

**Capabilities**:
- Load/save JSON, CSV, Excel (single/multi-sheet)
- Automatic UTC timestamps (when required)
- Org-env filename pattern enforcement
- Path helpers integration

**Multi-Sheet Excel Detection**:
```python
# Single sheet → single Excel file
data_handler.save(df, Dir.OUTPUT, "report.xlsx")

# Dict of DataFrames → multi-sheet Excel
sheets = {"Summary": summary_df, "Details": details_df}
data_handler.save(sheets, Dir.OUTPUT, "report.xlsx")
# Automatically detects dict and creates 2-sheet Excel
```

**UTC Timestamp Addition**:
```python
# save_with_timestamp adds ISO 8601 UTC timestamp before extension
data_handler.save_with_timestamp(data, Dir.OUTPUT, "report.xlsx", add_timestamp=True)
# Transforms: report.xlsx → report_2025-11-01T143022Z.xlsx
```

---

### api_factory.py - API Client Factory

**Purpose**: Create configured, retry-enabled, logged API clients

**Implementation Strategy**:
```python
def create_rest_api(config, api_name):
    """
    Creates API client with:
    1. Base URL from config['{api_name}-base-url']
    2. Credentials from config['{api_name}-api-key'] or OAuth
    3. Retry logic (exponential backoff, max 3 retries)
    4. Timeout from config['{api_name}-timeout']
    5. Request/response logging
    """
    return ConfiguredAPIClient(...)
```

**Retry Logic**:
- HTTP 429 (Rate Limit): Wait for Retry-After header
- HTTP 503 (Service Unavailable): Exponential backoff
- Connection Timeout: Retry immediately once
- Max retries: 3 attempts total

**Logging**: Every request/response logged with duration, status, body size

---

### logger.py - Structured Logging

**Purpose**: Context-aware, secure, AI-parseable logging

**Automatic Context**:
```python
logger = setup_logger()
# Reads _org_id and _env_type from environment/config

logger.info("Event happened", extra={'count': 100})
# Automatically includes org_id, env_type in every log
```

**Redaction Patterns**:
```json
// config/log-redaction-patterns.json
{
  "patterns": [
    {"pattern": "api[_-]?key", "replacement": "[REDACTED-API-KEY]"},
    {"pattern": "password", "replacement": "[REDACTED-PASSWORD]"},
    {"pattern": "bearer\\s+[a-zA-Z0-9\\-._~+/]+=*", "replacement": "bearer [REDACTED-TOKEN]"}
  ]
}
```

**Format**: JSON for machine parsing, human-readable for console

---

### path_helpers.py - Path Management

**Purpose**: Centralized, type-safe path operations

**Key Features**:
- `Dir` class with typed constants
- `get_path()` function with validation
- `cleanup_tmp()` for automatic cleanup
- `ProjectPaths` singleton for caching

**Validation**:
```python
# path_helpers.py validates category
if not Dir.validate(category):
    raise ValueError(f"Invalid category: {category}")
```

**Benefits**: Typo-proof, IDE-friendly, testable

---

## Configuration System Internals

### Two-File Pattern

**File 1**: `{org}-{env}-config.json` (checked into git)
```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "timeout": 30
  },
  "my-service": {
    "setting": "value"
  }
}
```

**File 2**: `{org}-{env}-config-secrets.json` (gitignored)
```json
{
  "api-key": "secret-here",
  "client-secret": "secret-here"
}
```

**Merging Strategy**: Shallow merge (secrets override main if key collision)

**Special Keys**: Framework adds `_org_id` and `_env_type`

**Validation**: Hard-fail on missing required keys (KeyError raised)

---

## Path Management Architecture

### ProjectPaths Singleton

**Design**: Frozen dataclass with `@lru_cache` for singleton pattern

```python
@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    config: Path
    data: Path
    # ...

    @classmethod
    @lru_cache(maxsize=1)
    def init(cls, root_path: Optional[Path] = None) -> 'ProjectPaths':
        # Singleton: Only initialized once per process
        ...
```

**Benefits**:
- Frozen: Cannot be accidentally modified
- Cached: No repeated path calculations
- Typed: IDE autocomplete for all paths

---

## API Factory Design

### Authentication Strategies

**1. API Key**:
```python
headers = {'Authorization': f"Bearer {config['api-key']}"}
```

**2. OAuth 2.0 Client Credentials**:
```python
# oauth_helpers.py handles token acquisition
token = get_oauth_token(config['client-id'], config['client-secret'])
```

**3. Custom Auth** (extensible):
```python
def custom_auth_strategy(config):
    # Implement your auth logic
    return headers
```

---

## Logging System Architecture

### Context Injection

**How It Works**:
```python
# 1. Logger initialization reads config
logger = setup_logger()  # Called once per script

# 2. Custom LoggerAdapter adds context to every log
class ContextAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs['extra'] = {
            **kwargs.get('extra', {}),
            'org_id': self.extra['org_id'],
            'env_type': self.extra['env_type']
        }
        return msg, kwargs

# 3. Every log call automatically includes context
logger.info("Message")  # org_id and env_type added automatically
```

---

## Data Handler Internals

### Type Detection

```python
def save(self, data, category, filename):
    """Auto-detects data type and saves appropriately"""
    if isinstance(data, dict) and all(isinstance(v, pd.DataFrame) for v in data.values()):
        # Dict of DataFrames → Multi-sheet Excel
        return self._save_excel_multi_sheet(data, path)
    elif isinstance(data, pd.DataFrame):
        # Single DataFrame → Single sheet
        return self._save_single_dataframe(data, path)
    elif isinstance(data, (list, dict)):
        # JSON serializable → JSON file
        return self._save_json(data, path)
```

---

## Compliance Validation System

### validate_tko_compliance.py

**Purpose**: Static analysis to catch ADR violations before deployment

**Checks**:
1. **ADR-B003**: Hard-fail config access (no `.get()` with defaults)
2. **ADR-B005**: No hardcoded secrets
3. **ADR-B010**: Use `Dir` constants, not strings
4. **ADR-B017**: Directory-specific UTC timestamp rules

**Usage**:
```bash
PYTHONPATH=. python utils/validate_tko_compliance.py src/my_script.py
```

**Implementation**: AST parsing + regex pattern matching

---

## Extending the Framework

### Adding a New Utils Module

**Steps**:
1. Create `utils/my_new_module.py`
2. Follow layered architecture (import only lower layers)
3. Add to `utils-quick-reference_v3.3.md`
4. Add tests in `tests/test_my_new_module.py`
5. Update ADRs if new patterns introduced

**Example**: Adding email notification utility
```python
# utils/email_helper.py
from utils.logger import setup_logger  # Layer 2
from utils.path_helpers import Dir     # Layer 1

logger = setup_logger()

def send_email(config, subject, body):
    """Sends email using config credentials"""
    smtp_server = config['smtp-server']
    # Implementation...
    logger.info("Email sent", extra={'subject': subject})
```

---

### Adding a New ADR

**When to Add**:
- New mandatory pattern for all scripts
- Architectural decision that affects framework structure
- Resolution of ambiguity (e.g., ADR-B017 clarified UTC rules)

**Process**:
1. Draft ADR in `ai/working/` (UPPERCASE.md)
2. Discuss and refine
3. Move to `ai/decided/txo-business-adr_v3.X.md`
4. Update compliance validator
5. Update prompt templates
6. Add to version history

---

## Document Archival Workflow

### old/ Directory Pattern (ADR-AI002)

**Purpose**: Keep workspace clean while preserving history

**Rules**:
1. **Manual archival**: User moves old versions, not automated
2. **AI ignores**: AI assistants skip `**/old/` directories automatically
3. **No cleanup**: Never delete from old/ (historical reference)

**Workflow**:
```bash
# When creating v3.4, archive v3.3
mkdir -p ai/decided/old
mv ai/decided/utils-quick-reference_v3.2.md ai/decided/old/

# Git tracks the move
git add ai/decided/old/utils-quick-reference_v3.2.md
git rm ai/decided/utils-quick-reference_v3.2.md
git commit -m "Archive v3.3 docs, promote v3.4"
```

**Locations**:
```
ai/old/                # Superseded working documents (TODO.md, STATUS.md)
ai/decided/old/        # Superseded ADRs, templates, references
ai/prompts/old/        # Superseded prompt templates
ai/reports/old/        # Superseded reports
```

---

## Contributing Guidelines

### Before Submitting Changes

**Checklist**:
- [ ] All tests pass
- [ ] Compliance validation passes
- [ ] Documentation updated (README, in-depth, ADRs)
- [ ] Version numbers synchronized
- [ ] CLAUDE.md updated if workflow changed
- [ ] Release notes updated

**Testing**:
```bash
# Run all tests
PYTHONPATH=. python -m pytest tests/

# Validate compliance
find src/ -name "*.py" -exec python utils/validate_tko_compliance.py {} \;

# Syntax check
find utils/ src/ -name "*.py" -exec python -m py_compile {} \;
```

### Git Commit Pattern

See `ai/reports/github-tagging-guide.md` for comprehensive guide

**Example commit for refactoring**:
```
feat(framework): Add ADR-B017 directory-specific UTC rules

**Context**: UTC timestamp requirement was implicit, leading to AI
inconsistency during script generation.

**Changes**:
- Add ADR-B017 with RFC 2119 keywords (MUST/SHOULD/MUST NOT)
- Define rules for 5 directories (output, tmp, generated_payloads, payloads, wsdl)
- Update compliance validator to check directory-specific patterns
- Add examples to utils-quick-reference and prompts

**Impact**: AI now consistently generates correct UTC patterns

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Version History

### v3.3.0 (2025-11-01)
- **ADR-B017**: Directory-specific UTC timestamp rules
- **Template Split**: 2 → 4 templates (script vs refactoring workflows)
- **old/ Documentation**: Added archival workflow explanation
- **README Structure**: Separated script vs framework concerns

### v3.2.0 (2025-10-29)
- Multi-sheet Excel as default pattern
- Enhanced compliance validation
- AI workflow ADRs (ADR-AI001 through ADR-AI006)

### v3.1.1 (2025-09-28)
- Fixed multi-sheet Excel save logic
- Added comprehensive examples

---

## References

- [README.md](README.md) - Quick start and basic usage
- [CLAUDE.md](CLAUDE.md) - AI assistant operating manual
- [ai/decided/txo-business-adr_v3.3.md](ai/decided/txo-business-adr_v3.3.md) - Business ADRs
- [ai/decided/txo-technical-standards_v3.3.md](ai/decided/txo-technical-standards_v3.3.md) - Technical ADRs
- [ai/decided/txo-ai-adr_v3.3.md](ai/decided/txo-ai-adr_v3.3.md) - AI workflow ADRs
- [ai/reports/github-tagging-guide.md](ai/reports/github-tagging-guide.md) - Commit and tagging patterns

---

**Version**: v3.3.0
**Domain**: Framework Architecture
**Audience**: Maintainers and Contributors
**Last Updated**: 2025-11-01
