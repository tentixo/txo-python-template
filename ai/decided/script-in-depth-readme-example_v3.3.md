# [Script Name] - In-Depth Guide v3.3

> **⚠️ TEMPLATE DOCUMENT - For Script Creating Workflow**
>
> **Purpose**: Pattern for AI to generate script-specific in-depth documentation
> **Usage**: Copy structure, replace ALL [placeholders] with actual script details
> **Audience**: Script maintainers and developers extending THIS SCRIPT
> **Workflow**: Script Creating (ai/prompts/script-ai-prompt-template_v3.3.md Phase 7)
>
> **AI Instructions**:
> - Focus on THIS SCRIPT's architecture, not TXO framework internals
> - Explain which TXO features THIS SCRIPT uses (reference framework docs)
> - Provide extension points specific to THIS SCRIPT
> - Include script-specific customization examples

---

# [Script Name] - In-Depth Guide

> **Audience**: Maintainers and developers who need to extend or customize this script
> **Prerequisite**: Read [README.md](README.md) for basic usage
> **Time Investment**: 30-60 minutes to full understanding

## Table of Contents

1. [Script Architecture](#script-architecture)
2. [Data Flow and Processing](#data-flow-and-processing)
3. [API Integration Details](#api-integration-details)
4. [Configuration Deep Dive](#configuration-deep-dive)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Customization Guide](#customization-guide)
7. [TXO Framework Features Used](#txo-framework-features-used)
8. [Testing and Validation](#testing-and-validation)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting Deep Dive](#troubleshooting-deep-dive)

---

## Script Architecture

### Overview

**Purpose**: [One-sentence description of script's purpose]

**Components**:
```
src/[script_name].py
├── main()                    # Entry point, orchestration
├── [function_1]()            # [Description]
├── [function_2]()            # [Description]
├── [function_3]()            # [Description]
└── [helper_function]()       # [Description]
```

### Key Design Decisions

**Decision 1: [Design Choice]**
- **Why**: [Rationale]
- **Trade-off**: [What we sacrificed for this choice]
- **Alternative considered**: [What else we could have done]

**Decision 2: [Another Choice]**
- **Why**: [Rationale]
- **Impact**: [How this affects the script]

### Module Structure

```python
# src/[script_name].py structure

# ===== IMPORTS =====
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.api_factory import create_rest_api
from utils.logger import setup_logger
from utils.path_helpers import Dir

# ===== CONFIGURATION =====
logger = setup_logger()
data_handler = TxoDataHandler()

# ===== CORE FUNCTIONS =====
def [main_processing_function](config, api_client):
    """
    [Description of what this function does]

    Args:
        config: Loaded configuration dict
        api_client: Authenticated API client

    Returns:
        [Return type and description]
    """
    # Implementation

def [helper_function_1](data, params):
    """[Description]"""
    # Implementation

# ===== ORCHESTRATION =====
def main():
    """Main entry point with TXO orchestration"""
    config = parse_args_and_load_config("[Script description]")
    api_client = create_rest_api(config, "[api-name]")

    # Core processing
    results = [main_processing_function](config, api_client)

    # Save results
    filename = f"{config['_org_id']}-{config['_env_type']}-results.xlsx"
    data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
```

---

## Data Flow and Processing

### High-Level Flow

```
1. Configuration Loading
   ↓
2. API Authentication
   ↓
3. [Data Source] Fetch → [Specific API/endpoint]
   ↓
4. Data Transformation → [Describe transformation]
   ↓
5. [Target System] Update → [Specific API/endpoint]
   ↓
6. Report Generation → [Output files]
   ↓
7. [Optional: Notifications]
```

### Detailed Processing Steps

#### Step 1: [Source Data] Fetching

**Endpoint**: `[API endpoint]`

**Request**:
```python
# Example API call
response = api_client.get("/[endpoint]", params={
    "[param1]": config['[setting]'],
    "[param2]": "[value]"
})
```

**Response Format**:
```json
{
  "[key]": "[description]",
  "[array_key]": [
    {"[field1]": "[value]", "[field2]": "[value]"}
  ]
}
```

**Transformation**:
```python
def transform_[source]_data(raw_data):
    """
    Transforms [source] data into format needed for [target]

    Mappings:
    - [source_field1] → [target_field1]
    - [source_field2] → [target_field2] (formatted as [format])
    - [source_field3] → [derived_field] (calculated using [logic])
    """
    transformed = []
    for item in raw_data['[array_key]']:
        transformed.append({
            '[target_field1]': item['[source_field1]'],
            '[target_field2]': format_[something](item['[source_field2]']),
            '[target_field3]': calculate_[something](item)
        })
    return transformed
```

#### Step 2: [Target System] Update

**Endpoint**: `[API endpoint]`

**Batch Processing**:
- **Batch size**: [Number] items per API call
- **Rationale**: [Why this batch size - API limits, performance, etc.]

**Error Handling**:
- **Transient errors**: Retry up to [N] times with exponential backoff
- **Permanent errors**: Log and continue with next item
- **Critical errors**: Stop processing and alert

---

## API Integration Details

### [API/Service Name 1] Integration

**Base URL**: From config `[api-name]-base-url`

**Authentication**: [Type - e.g., OAuth 2.0, API Key, etc.]

**Endpoints Used**:

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `[endpoint1]` | GET | [Description] | [Limit] |
| `[endpoint2]` | POST | [Description] | [Limit] |
| `[endpoint3]` | PUT | [Description] | [Limit] |

**TXO Integration**:
```python
# API client creation using TXO factory
api_client = create_rest_api(config, "[api-name]")

# Automatic features:
# - Credential loading from config-secrets.json
# - Base URL from config.json
# - Timeout handling
# - Structured logging of all requests
```

### [API/Service Name 2] Integration

**Base URL**: From config `[another-api]-base-url`

**Authentication**: [Type]

**Special Considerations**:
- [Consideration 1 - e.g., "Requires tenant-specific endpoints"]
- [Consideration 2 - e.g., "Uses pagination with continuation tokens"]
- [Consideration 3 - e.g., "Rate limited to 100 req/min"]

**Pagination Handling**:
```python
def fetch_all_[resources](api_client, endpoint):
    """Fetches all resources using pagination"""
    all_items = []
    next_token = None

    while True:
        response = api_client.get(endpoint, params={
            'continuation_token': next_token,
            'page_size': 100
        })

        all_items.extend(response['items'])

        next_token = response.get('next_token')
        if not next_token:
            break

    return all_items
```

---

## Configuration Deep Dive

### Required Configuration Keys

#### global Section

```json
{
  "global": {
    "[api1]-base-url": "https://api.example.com",
    "[api1]-timeout": 30,
    "[api2]-base-url": "https://another-api.example.com",
    "[api2]-timeout": 60
  }
}
```

**Key Details**:
- `[api1]-base-url`: [Detailed explanation - where to find it, what it controls]
- `[api1]-timeout`: [Why this timeout, when to adjust]

#### [Service-Specific] Section

```json
{
  "[service-name]": {
    "[setting1]": "[value/type]",
    "[setting2]": "[value/type]",
    "[optional-setting]": "[default if not specified]"
  }
}
```

**Setting Explanations**:
- **`[setting1]`**: [Purpose, valid values, impact]
- **`[setting2]`**: [Purpose, when to change it]
- **`[optional-setting]`**: [What it does, default behavior]

### Secrets Management

#### Required Secrets

```json
{
  "[api1]-api-key": "your-key",
  "[api2]-client-id": "your-client-id",
  "[api2]-client-secret": "your-secret"
}
```

**Obtaining Credentials**:
1. **`[api1]-api-key`**:
   - Navigate to: [Specific UI location]
   - Generate: [Step-by-step instructions]
   - Permissions needed: [List required permissions]

2. **`[api2]-client-id` and `[api2]-client-secret`**:
   - Navigate to: [App registration UI]
   - Create app: [Instructions]
   - Required scopes: [List API permissions needed]

### Environment-Specific Settings

**Development (`dev` environment)**:
```json
{
  "[api]-base-url": "https://sandbox.api.example.com",
  "[setting]": "[dev-appropriate value]"
}
```

**Production (`prod` environment)**:
```json
{
  "[api]-base-url": "https://api.example.com",
  "[setting]": "[prod-appropriate value]"
}
```

---

## Error Handling Strategy

### Error Categories

#### 1. Configuration Errors (Fail Fast)

**Philosophy**: Fail immediately if configuration is wrong

**Examples**:
```python
# TXO hard-fail pattern
api_url = config['global']['[api]-base-url']  # KeyError if missing

# This catches misconfiguration before API calls
```

**Benefit**: Production errors surface during development

#### 2. Transient API Errors (Retry)

**Strategy**: Exponential backoff with maximum retries

**Implementation**:
```python
# TXO create_rest_api includes retry logic
api_client = create_rest_api(config, "[api-name]")

# Automatic retries for:
# - HTTP 429 (Rate Limit)
# - HTTP 503 (Service Unavailable)
# - Connection timeouts
```

#### 3. Business Logic Errors (Log and Continue)

**Strategy**: Don't stop processing for individual item failures

**Example**:
```python
def process_items(items):
    """Process items, log failures but continue"""
    results = {'success': [], 'failed': []}

    for item in items:
        try:
            result = process_single_item(item)
            results['success'].append(result)
        except ValueError as e:
            logger.error(f"Invalid data for item {item['id']}: {e}",
                        extra={'item_id': item['id'], 'error': str(e)})
            results['failed'].append({'item': item, 'error': str(e)})

    return results
```

### Logging Strategy (Script-Specific)

**What This Script Logs**:
- [Log level 1]: [What events - e.g., "INFO: Each successful user sync"]
- [Log level 2]: [What events - e.g., "WARNING: API rate limit encountered"]
- [Log level 3]: [What events - e.g., "ERROR: User validation failed"]

**Log File Location**:
```
logs/[org]-[env]-[script]_[timestamp].log
```

**TXO Features Used**:
- Automatic log file creation with UTC timestamps
- Structured logging (JSON format for AI parsing)
- Credential redaction (never logs secrets)

---

## Customization Guide

### Extension Point 1: [Common Customization]

**Use Case**: [When you would customize this]

**Example**: [Specific business need]

**Implementation**:
```python
# In src/[script_name].py

def [custom_function](data, config):
    """
    Custom logic for [specific need]

    Customization points:
    - [What can be changed]
    - [What parameters are available]
    """
    # Add your custom logic here
    custom_result = []

    for item in data:
        # Example: Custom field mapping
        if config.get('[custom-setting]'):
            item['[custom_field]'] = compute_[something](item)

        custom_result.append(item)

    return custom_result

# Hook custom function into main flow
def main():
    config = parse_args_and_load_config("[Script]")
    data = fetch_data(config)

    # Add custom processing here
    if config.get('[enable-custom-feature]'):
        data = [custom_function](data, config)

    save_results(data)
```

### Extension Point 2: [Another Common Need]

**Use Case**: [When to use this]

**Configuration**:
```json
{
  "[script-section]": {
    "[custom-feature]": {
      "enabled": true,
      "[setting1]": "[value]",
      "[setting2]": "[value]"
    }
  }
}
```

**Implementation**: [Code example or file reference]

### Adding New [Feature Type]

**Steps**:
1. Add configuration in `config/[org]-[env]-config.json`
2. Create function in `src/[script_name].py`
3. Hook into main flow
4. Test with [specific test case]

---

## TXO Framework Features Used

This script leverages these TXO framework capabilities:

### 1. Configuration Management (ADR-B003)

**What This Script Uses**:
- Hard-fail config access: `config['key']` not `.get()`
- Org-env pattern: `[org]-[env]-config.json`
- Secrets separation: `config-secrets.json`

**Example from This Script**:
```python
# Hard-fail ensures we catch misconfiguration early
api_url = config['global']['[api]-base-url']
api_key = config['[api]-api-key']  # From secrets file
```

**For Framework Details**: See [TXO Framework - Configuration](https://github.com/tentixo/txo-python-template/in-depth-readme.md#configuration)

### 2. Directory Management (ADR-B010, ADR-B017)

**What This Script Uses**:
- Dir constants: `Dir.OUTPUT`, `Dir.DATA`, `Dir.TMP`
- UTC timestamps: `save_with_timestamp(..., add_timestamp=True)`

**Example from This Script**:
```python
# Output files automatically get UTC timestamps
filename = f"{config['_org_id']}-{config['_env_type']}-results.xlsx"
output_path = data_handler.save_with_timestamp(
    results, Dir.OUTPUT, filename, add_timestamp=True
)
# Produces: mycompany-prod-results_2025-11-01T143022Z.xlsx
```

**For Framework Details**: See [TXO Framework - Paths](https://github.com/tentixo/txo-python-template/in-depth-readme.md#path-management)

### 3. API Factory (ADR-B007)

**What This Script Uses**:
- `create_rest_api()`: Automatic credential loading, retry logic, logging

**Example from This Script**:
```python
# Single line creates authenticated, retry-enabled, logged API client
api_client = create_rest_api(config, "[api-name]")
```

**For Framework Details**: See [TXO Framework - API Factory](https://github.com/tentixo/txo-python-template/in-depth-readme.md#api-integration)

### 4. Structured Logging (ADR-B006)

**What This Script Uses**:
- Context logging: Automatic org/env in every log
- Credential redaction: Secrets never appear in logs
- AI-friendly format: JSON structured for parsing

**Example from This Script**:
```python
logger.info("Processing complete", extra={
    'users_processed': count,
    'success_rate': success_rate
})
# Automatically includes org_id, env_type, timestamp
```

**For Framework Details**: See [TXO Framework - Logging](https://github.com/tentixo/txo-python-template/in-depth-readme.md#logging)

---

## Testing and Validation

### Manual Testing

**Test Case 1: [Basic Scenario]**

**Setup**:
```bash
# Create test config
cp config/org-env-config_example.json config/test-lab-config.json
# Edit with test credentials
```

**Execute**:
```bash
PYTHONPATH=. python src/[script].py test lab
```

**Verify**:
- [ ] Output file created in `output/test-lab-*`
- [ ] [Specific expected result 1]
- [ ] [Specific expected result 2]
- [ ] Log file shows no errors

**Test Case 2: [Error Scenario]**

**Setup**: [How to trigger this error condition]

**Expected Result**: [What should happen]

### Automated Testing

**Test Script**: `tests/test_[script_name].py`

**Run Tests**:
```bash
PYTHONPATH=. python tests/test_[script_name].py demo test
```

**Test Coverage**:
- [Function/feature 1] - [What is tested]
- [Function/feature 2] - [What is tested]
- Error handling - [What error scenarios are tested]

---

## Performance Optimization

### Current Performance Baseline

**Typical Execution**:
- [N] [items] processed in [time]
- Bottleneck: [What limits performance]

### Optimization Opportunities

#### 1. [Optimization Approach 1]

**Current**: [How it works now]

**Optimized**: [How to make it faster]

**Configuration**:
```json
{
  "[optimization-setting]": "[value]"
}
```

**Expected Improvement**: [Percentage or time reduction]

#### 2. [Optimization Approach 2]

**Trade-off**: [What you sacrifice for speed]

**When to Use**: [Scenarios where this makes sense]

---

## Troubleshooting Deep Dive

### Debug Mode

**Enable Detailed Logging**:
```json
{
  "global": {
    "log-level": "DEBUG"
  }
}
```

**What This Shows**: [What additional info appears in logs]

### Common Issues and Root Causes

#### Issue: [Specific Problem]

**Symptoms**:
- [Observable symptom 1]
- [Observable symptom 2]

**Root Cause**: [Technical explanation]

**Diagnostic Steps**:
1. Check log file: `grep "[pattern]" logs/[org]-[env]-*.log`
2. Verify config: `cat config/[org]-[env]-config.json | jq '.[path]'`
3. Test API: `curl -X GET [endpoint] -H "Authorization: [...]"`

**Resolution**: [Detailed fix]

---

## References

### Related Documentation
- [README.md](README.md) - Quick start and basic usage
- [TXO Framework Architecture](https://github.com/tentixo/txo-python-template/in-depth-readme.md)
- [API Documentation]([link]) - [API/Service] reference
- [ADR-B017](https://github.com/tentixo/txo-python-template/ai/decided/txo-business-adr_v3.3.md#adr-b017) - UTC timestamp rules

### Version History

**Current Version**: [version] ([date])
- [Change or feature description]

**Previous Versions**:
- [v1.1] ([date]) - [Changes]
- [v1.0] ([date]) - Initial release

---

**Script Version**: [version]
**TXO Framework Version**: v3.3.0
**Last Updated**: [date]
**Maintainer**: [name/team]
