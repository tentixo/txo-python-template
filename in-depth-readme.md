# TXO Python Template - In-Depth Guide

## Overview

This template enforces consistent patterns across all Python scripts that interact with APIs. It's designed for beginners to create production-ready code while following established best practices.

## Core Patterns

### 1. Mandatory Parameters Pattern

Every script requires `org_id` and `env_type` as command-line arguments:

```python
# Always first two arguments
parser.add_argument("org_id", help="Organization identifier")
parser.add_argument("env_type", help="Environment type")
```

This creates predictable file naming:
- Config: `txo-prod-config.json`
- Output: `txo-prod-report_2025-01-15T1430Z.xlsx`

### 2. Configuration Injection Pattern

Configuration and derived values are injected into a single dict:

```python
config = parse_args_and_load_config("Script description")
# Automatically contains:
# config["_org_id"] - from command line
# config["_env_type"] - from command line  
# config["_token"] - from OAuth or secrets file
```

Pass the entire config dict to functions:

```python
# GOOD
def process_data(config: Dict[str, Any]):
    org_id = config["_org_id"]

# BAD
def process_data(org_id: str, env_type: str, token: str):
    pass
```

### 3. Logger-First Pattern

Every module starts with logger setup:

```python
# utils/any_module.py  <- Path comment always first
from utils.logger import setup_logger
logger = setup_logger()

# Then use throughout
logger.info("Processing started")
logger.debug("Detailed information")
logger.error("Error occurred", exc_info=True)
```

Never use print() statements.

### 4. Tuple Context Pattern

URL builders return both URL and logging context:

```python
url, ctx = build_api_url(config, env_id, resource)
logger.info(f"{ctx} Starting API call")
# Logs: [env_id:resource] Starting API call
```

### 5. Error Philosophy Pattern

Different approaches for different data types:

```python
# Configuration data - expect it to exist (hard fail)
tenant_id = config['global']['tenant-id']  # KeyError if missing

# API responses - might be optional (soft fail)
email = response.get('email')  # None if missing
```

### 6. Path Centralization Pattern

Never construct paths manually:

```python
# GOOD
from utils.path_helpers import get_path
config_file = get_path('config', 'settings.json')

# BAD
config_file = Path('config/settings.json')
config_file = 'config/settings.json'
```

### 7. Result Tracking Pattern

Use standardized result tracking:

```python
@dataclass
class ProcessingResults:
    success: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    
    def is_success(self) -> bool:
        return len(self.failed) == 0
```

### 8. Output File Naming Pattern

Output files include organization, environment, and UTC timestamp:

```python
from datetime import datetime, timezone

current_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
filename = f"{config['_org_id']}-{config['_env_type']}-report_{current_utc}.xlsx"
# Creates: txo-prod-report_2025-01-15T1430Z.xlsx
```

## Helper Files Overview

### Core Utilities
- `config_loader.py` - Load and validate configuration
- `logger.py` - Centralized logging setup
- `path_helpers.py` - Path management
- `exceptions.py` - Custom exception classes

### API Utilities
- `api_factory.py` - Create configured API clients
- `rest_api_helpers.py` - REST API operations
- `soap_api_helpers.py` - SOAP API operations
- `oauth_helpers.py` - OAuth authentication

### Data Utilities
- `load_n_save.py` - File I/O operations
- `url_builders.py` - URL construction with context

### Script Utilities
- `script_runner.py` - Standard script initialization
- `concurrency.py` - Parallel processing

## Script Structure Template

```python
# src/my_script.py
"""
Script description here

Usage:
    python my_script.py <org_id> <env_type>
"""

from datetime import datetime, timezone
from typing import Dict, Any

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.api_factory import create_rest_api

logger = setup_logger()
data_handler = TxoDataHandler()

def process_data(config: Dict[str, Any]) -> bool:
    """Main processing logic"""
    api = create_rest_api(config)
    # Your logic here
    return True

def main():
    """Entry point"""
    config = parse_args_and_load_config("Script description")
    
    logger.info(f"Starting process for {config['_org_id']}-{config['_env_type']}")
    
    success = process_data(config)
    
    if success:
        logger.info("✅ Process completed successfully")
    else:
        logger.error("❌ Process failed")
        
if __name__ == "__main__":
    main()
```

## Best Practices

1. **Always validate input** - Check config keys exist
2. **Log extensively** - Use DEBUG for details, INFO for milestones
3. **Handle errors gracefully** - Use try/except with specific exceptions
4. **Document functions** - Include docstrings with type hints
5. **Keep scripts focused** - One main purpose per script
6. **Reuse helpers** - Don't duplicate functionality
7. **Test locally first** - Use test/demo environment

## Common Pitfalls to Avoid

1. Using print() instead of logger
2. Hardcoding paths instead of using path_helpers
3. Passing individual parameters instead of config dict
4. Missing type hints
5. Not validating configuration
6. Constructing URLs manually
7. Ignoring the tuple context pattern

## For More Information

- See `ai/decided/adr-records.md` for architecture decisions
- Upload `ai/prompts/txo-python-template.xml` to AI for assistance
- Check `src/test_github_api.py` for working example