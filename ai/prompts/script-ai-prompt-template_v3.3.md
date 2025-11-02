# TXO AI Development Prompt Template v3.1.1

**\<remove_before_ai>**

> **Purpose**: Enhanced structured prompt with mandatory validation and clear documentation separation
> **Workflow**: 8 phases with explicit flow control and user confirmation points
> **Key Improvement**: Prevents AI from skipping validation and ensures proper documentation balance

## ⚠️ Human TODO before use

### Step-by-step Setup
1. Copy this prompt file and change its name
2. **Read** `ai/decided/txo-business-adr_v3.3.md` and browse `ai/decided/txo-technical-standards_v3.3.md`
3. Understand your requirements and target environment
4. Decide your `org_id` and `env_type` parameters
5. Fill in your details in Phase 2 (ERD in Mermaid format is recommended!)
6. Remove everything between "<remove_before_ai>" including the tags
7. Upload to AI with the command: **"Wait for my explicit command before starting each phase."**

### Template Validation Checklist
Before using this template, verify:
- [ ] All Phase 1 documents are current version (v3.2)
- [ ] You have specific, actionable requirements for Phase 2
- [ ] Script purpose aligns with TXO patterns (automation, data processing, API integration)
- [ ] You understand the difference between README vs in-depth documentation targets
- [ ] You understand v3.2 changes (logger exceptions, AsyncOperationResult, no sys.exit() in library code)

---
**\</remove_before_ai>**

## Phase 1: Context Upload (RESEARCH ONLY - NO CODE)

**🚨 CRITICAL: DO NOT WRITE ANY CODE IN THIS PHASE. RESEARCH AND UNDERSTANDING ONLY.**

**Upload these documents to establish TXO patterns and available functions:**

```xml
<required-documents>
    <required-document>
        <doc-type>business-rules</doc-type>
        <file>ai/decided/txo-business-adr_v3.3.md</file>
        <purpose>Organizational patterns, hard-fail philosophy, naming conventions, validation timing</purpose>
    </required-document>

    <required-document>
        <doc-type>technical-standards</doc-type>
        <file>ai/decided/txo-technical-standards_v3.3.md</file>
        <purpose>Python patterns, threading, exception handling, library boundaries (NEW: ADR-T011, ADR-T012)</purpose>
    </required-document>

    <required-document>
        <doc-type>function-reference</doc-type>
        <file>ai/decided/utils-quick-reference_v3.3.md</file>
        <purpose>Complete list of existing functions - DO NOT INVENT THESE (includes AsyncOperationResult, enhanced CircuitBreaker)</purpose>
    </required-document>
</required-documents>
```

**Instructions for Phase 1:**
- **READ AND UNDERSTAND** TXO business rules and technical patterns
- **STUDY** the available functions in `utils/` - DO NOT create new versions of existing functions
- **ANALYZE** the configuration patterns and JSON schema requirements
- **UNDERSTAND** the documentation separation: README (15-min success) vs in-depth (maintainer focus)

### AI Document Structure Awareness (v3.2)

**Understand the ai/ directory before starting**:

```xml
<ai-directory-overview>
    <permanent-docs format="kebab-case_v3.3.md">
        <location>ai/decided/, ai/prompts/, ai/reports/</location>
        <purpose>ADRs, patterns, examples - READ for guidance</purpose>
        <ai-action>READ only, DO NOT modify</ai-action>
        <includes>txo-ai-adr_v3.3.md - AI workflow standards (NEW)</includes>
    </permanent-docs>

    <working-docs format="UPPERCASE.md">
        <location>ai/ (root) or ai/working/</location>
        <purpose>AI tracking documents (temporary)</purpose>
        <ai-action>CREATE only if needed (see below)</ai-action>
        <visual-signal>UPPERCASE = AI working file (user can skip/delete)</visual-signal>
    </working-docs>

    <ignore-dirs>
        <pattern>*/old/</pattern>
        <rule>AI MUST ignore (per ADR-AI002)</rule>
        <reason>Contains superseded versions</reason>
    </ignore-dirs>
</ai-directory-overview>
```

**For script creation**: META-DOCUMENTS usually NOT needed
- Single script = straightforward, no TODO.md needed
- If complex/multi-phase: ASK USER "Create TODO.md for tracking?"
- See `ai/decided/txo-ai-adr_v3.3.md` for full AI workflow standards

**What AI WILL Create**:
- Your script code
- Configuration examples
- README.md + in-depth-readme.md (per ADR-B015)
- Tests (if user requested)

**What AI usually WON'T Create** (for single scripts):
- ai/TODO.md (overkill for single script)
- ai/PROJECT-STATUS.md (not needed)
- Meta-tracking documents

**🛑 PHASE 1 COMPLETE: Wait for user command "begin phase 2" before proceeding.**

---

## Phase 2: Requirements Specification (PLANNING ONLY - NO CODE)

**🚨 CRITICAL: DO NOT WRITE ANY CODE IN THIS PHASE. REQUIREMENTS GATHERING ONLY.**

**Fill in your script requirements below:**

### Script Metadata (for AI extraction)
```xml
<script-metadata>
    <script-name>[your_script_name]</script-name>
    <script-purpose>[One sentence: What business problem does this solve?]</script-purpose>
    <complexity>[simple|moderate|complex]</complexity>
</script-metadata>
```

---

## Script Requirements

### 1. Organization & Environment
- **Organization ID**: `[your-org-id]`
- **Environment Type**: `[test|qa|prod]`
- **Requires Authentication**: `[yes|no]`
- **Primary Use Case**: `[daily operations | one-time migration | data analysis | reporting]`

### 2. Environment Reality
Describe the actual environment this script will work with:

```
Example:
- Azure Tenant UUID: [tenant-id-here]
- Business Central environment: [environment-name]
- Companies to process: [company-list or "all companies"]
- APIs required: [which endpoints/services]
- Authentication method: [client-credentials | managed-identity | etc.]
- Rate limits: [X calls per minute]
```

### 3. Data Contracts

#### Input Data
What data does the script process? Be specific about formats.

```
Example:
- CSV file: data/customers.csv
  Columns: [name, email, phone, address, country]
  Size: ~1000 rows, <1MB

- API responses: JSON from GET /customers
  Schema: {"id": "string", "name": "string", ...}

- Excel file: data/products.xlsx
  Sheet: "Products", Columns: [sku, price, stock]
```

#### Output Data
What does the script produce? Specify formats and naming patterns.

```
Example:
- Excel report: output/{org}-{env}-sync-results_{UTC}.xlsx
  Sheets: ["Summary", "Details", "Errors"]

- JSON summary: output/{org}-{env}-processing-summary_{UTC}.json
  Structure: {"total": 150, "success": 145, "failed": 5}

- Log files: logs/{org}-{env}-script_{UTC}.log
  Format: Structured JSON logs
```

#### Success Criteria
How do you know the script worked?

```
Example:
- All records processed without fatal errors
- Output file created with expected row count
- ProcessingResults shows: "✅ All 150 operations successful: 75 created, 75 updated"
- No ERROR level logs in log file
- Email notification sent to admins
```

### 4. Business Logic
What are the core processing rules?

```
Example:
- Skip records with missing required fields (email, name)
- For each customer record:
  * Check if exists in target system (match by email)
  * If exists: UPDATE customer data
  * If not exists: CREATE new customer
- Generate summary with counts: created, updated, skipped, failed
- Flag duplicates: If multiple records have same email, process first and warn
```

### 5. API Integrations

#### Endpoints
```
Example:
- Business Central: GET/POST /api/v2.0/companies/{companyId}/customers
  Base URL: https://api.businesscentral.dynamics.com/v2.0/production
  Auth: OAuth client credentials

- External API: GET https://api.example.com/data/customers
  Auth: API key in header
```

#### Resilience Requirements
```
Example:
- Circuit breaker: After 5 consecutive failures, stop and alert
- Rate limiting: Max 100 API calls per minute
- Retry strategy: On 5xx errors, retry 3 times with exponential backoff (2s, 4s, 8s)
- Timeout: 30 seconds per API request
- Batch processing: Process in batches of 50 records
```

### 6. Error Handling
How should different error types be handled?

```
Example:
- Invalid CSV format:
  * Stop immediately
  * Show error: "CSV missing required column 'email' at row 15"
  * Exit code 1

- API rate limit hit (429):
  * Wait for Retry-After header duration
  * Resume automatically
  * Log warning

- Network timeout:
  * Retry 3 times
  * If still fails: Log error, continue with next record

- Missing config:
  * Show error: "Missing required config: 'api-base-url'"
  * Show example config snippet
  * Exit code 1
```

### 7. Additional Requirements
```
Example:
- Performance: Script should complete 1000 records in <5 minutes
- Scheduling: Should be safe to run via cron (idempotent)
- Notifications: Email summary report to admins on completion
- Dry-run mode: Option to preview changes without writing
```

---

**Instructions for Phase 2:**
- **BE SPECIFIC** about data formats, API endpoints, and business rules
- **DEFINE CLEAR** success/failure criteria and error handling expectations
- **IDENTIFY** configuration that should be adjustable vs hard-coded
- **ASK USER** if any requirements are unclear or missing

**After requirements filled, ASK USER:**

```xml
<user-decisions>
    <testing-strategy>
        <question>What level of automated testing do you want for this script?</question>
        <options>
            <comprehensive>
                Full test suite (unit tests + integration tests)
                - Recommended for production scripts
                - Covers main logic, error paths, edge cases
                - Generates tests/test_your_script.py
            </comprehensive>
            <smoke-tests>
                Basic smoke tests only (happy path + basic error handling)
                - Faster to generate
                - Validates script works
                - Good for moderate complexity
            </smoke-tests>
            <no-tests>
                No automated tests
                - Manual testing only
                - For prototypes or throwaway scripts
            </no-tests>
        </options>
        <default>Ask user - don't assume</default>
    </testing-strategy>

    <documentation-confirmation>
        <question>Generate README.md + in-depth-readme.md documentation?</question>
        <note>Per ADR-B015, documentation is mandatory for user-facing scripts</note>
        <options>
            <yes-full>Both README + in-depth (scaled to script complexity)</yes-full>
            <yes-readme-only>README only (if very simple script)</yes-readme-only>
            <defer>Code first, documentation later (not recommended)</defer>
        </options>
        <default>yes-full (per ADR-B015)</default>
    </documentation-confirmation>

    <phase-adjustments>
        Based on answers, AI adjusts workflow:
        - If no-tests: Skip test generation in Phase 3
        - If smoke-tests: Generate basic test file only
        - If comprehensive: Full test suite with edge cases
        - If yes-full docs: Phases 6-7-8 all execute
        - If yes-readme-only: Skip Phase 7 (in-depth), Phase 8 (balance)
        - If defer docs: Skip Phases 6-7-8, remind user to create later
    </phase-adjustments>
</user-decisions>
```

**🛑 PHASE 2 COMPLETE: Wait for user command "begin phase 3" before proceeding.**

---

## Phase 3: Code Generation

**🚨 CRITICAL REMINDERS (Common AI Mistakes - Check These First):**

```xml
<critical-pattern-reminders>
    <!-- TOP 16 violations from real usage - v3.3 updated with ADR-B017 directory rules -->

    <!-- MANDATORY PATTERNS (v3.3 - ADR-B017) -->
    <imports>✅ Use create_rest_api() NOT import requests</imports>
    <config-access>✅ Use config['key'] NOT config.get('key', default) - HARD FAIL on required config</config-access>
    <directories>✅ Use Dir.OUTPUT NOT 'output' strings</directories>

    <!-- NEW v3.3: Directory-specific timestamp rules (ADR-B017) -->
    <timestamps-output>✅ MUST: Dir.OUTPUT → save_with_timestamp(..., add_timestamp=True) - UTC mandatory</timestamps-output>
    <timestamps-tmp>✅ SHOULD: Dir.TMP → save_with_timestamp(..., add_timestamp=True) - UTC recommended</timestamps-tmp>
    <timestamps-payloads>❌ MUST NOT: Dir.GENERATED_PAYLOADS → save() directly - NO UTC (deterministic for human validation)</timestamps-payloads>
    <filename-pattern>✅ MUST: f"{config['_org_id']}-{config['_env_type']}-description.ext" - both org AND env required</filename-pattern>

    <existing-helpers>✅ CHECK utils-quick-reference_v3.3.md - DO NOT reinvent existing functions</existing-helpers>
    <config-preservation>✅ DO NOT remove existing config data without clear user instructions</config-preservation>
    <schema-updates>✅ UPDATE JSON schema if adding new configuration fields</schema-updates>

    <!-- v3.2 NEW PATTERNS - Critical for library code -->
    <logger-exceptions>✅ Application code MUST handle logger exceptions (try/except with LoggerConfigurationError, LoggerSecurityError)</logger-exceptions>
    <no-sys-exit-library>✅ NEVER use sys.exit() in utils/ library code - raise exceptions instead (ADR-T012)</no-sys-exit-library>
    <async-result-compatibility>✅ _execute_request() may return AsyncOperationResult for 202 responses - both have .json(), .ok, .content</async-result-compatibility>
    <static-methods>✅ Make helper methods @staticmethod if they don't use self (clearer intent, PyCharm will suggest)</static-methods>
    <indirect-imports>✅ Keep imports like 'openpyxl' even if PyCharm flags them - pandas needs them via engine='openpyxl'</indirect-imports>

    <!-- EVOLUTION TRACKING: Common patterns from v3.2 refactoring -->
    <!-- Removed violations that are no longer issues:
    - sys.exit() in library code (now prevented by ADR-T012)
    - Broad exception catches (now split into specific handlers)
    - Third-party object mutation (now using wrapper pattern)
    -->
</critical-pattern-reminders>
```

**🔑 Directory-Specific Examples (ADR-B017):**

```python
# ✅ CORRECT - OUTPUT files WITH UTC (MUST)
filename = f"{config['_org_id']}-{config['_env_type']}-sync-results.json"
output_path = data_handler.save_with_timestamp(results, Dir.OUTPUT, filename, add_timestamp=True)
# Produces: output/txo-lab-sync-results_2025-11-01T143022Z.json

# ✅ CORRECT - TMP files WITH UTC (SHOULD)
filename = f"{config['_org_id']}-{config['_env_type']}-processing-cache.json"
tmp_path = data_handler.save_with_timestamp(cache, Dir.TMP, filename, add_timestamp=True)
# Produces: tmp/txo-lab-processing-cache_2025-11-01T143022Z.json

# ✅ CORRECT - GENERATED_PAYLOADS WITHOUT UTC (MUST NOT)
filename = f"{config['_org_id']}-{config['_env_type']}-create-user-request.json"
payload_path = data_handler.save(request_payload, Dir.GENERATED_PAYLOADS, filename)
# Produces: generated_payloads/txo-lab-create-user-request.json (deterministic for human validation)

# ❌ WRONG - OUTPUT without UTC timestamp
data_handler.save(data, Dir.OUTPUT, "report.json")  # Missing UTC!

# ❌ WRONG - Filename missing env_type
filename = f"results-{config['_org_id']}.json"  # Only org, no env!

# ❌ WRONG - Generated payload WITH UTC (should be deterministic)
data_handler.save_with_timestamp(payload, Dir.GENERATED_PAYLOADS, filename, add_timestamp=True)  # NO!
```

---

**Now generate a complete Python script that:**

```xml
<code-requirements>
    <tko-compliance>
        <mandatory-patterns>
            - Use utils.script_runner.parse_args_and_load_config() for initialization
            - Use utils.load_n_save.TxoDataHandler() for all file operations
            - Use utils.path_helpers.Dir.* constants (NEVER string literals)
            - Use utils.api_factory.create_rest_api() for HTTP clients
            - Use utils.logger.setup_logger() for logging WITH exception handling (v3.2)
        </mandatory-patterns>

        <v3.2-specific-patterns>
            - WRAP setup_logger() in try/except (LoggerConfigurationError, LoggerSecurityError)
            - Application code may call sys.exit(1) after catching exceptions
            - Helper methods that don't use self should be @staticmethod
            - Keep indirect imports like 'openpyxl' (needed by pandas, add explanatory comment)
            - AsyncOperationResult and Response both provide .json(), .ok, .content (compatible)
        </v3.2-specific-patterns>

        <forbidden-patterns>
            - DO NOT import requests directly (use create_rest_api)
            - DO NOT use manual datetime formatting (use get_utc_timestamp)
            - DO NOT use string literals for directories (use Dir.*)
            - DO NOT add timing/performance metrics unless requested
            - DO NOT use config.get() with defaults on required config (use config[] hard-fail)
            - DO NOT use sys.exit() in library code (utils/) - raise exceptions instead
            - DO NOT mutate third-party object internals (e.g., response._content)
            - DO NOT use broad exception catches - be specific (JSONDecodeError, KeyError, etc.)
        </forbidden-patterns>
    </tko-compliance>

    <code-structure>
        <imports>Standard TXO imports from utils-quick-reference</imports>
        <main-function>Business logic implementation</main-function>
        <error-handling>Use TXO exception patterns</error-handling>
        <logging>Structured logging with context</logging>
        <results-tracking>Use ProcessingResults pattern for bulk operations</results-tracking>
    </code-structure>
</code-requirements>
```

**Deliverables for Phase 3:**
1. **Complete Python script** following TXO patterns exactly
2. **Configuration updates** if new settings needed
3. **Usage instructions** with example command line

**🛑 PHASE 3 COMPLETE: Wait for user command "begin validation" before proceeding.**

---

## Phase 4: TXO Compliance Validation (MANDATORY)

**🚨 CRITICAL: This phase is MANDATORY. You cannot proceed to documentation without validation.**

**Note on TXO 10-Step Lifecycle**:
- Script Creating workflow: Steps 1-5, 7-10 apply
- **Step 6 (Utils Reference): N/A** (not modifying utils/ framework)
- Step 6 is for Refactoring workflow only

### **Mandatory TXO Compliance Check**

**Step 1: Run Automated Validation**
```bash
PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py
```

**Step 2: Manual Pattern Review**
Review the generated script against this checklist:

```xml
<tko-compliance-validation>
    <api-patterns>
        <question>Does the script use create_rest_api() instead of manual requests.Session()?</question>
        <violation-check>Look for: import requests, session = requests.Session()</violation-check>
        <required-fix>Replace with: from utils.api_factory import create_rest_api</required-fix>
    </api-patterns>

    <timestamp-patterns>
        <question>Does the script use get_utc_timestamp() for timestamps?</question>
        <violation-check>Look for: datetime.now().strftime(), manual UTC formatting</violation-check>
        <required-fix>Replace with: TxoDataHandler.get_utc_timestamp(), save_with_timestamp()</required-fix>
    </timestamp-patterns>

    <directory-patterns>
        <question>Does the script use Dir.* constants instead of string literals?</question>
        <violation-check>Look for: 'output', 'config', 'data' as strings</violation-check>
        <required-fix>Replace with: Dir.OUTPUT, Dir.CONFIG, Dir.DATA</required-fix>
    </directory-patterns>

    <configuration-patterns>
        <question>Does the script use hard-fail config access?</question>
        <violation-check>Look for: config.get('key', default)</violation-check>
        <required-fix>Replace with: config['key']  # Hard-fail if missing</required-fix>
    </configuration-patterns>

    <complexity-patterns>
        <question>Does the script avoid unnecessary complexity?</question>
        <violation-check>Look for: timing code, file size logging, performance metrics</violation-check>
        <required-fix>Remove unless specifically requested by user</required-fix>
    </complexity-patterns>

    <framework-patterns>
        <question>Does the script follow the standard TXO script pattern?</question>
        <violation-check>Check: parse_args_and_load_config(), TxoDataHandler(), setup_logger()</violation-check>
        <required-fix>Use utils-quick-reference_v3.3.md complete script pattern</required-fix>
    </framework-patterns>

    <v3.2-new-patterns>
        <question>Does the script handle logger exceptions properly? (v3.2 BREAKING CHANGE)</question>
        <violation-check>Look for: logger = setup_logger() without try/except</violation-check>
        <required-fix>Wrap in try/except (LoggerConfigurationError, LoggerSecurityError), call sys.exit(1) after logging</required-fix>
    </v3.2-new-patterns>
</tko-compliance-validation>
```

**Step 3: Fix Any Violations**
If violations found, **IMMEDIATELY REFACTOR** before proceeding.

**Step 4: Track Patterns for Improvement**
Note any new common violations not covered by critical reminders above.
These should be considered for addition to improve prevention over time.

**🛑 PHASE 4 REQUIRES USER CONFIRMATION:**
**User must respond with either:**
- **"validation complete"** - All TXO compliance issues resolved
- **"did not do validation"** - Acceptable to skip (but not recommended)

**🚨 DO NOT PROCEED TO PHASE 5 WITHOUT USER CONFIRMATION**

---

## Phase 5: Code Quality Review (OPTIONAL - Choose Your Approach)

**This phase is optional but recommended for professional code quality.**

### **Option A: PyCharm Inspection (Most Comprehensive)**

**Step-by-Step PyCharm Inspection Instructions:**

```
1. In PyCharm: Go to menu "Code" → "Inspect Code..."
2. In the dialog: Select "Whole project"
3. Click "OK" and wait for inspection to complete
4. When finished, in the "Inspection Results" panel:
   - Click "Export" button (or right-click → Export)
   - Select "XML" format
   - Save to your project's "code_inspection/" directory
   - Use filename like "inspection-results-YYYY-MM-DD.xml"
5. Upload or paste the PYTHON-SPECIFIC inspection results below
```

**Focus on Python Issues Only** (ignore markdown, spelling warnings):
- **PyTypeCheckerInspection**: Type mismatches, missing hints
- **PyUnusedImportsInspection**: Unused imports (check for false positives like openpyxl)
- **PyBroadExceptionInspection**: Overly broad exception handling
- **PyShadowingNamesInspection**: Variable naming conflicts
- **PyUnusedLocalInspection**: Unused variables (review if legitimate pattern)
- **PyMethodMayBeStaticInspection**: Methods that could be @staticmethod

**If user provides PyCharm Code Inspection feedback:**

```xml
<pycharm-inspection-feedback>
    <inspection-summary>
        [User pastes PYTHON-ONLY findings from PyCharm's "Inspection Results"]

        IGNORE: markdown numbering, spelling, documentation warnings
        FOCUS ON:
        - PyTypeCheckerInspection: Type mismatches, missing hints
        - PyUnusedImportsInspection: Remove unused imports
        - PyBroadExceptionInspection: Make exceptions more specific
        - PyShadowingNamesInspection: Variable naming conflicts
        - Any CRITICAL or ERROR severity issues
    </inspection-summary>

    <ai-improvement-request>
        Please review and fix the PyCharm inspection issues in the script.
        Prioritize:
        1. Critical issues (potential bugs, runtime errors)
        2. Type safety improvements
        3. Code style consistency
        4. Remove unused imports/variables

        Maintain TXO compliance while addressing these issues.
    </ai-improvement-request>
</pycharm-inspection-feedback>
```

### **Option B: Lightweight Validation (Faster Alternative)**

**If PyCharm not available, use these quick validation commands:**

```bash
# 1. Syntax validation
python -m py_compile src/your_script.py

# 2. TXO compliance check
PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py

# 3. Basic type checking (if mypy installed)
mypy src/your_script.py --ignore-missing-imports --no-strict-optional

# 4. Check for common issues
grep -n "sys\.exit" src/your_script.py  # Should not be in library code
grep -n "import requests" src/your_script.py  # Should use create_rest_api()
grep -n "config\.get(" src/your_script.py  # Review each for hard-fail vs soft-fail
```

**Expected Results**:
- ✅ Syntax validation: No errors
- ✅ TXO compliance: No violations (or only cosmetic issues)
- ✅ No sys.exit() in library code
- ✅ No direct requests imports

**If issues found**: Fix them before proceeding to documentation

### **Option C: Skip Quality Review**

**Not recommended for production code, but acceptable for:**
- Quick prototypes
- Internal tools
- Code that will be reviewed later

**User responds with**: "used option A", "used option B", or "skipped phase 5"

**🛑 PHASE 5 COMPLETE: Wait for user command "begin documentation" before proceeding.**

---

## Phase 6: README Generation (15-MINUTE SUCCESS FOCUS)

**🎯 Target Audience: "New developer needs 15 minutes to success"**

**⚠️ IMPORTANT**: You are creating README.md for **THE SCRIPT**, not the template

**Template to use**: `ai/decided/readme-example_v3.3.md`
- This is a PATTERN to copy (has header explaining it's a template)
- Replace ALL placeholders with script-specific content
- Do NOT copy verbatim - adapt to your script

**Generated README.md**:
- Documents YOUR script (not the TXO Template)
- Explains what your script does, how to run it, configuration
- Audience: Users of your script

**README.md Content Contract:**
```xml
<readme-specifications>
    <target-audience>New developers who need quick success</target-audience>
    <time-goal>15 minutes from clone to first successful run</time-goal>
    <content-limit>Maximum 2 screens of content</content-limit>

    <required-sections>
        <purpose-scope>
            - What the script does and why it exists
            - Business problem it solves
            - One-sentence scope definition
        </purpose-scope>

        <prerequisites>
            - Python version requirement
            - Virtual environment setup
            - Dependencies (reference pyproject.toml)
        </prerequisites>

        <setup-instructions>
            - Clone/download steps (or "Use this template" on GitHub)
            - Virtual environment creation
            - Dependency installation (pip install -r requirements.txt OR uv sync)
            - Configuration file preparation
            - First run verification
            - Optional: Update dependencies (uv pip list --outdated, then uv remove/add for updates)
        </setup-instructions>

        <usage>
            - CLI invocation examples
            - PyCharm run hints
            - Parameter explanations
        </usage>

        <config-overview>
            - Basic configuration structure
            - Link to JSON schema
            - Minimal working example
        </config-overview>

        <output-contract>
            - File formats and naming conventions
            - Output directory expectations
            - Success indicators
        </output-contract>

        <logging-contract>
            - Where logs appear
            - Key log messages to expect
            - Debug mode activation
        </logging-contract>

        <processing-results-summary>
            - Success message examples
            - Warning message examples
            - Failure message examples
        </processing-results-summary>

        <troubleshooting>
            - Common HelpfulError messages and solutions
            - Configuration problems and fixes
            - Quick diagnostic steps
        </troubleshooting>
    </required-sections>

    <forbidden-content>
        - NO architectural deep-dives
        - NO comprehensive configuration options
        - NO advanced customization details
        - NO implementation explanations
    </forbidden-content>
</readme-specifications>
```

**Generate README.md following the EXACT pattern in `ai/decided/readme-example_v3.3.md`**

**CRITICAL**: Use the example template as your TEMPLATE - copy the structure, sections, and style. Adapt the content to your specific script but maintain the same organization and approach.

**🛑 PHASE 6 COMPLETE: Wait for user command "begin in-depth documentation" before proceeding.**

---

## Phase 7: In-Depth Documentation (MAINTAINER FOCUS)

**🎯 Target Audience: "Experienced developer/maintainer needs deep understanding"**

**⚠️ IMPORTANT**: You are creating in-depth-readme.md for **THE SCRIPT**, not the template

**Template to use**: `ai/decided/in-depth-readme-example_v3.3.md`
- This is a PATTERN to copy (has header explaining it's a template)
- Replace placeholders with script-specific technical details
- Scale depth to script complexity (simple script = shorter, complex = comprehensive)

**Generated in-depth-readme.md**:
- Explains architecture and design rationale of YOUR script
- How to extend and customize your script
- Audience: Maintainers of your script

**in-depth-readme.md Content Contract:**
```xml
<in-depth-specifications>
    <target-audience>Experienced developers and maintainers</target-audience>
    <goal>Complete understanding for customization and maintenance</goal>
    <content-approach>Comprehensive reference with rationale</content-approach>

    <required-sections>
        <architecture-rationale>
            - Why TXO standardizes schema validation
            - Why ADR-B006 enforces UTC filenames
            - Why ProcessingResults pattern exists
            - Design decisions and trade-offs
        </architecture-rationale>

        <detailed-config-options>
            - Full explanation of script-behavior parameters
            - Timeout, retry, jitter, rate limiting configurations
            - Circuit breaker settings and edge cases
            - Batch handling parameters
        </detailed-config-options>

        <error-handling-patterns>
            - Complete HelpfulError taxonomy
            - When to treat empty results as warnings vs failures
            - Retry/backoff behavior details
            - Exception hierarchy usage
        </error-handling-patterns>

        <developer-extension-notes>
            - How to extend script to new APIs or companies
            - Adding new output formats
            - Logging integration patterns
            - Custom validation rules
        </developer-extension-notes>

        <comprehensive-examples>
            - Full configuration examples beyond minimal README ones
            - Advanced usage scenarios
            - Integration with other TXO scripts
            - Customization examples
        </comprehensive-examples>

        <references>
            - Links to relevant ADRs (B002–B012)
            - Links to utils-quick-reference_v3.3.md
            - Related TXO framework components
        </references>
    </required-sections>

    <content-principles>
        - DO NOT duplicate README content
        - EXPAND where README is minimal
        - EXPLAIN the "why" behind decisions
        - PROVIDE comprehensive examples
    </content-principles>
</in-depth-specifications>
```

**Generate in-depth-readme.md following the EXACT pattern in `ai/decided/in-depth-readme-example_v3.3.md`**

**CRITICAL**: Use the example template as your TEMPLATE - copy the structure, sections, and comprehensive approach. Focus on WHY decisions were made and HOW to customize/extend.

**🛑 PHASE 7 COMPLETE: Wait for user command "review documentation balance" before proceeding.**

---

## Phase 8: Documentation Balance Review (CONSISTENCY CHECK)

**🎯 Purpose: Ensure README and in-depth documentation complement each other properly**

**Documentation Balance Checklist:**

```xml
<documentation-balance-review>
    <consistency-check>
        <question>Do both documents reference the same script name and purpose?</question>
        <question>Are configuration examples consistent between files?</question>
        <question>Do command-line examples match in both documents?</question>
        <question>Are troubleshooting solutions consistent?</question>
    </consistency-check>

    <content-separation-audit>
        <readme-audit>
            - Contains ONLY quick-start essentials?
            - Stays within 2-screen limit?
            - Focuses on "how to run" not "how it works"?
            - No architectural explanations?
        </readme-audit>

        <in-depth-audit>
            - Contains comprehensive technical details?
            - Explains architectural decisions and rationale?
            - Provides advanced customization guidance?
            - Does NOT duplicate basic setup from README?
        </in-depth-audit>
    </content-separation-audit>

    <cross-reference-verification>
        - README points to in-depth for advanced topics?
        - in-depth references README for basic setup?
        - Both documents link to appropriate ADRs and utils-quick-reference?
    </cross-reference-verification>
</documentation-balance-review>
```

**If imbalances found:**
- **Adjust content allocation** between files
- **Fix duplications** or gaps
- **Ensure proper separation** of concerns

**Final Deliverables:**
1. **Compliant Python script** with TXO patterns
2. **README.md** targeting 15-minute success
3. **in-depth-readme.md** targeting maintainer deep-dive
4. **Configuration updates** if needed
5. **Documentation balance** verified

**🎉 PROJECT COMPLETE: All phases finished with proper validation and documentation separation**

---

## Final Step: Done-Done-Done (Git Operations)

**Project is done-done** (code + documentation complete)

**Next**: Git commit and tag for done-done-done (published)

**See**: `ai/reports/github-tagging-guide.md` for:
- TXO commit message template
- Git tagging strategy
- Example commit/tag for your script

**AI can help**:
- "Generate git commit message from my README.md and script following TXO pattern"
- AI will use github-tagging-guide template

**Commands**:
```bash
git add .
git commit -m "[TXO pattern message]"
git tag v1.0 -m "[tag message]"  # If creating release
```

---

## 🔧 **Enhanced Workflow Benefits**

### **For Non-Experienced Users:**
- **Cannot skip validation** - Mandatory Phase 4 with user confirmation
- **Clear content boundaries** - Know exactly what goes in each document
- **Step-by-step progression** - No overwhelming information dumps
- **Professional results** - PyCharm integration ensures code quality

### **For AI Compliance:**
- **Explicit phase boundaries** - Cannot rush through validation
- **Content specifications** - Clear guidelines for each deliverable
- **Pattern enforcement** - Multiple checkpoints prevent violations
- **Documentation balance** - Ensures proper separation of concerns

### **For Project Quality:**
- **Consistent documentation** - README vs in-depth serve different purposes
- **Validation pipeline** - Multiple quality gates
- **Professional standards** - PyCharm + TXO compliance
- **Maintainable output** - Proper separation supports long-term evolution

---

---

## Version History

### v3.2 (Current)
- Updated all document references to v3.2
- Added 5 new critical pattern reminders from refactoring learnings
- Enhanced Phase 5 with PyCharm alternatives (Options A/B/C)
- Added v3.2 patterns: logger exceptions, no sys.exit() in library code, AsyncOperationResult
- Added PyCharm false positive guidance (openpyxl, static methods)
- Updated forbidden patterns with v3.2 anti-patterns

### v3.1.1
- Enhanced prompt template with mandatory validation and documentation separation
- Added comprehensive phase-by-phase workflow

---

**Version:** v3.2
**Last Updated:** 2025-10-29
**Domain:** AI Development Workflow
**Purpose:** Enhanced prompt template with mandatory validation, v3.2 patterns, and flexible quality review options