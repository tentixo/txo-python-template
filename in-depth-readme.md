# TXO Python Template v3.1.1 - In-Depth Guide

> **Audience**: Framework maintainers, experienced developers, and customization needs
> **Purpose**: Deep understanding of architecture, rationale, and extension points
> **Prerequisite**: Read [README.md](README.md) for basic setup

---

## Table of Contents

1. [Architecture & Design Rationale](#architecture--design-rationale)
2. [Detailed Configuration Options](#detailed-configuration-options)
3. [Error Handling Patterns](#error-handling-patterns)
4. [Developer Extension Notes](#developer-extension-notes)
5. [Comprehensive Examples](#comprehensive-examples)
6. [References](#references)

---

## Architecture & Design Rationale

### Why TXO Enforces Hard-Fail Configuration (ADR-B003)

**Problem**: Traditional scripts use defaults that mask configuration errors
**Solution**: Hard-fail immediately on missing configuration
**Benefit**: Production errors surface during development, no hidden dependencies

```python
# TXO Way - Fails immediately if misconfigured
api_url = config['global']['api-base-url']  # KeyError if missing

# Traditional Way - Silent failure, hard to debug
api_url = config.get('global', {}).get('api-base-url', 'https://default.com')
```

### Why Multi-Sheet Excel is Default (v3.1.1)

**Problem**: Most business reports need multiple data views
**Solution**: Dict of DataFrames auto-detected for multi-sheet Excel
**Benefit**: Natural data organization, single save operation

```python
# Natural business report structure
report_data = {
    "Executive_Summary": summary_stats_df,
    "Detailed_Results": full_results_df,
    "Error_Analysis": errors_df,
    "Processing_Log": processing_log_df
}

# Single operation creates comprehensive report
data_handler.save_with_timestamp(report_data, Dir.OUTPUT, "monthly-report.xlsx", add_timestamp=True)
```

### Why Smart Logging Context (ADR-B006)

**Problem**: Generic logging context creates noise for simple operations
**Solution**: Proportional complexity - simple for local, detailed for external APIs
**Benefit**: Clear traceability without overwhelming local file processing

```python
# Local operations - simple, focused
logger.info("Processing customer data from CSV")
logger.info(f"✅ Saved {len(results)} records")

# External API operations - full hierarchical context
context = f"[{bc_env}/{company_name}/CustomerAPI]"
logger.info(f"{context} Starting synchronization")
logger.error(f"{context} Rate limit exceeded, retrying in {delay}s")
```

---

## Detailed Configuration Options

### Complete script-behavior Configuration

```json
{
  "script-behavior": {
    "rate-limiting": {
      "enabled": true,
      "calls-per-second": 50,
      "burst-size": 1.5
    },
    "circuit-breaker": {
      "enabled": true,
      "failure-threshold": 10,
      "timeout-seconds": 300
    },
    "retry-config": {
      "max-retries": 5,
      "backoff-factor": 2.0,
      "jitter": {
        "min-factor": 0.8,
        "max-factor": 1.2
      }
    },
    "timeouts": {
      "rest-timeout-seconds": 120,
      "async-poll-interval": 10,
      "async-max-wait": 1800
    },
    "batch-processing": {
      "read-batch-size": 50,
      "write-batch-size": 25
    }
  }
}
```

### Configuration Edge Cases

**Rate Limiting Disabled**: Set `enabled: false` - limiter objects still created but pass-through
**Circuit Breaker Timeout**: After timeout, circuit automatically closes and retries
**Async Operations**: Polls until complete or `async-max-wait` timeout
**Batch Processing**: Handles memory efficiency for large datasets

---

## Error Handling Patterns

### Complete HelpfulError Taxonomy

#### **Configuration Errors**
```python
raise HelpfulError(
    what_went_wrong="Configuration file missing",
    how_to_fix="Copy example files from config/ directory",
    example="cp config/org-env-config_example.json config/myorg-test-config.json"
)
```

#### **API Authentication Errors**
```python
raise ApiAuthenticationError(
    "Token expired or invalid",
    context=ErrorContext(
        operation="api_authentication",
        resource="CustomerAPI",
        details={"tenant_id": tenant_id, "client_id": client_id}
    )
)
```

#### **Data Validation Errors**
```python
raise ValidationError(
    "Excel sheet name too long",
    context=ErrorContext(
        operation="excel_sheet_validation",
        resource=filename,
        details={"sheet_name": sheet_name, "max_length": 31}
    )
)
```

### When to Treat Empty Results as Warnings vs Failures

**Warnings** (Processing continues):
- Optional data sources return empty
- Non-critical API endpoints unavailable
- Batch processing with some empty batches

**Failures** (Processing stops):
- Required configuration missing
- Authentication failures
- Critical data validation errors
- All API endpoints unavailable

---

## Developer Extension Notes

### Adding New Output Formats

1. **Add format detection** to `FORMAT_EXTENSIONS` mapping
2. **Implement save method** following `save_yaml()` pattern
3. **Add to smart routing** in `save()` method
4. **Update format validation** logic
5. **Add examples** to utils-quick-reference

### Extending to New APIs

1. **Use existing patterns** in `rest_api_helpers.py`
2. **Configure resilience** via script-behavior config
3. **Implement proper error handling** with context
4. **Follow ADR-B006** logging context strategy
5. **Add to ProcessingResults** tracking

### Custom Validation Rules

```python
# Add custom validators to utils/exceptions.py
class BusinessValidationError(ValidationError):
    """Custom business logic validation errors."""

# Use in main scripts
def validate_customer_data(customer):
    if not customer.get('email'):
        raise BusinessValidationError(
            "Customer missing required email address",
            context=ErrorContext(
                operation="customer_validation",
                resource=customer.get('id', 'unknown'),
                details=customer
            )
        )
```

---

## Comprehensive Examples

### Multi-Company API Synchronization
```python
# Process multiple companies with proper context and error handling
companies = data_handler.load(Dir.DATA, "companies.csv")

results_by_company = {}
for company in companies:
    context = f"[{config['bc-environment']}/{company['name']}/CustomerAPI]"

    try:
        api = create_rest_api(config, require_auth=True)
        customers = api.get(f"/companies/{company['id']}/customers")

        logger.info(f"{context} Retrieved {len(customers)} customers")
        results_by_company[f"{company['name']}_Results"] = pd.DataFrame(customers)

    except ApiError as e:
        logger.error(f"{context} Failed: {e}")
        results_by_company[f"{company['name']}_Errors"] = pd.DataFrame([{"error": str(e)}])

# Save comprehensive multi-sheet report
data_handler.save_with_timestamp(
    results_by_company, Dir.OUTPUT, "company-sync-report.xlsx",
    add_timestamp=True
)
```

### Advanced Configuration with All Features
```json
{
  "global": {
    "api-base-url": "https://api.businesscentral.dynamics.com",
    "tenant-id": "your-tenant-uuid",
    "client-id": "your-client-uuid",
    "timeout-seconds": 60,
    "bc-environment": "BC-Prod"
  },
  "script-behavior": {
    "rate-limiting": {
      "enabled": true,
      "calls-per-second": 100,
      "burst-size": 2.0
    },
    "circuit-breaker": {
      "enabled": true,
      "failure-threshold": 15,
      "timeout-seconds": 600
    },
    "retry-config": {
      "max-retries": 5,
      "backoff-factor": 1.5,
      "jitter": {
        "min-factor": 0.9,
        "max-factor": 1.1
      }
    },
    "timeouts": {
      "rest-timeout-seconds": 90,
      "async-poll-interval": 15,
      "async-max-wait": 3600
    },
    "batch-processing": {
      "read-batch-size": 100,
      "write-batch-size": 50
    }
  },
  "custom-settings": {
    "data-validation": {
      "strict-mode": true,
      "required-fields": ["id", "name", "email"]
    }
  }
}
```

---

## References

### TXO Framework Documentation
- **Business Rules**: `ai/decided/txo-business-adr_v3.1.md`
- **Technical Standards**: `ai/decided/txo-technical-standards_v3.1.md`
- **Function Reference**: `ai/decided/utils-quick-reference_v3.1.md`
- **AI Development**: `ai/prompts/ai-prompt-template_v3.1.1.md`

### Key ADRs for Framework Understanding
- **ADR-B003**: Hard-Fail Configuration Philosophy
- **ADR-B006**: Smart Logging Context Strategy
- **ADR-B007**: Standardized Operation Result Tracking
- **ADR-B014**: Documentation Separation Principles

### Framework Architecture
- **Visual Overview**: `module-dependency-diagram.md`
- **Technical Details**: `ai/reports/refactoring.md`
- **Release History**: `ai/reports/release-notes-v3.1.1.md`

---

**Version:** v3.1.1
**Last Updated:** 2025-09-28
**Domain:** TXO Framework - Maintainer Guide
**Purpose:** Deep understanding for customization and extension