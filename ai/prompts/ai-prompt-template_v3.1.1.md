# TXO AI Development Prompt Template v3.1.1

**\<remove_before_ai>**

> **Purpose**: Enhanced structured prompt with mandatory validation and clear documentation separation
> **Workflow**: 8 phases with explicit flow control and user confirmation points
> **Key Improvement**: Prevents AI from skipping validation and ensures proper documentation balance

## ⚠️ Human TODO before use

### Step-by-step Setup
1. Copy this prompt file and change its name
2. **Read** `ai/decided/txo-business-adr_v3.1.md` and browse `ai/decided/txo-technical-standards_v3.1.md`
3. Understand your requirements and target environment
4. Decide your `org_id` and `env_type` parameters
5. Fill in your details in Phase 2 (ERD in Mermaid format is recommended!)
6. Remove everything between "<remove_before_ai>" including the tags
7. Upload to AI with the command: **"Wait for my explicit command before starting each phase."**

### Template Validation Checklist
Before using this template, verify:
- [ ] All Phase 1 documents are current version (v3.1)
- [ ] You have specific, actionable requirements for Phase 2
- [ ] Script purpose aligns with TXO patterns (automation, data processing, API integration)
- [ ] You understand the difference between README vs in-depth documentation targets

---
**\</remove_before_ai>**

## Phase 1: Context Upload (RESEARCH ONLY - NO CODE)

**🚨 CRITICAL: DO NOT WRITE ANY CODE IN THIS PHASE. RESEARCH AND UNDERSTANDING ONLY.**

**Upload these documents to establish TXO patterns and available functions:**

```xml
<required-documents>
    <required-document>
        <doc-type>business-rules</doc-type>
        <file>ai/decided/txo-business-adr_v3.1.md</file>
        <purpose>Organizational patterns, hard-fail philosophy, naming conventions</purpose>
    </required-document>

    <required-document>
        <doc-type>technical-standards</doc-type>
        <file>ai/decided/txo-technical-standards_v3.1.md</file>
        <purpose>Python patterns, threading, exception handling, docstring standards</purpose>
    </required-document>

    <required-document>
        <doc-type>function-reference</doc-type>
        <file>ai/decided/utils-quick-reference_v3.1.md</file>
        <purpose>Complete list of existing functions - DO NOT INVENT THESE</purpose>
    </required-document>

    <required-document>
        <doc-type>example-readme</doc-type>
        <file>ai/decided/readme-example_v3.1.md</file>
        <purpose>Template for quick-start README.md targeting new developers</purpose>
    </required-document>

    <required-document>
        <doc-type>example-in-depth</doc-type>
        <file>ai/decided/in-depth-readme-example_v3.1.md</file>
        <purpose>Template for comprehensive documentation targeting maintainers</purpose>
    </required-document>
</required-documents>
```

**Instructions for Phase 1:**
- **READ AND UNDERSTAND** TXO business rules and technical patterns
- **STUDY** the available functions in `utils/` - DO NOT create new versions of existing functions
- **ANALYZE** the configuration patterns and JSON schema requirements
- **UNDERSTAND** the documentation separation: README (15-min success) vs in-depth (maintainer focus)

**🛑 PHASE 1 COMPLETE: Wait for user command "begin phase 2" before proceeding.**

---

## Phase 2: Requirements Specification (PLANNING ONLY - NO CODE)

**🚨 CRITICAL: DO NOT WRITE ANY CODE IN THIS PHASE. REQUIREMENTS GATHERING ONLY.**

**Fill in your script requirements below:**

```xml
<script-requirements>
    <script-metadata>
        <script-name>[your_script_name]</script-name>
        <script-purpose>[What business problem does this solve? Why does this script exist?]</script-purpose>
        <target-audience>[Who will use this? Technical level?]</target-audience>
        <complexity-level>[simple/moderate/complex]</complexity-level>
    </script-metadata>

    <org-env-context>
        <org-id>[your organization identifier]</org-id>
        <env-type>[test/qa/prod]</env-type>
        <requires-authentication>[true/false]</requires-authentication>
        <primary-use-case>[daily operations/one-time migration/data analysis/etc.]</primary-use-case>
    </org-env-context>

    <environment-reality>
        <!-- Describe the actual environment this script will work with -->
        [EXAMPLE:
        - Azure Tenant UUID: [tenant-id]
        - Business Central environment: [environment-name]
        - Companies to process: [company-list]
        - APIs required: [api-endpoints]
        - Authentication method: [client-credentials/etc.]
        - Rate limits: [calls per minute]
        ]
    </environment-reality>

    <data-contracts>
        <input-data>
            <!-- What data does the script process? Be specific about formats -->
            [EXAMPLE:
            - CSV file: data/customers.csv with columns [name, email, phone, address]
            - API responses: JSON with specific schema
            - File size expectations: [small <1MB / large >10MB]
            ]
        </input-data>

        <output-data>
            <!-- What does the script produce? Specify formats and naming -->
            [EXAMPLE:
            - Excel report: output/sync-results_YYYY-MM-DDTHHMMSZ.xlsx
            - JSON summary: output/processing-summary_YYYY-MM-DDTHHMMSZ.json
            - Log files: logs/script-execution_YYYY-MM-DDTHHMMSZ.log
            ]
        </output-data>

        <success-criteria>
            <!-- How do you know the script worked? -->
            [EXAMPLE:
            - All records processed without errors
            - Output file contains expected number of results
            - ProcessingResults shows: "✅ All 150 operations successful: 75 created, 75 updated"
            ]
        </success-criteria>
    </data-contracts>

    <business-logic>
        <!-- What are the processing rules? -->
        [EXAMPLE:
        - Skip records with missing email addresses
        - Update existing customers, create new ones
        - Generate summary report with counts and errors
        - Handle duplicate detection by email field
        ]
    </business-logic>

    <api-integrations>
        <api-endpoints>
            [EXAMPLE:
            - Business Central: GET/POST /api/v2.0/companies/{companyId}/customers
            - External API: GET https://api.example.com/data
            - Authentication: OAuth client credentials flow
            ]
        </api-endpoints>

        <resilience-requirements>
            [EXAMPLE:
            - Circuit breaker after 5 consecutive failures
            - Rate limiting: 100 calls per minute
            - Retry on 5xx errors with exponential backoff
            - Timeout: 30 seconds per request
            ]
        </resilience-requirements>
    </api-integrations>

    <error-handling>
        <!-- How should errors be handled? -->
        [EXAMPLE:
        - Invalid CSV format: Stop with helpful error message
        - API rate limit hit: Wait and retry automatically
        - Network timeout: Retry 3 times, then fail gracefully
        - Missing config: Exit with clear setup instructions
        ]
    </error-handling>
</script-requirements>
```

**Instructions for Phase 2:**
- **BE SPECIFIC** about data formats, API endpoints, and business rules
- **DEFINE CLEAR** success/failure criteria and error handling expectations
- **IDENTIFY** configuration that should be adjustable vs hard-coded
- **ASK USER** if any requirements are unclear or missing

**🛑 PHASE 2 COMPLETE: Wait for user command "begin phase 3" before proceeding.**

---

## Phase 3: Code Generation

**🚨 CRITICAL REMINDERS (Common AI Mistakes - Check These First):**

```xml
<critical-pattern-reminders>
    <!-- TOP 7 violations from real usage - update based on validation feedback -->
    <imports>✅ Use create_rest_api() NOT import requests</imports>
    <config-access>✅ Use config['key'] NOT config.get('key', default) - HARD FAIL</config-access>
    <directories>✅ Use Dir.OUTPUT NOT 'output' strings</directories>
    <timestamps>✅ Use save_with_timestamp() NOT manual datetime formatting - framework handles UTC</timestamps>
</invoke>
    <existing-helpers>✅ CHECK utils-quick-reference_v3.1.md - DO NOT reinvent existing functions</existing-helpers>
    <config-preservation>✅ DO NOT remove existing config data without clear user instructions</config-preservation>
    <schema-updates>✅ UPDATE JSON schema if adding new configuration fields</schema-updates>

    <!-- EVOLUTION TRACKING: Add new common violations here, remove ones that are no longer issues -->
    <!-- Example future additions based on usage patterns:
    <logging-context>✅ Use simple logging for local operations, hierarchical context only for external APIs</logging-context>
    <file-headers>✅ NO unnecessary "# src/script_name.py" file header comments</file-headers>
    -->
</critical-pattern-reminders>
```

**Now generate a complete Python script that:**

```xml
<code-requirements>
    <tko-compliance>
        <mandatory-patterns>
            - Use utils.script_runner.parse_args_and_load_config() for initialization
            - Use utils.load_n_save.TxoDataHandler() for all file operations
            - Use utils.path_helpers.Dir.* constants (NEVER string literals)
            - Use utils.api_factory.create_rest_api() for HTTP clients
            - Use utils.logger.setup_logger() for logging
        </mandatory-patterns>

        <forbidden-patterns>
            - DO NOT import requests directly (use create_rest_api)
            - DO NOT use manual datetime formatting (use get_utc_timestamp)
            - DO NOT use string literals for directories (use Dir.*)
            - DO NOT add timing/performance metrics unless requested
            - DO NOT use config.get() with defaults (use config[] hard-fail)
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
        <required-fix>Use utils-quick-reference_v3.1.md complete script pattern</required-fix>
    </framework-patterns>
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

## Phase 5: PyCharm Quality Review (OPTIONAL ENHANCEMENT)

**This phase is optional but recommended for professional code quality.**

### **Step-by-Step PyCharm Inspection Instructions**

**Please follow these exact steps to generate code quality feedback:**

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
- **PyUnusedImportsInspection**: Unused imports
- **PyBroadExceptionInspection**: Overly broad exception handling
- **PyShadowingNamesInspection**: Variable naming conflicts
- **PyUnusedLocalInspection**: Unused variables (review if legitimate pattern)

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

**🛑 PHASE 5 COMPLETE: Wait for user command "begin documentation" before proceeding.**

---

## Phase 6: README Generation (15-MINUTE SUCCESS FOCUS)

**🎯 Target Audience: "New developer needs 15 minutes to success"**

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
            - Clone/download steps
            - Virtual environment creation
            - Dependency installation
            - Configuration file preparation
            - First run verification
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

**Generate README.md following the EXACT pattern in `ai/decided/readme-example_v3.1.md`**

**CRITICAL**: Use the example template as your TEMPLATE - copy the structure, sections, and style. Adapt the content to your specific script but maintain the same organization and approach.

**🛑 PHASE 6 COMPLETE: Wait for user command "begin in-depth documentation" before proceeding.**

---

## Phase 7: In-Depth Documentation (MAINTAINER FOCUS)

**🎯 Target Audience: "Experienced developer/maintainer needs deep understanding"**

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
            - Links to utils-quick-reference_v3.1.md
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

**Generate in-depth-readme.md following the EXACT pattern in `ai/decided/in-depth-readme-example_v3.1.md`**

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

**Version:** v3.1.1
**Last Updated:** 2025-09-28
**Domain:** AI Development Workflow
**Purpose:** Enhanced prompt template with mandatory validation and documentation separation