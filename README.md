# txo-python-template

![Python 3.13](https://img.shields.io/badge/python-3.13-blue)

**Tentixo's Python template** for API automation and data processing scripts

## License

Released under the MIT License. See [LICENSE](./LICENSE) for details.

## Table of Contents

- [Quick Start](#quick-start)
- [Description](#description)
- [Project Structure](#project-structure)
- [General Guidelines](#general-guidelines)
- [Naming Convention](#naming-convention)
- [Getting Started](#getting-started)
- [Dependencies](#dependencies)
- [Configuration](#configuration)

## Quick Start

### Option A: AI-Assisted Development (5 minutes)
1. Upload `ai/prompts/txo-python-template.xml` to your AI assistant
2. Describe what you want to build
3. Get working code following TXO patterns

### Option B: Run Test Script (2 minutes)
```bash
# Clone template
git clone https://github.com/tentixo/txo-python-template.git
cd txo-python-template

# Install dependencies with uv
uv pip install -r pyproject.toml

# Run test script (no authentication needed)
python src/test_github_api.py demo test

# Check output
ls output/
```

## Description

This template provides a standardized structure for Python scripts that interact with APIs. Key features:

* **Dual parameter system**: Uses `org_id` and `env_type` to separate configurations for multi-organizational code
* **Automatic file organization**: Input/output files are prefixed with org_id-env_type
* **Built-in logging**: INFO to console, DEBUG to file in `logs/` directory
* **Helper utilities**: Reusable functions for API calls, file I/O, configuration management
* **Git-LFS ready**: Binary files handled properly with `.gitattributes`
* **Secrets management**: Secrets kept in `-secrets.json` files (gitignored)

## Project Structure

```
txo-python-template/
├── config/             # Configuration files
│   ├── logging-config.json
│   ├── <org_id>-<env_type>-config.json
│   ├── <org_id>-<env_type>-config-secrets.json      # gitignored
│   └── <org_id>-<env_type>-config-secrets_example.json
├── data/               # Project-specific input files
├── files/              # General file directory
├── generated_payloads/ # Draft payloads (validate before use)
│   └── .gitignore
├── logs/               # Log files
│   └── .gitignore
├── output/             # Generated output files
├── payloads/           # Validated payloads ready to send
├── ai/                 # AI assistance files
│   ├── prompts/        # AI prompt files
│   └── decided/        # Architecture decisions
├── schemas/            # JSON schema validation files
├── src/                # Main scripts
│   └── test_github_api.py
└── utils/              # Helper files
```

## General Guidelines

1. **Don't Reinvent the Wheel** - Check utils/ before writing new helpers
2. **Logger First** - Always use logger, never print()
3. **Configuration Injection** - Pass config dict, not individual parameters
4. **Path Management** - Use path_helpers, never construct paths manually
5. **Error Handling** - Use custom exceptions from utils/exceptions.py
6. **API Patterns** - Use api_factory to create clients
7. **File I/O** - Use TxoDataHandler for all file operations
8. **Type Hints** - Always include type hints
9. **Validation** - JSON schemas for all config files
10. **Documentation** - Create docs before coding

## Naming Convention

* Python files: `snake_case.py`
* JSON config files: `kebab-case.json`
* Markdown files: `kebab-case.md`
* Output files: `{org_id}-{env_type}-{purpose}_{UTC}.{ext}`

## Getting Started

1. Clone this repository
2. Install Python 3.13+
3. Install uv package manager
4. Run `uv pip install -r pyproject.toml`
5. Try the test script: `python src/test_github_api.py demo test`
6. Read [in-depth-readme.md](in-depth-readme.md) for detailed patterns

## Dependencies

- Python 3.13+
- See `pyproject.toml` for package dependencies
- Use `uv` as package manager

## Configuration

Configuration files go in `config/` directory:
- Main config: `{org_id}-{env_type}-config.json`
- Secrets: `{org_id}-{env_type}-config-secrets.json`
- Schema validation: `schemas/org-env-config-schema.json`