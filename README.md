![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
# txo-python-template

**Tentixo's Python template** for directories and helper files (utils/)

## License
Released under the MIT License. See [LICENSE](./LICENSE) for details.

## Table of Contents
1. [Description](#description)
2. [Getting Started](#getting-started)
3. [Dependencies](#dependencies)
4. [Configuration](#configuration)
5. [Initialization](#initialization)
6. [Utilities Overview](#utilities-overview)
7. [General Guidelines](#general-guidelines)
8. [Human Instructions](#human-instructions)
9. [AI Instructions](#ai-instructions)

## Description

* This project structure uses two input parameters:
    * `org_id`: A chosen ORG ID to separate config files needed for multi-organizational code.
    * `env_type`: To separate environments: dev, test, stage, prod, according to your needs.
* You can add a project-specific name for your log naming in `utils/loggger.py` about row 97.
* Active Git-LFS. Add your binary files to `.gitattributes` if not already there.
* Always keep your secrets in a file that ends with `-secrets.json` in `config/` so they are not committed.
* Use `uv` as your package handler.
* Make sure you have set up your developer environment including `.zsch` and `.zprofile`files (se repo `txo-brain-pain`
  for instructions)
* Logging to console is INFO and up, and full logs, DEBUG and up, to file in `logs` directory.

## General Guidelines

1.	Don’t Reinvent the Wheel  
Before writing new helper code, search in utils/. Extend or reuse existing helpers rather than duplicating
functionality.
2. Clear, Human-Friendly Logging  
Use the shared logger everywhere. Log at INFO or DEBUG to file—avoid ad-hoc print() calls.
3. Entry-Point Only  
Reference only public “entry” methods (functions or class methods) in docs or AI prompts. Internal helpers (leading _)
need not be mentioned.
4. Path & Config Handling  
Never manipulate paths directly—always use TxoDataHandler and ConfigLoader, which leverage path_helpers under the hood.
5. Error Handling  
Use custom exceptions from utils/exceptions.py (e.g. ConfigError, APIError) for clearer catch-blocks.
6. Concurrency Patterns  
Use run_parallel_environments() or run_script() from concurrency.py instead of rolling your own threading/process
boilerplate.
7. API Calls  
Always call REST/SOAP via RestAPI/SoapAPI in api_helpers.py—it handles retries, backoff, and error parsing.
8. Saving & Loading Data  
Use TxoDataHandler for file I/O (JSON, CSV, Excel, Pickle). It creates directories and writes atomically.
9. Dependency Management  
Target Python 3.13; install via pyproject.toml (uv). PyCharm will pick this up automatically.


## Human Instructions

* Always add the path and name of any Python file as a comment on the first line: `# utils/load_n_save.py`
* Keep active scripts in `src/` directory
* Always use helper files from `utils/` for
    * Loading config
    * Saving files
    * Handle logging
    * Do API calls. The code handles exceptions → No need to have this in the active scripts
    * Handle concurrent API calls
* If you generated payloads, save them in `generated_payloads/` and send them from `payloads/` directory after
  validation. Remember to move the files `generated_payloads/` → `payloads/` before trying to send the latest version.
* Remember to adapt the JSON Schema file to your main config structure.
* When you (a human developer) need tokens, choose one of two patterns:
  1. Manual Token (Auth Code Flow)
     * Obtain an Azure token via Postman.
     * Add it to your secrets file (`<org_id>-<env_type>-secrets.json`):
       ```json
       {
         "az-token": "ey..."
       }
       ```  
  2. Client Credentials Flow 
     * Us the built-in OAuth helper:
       ```text
       from utils.oauth_client_credentials import OAuthClientCredentials

       oauth = OAuthClientCredentials.from_org_env("txo", "test")
       token = oauth.get_access_token_string()
       ```

## AI Instructions

* Do not use print-use extensive logging.
* Only invoke public helpers from utils/.
* Adhere to DRY principles—prefer clarity over micro-optimizations.
* Include inline docstrings matching this repo’s style.
* Do not assume any behavior not already covered by our helpers (e.g., path resolution, logging, configuration loading).


## Project Structure

Tentixo's project structure with explanation of directories and files.

```
example-project/
    ├── config/             # Config files for logger and <org_id>-<env_type>-config and <org_id>-<env_type>-config-secrets.json 
    │   ├── logging-config.json                       # Tentixo's default logging config
    │   ├── <org_id>-<env_typoe>-config.json          # Naming convention of config files. Input parameters org_id and env_type
    │   └── <org_id>-<env_typoe>-config-secrets.json  # As above but for passwords and credentials. Pattern in .gitignore
    ├── data/               # Input files (especially designed for the project)
    ├── files/              # General file directory (default downloaded files)
    ├── generated_payloads/ # For drafts and intermediate payloads; move to payloads/ after validation.  
    │   └── .gitignore        # To block check-in of this content
    ├── logs/               # Log files
    │   └── .gitignore        # To block check-in of this content
    ├── output/             # Output files
    ├── payloads/           # Payload files to be sent to API. Moved here from generated_payload/
    ├── prompts/            # Project context for AI
    ├── schemas/            # Schemas for config files validation (not schemas for edi_parser)
    │   └── org-env-config-schema.json        # Schema file for main config file for all org_id and env_type.
    ├── src/                # Source code, main scripts
    └── utils/              # Helper files
        ├── api_helpers.py    # API helper for REST and SOAP
        ├── concurrency.py    # To handle concurrent API calls
        ├── config_loader.py  # To load config data and config-secrets
        ├── exceptions.py     # Exception handling for API calls
        ├── load_n_save.py    # To load and save need files
        ├── logger.py         # Txo default logger: INFO to conssole, DEBUG to file (logs/)
        ├── oauth_client_credentials.py  # Auto token retriever for Client Credential flow
        └── path_helpers.py   # Helper to find and save in the correct directory
```

---

## Utilities Overview

### `utils/api_helpers.py`

**Purpose:** API helper for REST and SOAP calls, with retries and error handling.  
**Entry Functions:**

- `soap_error_handler`
- `retry_api_call`

**Entry Classes & Methods:**

- **`RestAPI`**: `from_headers`, `get`, `post`, `patch`, `put`, `delete`
- **`SoapAPI`**: `from_headers`, `reinitialize`, `get_client`, `read`, `read_multiple`, `create`, `update`, `delete`,
  `patch`, `fetch_key_for_api`
- **`BusinessCentralErrorClassifier`**: `classify_error`, `create_business_exception`
- **`SOAPFaultDetector`**: `detect_fault_in_response`
- **`APIResponse`**: `success`, `to_exception`

---

### `utils/concurrency.py`

**Purpose:** Utilities for running tasks in parallel environments or threads.  
**Entry Functions:**

- `run_parallel_environments`
- `run_script`
- `load_bc_config`

_No entry classes (only internal helpers)._

---

### `utils/config_loader.py`

**Purpose:** Load and validate configuration files and headers.  
**Entry Functions:**

- `get_config_loader`
- `load_config_and_headers`

**Entry Class & Methods:**

- **`ConfigLoader`**:
    - `config_filename`
    - `secrets_filename`
    - `validate_schema`
    - `load`
    - `get_token`
    - `get_headers`
    - `get_cb_user_password`
    - `get_oauth_tenant_id`
    - `get_oauth_client_id`
    - `get_oauth_client_secret`
    - `get_oauth_scope`

---

### `utils/exceptions.py`

**Purpose:** Custom exception types and structured error context.  
**Entry Class & Methods:**

- **`ErrorContext`**: `to_dict`

_No entry functions._

---

### `utils/load_n_save.py`

**Purpose:** Load and save various data formats (JSON, CSV, Excel, Pickle).  
**Entry Class & Methods:**

- **`TxoDataHandler`**:
    - `load_mapping_sheet`
    - `load_vat_config`
    - `load_json`
    - `load_excel`
    - `load_package`
    - `save`

_No entry functions._

---

### `utils/logger.py`

**Purpose:** Configure structured logging (console + file).  
**Entry Function:**

- `setup_logger`

**Entry Classes & Methods:**

- **`ContextFilter`**: `filter`
- **`SafeFormatter`**: `format`
- **`TxoDefaultLogger`**: `set_context`, `debug`, `info`, `warning`, `error`, `critical`

---

### `utils/oauth_client_credentials.py`

**Purpose:** OAuth 2.0 flows (manual tokens & client credentials).  
_No entry functions._

**Entry Classes & Methods:**

- **`OAuthClientCredentials`**: `from_config_loader`, `from_org_env`, `get_token`, `get_access_token_string`,
  `get_headers`, `invalidate_cache`, `get_token_info`
- **`TokenResponse`**: `is_expired`, `bearer_token`, `to_headers`

---

### `utils/path_helpers.py`

**Purpose:** Resolve and manage project directory paths.  
**Entry Functions:**

- `get_path`
- `set_project_root`

**Entry Class & Methods:**

- **`ProjectPaths`**: `init`, `ensure_dirs`

---

## Getting Started

1. Clone this repository.
2. See [Tentixo’s `txo-brain-pain` repo](https://github.com/tentixo/txo-brain-pain) for environment setup, including
   `.zshrc`, `.zprofile`, and `uv` installation.

---

## Dependencies

- **Python 3.13**
- Install via `pyproject.toml` (uv). PyCharm will auto-detect this—**do not** edit `requirements.txt` directly.

---

## Configuration

Place your config files in a `config/` folder at the project root:

- **Public config**: `<org_id>-<env_type>.json`  
  (e.g. `txo-test-config.json`)
- **Secrets**: `<org_id>-<env_type>-secrets.json`  
  (e.g. `txo-test-secrets.json`)

The filename indicates which JSON Schema (`org-env-config-schema.json`) it must conform to.

---

## Initialization

At the top of every module, initialize core helpers:

```python
from utils.logger import setup_logger
from utils.load_n_save import TxoDataHandler

logger = setup_logger()
data_handler = TxoDataHandler()