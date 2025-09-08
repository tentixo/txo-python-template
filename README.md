# txo-python-template

![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![Version](https://img.shields.io/badge/version-3.0.0-green)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PyCharm](https://img.shields.io/badge/IDE-PyCharm-green)

**Tentixo's Python Template v3.0** - Production-ready framework for Python automation with mandatory configuration, type-safe path management, and enterprise-grade security features.

> **⚠️ BREAKING CHANGES in v3.0**: See [Migration Guide](#migration-from-v2x) for upgrade instructions.

## What's New in v3.0.0

### 🎯 Major Improvements
- **Type-Safe Path Management** - Use `Categories.CONFIG` instead of `'config'` strings
- **Token Optional by Default** - Most scripts don't need authentication
- **Smart I/O** - Single `save()` method auto-detects file types
- **Mandatory Security** - No defaults, configs required for all scripts
- **Thread-Safe Operations** - Lazy loading with proper locking
- **Nested Config Structure** - Cleaner organization of settings

### 🔒 Security First
All scripts REQUIRE three configuration files (will exit if missing):
1. `{org}-{env}-config.json` - Main configuration
2. `logging-config.json` - Logging setup
3. `log-redaction-patterns.json` - Token redaction patterns

## Quick Start - 5 Minutes to Success

### Step 1: Clone and Setup

```bash
# Clone the template
git clone https://github.com/tentixo/txo-python-template.git
cd txo-python-template

# Install dependencies (PyCharm will do this automatically)
pip install uv
uv pip install -r pyproject.toml
```

### Step 2: Copy Required Config Files

```bash
# Copy MANDATORY config templates
cp config/templates/logging-config.json config/
cp config/templates/log-redaction-patterns.json config/

# Copy example config for your org/env
cp config/templates/org-env-config_example.json config/demo-test-config.json
cp config/templates/org-env-config-secrets_example.json config/demo-test-config-secrets.json
```

### Step 3: Run the Try-Me Script

```bash
# Test everything works with our simple demo
python examples/try-me-script.py demo test

# This will:
# 1. Validate all config files exist
# 2. Fetch data from GitHub's public API (no auth needed)
# 3. Save results using smart save()
# 4. Demonstrate all v3.0 patterns
```

## Core v3.0 Patterns

### 1. Type-Safe Path Management (NEW)
```python
from utils.path_helpers import Categories

# ALWAYS use Categories constants
config = data_handler.load_json(Categories.CONFIG, 'settings.json')
data_handler.save(results, Categories.OUTPUT, 'results.json')

# NEVER use strings
# config = data_handler.load_json('config', 'settings.json')  # NO!
```

Available categories:
- `Categories.CONFIG` - Configuration files
- `Categories.DATA` - Input data files
- `Categories.OUTPUT` - Generated output
- `Categories.LOGS` - Log files
- `Categories.TMP` - Temporary files
- `Categories.SCHEMAS` - JSON schemas
- Plus: FILES, GENERATED_PAYLOADS, PAYLOADS, WSDL

### 2. Token is Optional (CHANGED)
```python
# Most scripts DON'T need authentication
config = parse_args_and_load_config(
    "My data processing script"
    # require_token=False is the DEFAULT
)

# Only API scripts need tokens
config = parse_args_and_load_config(
    "Business Central API sync",
    require_token=True  # Must be explicit
)
```

### 3. Smart Save/Load (NEW)
```python
# One method for everything - auto-detects from extension
data_handler.save(dict_data, Categories.OUTPUT, "data.json")      # JSON
data_handler.save(dataframe, Categories.OUTPUT, "report.xlsx")    # Excel
data_handler.save(dataframe, Categories.OUTPUT, "report.csv")     # CSV
data_handler.save("text", Categories.OUTPUT, "readme.txt")        # Text
data_handler.save(config, Categories.CONFIG, "settings.yaml")     # YAML

# Load also auto-detects
data = data_handler.load(Categories.DATA, "input.csv")  # Returns DataFrame
```

### 4. Mandatory Configuration (ENHANCED)
```python
# Script will exit(1) if ANY config file is missing
logger = setup_logger()  # Exits if logging configs missing

# Configuration MUST exist - no defaults
config = parse_args_and_load_config("Script")  # Exits if config missing

# Hard fail on missing keys - no soft defaults
api_url = config['global']['api-base-url']  # KeyError is good!
```

### 5. Nested Config Structure (CHANGED)
```json
{
  "script-behavior": {
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
}
```

## Project Structure

```
txo-python-template/
├── examples/               # Example scripts (NEW location)
│   └── try-me-script.py    # ⭐ START HERE
├── tests/                  # Test scripts (NEW location)
│   └── test_features.py    # Feature validation
├── utils/                  # Core framework (DON'T MODIFY)
│   ├── api_common.py       # Rate limiting, circuit breaker
│   ├── api_factory.py      # API client creation
│   ├── config_loader.py    # Config validation
│   ├── exceptions.py       # HelpfulError pattern
│   ├── load_n_save.py      # Smart I/O with auto-detection
│   ├── logger.py           # Mandatory security logging
│   ├── path_helpers.py     # Categories constants (NEW)
│   ├── rest_api_helpers.py # REST client
│   └── script_runner.py    # Script initialization
├── config/                 
│   ├── templates/          # Example configs to copy
│   ├── {org}-{env}-config.json
│   ├── {org}-{env}-config-secrets.json
│   ├── logging-config.json         # MANDATORY
│   └── log-redaction-patterns.json # MANDATORY
├── schemas/
│   └── org-env-config-schema.json  # Validates all configs
├── output/                 # Generated files
├── logs/                   # Log files (gitignored)
└── data/                   # Input data files
```

## Configuration Files

### Required Files (Script exits if missing)

#### 1. Main Config: `config/{org}-{env}-config.json`
```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "api-version": "v2",
    "tenant-id": "",  // Empty for non-API scripts
    "client-id": "",  // Empty for non-API scripts
    "oauth-scope": "" // Empty for non-API scripts
  },
  "script-behavior": {
    "api-delay-seconds": 1,
    "api-timeouts": {
      "rest-timeout-seconds": 60,
      "async-max-wait": 300,
      "async-poll-interval": 5
    },
    "retry-strategy": {
      "max-retries": 5,
      "backoff-factor": 3.0
    },
    "jitter": {
      "min-factor": 0.8,
      "max-factor": 1.2
    },
    "rate-limiting": {
      "enabled": false,
      "calls-per-second": 10,
      "burst-size": 1
    },
    "circuit-breaker": {
      "enabled": false,
      "failure-threshold": 5,
      "timeout-seconds": 60
    },
    "batch-handling": {
      "read-batch-size": 20,
      "update-batch-size": 10
    }
  }
}
```

#### 2. Logging: `config/logging-config.json`
Controls console (INFO+) and file (DEBUG+) logging. MUST exist.

#### 3. Redaction: `config/log-redaction-patterns.json`
Defines patterns to redact from logs. MUST exist for security.

### Optional: Secrets File (gitignored)
`config/{org}-{env}-config-secrets.json`:
```json
{
  "client-secret": "oauth-secret",
  "az-token": "Bearer eyJ...",
  "api-key": "sk-..."
}
```
Injected with underscore: `config['_client_secret']`, `config['_az_token']`

## Standard Script Template

### Local Processing Script (No Auth)
```python
# examples/process_data.py
"""Process local data files - no authentication needed."""

from typing import Dict, Any
from datetime import datetime, timezone

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Categories
from utils.exceptions import HelpfulError

logger = setup_logger()
data_handler = TxoDataHandler()

def main():
    # No token needed (the default)
    config = parse_args_and_load_config("Process local data")
    
    org_id = config['_org_id']
    env_type = config['_env_type']
    logger.info(f"Starting for {org_id}-{env_type}")
    
    # Load data
    data = data_handler.load(Categories.DATA, "input.csv")
    
    # Process...
    
    # Save with timestamp
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    filename = f"{org_id}-{env_type}-results_{utc}.xlsx"
    data_handler.save(data, Categories.OUTPUT, filename)

if __name__ == "__main__":
    main()
```

### API Integration Script (Needs Auth)
```python
# examples/sync_api.py
"""Sync with external API - requires authentication."""

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.api_factory import create_rest_api
from utils.path_helpers import Categories

logger = setup_logger()

def main():
    # Explicitly require token for API access
    config = parse_args_and_load_config(
        "API sync script",
        require_token=True  # Required for API
    )
    
    # Create API client (uses _token from config)
    api = create_rest_api(config)
    
    # API operations...

if __name__ == "__main__":
    main()
```

## Migration from v2.x

### Breaking Changes

1. **Path strings → Categories constants**
   ```python
   # Old (v2.x)
   data_handler.load_json('config', 'settings.json')
   
   # New (v3.0)
   data_handler.load_json(Categories.CONFIG, 'settings.json')
   ```

2. **Token required → optional by default**
   ```python
   # Old (v2.x) - token required by default
   config = parse_args_and_load_config("Script")
   
   # New (v3.0) - token optional by default
   config = parse_args_and_load_config("Script")  # No token
   config = parse_args_and_load_config("Script", require_token=True)  # With token
   ```

3. **Flat → nested config structure**
   ```json
   // Old (v2.x)
   "enable-rate-limiting": true,
   "rate-limit-per-second": 10
   
   // New (v3.0)
   "rate-limiting": {
     "enabled": true,
     "calls-per-second": 10,
     "burst-size": 1
   }
   ```

4. **Scripts location**
   - Move scripts from `src/` to `examples/` or `tests/`

5. **Mandatory config files**
   - Must have `logging-config.json`
   - Must have `log-redaction-patterns.json`
   - No defaults - script exits if missing

## Best Practices

### ✅ DO
- Use Categories constants for all paths
- Let config access hard-fail (no `.get()` for required keys)
- Use `save()` for all file types (auto-detection)
- Include UTC timestamps in output filenames
- Use HelpfulError for user-facing errors
- Set `require_token=True` ONLY for API scripts

### ❌ DON'T
- Use string literals for paths (`'config'`, `'output'`)
- Require tokens for local processing scripts
- Use soft defaults for configuration
- Use `print()` - always use logger
- Build paths manually - use `get_path()`

## Common Commands

```bash
# Run example script (no auth needed)
python examples/try-me-script.py demo test

# Run with custom org/env
python examples/script.py mycompany prod

# Test all features
python tests/test_features.py demo test

# Debug mode (if configured)
DEBUG_LOGGING=1 python examples/script.py demo test
```

## Troubleshooting

### Config File Not Found
```
CRITICAL CONFIGURATION ERROR
Configuration file not found!
```
**Solution**: Copy templates from `config/templates/`

### Token Required But Not Configured
```
❌ Problem: Token required but OAuth config incomplete
✅ Solution: Either configure OAuth or use require_token=False
```

### Invalid Category
```
ValueError: Invalid category 'config'. Use Categories.* constants
```
**Solution**: Import and use `Categories.CONFIG` instead of `'config'`

## Documentation

- **[Architecture Decisions](ai/decided/adr-records.md)** - Why we built it this way
- **[In-Depth Guide](in-depth-readme.md)** - Comprehensive documentation
- **[Module Dependencies](module-dependency-diagram.md)** - Visual architecture
- **AI Assistance** - Upload `ai/prompts/txo-xml-prompt-v3.0.xml` to Claude/GPT-4

## Support

- **Issues**: [GitHub Issues](https://github.com/tentixo/txo-python-template/issues)
- **Template Version**: v3.0.0
- **Python Required**: 3.10+ (3.13+ recommended)

## License

MIT License - See [LICENSE](LICENSE) for details.