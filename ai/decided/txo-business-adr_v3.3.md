# TXO Business Architecture Decision Records v3.1.1

These ADRs define **TXO-specific business rules and organizational patterns** that reflect how TentXO operates,
regardless of the underlying technology.

---

## ADR-B001: Mandatory Organizational Context Parameters

**Status:** MANDATORY
**Date:** 2025-01-01

### Context

TXO operates across multiple organizations and environments. Data mixing and configuration errors must be prevented at
the parameter level.

### Decision

**All scripts require exactly two positional parameters:**

1. `org_id` (first position, never named)
2. `env_type` (second position, never named)
3. Additional parameters may use named arguments (3rd position onwards)

### Implementation

```bash
# ✅ CORRECT
python script.py txo prod
python script.py company1 test --input-file data.csv
python complex_script.py myorg dev arg3 --verbose --retries 5

# ❌ WRONG
python script.py --org-id=txo --env-type=prod
python script.py prod txo  # Wrong order
```

### Consequences

- Positive: Clear data separation, predictable file naming, consistent CLI
- Negative: No flexibility in parameter order
- Mitigation: Helpful error messages guide users to correct usage

---

## ADR-B002: Configuration Injection with Underscore Prefix

**Status:** MANDATORY
**Date:** 2025-01-01

### Context

TXO functions need access to runtime metadata (org, env, tokens) alongside configuration data.

### Decision

Pass single `config` dictionary with underscore-prefixed injected runtime fields.

### Standard Injected Fields

- `_org_id` - Organization identifier from command line
- `_env_type` - Environment type from command line
- `_token` - OAuth token (if acquired)
- Additional runtime data as needed

### Implementation

```python
# Framework injects these automatically
config["_org_id"] = args.org_id
config["_env_type"] = args.env_type
config["_token"] = acquired_token


# Functions receive complete context
def process_data(config: Dict[str, Any]) -> None:
    org_id = config["_org_id"]
    api_url = config["global"]["api-base-url"]
    token = config["_token"]
```

### Consequences

- Positive: Cleaner function signatures, easier testing, complete context
- Negative: Less explicit about dependencies
- Mitigation: Document injected fields clearly in function docstrings

---

## ADR-B003: Hard-Fail Configuration Philosophy

**Status:** MANDATORY
**Date:** 2025-01-01

### Context

TXO values predictable, consistent behavior. Configuration errors should fail immediately and clearly.

### Decision

- **Hard fail** (`dict['key']`) for ALL configuration data - let KeyError propagate
- **Soft fail** (`dict.get('key')`) ONLY for external API responses and optional data
- **No defaults** for configuration values in code

### Implementation

```python
# ✅ CORRECT - Configuration (hard fail)
api_url = config['global']['api-base-url']  # KeyError if missing
rate_config = config['script-behavior']['rate-limiting']
enabled = rate_config['enabled']  # KeyError if malformed

# ✅ CORRECT - External data (soft fail OK)
email = api_response.get('email')  # None OK for missing field
customer_name = external_data.get('name', 'Unknown')

# ❌ WRONG - Configuration with defaults
timeout = config.get('timeout', 30)  # Masks configuration errors
```

### Consequences

- Positive: Fail fast on misconfiguration, no silent errors
- Negative: Must have complete configuration files
- Mitigation: Provide complete templates and clear error messages

---

## ADR-B004: JSON Schema Validation Requirements

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

TXO processes complex configuration and data files. Invalid structure causes runtime errors and data corruption.

### Decision

JSON Schema validation requirements by file type:

- **MUST** validate main configuration files (`{org}-{env}-config.json`)
- **SHOULD** validate large input files and API payloads (RFC 2119)
- **MAY** validate simple data files and outputs

### Implementation

```python
# Main config - always validate
config_loader.validate_schema(config, 'org-env-config-schema.json')

# Large input files - should validate
if file_size > 1MB or record_count > 1000:
    validate_schema(data, 'input-data-schema.json')

# Simple outputs - optional validation
if strict_mode:
    validate_schema(output, 'output-schema.json')
```

### Validation Timing Strategy

**When should validation happen?** Choose based on file type and use case.

#### Early Validation (Preferred - Fail Fast)

**Validate at load time** for:

- ✅ Configuration files (MANDATORY)
- ✅ Small input files (<1MB)
- ✅ Critical data that affects program flow
- ✅ Schema-dependent processing logic

```python
# ✅ Configuration - validate immediately at load
def load_config(org_id: str, env_type: str):
    """Load and validate configuration."""
    config = _load_json(config_file)
    validate_schema(config, 'org-env-config-schema.json')  # Fail immediately
    return config
```

**Benefits:**

- Fail immediately before any processing
- Clear, actionable error messages upfront
- No partial processing of invalid data
- Easier debugging (errors at load, not deep in processing)

#### Late Validation (When Needed - Performance)

**Validate on demand** for:

- ✅ Large data files (>1MB) where early validation is expensive
- ✅ Optional features (only validate when feature is used)
- ✅ Streaming data (validate chunks as processed)
- ✅ Already-validated data (don't re-validate in tight loops)

```python
# ✅ Large data - validate selectively
def process_large_dataset(data_file: Path):
    """Process large dataset with selective validation."""
    # Don't validate entire file upfront (expensive)
    for chunk in read_chunks(data_file, chunk_size=1000):
        if is_critical_operation(chunk):
            validate_schema(chunk, 'data-schema.json')  # Validate when needed
        process_chunk(chunk)
```

**Benefits:**

- Better performance for large files
- Avoid unnecessary validation overhead
- Flexible validation based on runtime conditions

#### Hybrid Validation (Best of Both)

**Validate structure early, content late** for complex scenarios:

```python
# ✅ Hybrid - structure early, content late
def import_customer_data(input_file: Path):
    """Import customer data with hybrid validation."""

    # Early: Validate file structure immediately
    data = _load_json(input_file)
    validate_structure(data, 'customer-structure-schema.json')  # Fast check

    # Late: Validate content for each record during processing
    results = ProcessingResults()
    for customer in data['customers']:
        try:
            if needs_api_sync(customer):
                validate_schema(customer, 'customer-full-schema.json')  # Detailed check
            sync_customer(customer)
            results.created.append(customer['id'])
        except ValidationError as e:
            results.failed.append(f"{customer.get('id', 'unknown')}: {e}")

    return results
```

#### Validation Decision Matrix

| File Type         | Size | Validation Timing   | Rationale                                |
|-------------------|------|---------------------|------------------------------------------|
| **Configuration** | Any  | Early (load time)   | MANDATORY - fail fast on invalid config  |
| **Input Data**    | <1MB | Early (load time)   | Fast validation, clear errors            |
| **Input Data**    | >1MB | Late (on use)       | Performance - validate chunks/on-demand  |
| **API Payloads**  | Any  | Early (before send) | Prevent bad API calls                    |
| **API Responses** | Any  | Late (optional)     | Trust external API, validate if critical |
| **Output Files**  | Any  | Late (optional)     | Don't slow down output generation        |
| **Cached Data**   | Any  | Skip                | Already validated, don't repeat          |

### Consequences

- Positive: Catch errors early, consistent data structure, self-documenting
- Positive: Clear validation timing strategy (early vs late vs hybrid)
- Positive: Performance-conscious validation for large files
- Negative: Additional schema maintenance overhead
- Negative: Developers must choose appropriate timing strategy
- Mitigation: Generate schemas from examples, version schemas with configs, use decision matrix above

---

## ADR-B005: Never Print - Always Log

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

TXO needs consistent, structured, searchable output for debugging and audit trails.

### Decision

**Absolute prohibition on print() statements.** All output must use structured logging.

### Logging Levels

- **Debug**: File only (detailed troubleshooting info)
- **Info**: Console + file (normal operation status)
- **Warning/Error**: Console + file (issues requiring attention)

### Debugging Workflow

1. Delete existing log file
2. Run script with debug logging enabled
3. Upload log file to AI for analysis
4. Use structured log data for troubleshooting

### Implementation

```python
# ✅ CORRECT
logger.info("Processing started for %d records", len(data))
logger.debug("API request payload: %s", json.dumps(payload))
logger.error("Failed to process record %s: %s", record_id, error)

# ❌ WRONG
print(f"Processing {len(data)} records")  # Not captured in logs
print("Debug info:", payload)  # Not structured
```

### Consequences

- Positive: All output captured, structured for analysis, AI-friendly debugging
- Negative: Requires logger setup in every module
- Mitigation: Logger setup is mandatory framework requirement

---

## ADR-B006: Smart Logging Context Strategy

**Status:** MANDATORY
**Date:** 2025-09-28 (Enhanced)

### Context

TXO operates across local processing and external API integrations. Logging context should be **proportional to
complexity** - simple for local operations, detailed for external API calls that span multiple organizational layers.

### Decision

**Use smart context strategy** based on operation type, aligned with TXO's ERD structure.

### Context Requirements by Operation Type

#### **Local Operations** (File processing, data transformation)

**Context**: **Optional** - Use simple, result-focused logging

```python
# Local file operations - simple logging
logger.info("Processing customer data from CSV")
logger.info(f"Saved {len(results)} records to {output_path}")
logger.info("✅ Local processing completed successfully")
```

#### **External API Operations** (Following ERD Hierarchy)

**Context**: **Mandatory** - Full hierarchical context for traceability

**ERD-Aligned Hierarchy**: `[BC_Environment/Company/API]`

- **BC_Environment**: Business Central environment (`BC-Prod`, `BC-Test`, `BC-Dev`)
- **Company**: Specific company within that environment (`Contoso`, `Fabrikam`, `Adventure-Works`)
- **API**: Specific API endpoint being called (`CustomerAPI`, `SalesOrderAPI`, `ItemAPI`)

```python
# External API operations - full context
context = f"[{bc_env_name}/{company_name}/{api_name}]"
logger.info(f"{context} Starting API synchronization")
logger.debug(f"{context} Processing batch {batch_num} of {total_batches}")
logger.error(f"{context} API call failed: {error_message}")
```

### Implementation Examples

#### **Local Processing Script**:

```python
# Simple, focused logging for local operations
logger.info("🚀 Starting customer data processing")
logger.info(f"Loaded {len(customers)} customers from {input_file}")
logger.info(f"✅ Saved processed data to {output_file}")
```

#### **API Integration Script**:

```python
# Full hierarchical context for external API calls
context = f"[{config['bc-environment']}/{company['name']}/{api_endpoint}]"
logger.info(f"{context} Starting synchronization")
logger.debug(f"{context} Request payload: {sanitized_payload}")
logger.error(f"{context} Rate limit exceeded, retrying in {delay}s")

# Real examples following ERD:
logger.info("[BC-Prod/Contoso/CustomerAPI] Retrieved 150 customers")
logger.error("[BC-Test/Fabrikam/SalesOrderAPI] Authentication failed: token expired")
logger.debug("[BC-Dev/Adventure-Works/ItemAPI] Processing batch 3 of 10")
```

#### **Mixed Operations Script**:

```python
# Local operations - simple logging
logger.info("Loading customer data from CSV")

# External API calls - full context
for company in companies:
    context = f"[{bc_env}/{company['name']}/CustomerAPI]"
    logger.info(f"{context} Syncing {len(customers)} customers")

    # API operations with context
    try:
        response = api.post(f"/companies/{company['id']}/customers", data=customer_data)
        logger.info(f"{context} ✅ Created {len(response)} customer records")
    except ApiError as e:
        logger.error(f"{context} ❌ Sync failed: {e}")

# Local operations - simple logging
logger.info(f"✅ Sync completed. Results saved to {output_file}")
```

### Context Decision Rules

#### **When to Use Full Context** `[BC_Env/Company/API]`:

- Making external API calls
- Operations spanning multiple companies or environments
- Need for detailed traceability and debugging
- Integration with external systems

#### **When to Use Simple Logging**:

- Local file processing only
- Data transformation without external calls
- Single-environment operations
- Internal utility functions

#### **Context Building Pattern**:

```python
# For API operations - build from config and runtime data
bc_env = config["bc-environment"]  # From configuration
company_name = company_data["tech_name"]  # From data being processed
api_name = "CustomerAPI"  # From the specific API being called

context = f"[{bc_env}/{company_name}/{api_name}]"
```

### ERD Alignment

**Follows TXO ERD Structure**:

```
Tenant ||--o{ BC_Env: "has"
BC_Env ||--o{ Company: "contains"
Company ||--o{ API: "exposes"
```

**Logging Context Reflects Reality**:

- **BC_Env**: The environment within the tenant
- **Company**: The specific company being processed
- **API**: The specific API endpoint being used

### Consequences

**Positive**:

- **Proportional complexity**: Simple ops get simple logging, complex ops get detailed context
- **ERD alignment**: Logging structure matches actual system architecture
- **Clear traceability**: Easy to trace issues through the hierarchy
- **Reduced noise**: Local operations don't clutter logs with unnecessary context

**Negative**:

- **Decision overhead**: Developers must choose appropriate context level
- **Consistency risk**: Mixed approaches could lead to inconsistent logging

**Mitigation**:

- **Clear rules**: Simple decision tree for context requirements
- **Helper functions**: Context building utilities in framework
- **Examples**: Comprehensive patterns for both operation types

---

## ADR-B007: Standardized Operation Result Tracking

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

TXO scripts perform bulk operations across multiple entities. Users need clear summaries of what succeeded, failed, and
requires attention.

### Decision

All scripts must use standardized `ProcessingResults` pattern for operation tracking and user-friendly reporting.

### Implementation

```python
@dataclass
class ProcessingResults:
    """Track all operation results for summary reporting"""
    created: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    expected_errors: int = 0

    def add_result(self, api_name: str, company_id: str, result: OperationResult):
        """Add an operation result"""
        identifier = f"{api_name}/{company_id}/{result.entity_id}"

        if result.success:
            if result.operation == "created":
                self.created.append(identifier)
            elif result.operation == "updated":
                self.updated.append(identifier)
                if result.expected_error:
                    self.expected_errors += 1
        else:
            self.failed.append(f"{identifier}: {result.message}")

    def summary(self) -> str:
        """Generate user-friendly summary"""
        total_success = len(self.created) + len(self.updated)

        if self.failed:
            return (f"❌ Completed with {len(self.failed)} failures: "
                    f"{len(self.created)} created, {len(self.updated)} updated, "
                    f"{len(self.failed)} failed")
        else:
            expected_note = f" ({self.expected_errors} handled expected duplicates)" if self.expected_errors > 0 else ""
            return (f"✅ All {total_success} operations successful: "
                    f"{len(self.created)} created, {len(self.updated)} updated{expected_note}")
```

### Usage Pattern

```python
results = ProcessingResults()

for record in data:
    try:
        if process_record(record):
            results.add_legacy_result("SalesAPI", company_id, record.id, True, "created")
        else:
            results.add_legacy_result("SalesAPI", company_id, record.id, False)
    except Exception as e:
        results.failed.append(f"SalesAPI/{company_id}/{record.id}: {str(e)}")

# Always show summary
logger.info(results.summary())
```

### Consequences

- Positive: Consistent user feedback, clear success/failure tracking, audit trail
- Negative: Additional boilerplate for simple scripts
- Mitigation: Helper methods for common patterns, framework integration

---

## ADR-B008: Token Optional by Default

**Status:** MANDATORY
**Date:** 2025-01-16

### Context

Most TXO scripts process local data and don't require external API authentication. Requiring OAuth setup for simple
scripts creates unnecessary friction.

### Decision

Scripts default to **no authentication required**. API scripts must explicitly request tokens.

### Implementation

```python
# ✅ Local scripts (most common)
config = parse_args_and_load_config("Local data processing")  # No token

# ✅ API scripts (explicit)
config = parse_args_and_load_config("BC sync script", require_token=True)
```

### Consequences

- Positive: Easier onboarding, simpler config for local scripts
- Positive: Clear distinction between local and API scripts
- Negative: Breaking change from previous versions
- Mitigation: Clear documentation and migration examples

---

## ADR-B009: Mandatory Configuration Files

**Status:** MANDATORY
**Date:** 2025-01-16

### Context

TXO values consistency and security. Optional configurations with defaults hide misconfigurations and security
vulnerabilities.

### Decision

Three configuration files are **mandatory** - script exits if any are missing:

1. `{org}-{env}-config.json` - Main business configuration
2. `logging-config.json` - Logging setup and levels
3. `log-redaction-patterns.json` - Security token redaction

### Implementation

```bash
# Required files for txo-prod
config/txo-prod-config.json
config/logging-config.json
config/log-redaction-patterns.json

# Templates provided
config/org-env-config_example.json
config/logging-config.json
config/log-redaction-patterns.json
```

### Consequences

- Positive: Consistent behavior, security always active, fail fast
- Negative: Cannot run without setup
- Mitigation: Provide complete templates, clear setup instructions

---

## ADR-B010: Standardized Project Directory Structure

**Status:** MANDATORY
**Date:** 2025-01-16

### Context

TXO scripts work across multiple projects and environments. Consistent directory structure enables predictable
automation, backup strategies, and team collaboration.

### Decision

Mandatory directory structure for all TXO Python projects:

#### Used by code

```
txo-project-root/
├── config/              # Configuration files (mandatory)
│   ├── {org}-{env}-config.json              # Main config created by user (nested, non-secret data)
│   ├── {org}-{env}-config-secrets.json      # Secrets created by user (flat, secret data, always gitignored)
│   ├── log-redaction-patterns.json          # Security patterns to obscure in logs(checked in)
│   ├── logging-config.json                  # Logging setup (checked in)
│   ├── org-env-config-secrets_example.json  # Excample file with keys only, no secret values (checked in, to copy)
│   └── org-env-config_example.json          # Exampple file for main config (checked in, to copy)
├── data/                # Input data files
├── output/              # Generated files and reports (with UTC suffix)
├── files/               # External files used as is
├── logs/                # Log files (gitignored)
├── tmp/                 # Temporary files (with UTC suffix, gitignored)
├── schemas/             # JSON schema files for validation
├── utils/               # Helper files TXO framework code (do not modify)
├── generated_payloads/  # To be manually validated before moving to payloads/ (without UTC suffix, gitignored)
├── payloads/            # Files ready to send via API (moved manually from generated_payloads/)
├── tests/               # Test scripts
├── src/                 # Main scripts
└── wsdl/                # SOAP service definitions (if needed)
```

#### In any directory

```
old/  # Directory for older archved versions of any file. (claudeignore)
```

#### Human, AI, and documentation

```
txo-project-root/
├── ai/                 # AI and human files
│   ├── diecided/       # Patterns defined human and AI together 
│   ├── prompts/        # Prompts to edit and upload to AI
│   ├── reports/        # AI generated reports
│   └── working/        # AI session and process files
├── code_inspection/    # For saving PyCharm's Code/Inspect Code.. reports
├── docs/               # Genral documents
├── skills/             # Claude Skills
├── in-depth-readme.md
├── module-dependency-diagram.md
└── README.md
```

### Type-Safe Path Access

Use `Dir.*` constants instead of string literals:

```python
from utils.path_helpers import Dir

# ✅ CORRECT - Type-safe directory access
config_path = get_path(Dir.CONFIG, 'settings.json')
data_file = data_handler.load(Dir.DATA, 'input.csv')
data_handler.save(results, Dir.OUTPUT, 'report.xlsx')

# ✅ CORRECT - Multi-sheet Excel with UTC timestamp (v3.1.1)
report_sheets = {
    "Summary": processing_summary_df,
    "Created_Records": created_df,
    "Failed_Records": failed_df
}
data_handler.save_with_timestamp(report_sheets, Dir.OUTPUT, 'sync-report.xlsx', add_timestamp=True)

# ❌ WRONG - String literals (typo-prone)
config_path = get_path('config', 'settings.json')
data_file = load('data', 'input.csv')
```

### Directory Constants

- `Dir.CONFIG` - Configuration and secrets files
- `Dir.DATA` - Input data files
- `Dir.OUTPUT` - Generated reports and files
- `Dir.LOGS` - Application log files
- `Dir.TMP` - Temporary processing files
- `Dir.SCHEMAS` - JSON schema validation files
- `Dir.WSDL` - SOAP service definitions
- `Dir.FILES` - General file storage
- `Dir.PAYLOADS` - API request/response samples
- `Dir.GENERATED_PAYLOADS` - Auto-generated API payloads

### Git Configuration

```gitignore
# Generated files
/logs/
/tmp/

# Secrets and sensitive data
*-secrets.*
*-secrets/
*.secret

# IDE and system files
.idea/
.vscode/
__pycache__/
*.pyc
```

### Consequences

- Positive: Consistent structure across projects, predictable automation
- Positive: IDE autocomplete, no typos, refactoring support
- Positive: Clear separation of concerns (config vs data vs output)
- Negative: Must import Dir constants, rigid structure
- Mitigation: Framework handles directory creation automatically

---

## ADR-B011: Secrets Management and Git Security

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

TXO handles sensitive data (tokens, API keys, passwords) that must never be committed to version control. Secrets
management must be consistent and secure across all environments.

### Decision

Standardized secrets management with git exclusion and flat JSON structure:

1. **Secrets stored** in `{org}-{env}-config-secrets.json`
2. **Git ignore pattern**: `*-secrets.*` in `.gitignore`
3. **Template provided**: `{org}-{env}-config-secrets_example.json` (checked in, empty/example values)
4. **Flat structure only**: No nested objects in secrets files

### Implementation

```json lines
// ✅ CORRECT - txo-prod-config-secrets.json (gitignored)
{
  "client-secret": "actual-secret-value-here",
  "api-token": "real-token-value",
  "database-password": "actual-password"
}

// ✅ CORRECT - txo-prod-config-secrets_example.json (checked in)
{
  "client-secret": "",
  "api-token": "your-api-token-here",
  "database-password": "your-db-password"
}

// ❌ WRONG - Nested structure
{
  "oauth": {
    "client-secret": "value"
    // No nesting allowed
  }
}
```

### Git Configuration

```gitignore
# In .gitignore
*-secrets.*
*-secrets/
*.secret
```

### Consequences

- Positive: No secrets in version control, consistent structure
- Positive: Easy setup with templates, flat structure simplifies access
- Negative: Must maintain separate secrets files per environment
- Mitigation: Clear templates and setup documentation

---

## ADR-B012: Naming Convention Standards

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

Consistent naming conventions improve readability, reduce cognitive load, and support tooling integration across TXO's
multi-format codebase. Different naming conventions also provide visual cues about data origins.

### Decision

Format-specific naming conventions based on community standards:

### Naming Rules by Format

- **Markdown files**: `kebab-case_v1.0.md` (e.g., `user-guide_v1.0.md`, `api-reference_v2.1.md`)
- **JSON keys**: `kebab-case` (e.g., `"api-base-url"`, `"retry-count"`)
- **Python files**: `snake_case.py` (e.g., `data_handler.py`, `api_client.py`)
- **YAML keys**: `snake_case` (e.g., `api_base_url:`, `retry_count:`)

### Visual Data Origin Distinction

The mixed conventions create helpful visual cues in Python code:

```python
# ✅ CORRECT - Clear data source distinction
api_base_url = config['global']['api-base-url']  # kebab-case = JSON origin
timeout_seconds = config['global']['timeout-seconds']  # kebab-case = JSON origin
retry_count = 3  # snake_case = Python variable

# Injected secrets preserve JSON format for consistency
client_token = config['_client-secret']  # kebab-case shows JSON origin
database_password = config['_database-password']  # kebab-case shows JSON origin
```

### Implementation

```bash
# ✅ CORRECT - File names
docs/installation-guide.md
utils/config_loader.py
schemas/api-request-schema.json
deployment/staging-config.yaml

# ✅ CORRECT - JSON keys
{
  "global": {
    "api-base-url": "https://api.example.com",
    "timeout-seconds": 30,
    "rate-limiting": {
      "calls-per-second": 10,
      "burst-size": 1
    }
  }
}

# ✅ CORRECT - YAML keys
database:
  connection_string: "postgresql://..."
  pool_size: 10
  timeout_seconds: 30

# ✅ CORRECT - Python with visual distinction
class ConfigLoader:
    def load_api_config(self):
        base_url = self.config['global']['api-base-url']  # JSON → Python
        return base_url

# ✅ CORRECT - Secrets injection preserves format
def inject_secrets(config: Dict[str, Any], secrets: Dict[str, Any]) -> None:
    for key, value in secrets.items():
        # Preserve kebab-case to show JSON origin
        config[f'_{key}'] = value  # "client-secret" → "_client-secret"
```

### Rationale

- **kebab-case**: Standard for URLs, markdown files, JSON APIs
- **snake_case**: Python PEP 8 standard, YAML community preference
- **Visual distinction**: Different cases immediately show data origin
- **Consistency**: Each format follows its ecosystem conventions
- **No transformation**: JSON keys stay as-is throughout the system

### Consequences

- Positive: Follows community standards, consistent within format
- Positive: Visual cues help developers understand data flow
- Positive: No hidden transformations, what you see is what you get
- Negative: Mixed conventions across formats
- Negative: Slightly awkward kebab-case in Python dict keys
- Mitigation: Clear rules per format, benefits outweigh minor awkwardness

---

## ADR-B013: Documentation Format Standards

**Status:** MANDATORY
**Date:** 2025-01-25

### Context

TXO creates extensive documentation (ADRs, guides, specifications) that must be versioned, organized, and consistently
formatted across teams and projects.

### Decision

Standardized documentation format with mandatory versioning, kebab-case naming, and Markdown-first approach with
structured XML when needed.

### Format Standards

#### **Primary Format: Markdown with Inline XML**

- **Base format**: Markdown (`.md`) for readability and universal support
- **Structured data**: Inline XML elements when precision is needed
- **AI prompts**: Markdown + XML hybrid instead of pure XML files

#### **Naming Convention**

**Format**: `document-name_v1.0.md`

- **Document name**: kebab-case (lowercase, hyphen-separated)
- **Version**: underscore + semantic version (`_v1.0`, `_v2.1`, `_v3.0.1`)
- **Extension**: `.md` (Markdown)

### Versioning Rules

- **Major version** (`v1.0` → `v2.0`): Breaking changes, incompatible updates
- **Minor version** (`v1.0` → `v1.1`): New content, backward-compatible additions
- **Patch version** (`v1.1.0` → `v1.1.1`): Corrections, clarifications, typo fixes

### Version Synchronization

**All documentation in a project should use the same version number as the git tag/release version.**

- **Project at v3.1**: All docs should be `*_v3.1.md`
- **Project at v2.0**: All docs should be `*_v2.0.md`
- **Individual documents**: Do NOT have independent versioning

```bash
# ✅ CORRECT - All docs sync with project version
git tag: v3.1
├── txo-business-adr_v3.1.md
├── txo-technical-standards_v3.1.md
├── utils-quick-reference_v3.1.md
└── module-dependency-diagram_v3.1.md

# ❌ WRONG - Mixed versions create confusion
git tag: v3.1
├── txo-business-adr_v3.1.md
├── utils-quick-reference_v1.0.md    # Out of sync!
└── api-guide_v2.5.md                # Out of sync!
```

### Implementation

```bash
# ✅ CORRECT - TXO documentation naming
txo-business-adr_v3.1.md
utils-quick-reference_v1.0.md
api-integration-guide_v2.0.md
troubleshooting-guide_v1.2.1.md

# ✅ CORRECT - Project-specific docs
customer-sync-specification_v1.0.md
business-central-setup_v2.1.md
data-mapping-rules_v1.0.md

# ❌ WRONG - No versioning
user-guide.md
api-reference.md

# ❌ WRONG - Wrong format
UserGuide_v1.0.md          # PascalCase
user_guide_v1.0.md         # snake_case
api-reference-v1.0.md      # hyphen instead of underscore before version
```

### Document Categories by Purpose

#### **ADRs (Architecture Decision Records)**

- Format: `{scope}-adr_v{version}.md`
- Examples: `txo-business-adr_v3.1.md`, `project-technical-adr_v1.0.md`

#### **Reference Documents**

- Format: `{topic}-reference_v{version}.md`
- Examples: `utils-quick-reference_v1.0.md`, `api-reference_v2.0.md`

#### **Guides and Tutorials**

- Format: `{topic}-guide_v{version}.md`
- Examples: `installation-guide_v1.0.md`, `troubleshooting-guide_v2.1.md`

#### **Specifications**

- Format: `{feature}-specification_v{version}.md`
- Examples: `data-sync-specification_v1.0.md`, `oauth-flow-specification_v1.1.md`

### Version Management Strategy

#### **When to Create New Version**

```bash
# Minor updates - increment minor version
api-reference_v1.0.md → api-reference_v1.1.md

# Major restructure - increment major version
user-guide_v1.2.md → user-guide_v2.0.md

# Typo fixes - increment patch version
installation-guide_v1.0.md → installation-guide_v1.0.1.md
```

#### **Version Archive Strategy**

- **Keep current version** in main directory
- **Archive old versions** in `old/` subdirectory when superseded (user manually archives)
- **Maintain compatibility** for at least one major version
- **AI behavior**: ALWAYS ignore old/ directories (see ADR-AI002)

```bash
# Current structure
ai/decided/
├── txo-business-adr_v3.3.md          # Current
├── txo-technical-standards_v3.2.md   # Current
├── utils-quick-reference_v3.2.md     # Current
└── old/                               # AI IGNORES this
    ├── txo-business-adr_v3.1.md       # Previous
    └── adr_v3.0.md                    # Legacy format
```

**AI Ignore Rules** (per ADR-AI002):

- **old/** directories may exist anywhere (root, ai/, ai/decided/, ai/prompts/, ai/reports/)
- **AI MUST ignore** all old/ subdirectories unless explicitly instructed
- **Rationale**: Prevents AI from using outdated patterns
- **User control**: Manual archival, user decides when to delete/move
- **Advanced**: Pro users can create .claudeignore for additional control

### Content Structure Standards

#### **Required Header Block**

```markdown
# Document Title v3.1

> **Purpose**: Brief description of what this document covers
> **Audience**: Who should read this (developers, business stakeholders, etc.)
> **Last Updated**: 2025-01-25

## Version History

- **v3.1** (2025-01-25): Added documentation standards
- **v3.0** (2025-01-16): Major restructure with new ADRs
- **v2.1** (2024-12-01): Initial version

---
```

#### **Markdown + XML Hybrid Examples**

**✅ PREFERRED - Readable Markdown with XML precision:**

```markdown
# Utils Quick Reference v1.0

## 🏗️ Script Setup Functions

### Script Initialization (`utils.script_runner`)

```python
# Most common pattern (no authentication)
config = parse_args_and_load_config("Process local data")
```

```xml


<function-signature>
    <name>parse_args_and_load_config</name>
    <params>description: str, require_token: bool = False</params>
    <returns>Dict[str, Any]</returns>
    <injected-fields>_org_id, _env_type, _token</injected-fields>
</function-signature>
```

**❌ AVOID - Pure XML (hard to read):**

```xml

<documentation>
    <module name="script_runner">
        <function name="parse_args_and_load_config">
            <signature>description: str, require_token: bool = False</signature>
            <returns>Dict[str, Any]</returns>
            <description>Parse arguments and load configuration</description>
        </function>
    </module>
</documentation>
```

**❌ AVOID - Pure Markdown (imprecise):**

```markdown
## script_runner module

Function that parses arguments and loads config. Returns a dictionary.
```

#### **ADR-Specific Structure**

```markdown
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
```

#### **Standard Footer Template**

All TXO documentation must end with this standardized footer:

```markdown
---

## Version History

**Version:** v3.1 | **Last Updated:** 2025-01-25

### v3.1 (Current)
- Added documentation format standards and version synchronization
- Enhanced security requirements and naming conventions

### v3.0
- Major restructure: separated business and technical ADRs
- Implemented type-safe path management and mandatory config files

---

**Version:** v3.1 | **Domain:** [Document Domain] | **Purpose:** [Brief document purpose]
```

**Footer Guidelines:**

- **Dense history**: Maximum 2-3 version entries, focus on major changes only
- **Current indicator**: Mark active version with "(Current)"
- **Meaningful descriptions**: Explain business impact, not technical details
- **Metadata line**: Version | Domain | Purpose for quick reference
- **Synchronized versioning**: Must match project git tag version

### File Organization

```text
# Project documentation structure
docs/
├── adr/                 # Architecture decisions
│   ├── business-adr_v3.1.md
│   ├── technical-adr_v3.1.md
│   └── archive/
├── guides/              # User guides
│   ├── installation-guide_v1.0.md
│   ├── user-manual_v2.0.md
│   └── archive/
├── reference/           # Reference materials
│   ├── api-reference_v1.0.md
│   ├── utils-reference_v1.0.md
│   └── archive/
└── specifications/      # Technical specifications
    ├── data-sync-spec_v1.0.md
    └── archive/
```

### Git Integration

```gitignore
# Don't ignore documentation
!/docs/**/*.md

# Archive old versions but keep accessible
!/docs/**/archive/*.md
```

### Rationale

- **Markdown-first**: Universal readability, git-friendly, works with all tools
- **XML when needed**: Structured precision for AI consumption, function signatures, metadata
- **Hybrid approach**: Best of both worlds - readable by humans, parseable by AI
- **Semantic versioning**: Clear compatibility and change tracking
- **kebab-case consistency**: Matches TXO naming conventions

### Consequences

- Positive: Clear versioning, organized documentation, easy to find current version
- Positive: Consistent format across teams and projects, readable + structured
- Positive: Historical context preserved in archives
- Positive: Markdown + XML hybrid optimizes for both human and AI consumption
- Negative: More complex naming than simple `.md` files
- Negative: Must remember to update versions and maintain XML structure
- Mitigation: Clear guidelines and examples, version control helps track changes

---

## Summary

These Business ADRs define **how TXO operates** - our organizational patterns, security requirements, and user
experience expectations. They should apply regardless of whether we implement in Python, Node.js, or any other
technology.

The key themes are:

1. **Predictability**: Hard-fail configs, mandatory parameters, consistent structure
2. **Security**: Secrets management, mandatory redaction, no defaults in version control
3. **Usability**: Clear error messages, result summaries, type safety
4. **Traceability**: Hierarchical context, operation tracking, audit trails
5. **Consistency**: Naming conventions, file structure, format standards

These rules reflect TXO's values and operational requirements, separate from technical implementation choices.

---

## ADR-B014: Documentation Separation Principles

**Status:** MANDATORY
**Date:** 2025-09-28

### Context

TXO projects generate multiple documentation files that serve different audiences with different time constraints and
expertise levels. Without clear separation principles, documentation becomes redundant, overwhelming, or misaligned with
user needs.

### Decision

**Implement strict documentation separation** based on target audience and time-to-success goals.

### Documentation Contracts

#### **README.md Contract**

**Target**: "New dev, 15 minutes to success"
**Content Limit**: Maximum 2 screens
**Focus**: What, How (basic), Quick start

**Required Sections**:

1. Purpose/Scope - What and why (1-2 sentences)
2. Prerequisites - Python version, dependencies
3. Setup Instructions - Clone to first run
4. Usage - CLI invocation and examples
5. Config Overview - Basic structure, link to schema
6. Output Contract - File formats and naming
7. Logging Contract - Where logs appear, key messages
8. ProcessingResults Summary - Success/warning/failure examples
9. Troubleshooting - Common issues and quick fixes

**Forbidden Content**: Architecture deep-dives, comprehensive config options, advanced customization, implementation
explanations

#### **in-depth-readme.md Contract**

**Target**: "Experienced dev/maintainer, deep understanding"
**Focus**: Why, How (advanced), Architecture, Extension points

**Required Sections**:

1. Architecture & Design Rationale - Why decisions were made
2. Detailed Config Options - Full parameter explanations
3. Error Handling Patterns - Complete taxonomy and strategies
4. Developer Notes - Extension and customization guidance
5. Comprehensive Examples - Advanced usage scenarios
6. References - Links to ADRs and framework components

**Content Principles**: DO NOT duplicate README, EXPAND where minimal, EXPLAIN rationale, PROVIDE advanced examples

### Implementation

**Documentation Balance Requirements**:

- README: "How to run successfully"
- in-depth: "How to understand, customize, and maintain"

**Quality Gates**:

1. README Review: Can new developer succeed in 15 minutes?
2. in-depth Review: Can maintainer understand and extend?
3. Balance Review: No duplication or gaps?
4. Consistency Review: Examples and configs match?

### Consequences

- **Positive**: Clear audiences, no overwhelming beginners, comprehensive maintainer reference
- **Negative**: Two files to maintain, coordination needed
- **Mitigation**: Phase 8 balance review, clear contracts, cross-referencing

---

## ADR-B015: Documentation as First-Class Deliverable

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

TentXO (TXO) values user independence and long-term maintainability. Undocumented code creates support burden, increases
onboarding time, and reduces adoption. Different work types (Script Creating vs Refactoring workflows) have different
documentation needs.

### Decision

Documentation is a **first-class deliverable** with mandatory requirements based on work type.

### Documentation Hierarchy

**Priority Order** (from most to least critical):

1. **User Documentation** - Enables users to succeed independently
2. **Maintainer Documentation** - Enables extension and troubleshooting
3. **Internal Documentation** - Tracks decisions and rationale

**Rationale**: User success is paramount. Maintainers can read code if needed. Internal docs support continuity.

### Documentation Requirements by Work Type

#### For Script Creating Workflow (User-Facing)

**MANDATORY**:

- `README.md` - Quick-start guide (15-minute success target, ADR-B014)
- `in-depth-readme.md` - Maintainer guide (comprehensive reference, ADR-B014)
- Usage examples in docstrings
- Configuration file templates with comments

**OPTIONAL**:

- Architecture diagrams (for complex integrations)
- Troubleshooting guides (if common issues expected)

**Scaling Rule**:

- Simple scripts: Lighter in-depth-readme (~1 screen)
- Complex scripts: Full in-depth-readme (5+ screens)
- Both files always created (consistent process)

#### For Refactoring Workflow (Internal)

**MANDATORY**:

- `ai/TODO.md` - Task tracking with status (enables resumability)
- Test coverage for changed code
- ADR updates if new patterns introduced
- Session summary for multi-session work

**OPTIONAL**:

- Extensive user documentation (framework is internal)
- README updates only if user-facing changes
- In-depth docs only if architecture changed significantly

**Focus**: Tests + tracking > extensive documentation

### Implementation

**Script Creating Workflow** (ai-prompt-template):

```
Phase 1: Context upload
Phase 2: Requirements (ask about tests, confirm docs)
Phase 3: Code generation
Phase 4: Validation
Phase 5: Quality review (optional)
Phase 6: README.md (mandatory)
Phase 7: in-depth-readme.md (mandatory, scaled to complexity)
Phase 8: Balance review
```

**Refactoring Workflow** (refactoring-ai-prompt):

```
Phase 0: Assessment (create ai/TODO.md - mandatory)
Phase 1-N: Refactor by priority (update ai/TODO.md)
Phase N+1: Test coverage verification (mandatory)
Phase N+2: ADR updates (if new patterns)
Phase N+3: Validation
Documentation: Only if user-facing changes
```

### TXO 10-Step Lifecycle Applicability

**Script Creating Workflow**:

- **Steps 1-5**: Discuss, Decision, Todo, Code, Validate (ALL apply)
- **Step 6**: Utils Reference - **NOT applicable** (not modifying utils/)
- **Steps 7-10**: AI Prompts, Documentation, Release Notes, Leftovers (ALL apply)

**Refactoring Workflow**:

- **Steps 1-5**: ALL apply
- **Step 6**: Utils Reference - **MANDATORY if utils/ modified**
   - Check: Did we add/change functions, classes, methods, properties?
   - Action: Update ai/decided/utils-quick-reference_v{X}.md
   - **Critical**: Often forgotten - explicitly verify before done-done
- **Steps 7-10**: ALL apply

**Step 6 Trigger for Refactoring**:

- Added new functions or changed signatures
- Created new classes (e.g., AsyncOperationResult)
- Added properties (e.g., CircuitBreaker.stats)
- Implemented stub functions (e.g., update_from_headers)
- Changed parameters (e.g., setup_logger(strict=False))

**If YES to any**: Update utils-quick-reference is MANDATORY

### Template Requirements

**README.md Template**:

- Purpose/Scope
- Prerequisites
- Setup Instructions
- Usage
- Configuration Overview
- Output Contract
- Logging Contract
- Troubleshooting

**in-depth-readme.md Template**:

- Architecture & Design Rationale
- Detailed Configuration Options
- Error Handling Patterns
- Developer Extension Notes
- Comprehensive Examples
- References to ADRs

**ai/TODO.md Template** (for Refactoring workflow):

- Task list with status (pending/in-progress/completed)
- Priority ranking
- Estimated effort
- Success criteria
- File references with line numbers

### Template vs Project Documentation Distinction

**IMPORTANT**: Differentiate between documentation templates and project documentation

#### Template Examples (ai/decided/*-example_v3.3.md)

**Purpose**: Patterns for AI to copy during Script Creating workflow

- `readme-example_v3.3.md` - Template for script's README.md
- `in-depth-readme-example_v3.3.md` - Template for script's in-depth documentation

**Content**: Generic structure with placeholders like [Your Script Name], [What it does]

**AI Action**:

- **During Script Creating**: Copy structure, replace ALL placeholders with script-specific content
- **During Refactoring**: Update ONLY if template shows outdated patterns

**Not For**: Documenting the TXO Template project itself

#### Project Documentation (root README.md)

**Purpose**: Explains the TXO Python Template project itself

**Content**: How to use the template, setup instructions, features

**Updated By**:

- **Refactoring workflow**: Update if template features changed
- **Script Creating workflow**: User may replace if developing script in template repo

**Key Distinction**:

- Template examples: AI copies for generated scripts
- Project README: Explains the template itself

### Consequences

**Positive**:

- Consistent documentation quality across all scripts
- Users can succeed independently (reduces support burden)
- Maintainers can extend without original author
- Refactoring work is resumable (ai/TODO.md enables breaks)
- Clear expectations for AI assistants
- Documentation hierarchy reflects value priorities

**Negative**:

- Takes time to create proper documentation
- Simple scripts get more docs than minimal approach
- Framework refactoring requires task tracking overhead

**Mitigation**:

- Templates make documentation faster
- Scale in-depth docs to script complexity
- ai/TODO.md saves time in long refactorings (prevents re-work)
- AI generates documentation, not manual work

### Validation

**For Script Creating Workflow**:

```bash
# Check documentation exists
ls README.md in-depth-readme.md

# Verify README targets 15-min success
wc -l README.md  # Should be <100 lines (2 screens)

# Check both docs cross-reference
grep -i "in-depth" README.md
grep -i "README" in-depth-readme.md
```

**For Refactoring Workflow**:

```bash
# Check task tracking exists
ls ai/TODO.md

# Verify test coverage
python -m pytest --cov=utils tests/

# Check ADRs updated if new patterns
git diff ai/decided/
```

---

**Mitigation**: Clear templates, AI generation, scaled to complexity

---

## ADR-B016: Human-Friendly AI Prompts

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

TXO uses AI prompts for Script Creating and Refactoring workflows. These prompts are version-controlled documents that
must be:

- Effective for AI consumption (Claude and future models)
- Readable and maintainable by humans
- Easy to review in git diffs
- Simple to update based on learnings

Pure XML prompts are difficult for humans to read and edit, while providing no proven advantage for modern AI models (
Claude Sonnet 4.5+ verified).

### Decision

**Use Markdown-first format with inline XML blocks only for structured data.**

### Format Standard

**Base Format**: Markdown

- Readable prose and explanations
- Clear hierarchy with headers (##, ###)
- Bullet points and numbered lists
- Code blocks for examples

**Structured Data**: XML blocks

- Use only where structure matters more than prose
- Embedded in markdown with triple-backtick code fences
- Provides precision for checklists, metadata, options

**Prohibited**: Pure XML files

- Harder to maintain
- Poor readability
- No AI advantage (verified)
- Difficult git diffs

### When to Use XML vs Markdown

**Use XML Blocks For**:

- Document lists with type/version attributes: `<doc type="adr" version="v3.2">`
- Checklists with priority/status: `<check priority="critical" status="required">`
- Nested options with properties: `<option value="comprehensive" effort="high">`
- Metadata blocks: `<metadata><version>3.2</version></metadata>`

**Use Markdown For**:

- Instructions and workflows (numbered or bulleted)
- Explanations and rationale (prose paragraphs)
- Examples and code samples (code blocks)
- Discussion and context (natural language)
- Lists and sequences (markdown lists)

### Implementation Pattern

**Good Example** (from ai-prompt-template_v3.3.md):

```markdown
## Phase 1: Context Upload (CRITICAL)

**Upload these documents to establish TXO patterns:**

```xml
<required-documents>
    <doc type="business-rules" version="v3.2">
        <file>ai/decided/txo-business-adr_v3.3.md</file>
        <purpose>Organizational patterns, hard-fail philosophy</purpose>
    </doc>
    <doc type="technical-standards" version="v3.2">
        <file>ai/decided/txo-technical-standards_v3.3.md</file>
        <purpose>Python patterns, ADR-T011, ADR-T012</purpose>
    </doc>
</required-documents>
```

**Instructions**:

1. READ and UNDERSTAND the business rules
2. STUDY the available functions
3. ANALYZE configuration patterns

```

**Poor Example** (pure XML):
```xml
<phase>
    <number>1</number>
    <title>Context Upload</title>
    <priority>critical</priority>
    <instruction>
        <action>Upload documents</action>
        <document>
            <type>business-rules</type>
            <file>ai/decided/txo-business-adr_v3.3.md</file>
        </document>
    </instruction>
    <steps>
        <step>Read and understand</step>
        <step>Study available functions</step>
    </steps>
</phase>
```

### File Naming Convention

**Format**: `prompt-name_v{version}.md`

- Extension: `.md` (not `.xml.md`)
- Use markdown extension for markdown-first files
- Indicates primary format to tools and IDEs

**Examples**:

- ✅ `ai-prompt-template_v3.3.md`
- ✅ `refactoring-ai-prompt_v3.3.md`
- ❌ `refactoring-xml-ai-prompt_v3.0.xml.md` (old pattern)

### Rationale

**Why Markdown-First**:

- Universal developer skill (everyone knows markdown)
- Better IDE support (preview, formatting, navigation)
- Clear git diffs (see what changed)
- Encourages humans to read and improve prompts
- Natural language flow for context and explanations

**Why Keep Some XML**:

- Structured data benefits from explicit tags
- Attributes provide metadata efficiently
- Hierarchy clear in nested structures
- Precision for checklists and validation criteria

**Why This Matters**:

- Prompts evolve based on learnings (like our v3.2 updates)
- Humans must maintain prompts (update patterns, add learnings)
- Collaboration requires readability (team reviews prompts)
- Future maintainers inherit these documents

### AI Effectiveness Validation

**Tested With**: Claude Sonnet 4.5 during v3.2 refactoring
**Result**: Markdown+XML hybrid (ai-prompt-template_v3.3.md) worked flawlessly

**Claude's Reality**:

- Markdown headers understood as hierarchy (`## Phase 1` = structure)
- Bullet points parsed as sequences (no `<step>` tags needed)
- Code blocks preferred for examples (clearer than escaped XML)
- XML blocks understood when present (parsed equally well)
- **No advantage to pure XML** - possibly slight disadvantage (more tokens, less context)

### Consequences

**Positive**:

- Human-readable and maintainable by any developer
- AI parses equally well (Claude Sonnet 4.5 verified in practice)
- Better collaboration (team can review and improve)
- Clear git diffs (see changes easily)
- Encourages prompt evolution (easier to update)
- Aligns with TXO values (usability, clarity, independence)
- Future-proof (AI trends toward natural language)

**Negative**:

- Cannot validate entire file with XML parser
- Requires understanding both markdown and XML syntax
- Less rigid structure (though flexibility can be positive)
- Mixed format (but commonly used in documentation)

**Mitigation**:

- Provide clear templates (ai-prompt-template as reference)
- Document when to use XML vs markdown (this ADR)
- Use XML sparingly (only where structure truly helps)
- Validate prompts through actual use, not parsers

---

**Mitigation**: Templates provided, actual usage validates effectiveness

---

## ADR-B017: Output File Naming and Directory-Specific Timestamp Rules

**Status:** MANDATORY
**Date:** 2025-11-01
**RFC 2119 Keywords:** This ADR uses MUST, SHOULD, MUST NOT per RFC 2119

### Context

TXO operates across multiple organizations and environments. Output files must be:
- Distinguishable by organization and environment
- Traceable to execution time (where appropriate)
- Non-overwriting for audit trails (output/)
- Deterministic for human workflows (payloads/)

Different directories serve different purposes and require different naming strategies.

### Decision

#### Rule 1: Filename Pattern (MANDATORY for all directories)

**All files written by code MUST follow:**
```
{org_id}-{env_type}-{description}.{extension}
```

Where:
- `org_id`: Organization identifier from config['_org_id']
- `env_type`: Environment type from config['_env_type']
- `description`: Human-readable file purpose (kebab-case)
- `extension`: File format (.json, .xlsx, .csv, .txt, .xml)

**Exception**: wsdl/ MAY use service-versioned naming (e.g., `UserService_v2.1.wsdl`)

#### Rule 2: UTC Timestamp Rules (Directory-Specific)

**MUST use UTC timestamps** (save_with_timestamp with add_timestamp=True):
- `Dir.OUTPUT` - Final results, reports, exports
  - Pattern: `{org}-{env}-{desc}_{YYYY-MM-DDTHHMMSSZ}.{ext}`
  - Rationale: Each run creates unique file, audit trail, traceability

**SHOULD use UTC timestamps**:
- `Dir.TMP` - Temporary processing files
  - Pattern: `{org}-{env}-{desc}_{YYYY-MM-DDTHHMMSSZ}.{ext}` (flexible)
  - Rationale: Multi-run debugging, but MAY be relaxed for ephemeral caches

**MUST NOT use UTC timestamps**:
- `Dir.GENERATED_PAYLOADS` - Code-generated JSON for human validation
  - Pattern: `{org}-{env}-{desc}.json` (NO timestamp)
  - Rationale: Overwrites desired, human validates before sending

- `Dir.PAYLOADS` - Ready-to-send API payloads (manually moved from generated_payloads/)
  - Pattern: `{org}-{env}-{desc}.json` (NO timestamp)
  - Rationale: Human-curated, manual workflow

- `Dir.WSDL` - SOAP service definitions
  - Pattern: `ServiceName_v{version}.wsdl` (service-versioned)
  - Rationale: Versioned by service version, not time

### Implementation

#### Example 1: Output Files (MUST use UTC)
```python
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir

data_handler = TxoDataHandler()

# ✅ CORRECT - JSON output with UTC
filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
output_path = data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
# Produces: output/txo-lab-sync-results_2025-11-01T143022Z.json

# ✅ CORRECT - Multi-sheet Excel with UTC
report_sheets = {"Summary": summary_df, "Details": details_df}
filename = f"{config['_org_id']}-{config['_env_type']}-analysis-report.xlsx"
output_path = data_handler.save_with_timestamp(report_sheets, Dir.OUTPUT, filename, add_timestamp=True)
# Produces: output/txo-lab-analysis-report_2025-11-01T143022Z.xlsx
```

#### Example 2: Tmp Files (SHOULD use UTC)
```python
# ✅ CORRECT - Processing cache with UTC
filename = f"{config['_org_id']}-{config['_env_type']}-processing-cache.json"
tmp_path = data_handler.save_with_timestamp(cache_data, Dir.TMP, filename, add_timestamp=True)
# Produces: tmp/txo-lab-processing-cache_2025-11-01T143022Z.json

# ✅ ACCEPTABLE - Simple tmp without UTC (ephemeral data)
tmp_path = data_handler.save({"temp": "data"}, Dir.TMP, "quick-cache.json")
# Produces: tmp/quick-cache.json (acceptable for truly ephemeral data)
```

#### Example 3: Generated Payloads (MUST NOT use UTC)
```python
# ✅ CORRECT - Generated payload WITHOUT UTC (deterministic)
filename = f"{config['_org_id']}-{config['_env_type']}-create-user-request.json"
payload_path = data_handler.save(request_payload, Dir.GENERATED_PAYLOADS, filename)
# Produces: generated_payloads/txo-lab-create-user-request.json

# Human workflow:
# 1. Code generates → generated_payloads/txo-lab-create-user-request.json
# 2. Human validates → checks JSON structure, field values
# 3. Human moves → cp to payloads/txo-lab-create-user-request.json
# 4. Code/human sends → reads from payloads/ directory
```

#### Example 4: WSDL Files (MUST NOT use UTC)
```python
# ✅ CORRECT - Service-versioned naming
filename = "UserService_v2.1.wsdl"
wsdl_path = data_handler.save(wsdl_content, Dir.WSDL, filename)
# Produces: wsdl/UserService_v2.1.wsdl
```

#### Anti-Patterns (WRONG)
```python
# ❌ WRONG - OUTPUT without UTC timestamp
filename = f"{config['_org_id']}-{config['_env_type']}-report.json"
data_handler.save(data, Dir.OUTPUT, filename)  # Missing UTC!

# ❌ WRONG - Filename missing env_type
filename = f"results-{config['_org_id']}.json"  # Only org, no env!

# ❌ WRONG - Generated payload WITH UTC (should be deterministic)
filename = f"{config['_org_id']}-{config['_env_type']}-request.json"
data_handler.save_with_timestamp(payload, Dir.GENERATED_PAYLOADS, filename, add_timestamp=True)

# ❌ WRONG - Manual UTC formatting (use framework method)
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
filename = f"data_{timestamp}.json"  # Use save_with_timestamp() instead
```

### Rationale

**Consistency with Configuration Files:**
- Config pattern: `{org}-{env}-config.json` (e.g., `txo-lab-config.json`)
- Output pattern: `{org}-{env}-description_{timestamp}.{ext}` (matches config structure)

**Environment Isolation:**
- Output directory may contain files from multiple environments
- `env_type` distinguishes: `txo-prod-*` vs `txo-test-*` vs `txo-lab-*`

**Traceability (Output files):**
- UTC timestamp enables time-based analysis
- Each execution creates unique file (no overwrites)
- Debug workflow: "Upload output file from 2025-11-01T14:30 run"

**Deterministic Naming (Payloads):**
- Human validation workflow requires stable filenames
- No timestamp = always overwrites with latest version
- Simplifies payload references in documentation

**Framework Standardization:**
- `save_with_timestamp()` enforces ISO 8601 format
- Framework handles UTC conversion (no manual datetime code)
- Prevents timezone inconsistencies

### Consequences

**Positive:**
- Clear filename structure across all TXO projects
- Easy to find files for specific org/env combinations
- Non-destructive output (never overwrites previous results)
- Audit trail for compliance and debugging
- Deterministic payloads for human validation workflow

**Negative:**
- Longer filenames for output files
- Output directory accumulates files over time
- Developers must remember directory-specific rules

**Mitigation:**
- Use `cleanup_tmp()` for temporary files (path_helpers.py)
- Archive old output files periodically
- Compliance validator checks correct patterns
- Filenames remain human-readable despite length
- Critical reminders in AI prompt templates

### Validation

ADR-B017 compliance checked by `utils/validate_tko_compliance.py`:
- ✅ OUTPUT uses save_with_timestamp with add_timestamp=True
- ✅ Filenames include both org_id AND env_type
- ✅ GENERATED_PAYLOADS does NOT use save_with_timestamp
- ⚠️  TMP should use save_with_timestamp (warning, not error)

### References

- ADR-B010: Directory Structure and Path Management (foundation)
- ADR-B006: Smart Logging Context Strategy (logging UTC, not filenames)
- `utils/path_helpers.py`: Dir constants and directory definitions
- `utils/load_n_save.py`: save_with_timestamp() implementation

---

## Version History

### v3.2 (Current)

- Added ADR-B015: Documentation as First-Class Deliverable
- Added ADR-B016: Human-Friendly AI Prompts (markdown+XML hybrid mandatory)
- Enhanced ADR-B004: Validation timing strategy (early vs late vs hybrid)
- Documented documentation hierarchy (User > Maintainer > Internal)
- Made ai/TODO.md mandatory for Refactoring workflow
- Added validation decision matrix for file types and sizes
- Documented fail-fast vs performance trade-offs
- Aligned with v3.2 refactoring efforts

### v3.1.1

- Enhanced ADR-B006: Smart Logging Context Strategy with ERD alignment
- Implemented proportional complexity (simple local vs detailed external operations)
- Added clear decision rules for when to use hierarchical context
- Aligned logging structure with TXO ERD (BC_Environment/Company/API)

### v3.1

- Added documentation format standards and version synchronization
- Enhanced security requirements and naming conventions
- Added documentation separation principles (ADR-B014)
- Implemented README vs in-depth documentation contracts

### v3.0

- Major restructure: separated business and technical ADRs
- Implemented type-safe path management and mandatory config files

---

**Version:** v3.2
**Last Updated:** 2025-10-29
**Domain:** TXO Business Architecture
**Purpose:** Organizational patterns and operational requirements  