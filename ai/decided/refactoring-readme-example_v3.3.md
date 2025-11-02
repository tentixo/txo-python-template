# TXO Python Template README v3.3

> **⚠️ TEMPLATE DOCUMENT - For Refactoring Workflow**
>
> **Purpose**: Pattern for root README.md during framework refactoring
> **Usage**: Content for users who want to USE this template to CREATE scripts
> **Audience**: Developers using TXO Template to build business scripts
> **Workflow**: Refactoring (ai/prompts/refactoring-ai-prompt_v3.3.md)
>
> **AI Instructions**:
> - This template IS for the framework repository itself
> - Update during done-done phase when refactoring framework
> - Keep version numbers synchronized (v3.3.0 across all docs)
> - Focus on how to USE the template, not internals

---

# TXO Python Template v3.3.0

> **Problem Solved**: Build production-ready Python automation scripts fast with AI-assisted workflow
> **Get Running**: 5 minutes from clone to first script execution

## What This Template Provides

**Before TXO Template**:
- ❌ Scripts break across environments (dev vs prod)
- ❌ Secrets accidentally committed to git
- ❌ Inconsistent logging makes debugging impossible
- ❌ AI generates non-compliant code patterns
- ❌ Manual configuration for every new project

**After TXO Template**:
- ✅ Environment-aware configuration (org-env pattern)
- ✅ Mandatory security patterns (secrets never leak)
- ✅ AI workflow with automatic compliance validation
- ✅ Multi-sheet Excel reports with UTC timestamps
- ✅ Structured logging with AI-friendly debug files

---

## Quick Start (5 Minutes)

### 1. Clone and Setup (1 minute)
```bash
# Clone template
git clone https://github.com/tentixo/txo-python-template.git my-project
cd my-project

# Copy configuration templates
cp config/org-env-config_example.json config/demo-test-config.json
cp config/org-env-config-secrets_example.json config/demo-test-config-secrets.json
```

### 2. Run Demo Script (30 seconds)
```bash
# No authentication needed - demonstrates TXO patterns
PYTHONPATH=. python src/try_me_script.py demo test

# Expected output file:
# output/demo-test-try-me-results_2025-11-01T143022Z.json
```

### 3. Verify TXO Features (30 seconds)
```bash
# Check output file with UTC timestamp
ls -ltr output/demo-test-*

# Check structured log
cat logs/demo-test-try_me_script_*.log
```

---

## Understanding Output Files

TXO scripts generate files with consistent patterns:

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

## Two Workflows: Script Creating vs Refactoring

TXO Template supports two distinct workflows:

### Workflow 1: Script Creating (Most Common)

**Use Case**: Create business automation script using template

**Process**:
1. Clone template to new project
2. Use AI with `ai/prompts/script-ai-prompt-template_v3.3.md`
3. Generate script following TXO patterns
4. **Replace** README.md with script-specific documentation
5. Deploy and run

**README behavior**: REPLACE framework README with script README

**Example**: "Create Salesforce-to-Azure user sync script"

### Workflow 2: Refactoring (Framework Development)

**Use Case**: Improve the template framework itself

**Process**:
1. Work in template repository
2. Use AI with `ai/prompts/refactoring-ai-prompt_v3.3.md`
3. Modify framework (utils/, ADRs, templates)
4. **Update** README.md with new features
5. Commit, tag, push

**README behavior**: UPDATE framework README with improvements

**Example**: "Add ADR-B017 for directory-specific UTC rules"

---

## Creating Your First Script

### Option 1: Manual Development

**Basic script structure**:
```python
from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir

logger = setup_logger()
data_handler = TxoDataHandler()

def main():
    # Load config (org-env pattern)
    config = parse_args_and_load_config("Your script description")

    # Your business logic here
    results = process_data(config)

    # Save with UTC timestamp
    filename = f"{config['_org_id']}-{config['_env_type']}-results.xlsx"
    data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)

if __name__ == "__main__":
    main()
```

**Run your script**:
```bash
PYTHONPATH=. python src/your_script.py mycompany prod
```

### Option 2: AI-Assisted Development (Recommended)

**Use AI prompt template**:
```bash
# Show AI this template
cat ai/prompts/script-ai-prompt-template_v3.3.md

# AI generates TXO-compliant script automatically
# - Follows all ADR patterns
# - Includes error handling
# - Generates documentation
# - Passes compliance validation
```

**Validation**:
```bash
# Check compliance before deployment
PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py
```

---

## Configuration System

### Org-Env Pattern

TXO uses organization-environment pairs for isolation:

**Config files**:
```
config/mycompany-prod-config.json        # Production
config/mycompany-test-config.json        # Testing
config/mycompany-lab-config.json         # Development
```

**Secrets (separate file, gitignored)**:
```
config/mycompany-prod-config-secrets.json
config/mycompany-test-config-secrets.json
```

**Benefits**:
- Same codebase runs in any environment
- Secrets never committed to git
- Clear separation of concerns

### Configuration Structure

**Main config** (`{org}-{env}-config.json`):
```json
{
  "global": {
    "api-base-url": "https://api.example.com",
    "timeout": 30,
    "log-level": "INFO"
  },
  "my-service": {
    "setting1": "value1",
    "setting2": true
  }
}
```

**Secrets** (`{org}-{env}-config-secrets.json`):
```json
{
  "api-key": "your-secret-key",
  "client-id": "your-client-id",
  "client-secret": "your-client-secret"
}
```

---

## Framework Features

### 1. Hard-Fail Configuration (ADR-B003)

**TXO Way**:
```python
# Fail immediately if misconfigured
api_url = config['global']['api-base-url']  # KeyError if missing
```

**Why**: Production errors surface during development, not in production

### 2. Directory-Specific UTC Timestamps (ADR-B017)

**Rules**:
- `Dir.OUTPUT` - MUST use `save_with_timestamp(..., add_timestamp=True)`
- `Dir.TMP` - SHOULD use timestamps
- `Dir.GENERATED_PAYLOADS` - MUST NOT use timestamps (deterministic)

**Example**:
```python
# Output: With UTC timestamp
filename = f"{config['_org_id']}-{config['_env_type']}-report.xlsx"
data_handler.save_with_timestamp(data, Dir.OUTPUT, filename, add_timestamp=True)
# → output/mycompany-prod-report_2025-11-01T143022Z.xlsx

# Payload: Without timestamp (for human validation)
filename = f"{config['_org_id']}-{config['_env_type']}-create-user.json"
data_handler.save(payload, Dir.GENERATED_PAYLOADS, filename)
# → generated_payloads/mycompany-prod-create-user.json
```

### 3. Multi-Sheet Excel Support

**Natural business report structure**:
```python
report_data = {
    "Executive_Summary": summary_df,
    "Detailed_Results": results_df,
    "Error_Analysis": errors_df
}

data_handler.save_with_timestamp(report_data, Dir.OUTPUT, "report.xlsx", add_timestamp=True)
# Automatically creates 3-sheet Excel file
```

### 4. API Factory (ADR-B007)

**Single-line API client creation**:
```python
api_client = create_rest_api(config, "api-name")
# Automatic features:
# - Credential loading from secrets
# - Retry logic with exponential backoff
# - Structured logging of all requests
# - Timeout handling
```

### 5. Structured Logging (ADR-B006)

**Context-aware logging**:
```python
logger.info("Processing complete", extra={
    'users_processed': 100,
    'success_rate': 0.95
})
# Automatically includes: org_id, env_type, timestamp
# Format: JSON for AI parsing
# Security: Credentials automatically redacted
```

---

## Document Versioning and old/ Directories

### How Versioning Works

TXO uses semantic versioning in filenames:
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

### Common Issues

**Issue: Script can't find configuration**
```bash
# Verify file exists and uses correct naming pattern
ls config/{org}-{env}-config.json

# Example: If running "python script.py demo test"
ls config/demo-test-config.json
```

**Issue: Secrets not loading**
```bash
# Check secrets file exists
ls config/{org}-{env}-config-secrets.json

# Verify it's gitignored
git check-ignore config/{org}-{env}-config-secrets.json
# Should output the filename (meaning it's ignored)
```

**Issue: Import errors**
```bash
# Always set PYTHONPATH when running scripts
PYTHONPATH=. python src/your_script.py org env

# Or use module syntax
python -m src.your_script org env
```

**Issue: Output files missing timestamps**
```bash
# Check you're using save_with_timestamp with add_timestamp=True
# See ADR-B017 for directory-specific rules

# Validate compliance
PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py
```

---

## Project Structure

```
txo-python-template/
├── config/                          # Configuration files (org-env pattern)
│   ├── {org}-{env}-config.json              # Main config (checked into git)
│   ├── {org}-{env}-config-secrets.json      # Secrets (gitignored)
│   ├── logging-config.json                  # Logging setup
│   └── log-redaction-patterns.json          # Security patterns
├── src/                             # Your scripts go here
│   ├── try_me_script.py                    # Demo script
│   └── your_script.py                      # Your business scripts
├── utils/                           # TXO framework (DO NOT MODIFY)
│   ├── script_runner.py                    # Orchestration
│   ├── load_n_save.py                      # File operations
│   ├── api_factory.py                      # API client creation
│   ├── logger.py                           # Structured logging
│   └── path_helpers.py                     # Directory management
├── output/                          # Generated files (with UTC timestamps)
├── tmp/                             # Temporary files (gitignored)
├── generated_payloads/              # For human validation (gitignored)
├── payloads/                        # Validated, ready to send
├── logs/                            # Log files (gitignored)
├── data/                            # Input data files
├── tests/                           # Test scripts
├── ai/                              # AI workflow documentation
│   ├── decided/                           # ADRs, standards, references
│   ├── prompts/                           # AI prompt templates
│   ├── reports/                           # Release notes, guides
│   └── working/                           # Temporary working docs
├── README.md                        # This file (framework quick start)
├── in-depth-readme.md               # Framework architecture guide
└── CLAUDE.md                        # AI assistant operating manual
```

---

## Next Steps

### For Script Development
1. Read [CLAUDE.md](CLAUDE.md) - AI development workflow
2. Use [ai/prompts/script-ai-prompt-template_v3.3.md](ai/prompts/script-ai-prompt-template_v3.3.md)
3. See [ai/decided/utils-quick-reference_v3.3.md](ai/decided/utils-quick-reference_v3.3.md) for patterns

### For Framework Understanding
1. Read [in-depth-readme.md](in-depth-readme.md) - Architecture deep dive
2. See [ai/decided/txo-business-adr_v3.3.md](ai/decided/txo-business-adr_v3.3.md) - Business decisions
3. See [ai/decided/txo-technical-standards_v3.3.md](ai/decided/txo-technical-standards_v3.3.md) - Technical patterns

### For Contributing
1. Read [ai/decided/txo-ai-adr_v3.3.md](ai/decided/txo-ai-adr_v3.3.md) - AI workflow patterns
2. Follow refactoring workflow
3. Update documentation during done-done

---

## Version History

### v3.3.0 (2025-11-01)
- Added ADR-B017: Directory-specific UTC timestamp rules
- Split README templates: 2 → 4 (script vs refactoring workflows)
- Added old/ directory pattern documentation
- Enhanced output file pattern explanation

### v3.2.0 (2025-10-29)
- Multi-sheet Excel as default pattern
- Enhanced compliance validation
- AI workflow ADRs (ADR-AI001 through ADR-AI006)

### v3.1.1 (2025-09-28)
- Fixed multi-sheet Excel save logic
- Added comprehensive examples

---

**Version**: v3.3.0
**License**: [Your License]
**Repository**: https://github.com/tentixo/txo-python-template
**Maintainer**: [Your Name/Team]
