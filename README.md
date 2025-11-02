# Txo Python Template v3.3.0

> **Problem Solved**: Consistent, secure, production-ready Python automation with AI-assisted development workflow  
> **Get Running**: 5 minutes from GitHub template to first script execution in PyCharm  

## What This Solves

**Before Txo Template**:

- ❌ Scripts break across environments (dev vs prod)
- ❌ Secrets accidentally committed to git
- ❌ Inconsistent logging makes debugging impossible
- ❌ AI generates non-compliant code patterns

**After Txo Template**:

- ✅ Consistent behavior across all environments
- ✅ Mandatory security patterns (never leak tokens)
- ✅ AI workflow with automatic compliance validation
- ✅ Multi-sheet Excel reports with UTC timestamps

---

## Getting Started from GitHub

### Step 1: Create Your Project (1 minute)

**On GitHub**:

1. Navigate to [txo-python-template](https://github.com/tentixo/txo-python-template)
2. Click green **"Use this template"** button (top right, requires login)
3. Choose **"Create a new repository"**
4. Fill in:
   - **Repository name**: `my-automation-scripts` (your choice)
   - **Description**: (optional)
   - **Public/Private**: Your preference
5. Click **"Create repository"**

**Result**: You now have your own copy to customize freely!

### Step 2: Open in PyCharm (1 minute)

**Two options**:

**Option A: Clone in PyCharm** (Recommended for beginners):

1. Open PyCharm
2. **File** → **New** → **Project from Version Control**
3. Paste your repository URL: `https://github.com/YOUR-USERNAME/my-automation-scripts`
4. Choose local directory
5. Click **Clone**

**Option B: GitHub Desktop** (If you use it):

1. Click green **"Code"** button on GitHub
2. **Open with GitHub Desktop**
3. Clone to local folder
4. **File** → **Open** in PyCharm → Select cloned folder

---

## Quick Start in PyCharm (5 Minutes)

### 1. Setup Configuration Files (30 seconds)

**In PyCharm Project Explorer**:

1. Expand **config/** folder
2. Right-click **`org-env-config_example.json`** → **Copy**
3. Right-click **config/** folder → **Paste**
4. Name it: `demo-test-config.json`
5. Repeat for **`org-env-config-secrets_example.json`** → `demo-test-config-secrets.json`

**Why these names?**

- `demo` = organization ID (Txo pattern: identifies which company/team)
- `test` = environment type (Txo pattern: dev/test/prod)
- Pattern: `{org-id}-{env-type}-config.json` (MANDATORY in Txo)

**Result**: Templates work as-is for demo scripts!

### 2. Run Your First Script (1 minute)

**In PyCharm**:

1. Open `src/try_me_script.py` in editor
2. **Right-click** anywhere in the file
3. Select **"Modify Run Configuration..."**
4. In **Parameters** field, enter: `demo test`
   - `demo` = org_id (matches config file name)
   - `test` = env_type (matches config file name)
5. Click **OK**
6. Click green **▶ Run** button (top right)

**Expected results**:

```
✅ Successfully fetched 30 repositories from GitHub API
✅ Saved to: output/demo-test-github-repos_2025-11-02T143022Z.json
```

**What you learned**:

- ✅ Txo scripts require **org_id** and **env_type** (hard-fail, no defaults)
- ✅ Configuration files must match: `{org-id}-{env-type}-config.json`
- ✅ Output files include org-env in name: `demo-test-*.json`

### 3. Verify Output File (30 seconds)

**In PyCharm Project Explorer**:

1. Expand **output/** folder
2. Find file: `demo-test-github-repos_TIMESTAMP.json`
3. Double-click to open
4. See JSON data from GitHub API

**Txo Pattern**: Every run creates timestamped file (no overwrites)

### 4. Optional: Test Multi-Sheet Excel (2 minutes)

**Open Python Console in PyCharm** (bottom toolbar):

```python
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir
import pandas as pd

sheets = {
    "Summary": pd.DataFrame({"metric": ["success"], "count": [10]}),
    "Details": pd.DataFrame({"item": ["test"], "status": ["ok"]})
}

data_handler = TxoDataHandler()
path = data_handler.save_with_timestamp(sheets, Dir.OUTPUT, "test.xlsx", add_timestamp=True)
print(f"Created: {path}")
```

**Result**: `output/test_2025-11-02T143022Z.xlsx` with 2 sheets

---

## Advanced: Command Line Usage

**For experienced developers** who prefer terminal:

### Running Scripts via Command Line

```bash
# Requires PYTHONPATH set (tells Python where to find utils/)
PYTHONPATH=. python src/try_me_script.py demo test

# With your own config
PYTHONPATH=. python src/your_script.py mycompany prod
```

### Setup Configuration via Command Line

```bash
# Copy templates
cp config/org-env-config_example.json config/demo-test-config.json
cp config/org-env-config-secrets_example.json config/demo-test-config-secrets.json
```

**Note**: PyCharm handles PYTHONPATH automatically - beginners should use PyCharm workflow above.

### AI-Assisted Development

```bash
# Generate Txo-compliant scripts using enhanced AI workflow
# 1. Use ai/prompts/script-ai-prompt-template_v3.3.md
# 2. Follow 8-phase validation process
# 3. Run compliance check: PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py
```

---

## Updating Dependencies

### Check for Updates
```bash
# See what packages have newer versions available
uv pip list --outdated
```

### Update Packages (Updates pyproject.toml automatically)
```bash
# Update a single package
uv remove pandas && uv add pandas

# Update multiple packages at once (recommended before releases)
uv remove jsonschema && uv add jsonschema && \
uv remove pandas && uv add pandas && \
uv remove pyyaml && uv add pyyaml && \
uv remove xai-sdk && uv add xai-sdk

# Verify everything still works
uv sync
python -c "import jsonschema; import pandas; import yaml; import xai_sdk; print('✅ All imports successful')"
```

**What happens**:
- `uv remove` uninstalls the package
- `uv add` installs latest version AND updates `pyproject.toml` with new `>=` constraint
- Example: `pandas>=2.3.0` becomes `pandas>=2.3.3`

**When to update**:
- Before major releases (like v3.3.0)
- When security updates are available
- After adding new features that need newer package versions

**PyCharm users**: Open Terminal (bottom toolbar) and run these commands

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
    "rate-limiting": {
      "enabled": false,
      "calls-per-second": 10
    }
  }
}
```

**Full configuration options**: See [in-depth-readme.md](in-depth-readme.md)

---

## Understanding Output Files

Txo scripts generate files with consistent patterns:

### Filename Pattern

```
{org-id}-{env-type}-{description}_{UTC-timestamp}.{extension}
```

### Where Files Go

| Directory             | UTC Timestamp? | Purpose                  | Example                                    |
|-----------------------|----------------|--------------------------|--------------------------------------------|
| `output/`             | ✅ Always       | Final results, reports   | `demo-test-report_2025-11-01T143022Z.xlsx` |
| `tmp/`                | ✅ Usually      | Temporary files          | `demo-test-cache_2025-11-01T143022Z.json`  |
| `generated_payloads/` | ❌ Never        | For human validation     | `demo-test-create-user.json`               |
| `payloads/`           | ❌ Never        | Validated, ready to send | `demo-test-create-user.json`               |
| `logs/`               | ✅ Always       | Debug logs               | `demo-test-script_2025-11-01T143022Z.log`  |

**Why timestamps?**

- Each run creates unique file (no overwrites)
- Easy to find results from specific runs
- Debugging: "Check output from your 2pm run"

**Why no timestamps for payloads?**

- Human validation workflow requires stable filenames
- Always use latest version (overwrites intentionally)

### Finding Your Files

```bash
# Latest output for org-env
ls -t output/demo-test-* | head -1

# All outputs from today
ls output/*2025-11-01*
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

## Document Versioning and old/ Directories

### How Versioning Works

Txo uses semantic versioning in filenames:

- `txo-business-adr_v3.3.md` - Current version
- `utils-quick-reference_v3.3.md` - Current version

### old/ Directory Pattern (ADR-AI002)

**What**: When documents are superseded, old versions move to `old/` subdirectories

**Locations**:

```
ai/old/                  # Superseded working documents
ai/decided/old/          # Superseded ADRs and templates
ai/prompts/old/          # Superseded prompt templates
ai/reports/old/          # Superseded reports
```

**Manual workflow**:

```bash
# When v3.4 is created, user archives v3.3
mkdir -p ai/decided/old
mv ai/decided/utils-quick-reference_v3.2.md ai/decided/old/
```

**AI behavior**: AI assistants automatically ignore `**/old/` directories unless explicitly instructed

**Why**: Keeps workspace clean while preserving history for reference

---

## Troubleshooting

### PyCharm-Specific Issues

**"Parameters field is empty after restart"**

- PyCharm doesn't save parameters if you just type them once
- Must use **"Modify Run Configuration..."** (as shown in Quick Start Step 2)
- Saved configurations persist across PyCharm restarts

**"Script runs but says 'Config file not found'"**

- Check file is named exactly: `demo-test-config.json` (not `demo-testconfig.json`)
- Check file is in `config/` folder (not root or src/)
- Parameters must match filename: If file is `mycompany-prod-config.json`, parameters should be `mycompany prod`

**"ModuleNotFoundError: No module named 'utils'"**

- In PyCharm: This shouldn't happen (auto-configured)
- If it does: **File** → **Settings** → **Project** → **Project Structure** → Mark project root as "Sources Root"

**"Import error: pandas, openpyxl, requests"**

- Open PyCharm **Terminal** (bottom toolbar)
- Run: `pip install -r requirements.txt` (or `uv pip install -r pyproject.toml`)

### General Issues

| Problem                           | Solution                                                                     |
|-----------------------------------|------------------------------------------------------------------------------|
| `Config file not found`           | Copy example files from `config/` directory (see Quick Start Step 1)         |
| `Invalid category 'output'`       | Use `Dir.OUTPUT` instead of `'output'` string                                |
| `Import error: cannot import Dir` | Use `PYTHONPATH=.` when running from command line (PyCharm users: see above) |
| `Txo compliance violations`       | Run `PYTHONPATH=. python utils/validate_tko_compliance.py src/script.py`     |

---

## When You Need More

- **Architecture & Customization**: [in-depth-readme.md](in-depth-readme.md)
- **Function Reference**: `ai/decided/utils-quick-reference_v3.3.md`
- **AI Development Workflow**: `ai/prompts/script-ai-prompt-template_v3.3.md`
- **Architecture Decisions**: `ai/decided/txo-business-adr_v3.3.md`

---

**Version:** v3.3.0
**Last Updated:** 2025-11-02
**Domain:** Txo Framework
**Purpose:** 15-minute success for new developers