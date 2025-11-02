# Documentation Gaps and Inconsistencies for v3.2.1

> **Status**: Identified during v3.2 Script Creating workflow
> **Date**: 2025-10-31
> **Reporter**: User (morre) caught AI missing UTC timestamps
> **Impact**: Medium - AI can miss UTC timestamps, filename patterns inconsistent
> **Fix Target**: v3.2.1 refactoring

---

## Issue 1: UTC Timestamp Requirement Not Explicit in ADRs

### Problem

UTC timestamps for output files are:

- ✅ Shown by **example** in ADR-B010 (line 673)
- ✅ Documented in utils-quick-reference as "TXO standard format"
- ❌ **NOT mandated** with explicit "Status: MANDATORY" ADR
- ❌ **NOT in critical reminders** in ai-prompt-template_v3.2-morre.md
- ❌ **NOT validated** by utils/validate_tko_compliance.py

### Where to add UTC and not

This is where one normally add or not add UTC suffixes

```
txo-project-root/
├── output/              # Add UTC suffix
├── tmp/                 # Add UTC suffix
├── generated_payloads/  # Do not ddd UTC suffix
└── wsdl/                # Do not ddd UTC suffix
```

### What Happened

AI generated script using:

```python
output_path = data_handler.save(results, Dir.OUTPUT, output_filename)
```

Instead of:

```python
output_path = data_handler.save_with_timestamp(results, Dir.OUTPUT, output_filename, add_timestamp=True)
```

**Root cause**: Pattern is implicit (examples only), not explicit (ADR requirement).

### Current Documentation State

**ADR-B006**: "Smart Logging Context Strategy" (about logging, NOT filenames)

- **ERROR**: in-depth-readme-example_v3.2.md references "Why ADR-B006 enforces UTC filenames" ← WRONG ADR

**ADR-B010**: Shows UTC timestamp example (line 667-673) but no requirement statement

**ai-prompt-template_v3.2-morre.md**:

- Critical reminders section (lines 218-243) does NOT include UTC timestamps
- Should be added alongside other "MANDATORY PATTERNS"

### Recommendations

#### 1. Create ADR-B017: Output File Naming Standards

**File**: `ai/decided/txo-business-adr_v3.2.md`
**Location**: After ADR-B016 (around line 1683)

```markdown
## ADR-B017: Output File Naming Standards

**Status:** MANDATORY
**Date:** 2025-10-31

### Context

TXO operates across multiple organizations and environments. Output files must be:

- Distinguishable by organization and environment
- Traceable to execution time
- Non-overwriting (each run unique)

### Decision

**All output files MUST follow this pattern:**

`{org_id}-{env_type}-{description}_{UTC-timestamp}.{extension}`

Where:

- `org_id`: Organization identifier from command line
- `env_type`: Environment type from command line
- `description`: Human-readable file purpose (kebab-case)
- `UTC-timestamp`: ISO 8601 format `YYYY-MM-DDTHHMMSSZ`
- `extension`: File format (.json, .xlsx, .csv, .txt)

### Implementation

```python
# ✅ CORRECT - Full context with UTC timestamp
filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
output_path = data_handler.save_with_timestamp(data, Dir.OUTPUT, filename, add_timestamp=True)
# Produces: txo-lab-sync-results_2025-10-31T200601Z.json

# ✅ CORRECT - Multi-sheet Excel with timestamp
report_sheets = {"Summary": summary_df, "Details": details_df}
output_path = data_handler.save_with_timestamp(report_sheets, Dir.OUTPUT,
    f"{config['_org_id']}-{config['_env_type']}-report.xlsx", add_timestamp=True)
# Produces: txo-lab-report_2025-10-31T200601Z.xlsx

# ❌ WRONG - Missing env_type (can't distinguish lab vs prod vs test)
filename = f"results-{config['_org_id']}.json"

# ❌ WRONG - No UTC timestamp (overwrites previous runs, no traceability)
output_path = data_handler.save(data, Dir.OUTPUT, filename)

# ❌ WRONG - Manual timestamp formatting (use framework method)
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
filename = f"{config['_org_id']}-{config['_env_type']}-data_{timestamp}.json"
```

### Rationale

**Consistency with Configuration Files:**

- Config pattern: `{org}-{env}-config.json` (e.g., `txo-lab-config.json`)
- Output pattern: `{org}-{env}-description_{timestamp}.{ext}` (matches config structure)

**Environment Isolation:**

- Output directory may contain files from multiple environments
- `env_type` distinguishes: `txo-prod-*` vs `txo-test-*` vs `txo-lab-*`

**Traceability:**

- UTC timestamp enables time-based analysis
- Each execution creates unique file (no overwrites)
- Debug workflow: "Upload output file from 2025-10-31T14:30 run"

**Framework Standardization:**

- `save_with_timestamp()` enforces ISO 8601 format
- Framework handles UTC conversion (no manual datetime code)
- Prevents timezone inconsistencies

### Consequences

**Positive:**

- Clear filename structure across all TXO projects
- Easy to find files for specific org/env combinations
- Non-destructive (never overwrites previous results)
- Audit trail for compliance and debugging

**Negative:**

- Longer filenames
- Output directory accumulates files over time

**Mitigation:**

- Use `cleanup_tmp()` for temporary files (path_helpers.py)
- Archive old output files periodically
- Filenames remain human-readable despite length

```

#### 2. Update ai-prompt-template Critical Reminders

**File**: `ai/prompts/ai-prompt-template_v3.2-morre.md`
**Location**: Lines 218-243 (critical-pattern-reminders section)

**Add this line:**
```xml
<timestamps>✅ Use save_with_timestamp(..., add_timestamp=True) for ALL output files - mandatory UTC suffix</timestamps>
```

**Updated section should be:**

```xml

<critical-pattern-reminders>
    <!-- TOP 13 violations from real usage - v3.2.1 updated -->

    <!-- MANDATORY PATTERNS (v3.2.1) -->
    <imports>✅ Use create_rest_api() NOT import requests</imports>
    <config-access>✅ Use config['key'] NOT config.get('key', default) - HARD FAIL on required config</config-access>
    <directories>✅ Use Dir.OUTPUT NOT 'output' strings</directories>
    <timestamps>✅ Use save_with_timestamp(..., add_timestamp=True) for ALL output files - mandatory UTC suffix
    </timestamps>
    <filename-pattern>✅ Use f"{config['_org_id']}-{config['_env_type']}-description.ext" - MUST include both org AND
        env
    </filename-pattern>
    ...
</critical-pattern-reminders>
```

#### 3. Update utils-quick-reference Anti-Patterns

**File**: `ai/decided/utils-quick-reference_v3.2.md`
**Location**: Lines 375-401 (What NOT to Do section)

**Add to anti-patterns:**

```python
# ❌ DON'T CREATE - Use save_with_timestamp() with add_timestamp=True
data_handler.save(data, Dir.OUTPUT, "report.json")  # Missing UTC timestamp
filename = f"results-{org_id}.json"  # Missing env_type

# ❌ DON'T CREATE - Manual UTC formatting
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
filename = f"data_{timestamp}.json"  # Use framework method instead
```

#### 4. Fix Incorrect ADR Reference

**File**: `ai/decided/in-depth-readme-example_v3.2.md`
**Location**: Line 599 (search for "ADR-B006 enforces UTC")

**Change from:**

```markdown
- Why ADR-B006 enforces UTC filenames
```

**Change to:**

```markdown
- Why ADR-B017 enforces UTC filenames and org-env patterns
```

#### 5. Add Compliance Check

**File**: `utils/validate_tko_compliance.py`
**Location**: Add new validation check

**Pseudo-code for new check:**

```python
def check_output_files_use_timestamp(file_content: str) -> List[str]:
    """Check that output files use save_with_timestamp with add_timestamp=True."""
    violations = []

    # Pattern: data_handler.save(..., Dir.OUTPUT, ...) without save_with_timestamp
    if re.search(r'data_handler\.save\([^,]+,\s*Dir\.OUTPUT', file_content):
        if not re.search(r'save_with_timestamp.*add_timestamp\s*=\s*True', file_content):
            violations.append(
                "❌ Output files should use save_with_timestamp(..., add_timestamp=True) "
                "for UTC timestamp suffix (ADR-B017)"
            )

    # Check filename pattern includes both org_id and env_type
    if re.search(r'f"[^"]*\{config\[\'_org_id\'\]\}[^"]*\.json', file_content):
        if not re.search(r'f"[^"]*\{config\[\'_org_id\'\]\}[^"]*\{config\[\'_env_type\'\]\}', file_content):
            violations.append(
                "⚠️  Filename pattern should include both org_id AND env_type: "
                'f"{config[\'_org_id\']}-{config[\'_env_type\']}-description.ext" (ADR-B017)'
            )

    return violations
```

---

## Issue 2: Conflicting Filename Pattern Examples

### Problem

**Two different patterns shown in documentation:**

**Pattern A** (utils-quick-reference_v3.2.md line 476):

```python
f"sync-results-{config['_org_id']}.json"
# Produces: sync-results-txo_2025-10-31T200601Z.json
# ❌ Missing: env_type
```

**Pattern B** (Correct standard):

```python
f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
# Produces: txo-lab-sync-results_2025-10-31T200601Z.json
# ✅ Includes: both org_id AND env_type
```

### Why This Matters

**Config files use org-env pattern:**

- `txo-lab-config.json`
- `txo-prod-config.json`
- `company1-test-config.json`

**Output files MUST match:**

- `txo-lab-results_timestamp.json` ✅
- `results-txo_timestamp.json` ❌ (inconsistent, missing env)

**Real-world scenario:**

```bash
output/
├── txo-prod-sync-results_2025-10-31T140000Z.json  # Production run
├── txo-test-sync-results_2025-10-31T143000Z.json  # Test run
├── txo-lab-sync-results_2025-10-31T150000Z.json   # Lab run
```

Without `env_type`, files are ambiguous:

```bash
output/
├── sync-results-txo_2025-10-31T140000Z.json  # Which environment???
├── sync-results-txo_2025-10-31T143000Z.json  # Can't tell!
```

### Recommendations

#### Update utils-quick-reference Example

**File**: `ai/decided/utils-quick-reference_v3.2.md`
**Location**: Line 476 (Complete Script Pattern)

**Change from:**

```python
    # 5. Save results and summary
data_handler.save_with_timestamp(results, Dir.OUTPUT, f"sync-results-{config['_org_id']}.json", add_timestamp=True)
logger.info(results.summary())
```

**Change to:**

```python
    # 5. Save results and summary
filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
logger.info(results.summary())
# Produces: txo-lab-sync-results_2025-10-31T200601Z.json
```

---

## Priority Summary

### High Priority (Mandatory for v3.2.1)

1. ✅ **Add ADR-B017**: Output File Naming Standards (MANDATORY status)
2. ✅ **Update ai-prompt-template**: Add UTC timestamp to critical reminders
3. ✅ **Fix utils-quick-reference**: Correct filename pattern example (line 476)

### Medium Priority (Quality improvements)

4. ✅ **Fix in-depth-readme-example**: Correct ADR-B006 reference → ADR-B017
5. ✅ **Add compliance check**: validate_tko_compliance.py checks for UTC timestamps

### Low Priority (Nice to have)

6. ⏳ **Add anti-pattern examples**: Document wrong patterns more explicitly
7. ⏳ **Update README templates**: Show correct filename patterns in examples

---

## Files Requiring Changes

| File                                          | Change Type      | Lines           | Priority |
|-----------------------------------------------|------------------|-----------------|----------|
| `ai/decided/txo-business-adr_v3.2.md`         | Add ADR-B017     | After line 1683 | HIGH     |
| `ai/prompts/ai-prompt-template_v3.2-morre.md` | Add reminder     | Lines 218-243   | HIGH     |
| `ai/decided/utils-quick-reference_v3.2.md`    | Fix example      | Line 476        | HIGH     |
| `ai/decided/utils-quick-reference_v3.2.md`    | Add anti-pattern | Lines 375-401   | MEDIUM   |
| `ai/decided/in-depth-readme-example_v3.2.md`  | Fix ADR ref      | Line 599        | MEDIUM   |
| `utils/validate_tko_compliance.py`            | Add check        | New function    | MEDIUM   |

---

## Impact Assessment

**Without these fixes:**

- AI may generate scripts without UTC timestamps (happened in this session)
- AI may use inconsistent filename patterns (missing env_type)
- Users must manually catch these issues during review

**With these fixes:**

- Explicit MANDATORY requirement (ADR-B017)
- Critical reminder prevents AI omission
- Automated compliance check catches violations
- Consistent filename patterns across all scripts

---

## Version History

### 2025-10-31 (Initial Report)

- Identified during fat_fuck_statistics.py script creation
- User caught missing UTC timestamp
- Discovered conflicting filename pattern examples
- Created comprehensive fix recommendations for v3.2.1

---

**Version**: v3.2.1 (target)
**Reporter**: morre
**Session**: Script Creating workflow for weight statistics
**Status**: Ready for refactoring