# TXO Python Template v3.1.1

> **Problem Solved**: Consistent, secure, production-ready Python automation with AI-assisted development workflow
> **Get Running**: 5 minutes from clone to first script execution

## What This Solves

**Before TXO Template**:
- ❌ Scripts break across environments (dev vs prod)
- ❌ Secrets accidentally committed to git
- ❌ Inconsistent logging makes debugging impossible
- ❌ AI generates non-compliant code patterns

**After TXO Template**:
- ✅ Consistent behavior across all environments
- ✅ Mandatory security patterns (never leak tokens)
- ✅ AI workflow with automatic compliance validation
- ✅ Multi-sheet Excel reports with UTC timestamps

---

## Quick Start (5 Minutes)

### 1. Setup Configuration (30 seconds)
```bash
# Copy configuration templates
cp config/org-env-config_example.json config/demo-test-config.json
cp config/org-env-config-secrets_example.json config/demo-test-config-secrets.json

# Templates work as-is for demo scripts!
```

### 2. Run Your First Script (30 seconds)
```bash
# No authentication needed - demonstrates TXO patterns
PYTHONPATH=. python src/try_me_script.py demo test

# Expected output file:
# output/demo-test-github_repos_2025-09-28T123456Z.json
```

### 3. Verify Multi-Sheet Excel Support (1 minute)
```python
# Test multi-sheet Excel with UTC timestamps
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir
import pandas as pd

sheets = {
    "Summary": pd.DataFrame({"metric": ["success"], "count": [10]}),
    "Details": pd.DataFrame({"item": ["test"], "status": ["ok"]})
}

data_handler = TxoDataHandler()
path = data_handler.save_with_timestamp(sheets, Dir.OUTPUT, "test.xlsx", add_timestamp=True)
# Creates: test_2025-09-28T123456Z.xlsx with 2 sheets
```

---

## Usage

### Basic Script Execution
```bash
# PyCharm (recommended)
# Use Run Configuration with parameters: demo test

# Command line
PYTHONPATH=. python src/your_script.py org_id env_type

# Examples
PYTHONPATH=. python src/try_me_script.py demo test
PYTHONPATH=. python src/my_script.py mycompany prod
```

### AI-Assisted Development
```bash
# Generate TXO-compliant scripts using enhanced AI workflow
# 1. Use ai/prompts/ai-prompt-template_v3.1.1.md
# 2. Follow 8-phase validation process
# 3. Run compliance check: PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py
```

---

## Configuration Overview

### Required Files
```bash
config/
├── {org}-{env}-config.json           # Main settings
├── {org}-{env}-config-secrets.json   # API keys (gitignored)
├── logging-config.json               # Logging setup
└── log-redaction-patterns.json       # Security patterns
```

### Basic Configuration Structure
```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "timeout-seconds": 30
  },
  "script-behavior": {
    "rate-limiting": {"enabled": false, "calls-per-second": 10}
  }
}
```

**Full configuration options**: See [in-depth-readme.md](in-depth-readme.md)

---

## Output Contract

### File Naming Convention
- **With timestamps**: `filename_2025-09-28T123456Z.extension`
- **Without timestamps**: `filename.extension`
- **Multi-sheet Excel**: Dict of DataFrames → Multiple sheets automatically

### Expected Output Locations
```bash
output/          # Generated reports and data files
logs/           # Execution logs with token redaction
```

---

## Logging Contract

### Key Log Messages
```bash
# Success indicators
✅ All 150 operations successful: 75 created, 75 updated
✅ Saved 10 repositories to: output/report_2025-09-28T123456Z.json

# External API context (when applicable)
[BC-Prod/Contoso/CustomerAPI] Retrieved 150 customers

# Simple local operations
Processing customer data from CSV
```

---

## ProcessingResults Summary

### Success Examples
```bash
✅ All 150 operations successful: 75 created, 75 updated
✅ Completed with warnings: 145 successful, 5 skipped (expected)
```

### Failure Examples
```bash
❌ Completed with 10 failures: 140 created, 10 failed
❌ Configuration error: Missing required field 'api-base-url'
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Config file not found` | Copy example files from `config/` directory |
| `Invalid category 'output'` | Use `Dir.OUTPUT` instead of `'output'` string |
| `Import error: cannot import Dir` | Use `PYTHONPATH=.` when running from command line |
| `TXO compliance violations` | Run `PYTHONPATH=. python utils/validate_tko_compliance.py src/script.py` |

---

## When You Need More

- **Architecture & Customization**: [in-depth-readme.md](in-depth-readme.md)
- **Function Reference**: `ai/decided/utils-quick-reference_v3.1.md`
- **AI Development Workflow**: `ai/prompts/ai-prompt-template_v3.1.1.md`
- **Architecture Decisions**: `ai/decided/txo-business-adr_v3.1.md`

---

**Version:** v3.1.1
**Last Updated:** 2025-09-28
**Domain:** TXO Framework
**Purpose:** 15-minute success for new developers