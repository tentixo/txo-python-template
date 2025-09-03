# txo-python-template

![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![Version](https://img.shields.io/badge/version-2.1.0-green)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PyCharm](https://img.shields.io/badge/IDE-PyCharm-green)

**Tentixo's Python Template v2.1** - Production-ready framework for REST/OData API automation with built-in resilience patterns, automatic error handling, and enterprise-grade security features.

> **⚠️ Important**: Any changes to configuration structure MUST be reflected in `schemas/org-env-config-schema.json`. The schema validates all configuration files.

## What's New in v2.1.0

- 🔒 **Automatic Token Redaction** - Logs never expose sensitive data
- ⚡ **Rate Limiting** - Prevent API bans with configurable throttling
- 🔄 **Circuit Breakers** - Stop cascade failures automatically
- 📊 **Async Operation Support** - Handle 202 Accepted responses transparently
- 💡 **HelpfulError Pattern** - User-friendly error messages with solutions
- 🎯 **Intelligent Save** - Auto-detects file type from data and extension
- 🔧 **Hard-Fail Philosophy** - No silent failures on configuration errors

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

### Step 2: Run the Try-Me Script

```bash
# Test everything works with our simple demo
python src/try-me-script.py demo test

# This will:
# 1. Tell you to create a config file (follow the instructions)
# 2. Fetch data from GitHub's public API  
# 3. Save results to output/demo-test-github_repos_*.json
# 4. Show you all the patterns in action
```

### Step 3: Create Your Config (When Prompted)

The try-me script will tell you exactly what to create:

```json
# config/demo-test-config.json
{
  "global": {
    "api-base-url": "https://api.github.com",
    "api-version": "v3"
  },
  "script-behavior": {
    "api-delay-seconds": 1,
    "api-timeouts": {
      "rest-timeout-seconds": 30
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
      "read-batch-size": 100
    }
  }
}
```

## Project Structure

```
txo-python-template/
├── src/                    # Your scripts go here
│   ├── try-me-script.py    # ⭐ START HERE - Simple test script
│   └── test_v2_features.py # Advanced feature tests
├── utils/                  # Helper modules (DON'T MODIFY)
│   ├── api_common.py       # Rate limiting, circuit breaker
│   ├── api_factory.py      # API client creation
│   ├── concurrency.py      # Parallel processing
│   ├── config_loader.py    # Configuration management
│   ├── exceptions.py       # Custom exceptions with HelpfulError
│   ├── load_n_save.py      # Intelligent file I/O
│   ├── logger.py           # Logging with token redaction
│   ├── oauth_helpers.py    # OAuth 2.0 support
│   ├── path_helpers.py     # Cross-platform paths
│   ├── rest_api_helpers.py # REST client with resilience
│   ├── script_runner.py    # Script initialization
│   └── url_helpers.py      # URL construction
├── config/                 # Configuration files
│   ├── logging-config.json # Logging settings
│   └── {org}-{env}-config.json # Your config files
├── schemas/                # JSON schemas
│   └── org-env-config-schema.json # ⚠️ UPDATE when changing config structure
├── output/                 # Generated files go here
├── logs/                   # Log files (gitignored)
└── ai/                     # AI assistance
    ├── prompts/            # AI prompt templates
    └── decided/            # Architecture Decision Records

## Core Patterns

### 1. Standard Script Structure
Every script follows this pattern:

```python
# src/my_script.py
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.exceptions import HelpfulError

logger = setup_logger()
data_handler = TxoDataHandler()

def main():
    config = parse_args_and_load_config("My script description")
    logger.info(f"Starting {config['_org_id']}-{config['_env_type']}")
    
    # Your code here
    # config['_token'] is automatically injected if auth is needed
    
if __name__ == "__main__":
    main()
```

### 2. Error Handling with HelpfulError
Never show stack traces to users. Use HelpfulError:

```python
from utils.exceptions import HelpfulError

if not data_handler.exists("config", filename):
    raise HelpfulError(
        what_went_wrong="Config file 'settings.json' not found",
        how_to_fix="Create the file in config/ directory",
        example="Copy config/example.json to config/settings.json"
    )
```

### 3. Intelligent Save Pattern
The `save()` method auto-detects type from data and extension:

```python
# JSON (auto-handles Decimal types)
data_handler.save({"amount": Decimal("99.99")}, "output", "data.json")

# CSV from DataFrame
data_handler.save(df, "output", "report.csv", index=False)

# Excel from DataFrame  
data_handler.save(df, "output", "report.xlsx", sheet_name="Results")

# Plain text
data_handler.save("Report content", "output", "report.txt")
```

### 4. Configuration Philosophy
**Hard fail on missing required config** - no silent errors:

```python
# Required config - KeyError if missing (GOOD)
api_url = config['global']['api-base-url']  

# Optional API response - None if missing (GOOD)
email = response.get('email')

# NEVER do soft fail on config (BAD)
api_url = config.get('global', {}).get('api-base-url', 'default')  # NO!
```

## Configuration Management

### ⚠️ Critical Rule: Schema Must Match Config

**EVERY configuration change requires updating the JSON schema!**

When you add/modify configuration:
1. Update your `config/{org}-{env}-config.json`
2. **IMMEDIATELY** update `schemas/org-env-config-schema.json`
3. Use kebab-case for all keys: `"my-new-setting"`
4. Document the purpose in the schema description

### Configuration Structure

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
      "max-retries": 3,
      "backoff-factor": 2.0,
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
      "update-batch-size": 50
    }
  }
}
```

### Secrets Management (Never Commit!)

Create `config/{org}-{env}-config-secrets.json` (gitignored):

```json
{
  "client-secret": "oauth-secret-here",
  "az-token": "fallback-bearer-token",
  "api-key": "additional-api-key"
}
```

Secrets are automatically injected with underscore prefix:
- `client-secret` → `config['_client_secret']`
- `az-token` → `config['_az_token']`

## V2.1 Resilience Features

### Rate Limiting
Prevents API bans by throttling requests:
```python
api = create_rest_api(config)  # Rate limiting applied automatically
# Calls throttled to configured calls-per-second
```

### Circuit Breaker
Stops cascade failures when APIs are down:
- Opens after 5 consecutive failures
- Fails fast for 60 seconds
- Attempts to close after timeout

### Async Operations (202 Accepted)
Handles long-running operations transparently:
```python
result = api.post("/long-operation", data)
# Automatically:
# - Detects 202 Accepted response
# - Polls Location header
# - Respects Retry-After header
# - Returns final result when ready
```

### Token Redaction
Logger automatically redacts sensitive data:
```python
logger.info(f"Token: {token}")  # Logs: "Token: Bearer [REDACTED]"
logger.debug(f"Password: {pwd}")  # Logs: "Password: [REDACTED]"
```

## Best Practices

1. **ALWAYS update schema** when changing config structure
2. **Never use `print()`** - Use logger for all output
3. **Never hardcode paths** - Use `get_path()` helper
4. **Always include type hints** - Better IDE support
5. **Pass entire config dict** - Not individual parameters
6. **Use HelpfulError** - Clear, actionable error messages
7. **Hard fail on config** - No silent configuration errors
8. **Log extensively** - DEBUG for details, INFO for milestones

## Common Commands

```bash
# Run the try-me script (start here!)
python src/try-me-script.py demo test

# Run with different org/env
python src/try-me-script.py mycompany prod

# Optional flags
python src/script.py demo test --no-token      # Skip authentication
python src/script.py demo test --debug          # Enable debug logging
python src/script.py demo test --no-validation  # Skip schema validation

# Test all v2.1 features
python src/test_v2_features.py demo test
```

## PyCharm Setup (Recommended)

1. Open project in PyCharm
2. PyCharm auto-detects `pyproject.toml`
3. Let it create virtual environment
4. To run scripts with arguments:
   - Right-click script → Modify Run Configuration
   - Add parameters: `demo test`
   - Click Run

## Troubleshooting

### Config File Not Found
```
❌ Problem: Configuration file 'demo-test-config.json' not found
✅ Solution: Create the file in config/ directory
📝 Example: Copy config/example.json to config/demo-test-config.json
```

### Schema Validation Failed
```
❌ Problem: Configuration doesn't match schema
✅ Solution: Check schemas/org-env-config-schema.json for required fields
📝 Example: Ensure all required sections exist with correct structure
```

### Rate Limit Hit
Enable rate limiting in config to prevent this:
```json
"rate-limiting": {
  "enabled": true,
  "calls-per-second": 5
}
```

## Documentation

- **[In-Depth Guide](in-depth-readme.md)** - Comprehensive pattern documentation
- **[Architecture Decisions](ai/decided/adr-records.md)** - Why we built it this way
- **[Module Dependencies](module-dependency-diagram.md)** - Visual architecture
- **AI Assistance** - Upload `ai/prompts/txo-xml-prompt-v3.1.xml` to Claude

## Migration from v1.x

See [Migration Guide](docs/migration-v1-to-v2.md) for upgrading existing projects.

Key changes in v2.1:
- Config structure is now nested (rate-limiting, circuit-breaker as objects)
- All config access uses hard-fail philosophy
- HelpfulError replaces generic exceptions
- Token redaction is automatic
- Rate limiting and circuit breakers are built-in

## Contributing

1. Follow established patterns
2. **Update JSON schema for ANY config changes**
3. Use HelpfulError for user-facing errors
4. Add type hints and docstrings
5. Test with both test and prod configurations
6. Create ADR for significant changes

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/tentixo/txo-python-template/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tentixo/txo-python-template/discussions)
- **Template Version**: v2.1.0
- **Python Required**: 3.10+ (3.13+ recommended)
