# txo-python-template

![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![PyCharm](https://img.shields.io/badge/IDE-PyCharm-green)

**Tentixo's Python Template** - Production-ready framework for REST/OData API automation and data processing scripts with built-in best practices and error handling.

> **Note**: This template is for REST/OData APIs only. Contact Morre if you need SOAP support.

## Quick Start

### Step 1: Create Your Repository

**On GitHub:**
1. Click the green **"Use this template"** button above
2. Select **"Create a new repository"**
3. Name your repository (e.g., `my-api-integration`)
4. Clone your new repository locally

**Or clone directly:**
```bash
git clone https://github.com/tentixo/txo-python-template.git
cd txo-python-template
```

### Step 2: Setup Development Environment

This template is optimized for **PyCharm** - we recommend using it for the best experience.

**PyCharm Setup (Recommended):**
1. Open the project in PyCharm
2. PyCharm will automatically detect `pyproject.toml`
3. When prompted, let PyCharm create a virtual environment and install dependencies
4. If not prompted: Go to Settings → Project → Python Interpreter → Add Interpreter

**Manual Setup with uv:**
```bash
# Install uv if you haven't already
pip install uv

# Install dependencies
uv pip install -r pyproject.toml
```

### Step 3: Choose Your Organization and Environment

The template uses two key parameters for all scripts:
- **`org_id`**: Organization identifier (e.g., "acme", "demo", "mycompany")
- **`env_type`**: Environment type (e.g., "test", "prod", "dev")

These parameters ensure:
- Configuration files are properly separated: `acme-test-config.json` vs `acme-prod-config.json`
- Output files are clearly identified: `acme-test-report_2025-01-15.xlsx`
- Multiple organizations can use the same codebase

### Step 4: Run the Test Script

**Using PyCharm (Recommended):**
1. Right-click on `test_github_api.py` in the `src/` folder
2. Select **More Run/Debug → Modify Run Configuration...**
3. In **Script parameters** field, enter your chosen org_id and env_type (e.g., `demo test`)
4. Click **OK**
5. Click the green **Run** button (▶) in the top toolbar

**Using Command Line:**
```bash
# Run with your chosen org_id and env_type
python src/test_github_api.py demo test

# This will:
# 1. Create a config file requirement (follow the error message to create it)
# 2. Fetch data from GitHub's public API
# 3. Save results to output/demo-test-github_repos_*.json
```

## Getting Started - Recommended Reading Path

After the Quick Start, follow this learning path:

1. **Read this README completely** - Understand the structure and patterns
2. **Read [in-depth-readme.md](in-depth-readme.md)** - Learn all patterns in detail
3. **Read [Architecture Decision Records](ai/decided/adr-records.md)** - Understand why we built it this way
4. **Upload AI prompt to Claude** - Use `ai/prompts/txo-python-template-v3.0.xml` for AI assistance

## Troubleshooting with AI

When debugging issues with AI assistance, follow these steps for best results:

### 1. Generate Clean Debug Logs
Since we always have `debug` level logging to file, you have a lot of useful information in the file.
```bash
# Delete old log files to reduce noise
rm logs/*.log

# Run your failing script again
python src/your_script.py demo test

# The new log file will contain only relevant debug information
```

### 2. Provide Context to AI
Upload to the AI:
- The fresh log file from `logs/`
- Your script that's failing
- The specific error message
- Your config file (remove secrets first)

### 3. Common Issues to Check First
Before asking AI, verify:
- Config file exists: `config/{org_id}-{env_type}-config.json`
- Required keys are in config (check against schema)
- API endpoint is accessible (test with curl/Postman)
- Token is valid (check expiration)
- Output directory exists and is writable

### 4. Improving Debug Information
Add strategic debug logging to identify issues:
```python
# Log the actual values being used
logger.debug(f"API URL: {url}")
logger.debug(f"Headers: {headers}")
logger.debug(f"Payload size: {len(str(payload))} chars")

# Log before and after critical operations
logger.debug("About to call API...")
response = api.get(url)
logger.debug(f"API returned status: {response.status_code}")

# Log data transformations
logger.debug(f"Input records: {len(input_data)}")
logger.debug(f"After filtering: {len(filtered_data)}")
```

### 5. Error Pattern Recognition
The AI can better help if you identify the pattern:
- **ConfigurationError**: Missing or invalid config
- **ApiAuthenticationError**: Token/credential issues
- **ApiTimeoutError**: Network or performance issues
- **HelpfulError**: Already contains the solution
- **KeyError**: Missing required config key

### 6. Minimal Reproducible Example
Create a minimal script that reproduces the issue:
```python
# src/debug_test.py
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.api_factory import create_rest_api

logger = setup_logger()

def main():
    config = parse_args_and_load_config("Debug test")
    logger.debug(f"Config loaded: {list(config.keys())}")
    
    # Add only the failing operation
    api = create_rest_api(config)
    result = api.get("https://api.example.com/test")
    logger.info(f"Result: {result}")

if __name__ == "__main__":
    main()
```

## Project Structure

```
txo-python-template/
├── ai/                     # AI assistance files
│   ├── decided/            # Architecture Decision Records (ADRs) and finished AI reports
│   ├── prompts/            # AI prompt templates
│   └── reports/            # AI reports good but not finished
├── config/                 # Configuration files
│   ├── logging-config.json
│   └── {org}-{env}-config.json
├── data/                   # Input data files
├── files/                  # General files
├── generated_payloads/     # Draft payloads (validate before use)
├── logs/                   # Log files (gitignored)
├── output/                 # Generated output files
├── payloads/              # Validated payloads ready to send
├── schemas/               # JSON schemas for validation
├── src/                   # Main scripts
│   └── test_github_api.py
├── tmp/                   # Temporary files (gitignored)
├── utils/                 # Helper modules
│   ├── api_common.py      # Rate limiting, circuit breaker
│   ├── api_factory.py     # API client creation
│   ├── concurrency.py     # Parallel processing
│   ├── config_loader.py   # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   ├── load_n_save.py     # File I/O operations
│   ├── logger.py          # Logging setup
│   ├── oauth_helpers.py   # OAuth 2.0 support
│   ├── path_helpers.py    # Path management
│   ├── rest_api_helpers.py # REST client
│   ├── script_runner.py   # Script initialization
│   └── url_helpers.py     # URL construction
└── wsdl/                  # WSDL files (if needed)
```

## Core Patterns

### Standard Script Structure
```python
# src/my_script.py
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config

logger = setup_logger()

def main():
    config = parse_args_and_load_config("My script description")
    logger.info(f"Starting {config['_org_id']}-{config['_env_type']}")
    # Your code here

if __name__ == "__main__":
    main()
```

### Error Handling with HelpfulError
```python
from utils.exceptions import HelpfulError

raise HelpfulError(
    what_went_wrong="Config file 'settings.json' not found",
    how_to_fix="Create the file in config/ directory",
    example="See config/example.json for format"
)
```

## Configuration

### Basic Config Structure

**Important**: When you modify configuration structure, you MUST update the JSON Schema in `schemas/org-env-config-schema.json` to match your changes.

```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "tenant-id": "your-tenant",
    "client-id": "your-client-id",
    "oauth-scope": "https://api.example.com/.default"
  },
  "script-behavior": {
    "enable-rate-limiting": true,
    "rate-limit-per-second": 10,
    "api-timeouts": {
      "rest-timeout-seconds": 60,
      "max-retries": 3
    }
  }
}
```

### Secrets File (gitignored)
```json
{
  "client-secret": "your-oauth-secret",
  "az-token": "fallback-bearer-token"
}
```

## Architecture Decision Records (ADRs)

We use ADRs to document important architecture decisions. ADRs help:
- Understand why certain patterns were chosen
- Maintain consistency across the codebase
- Onboard new developers faster
- Avoid repeating past mistakes

Read our ADRs in [ai/decided/adr-records.md](ai/decided/adr-records.md)

When making significant changes, create a new ADR following the template in the file.

## Dependencies

### Core Requirements
- Python 3.13+
- jsonschema - Configuration validation
- openpyxl - Excel support
- pandas - Data manipulation
- python-dotenv - Environment variables
- requests - HTTP client

### Optional Extensions
- tenacity - Advanced retry patterns
- tqdm - Progress bars
- zeep - SOAP support (not included by default)

## Best Practices

1. **Never use `print()`** - Always use logger
2. **Never hardcode paths** - Use `get_path()` helper
3. **Always include type hints** - Better IDE support
4. **Pass config dict** - Not individual parameters
5. **Use HelpfulError** - Clear error messages
6. **Update JSON schemas** - When changing config structure
7. **Log extensively** - DEBUG for details, INFO for milestones

## Key Commands

```bash
# Run any script with org_id and env_type
python src/script_name.py <org_id> <env_type>

# With optional flags
python src/script_name.py txo prod --no-token    # Skip authentication
python src/script_name.py txo test --debug        # Enable debug logging
python src/script_name.py txo dev --no-validation # Skip schema validation
```

## Future Development

- Unit tests for helper modules
- Integration tests for API clients
- Performance benchmarks for parallel processing
- Additional API authentication methods
- GraphQL support

## Contributing

1. Follow the established patterns
2. Add type hints and docstrings
3. Use HelpfulError for user-facing errors
4. Update JSON schemas when changing config
5. Create ADRs for significant changes
6. Test with both test and prod configurations

## License

Released under the MIT License. See [LICENSE](./LICENSE) for details.

## Support

- **REST/OData Issues**: Open an issue on GitHub
- **SOAP Support**: Contact Morre directly
- **General Questions**: Check the in-depth documentation first

## Links

- [Tentixo GitHub](https://github.com/tentixo)
- [Issue Tracker](https://github.com/tentixo/txo-python-template/issues)
- [Architecture Decisions](ai/decided/adr-records.md)