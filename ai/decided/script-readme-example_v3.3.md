# [Script Name] README Template v3.3

> **⚠️ TEMPLATE DOCUMENT - For Script Creating Workflow**
>
> **Purpose**: Pattern for AI to generate script-specific README.md
> **Usage**: Copy structure, replace ALL [placeholders] with actual script details
> **Not For**: Documenting the TXO Template framework itself
> **Audience**: Users who want to USE the script (15-minute quick start)
> **Workflow**: Script Creating (ai/prompts/script-ai-prompt-template_v3.3.md Phase 7)
>
> **AI Instructions**:
> - Replace [Script Name], [Business Problem], [API/Service Names], etc.
> - Focus on THIS SCRIPT'S functionality, not TXO framework
> - Assume user already has TXO environment set up
> - Keep it concise: 15 minutes from reading to running

---

# [Script Name]

> **Problem Solved**: [One-sentence description of what business problem this script solves]
> **Get Running**: 15 minutes from setup to first execution

## What This Script Does

**Business Problem**:
[Describe the specific business problem - e.g., "Manual user provisioning takes 2 hours per user"]

**This Script's Solution**:
- [Specific action 1 - e.g., "Automatically syncs users from Salesforce to Azure AD"]
- [Specific action 2 - e.g., "Handles create, update, and deactivation operations"]
- [Specific action 3 - e.g., "Generates detailed sync report with error handling"]
- [Specific action 4 - e.g., "Sends summary email to admins"]

**Output**:
- [What files are generated - e.g., "Excel report with 3 sheets: Summary, Details, Errors"]
- [What actions are performed - e.g., "Creates/updates users in Azure AD"]
- [What notifications are sent - e.g., "Email summary to IT team"]

---

## Quick Start (15 Minutes)

### Prerequisites
- [ ] [Service/API] account with [required permissions]
- [ ] [Data source] access credentials
- [ ] Python 3.8+ installed

### 1. Configure Credentials (5 minutes)

```bash
# Edit configuration file for your organization and environment
# Example: mycompany-prod-config.json
vi config/[org]-[env]-config.json
```

**Required configuration keys**:
```json
{
  "global": {
    "[api-name]-base-url": "[API endpoint]",
    "[api-name]-timeout": 30
  },
  "[service-name]": {
    "[specific-setting]": "[value]"
  }
}
```

**Required secrets** (in `config/[org]-[env]-config-secrets.json`):
```json
{
  "[api-name]-api-key": "your-api-key-here",
  "[service-name]-client-id": "your-client-id",
  "[service-name]-client-secret": "your-client-secret"
}
```

### 2. Run the Script (2 minutes)

```bash
# Execute script with organization and environment
PYTHONPATH=. python src/[script_filename].py [org_id] [env_type]

# Example
PYTHONPATH=. python src/user_sync.py mycompany prod
```

### 3. Check the Output (1 minute)

```bash
# View generated reports
ls -ltr output/[org]-[env]-*

# Expected output files:
# output/mycompany-prod-[script-name]-results_2025-11-01T143022Z.xlsx
# output/mycompany-prod-[script-name]-errors_2025-11-01T143022Z.json
```

**What the report contains**:
- **[Sheet1/Section1]**: [Description - e.g., "Summary statistics: users created, updated, failed"]
- **[Sheet2/Section2]**: [Description - e.g., "Detailed results for each user"]
- **[Sheet3/Section3]**: [Description - e.g., "Error log with troubleshooting info"]

---

## Configuration Reference

### Main Configuration ([org]-[env]-config.json)

| Key | Description | Example | Required |
|-----|-------------|---------|----------|
| `[api-name]-base-url` | [Description] | `"https://api.example.com"` | Yes |
| `[setting-name]` | [Description] | `30` | No |
| `[option-name]` | [Description] | `true` | No |

### Secrets ([org]-[env]-config-secrets.json)

| Key | Description | How to Obtain | Required |
|-----|-------------|---------------|----------|
| `[api-name]-api-key` | [Description] | [Instructions] | Yes |
| `[service]-client-id` | [Description] | [Instructions] | Yes if using [feature] |

---

## Common Use Cases

### Use Case 1: [Scenario Name]

**Scenario**: [Describe when to use this]

**Command**:
```bash
PYTHONPATH=. python src/[script].py [org] [env]
```

**Expected Output**:
```
[Sample output showing what user should see]
```

**What Happens**:
1. [Step 1 - e.g., "Fetches users from Salesforce"]
2. [Step 2 - e.g., "Compares with Azure AD users"]
3. [Step 3 - e.g., "Creates missing users"]
4. [Step 4 - e.g., "Generates report"]

### Use Case 2: [Another Scenario]

**Scenario**: [Describe this variation]

**Configuration**:
```json
{
  "[setting]": "[value for this use case]"
}
```

**Command**:
```bash
PYTHONPATH=. python src/[script].py [org] [env] [optional-flag]
```

---

## Troubleshooting

### Error: [Common Error Message]

**Symptoms**:
```
[Exact error message or pattern]
```

**Cause**: [Why this error occurs]

**Solution**:
```bash
# [Step-by-step fix]
```

### Error: [Another Common Error]

**Symptoms**:
```
[Error pattern]
```

**Cause**: [Why this happens]

**Solution**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Getting Help

**Check the logs**:
```bash
# View detailed debug log
cat logs/[org]-[env]-[script]_[timestamp].log

# Search for errors
grep "ERROR" logs/[org]-[env]-[script]*.log | tail -20
```

**Common issues**:
- [Issue 1 and quick fix]
- [Issue 2 and quick fix]
- [Issue 3 and quick fix]

---

## Understanding Output Files

This script generates files following TXO naming patterns:

### Pattern
```
[org-id]-[env-type]-[description]_[UTC-timestamp].[extension]
```

### Examples
```
mycompany-prod-user-sync-results_2025-11-01T143022Z.xlsx
mycompany-prod-user-sync-errors_2025-11-01T143022Z.json
mycompany-prod-user-sync-summary_2025-11-01T143022Z.txt
```

### Finding Your Files
```bash
# Latest output for this org-env
ls -t output/mycompany-prod-* | head -3

# All outputs from today
ls output/*2025-11-01*

# Specific script outputs
ls output/*user-sync*
```

---

## Scheduling and Automation

### Run on Schedule (cron)

```bash
# Edit crontab
crontab -e

# Add line for daily execution at 2 AM
0 2 * * * cd /path/to/project && PYTHONPATH=. python src/[script].py [org] [env] >> logs/cron-[script].log 2>&1
```

### Run as Systemd Service

```ini
# /etc/systemd/system/[script-name].service
[Unit]
Description=[Script Name] - [Brief Description]

[Service]
Type=oneshot
WorkingDirectory=/path/to/project
Environment="PYTHONPATH=."
ExecStart=/usr/bin/python3 src/[script].py [org] [env]

[Install]
WantedBy=multi-user.target
```

---

## Advanced Configuration

### [Feature Name]

**Purpose**: [What this optional feature does]

**Configuration**:
```json
{
  "[feature-setting]": {
    "enabled": true,
    "[option1]": "[value]",
    "[option2]": "[value]"
  }
}
```

**Usage**:
```bash
# [How to use this feature]
```

### [Another Feature]

**Purpose**: [Description]

**Setup**: [How to enable]

---

## Performance Notes

**Typical Execution Time**: [Time estimate - e.g., "2-5 minutes for 1000 users"]

**Factors Affecting Performance**:
- [Factor 1 - e.g., "Number of API calls required"]
- [Factor 2 - e.g., "API rate limits"]
- [Factor 3 - e.g., "Data volume"]

**Optimization Tips**:
- [Tip 1 - e.g., "Run during off-peak hours"]
- [Tip 2 - e.g., "Increase batch size in config"]
- [Tip 3 - e.g., "Use filtering to reduce data volume"]

---

## Need More Details?

For maintainers and developers who need to customize or extend this script:
- See [in-depth-readme.md](in-depth-readme.md) for architecture and extension guide
- See [TXO Framework Docs](https://github.com/tentixo/txo-python-template) for framework patterns

---

## Version History

### Current Version
- [Version] - [Date] - [Brief description of script functionality]

### Recent Changes
- [Change 1] - [Date]
- [Change 2] - [Date]

---

**Script Version**: [version]
**TXO Framework Version**: Built with TXO Template v3.3.0
**Last Updated**: [date]
**Maintainer**: [name/team]
