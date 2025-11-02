# TXO Framework Refactoring Prompt v3.2

**Purpose**: Guide AI through systematic utils/ framework refactoring
**Audience**: Experienced coders, framework maintainers
**Workflow**: Assessment → Refactor → Validate → Document
**Duration**: 20-60 hours (varies by scope)
**Last Updated**: 2025-10-29

---

## 📋 Prompt Metadata

```xml
<refactoring-metadata>
    <version>3.2</version>
    <workflow-type>framework-refactoring</workflow-type>
    <audience>experienced-developers</audience>
    <breaking-changes>possible</breaking-changes>
    <requires-testing>mandatory</requires-testing>
    <requires-todo-tracking>mandatory</requires-todo-tracking>
</refactoring-metadata>
```

---

## 🎯 Phase 0: Pre-Assessment (MANDATORY)

**CRITICAL**: Do NOT start refactoring without completing this assessment phase.

### Required Reading (In Order)

1. **module-dependency-diagram.md** - Understand layer architecture ⭐ CRITICAL
   - Layer 1 (Foundation): exceptions, path_helpers
   - Layer 2 (Core): logger, api_common
   - Layer 3-6: All depend on Layer 2
   - **Key insight**: Logger is infrastructure (affects all layers)

2. **ai/decided/txo-business-adr_v3.3.md** - Business rules
   - Hard-fail philosophy (ADR-B003)
   - Documentation requirements (ADR-B015)
   - Naming conventions, secrets management

3. **ai/decided/txo-technical-standards_v3.3.md** - Technical patterns
   - **NEW in v3.2**: ADR-T011 (Memory Optimization), ADR-T012 (Library Boundaries)
   - Exception hierarchy (ADR-T004)
   - Method complexity limits (ADR-T010)

4. **ai/decided/utils-quick-reference_v3.3.md** - Available functions
   - Don't reinvent existing utilities
   - Understand what's already there

5. **CLAUDE.md** - TXO development workflow
   - 10-step development lifecycle
   - Commands and tools
   - Validation procedures

### User Preparation (Before Starting)

**Ask user to provide**:

```xml
<user-prep-checklist>
    <item priority="high" status="recommended">
        <action>Run PyCharm "Code → Inspect Code" on whole project</action>
        <output>Export XML results to code_inspection/ directory</output>
        <benefit>Finds issues across entire codebase, guides priorities</benefit>
    </item>
    <item priority="medium" status="optional">
        <action>Provide existing refactor plan</action>
        <file>ai/reports/refactor_v*.md</file>
        <benefit>Structured issues already identified</benefit>
    </item>
    <item priority="high" status="required">
        <action>Describe refactoring goals</action>
        <examples>Fix ADR violations, improve test coverage, reduce complexity</examples>
    </item>
</user-prep-checklist>
```

### AI META-DOCUMENTS (MANDATORY Creation)

**Per ADR-B015 and ADR-AI001-006, AI MUST create these working documents**:

```xml
<required-meta-documents>
    <document name="ai/TODO.md" status="MANDATORY">
        <format>UPPERCASE (AI working document)</format>
        <purpose>Granular task tracking (done → done-done)</purpose>
        <when>Phase 0 - BEFORE starting any refactoring</when>
        <content>
            - ALL issues found with priorities (HIGH/MEDIUM/LOW)
            - File paths and line numbers
            - Validation criteria per task
            - Status: pending/in-progress/completed
            - Estimated effort per task
        </content>
        <benefit>Enables resume, prevents forgotten tasks, tracks progress</benefit>
        <reference>ADR-B015 (mandatory), ADR-AI005 (pattern)</reference>
    </document>

    <document name="ai/PROJECT-STATUS.md" status="RECOMMENDED">
        <format>UPPERCASE (AI working document)</format>
        <purpose>High-level status (code/meta/hygiene progress)</purpose>
        <when>Phase 0 OR when work will span >1 session</when>
        <content>
            - Overall progress bars (code%, meta%, hygiene%)
            - What's complete vs pending
            - Hygiene checklist (meta-tasks for done-done)
            - High-level achievement summary
        </content>
        <benefit>Tracks done vs done-done, ensures completeness</benefit>
        <reference>ADR-AI005 (two-level tracking)</reference>
    </document>

    <document name="ai/AI-CONTEXT-BRIEF.md" status="OPTIONAL">
        <format>UPPERCASE (AI working document)</format>
        <purpose>Resume helper for multi-session (token optimization)</purpose>
        <when>If work expected to span multiple sessions or breaks</when>
        <content>
            - Key decisions made with rationale
            - Current status and next steps
            - What to read, what to ignore
            - Architecture insights discovered
        </content>
        <benefit>Quick resume with minimal token usage</benefit>
        <reference>ADR-AI003, large-refactoring-workflow_v3.3.md</reference>
    </document>
</required-meta-documents>
```

**Document Naming Convention** (per ADR-AI001):
- **UPPERCASE.md** = AI working files (temporary, user can delete after done-done)
- **kebab-case_v3.3.md** = Permanent docs (human-maintained, long-term)
- Visual signal: UPPERCASE immediately identifies AI scaffolding

**See**: `ai/decided/txo-ai-adr_v3.3.md` for complete AI workflow standards

### PROJECT-STATUS.md Template (Include TXO 10-Step Checklist)

**When creating ai/PROJECT-STATUS.md, include this structure**:

```markdown
## Meta-Work: TXO 10-Step Lifecycle

### Pre-Implementation (Optional)
- [ ] **Step 0: Update Dependencies** (before major releases)
  - Check: `uv pip list --outdated`
  - Update: `uv remove pkg && uv add pkg` (updates pyproject.toml)
  - Test: Verify imports and basic functionality

### Implementation Steps (1-5)
- [ ] Step 1: Discuss - Analyzed issues
- [ ] Step 2: Decision - ADRs updated
- [ ] Step 3: Todo - ai/TODO.md created
- [ ] Step 4: Code - Refactoring implemented
- [ ] Step 5: Validation - Tests passing

### Documentation Steps (6-10) ⚠️ OFTEN FORGOTTEN
- [ ] **Step 6: Utils Reference** ⚠️ UPDATE if functions added/changed
- [ ] Step 7: AI Prompts - Update if new patterns
- [ ] Step 8: Documentation - Update README if user-facing
- [ ] Step 9: Release Notes - Comprehensive changelog
- [ ] Step 10: Leftovers - Track future improvements

**Can't mark 100% done-done until ALL checked**
```

### ai/TODO.md Template (Include Meta-Tasks Section)

**ai/TODO.md should always include**:

```markdown
## META-TASKS (Steps 6-10 - Complete Before Done-Done)

### ⏳ Step 6: Update Utils Reference
- Check: Modified utils/*.py files?
- Action: Update utils-quick-reference_v{X}.md
- Add: New functions, classes, methods, properties
```

### AI Assessment (Mandatory Analysis)

**After creating META-DOCUMENTS, AI analyzes code**:

1. **Comprehensive code analysis**:
   - Analyze all utils/*.py files for ADR violations
   - Check PyCharm inspection results (if provided)
   - Review module-dependency-diagram.md for architectural issues
   - Identify specific line numbers for each violation

2. **Populate ai/TODO.md** with findings:
   - List ALL issues with priorities
   - Include file paths and line numbers
   - Add validation criteria per task
   - Estimate effort per task

3. **Update ai/PROJECT-STATUS.md** (if created):
   - Current overall status
   - Assessment complete, refactoring pending
   - Estimated progress to done-done

4. **Generate permanent assessment report**:
   - Create: ai/reports/assessment_v3.3.md (kebab-case, permanent)
   - Contains: Detailed findings, ADR gaps, recommendations
   - Reference from TODO.md for full context

5. **Present to user for approval**:
   - "Found X violations across Y files (see ai/TODO.md)"
   - "Estimated Z hours of work"
   - "Created ai/TODO.md with prioritized tasks"
   - "Potential breaking changes: ..."
   - **Wait for user "proceed" before starting Phase 1**

---

## ⚡ Critical Architecture Understanding

**From module-dependency-diagram.md**:

```
Layer 1 (Foundation) → Layer 2 (Core) → Layers 3-6 (Everything Else)
         ↓                    ↓                   ↓
    exceptions           logger              All import logger
    path_helpers        api_common          (8+ modules)
```

**CRITICAL INSIGHT**: Logger is **Layer 2 infrastructure**
- Imported at module level by ALL higher layers
- Changes to logger affect entire codebase
- **Infrastructure exception**: `setup_logger()` may call `sys.exit()` (see ADR-T012)
- Alternative (exception handling everywhere) violates DRY

**This understanding is CRITICAL** - guides decisions like logger strict mode pattern.

---

## 🔧 v3.2 Refactoring Principles

**Enforce these strictly** (per ADRs):

### Configuration (ADR-B003)
- ✅ Hard-fail on REQUIRED config: `config["key"]`
- ✅ Soft-fail on OPTIONAL data: `config.get("key")`
- ❌ Never soft-fail with defaults on required configuration

### Library Code Boundaries (ADR-T012)
- ❌ NO `sys.exit()` in library code (utils/)
- ✅ Library code raises exceptions
- ✅ **EXCEPTION**: `setup_logger()` infrastructure (documented in ADR-T012)
- ✅ Entry point functions (parse_args_and_load_config) may exit

### Object Encapsulation (ADR-T004)
- ❌ NO mutation of third-party object internals (e.g., `response._content`)
- ✅ Use wrapper classes (e.g., AsyncOperationResult)
- ✅ Type-safe and explicit

### Method Complexity (ADR-T010)
- ✅ Target: <50 lines per method
- ✅ Maximum: 100 lines (review required if exceeded)
- ✅ Extract helper methods for orchestration pattern

### Exception Handling (ADR-T004)
- ❌ NO broad catches: `except (JSONDecodeError, ValueError, AttributeError)`
- ✅ Specific handlers for each exception type
- ✅ Provide context in error messages

### Code Quality
- ✅ Make helper methods `@staticmethod` if they don't use `self`
- ✅ Keep indirect imports (e.g., `openpyxl` for pandas) with explanatory comments
- ✅ Remove unused imports from TYPE_CHECKING blocks

---

## 🎯 v3.2 Patterns to Implement

**NEW patterns from v3.2 refactoring experience**:

### 1. Logger Strict Mode
```python
# Normal usage - exits on error (infrastructure)
logger = setup_logger()

# Testing usage - raises exceptions
logger = setup_logger(strict=True)
```

**Why**: Layer 2 infrastructure, import-time initialization, avoids boilerplate

### 2. AsyncOperationResult Wrapper
```python
# For 202 Accepted responses
return AsyncOperationResult(
    data=result,
    status_code=200,
    original_response=response
)
# Provides .json(), .ok, .content (Response-compatible)
```

**Why**: No third-party mutation, type-safe, backward compatible

### 3. Circuit Breaker with Statistics
```python
breaker = CircuitBreaker(failure_threshold=5, timeout=60)
# New: .stats property with 9 metrics
stats = breaker.stats  # state, failure_rate, time_in_state, etc.
```

**Why**: Better observability, production monitoring

### 4. Adaptive Rate Limiting
```python
# Automatically adjusts based on X-RateLimit-* headers
# 4-tier system: 5%, 10%, 25%, 75% thresholds
manager.update_from_headers(url, response.headers)
```

**Why**: Prevents 429 errors proactively

---

## 📝 Refactoring Workflow

### Phase 1-N: Refactor by Priority

**For each task in ai/TODO.md**:

1. **Mark as in-progress** in ai/TODO.md
2. **Implement fix** following ADRs
3. **Validate immediately**:
   ```bash
   python -m py_compile utils/modified_file.py
   python tests/test_feature.py  # If test exists
   ```
4. **Mark as completed** in ai/TODO.md
5. **Move to next task**

**Don't batch**: Validate after EACH task, not at end

### Validation Commands

```bash
# After each file modification
python -m py_compile utils/file.py

# After each priority complete
python -m py_compile utils/*.py  # All utils
python tests/test_*.py  # All relevant tests

# Periodic ADR compliance check
grep -r "sys\.exit" utils/*.py  # Should only find setup_logger()
grep -r "config\.get(" utils/*.py  # Check each usage
```

---

## ✅ Success Discussion (Soft Criteria)

**After refactoring, AI should discuss** (not rigid checklist):

### Discussion Points

1. **ADR Compliance**
   - "Achieved 100% compliance across 15 ADRs"
   - "Are we compliant enough or need more work?"

2. **Trade-Offs Made**
   - "Logger infrastructure exception: practical over purist"
   - "Method at 65 lines: acceptable or should split further?"

3. **Breaking Changes**
   - "No breaking changes (infrastructure exception pattern)"
   - "Acceptable for release?"

4. **Test Coverage**
   - "Added 25 tests, all passing"
   - "Sufficient confidence for production?"

5. **Code Quality**
   - "Reduced complex code by 60%"
   - "Methods now average 44 lines (was 111)"
   - "Acceptable or more refactoring needed?"

6. **Architecture Alignment**
   - "Decisions aligned with module layers (logger = Layer 2)"
   - "Any architectural concerns?"

**Approach**: Collaborative discussion, not pass/fail metrics
**Reason**: Refactoring involves contextual trade-offs
**Goal**: User understands and agrees with decisions made

---

## 🔄 Multi-Session Support

**For refactorings >10 hours or spanning multiple days:**

See: `ai/prompts/large-refactoring-workflow_v3.3.md`

**Checkpoint Strategy**:
- ai/TODO.md updated continuously
- Session summaries created: ai/reports/session-summary_DATE.md
- ADR updates committed separately
- Git commits at priority boundaries

**Resume Pattern**:
```
1. Read ai/TODO.md (current status)
2. Read latest session summary (decisions made)
3. Verify last changes compile
4. Continue with next pending task
```

**Token Management**:
- Use Task tool for exploration (doesn't consume context)
- Reference documents by filename (not re-reading)
- Create summary docs frequently (external memory)

---

## 📚 Reference Documents

**Successful Example**: See ai/reports/refactor_v3.3.md and our actual v3.2 refactoring
- 16 tasks completed
- 100% ADR compliance achieved
- Demonstrates this workflow pattern working

**Workflow Pattern**: large-refactoring-workflow_v3.3.md
**Prompt Selection**: ai/prompts/README.md

---

## 🎓 Key Learnings from v3.2

**What Worked Exceptionally Well**:
1. ai/TODO.md tracking (managed 16 tasks effectively)
2. module-dependency-diagram.md understanding (guided logger decision)
3. PyCharm inspection (found issues across codebase)
4. Priority ranking (enabled logical break points)
5. Soft success discussion (enabled pragmatic trade-offs)

**Recommendations**:
- Always create ai/TODO.md in Phase 0 (ADR-B015 requirement)
- Always read module-dependency-diagram.md (architecture critical)
- Request PyCharm inspection results upfront (valuable data)
- Work priority-by-priority (enables resume)
- Discuss trade-offs explicitly (honesty > perfection)

---

## Before Marking Refactoring Complete - Step 6 Verification ⚠️

**CRITICAL**: AI MUST verify Step 6 (often forgotten in refactoring excitement)

**Check**: Did we add or modify any public functions/classes in utils/?

```xml
<step-6-verification>
    <question>What did we add/change in utils/?</question>
    <check-for>
        <item>New functions or methods</item>
        <item>New classes (e.g., AsyncOperationResult)</item>
        <item>Changed signatures (e.g., setup_logger gained strict parameter)</item>
        <item>New properties (e.g., CircuitBreaker.stats)</item>
        <item>Implemented stubs (e.g., update_from_headers)</item>
    </check-for>

    <if-yes>
        <action>Update ai/decided/utils-quick-reference_v{X}.md NOW</action>
        <add>
            - Function signatures with new parameters
            - New classes with usage examples
            - New properties with return types
            - Implemented features that were stubs
            - Update Version History section
        </add>
    </if-yes>

    <if-no>
        <action>Note in PROJECT-STATUS: "Step 6: N/A (no utils/ API changes)"</action>
    </if-no>
</step-6-verification>
```

**AI asks user before marking done-done**:
"I've completed refactoring. Should I update utils-quick-reference_v{X}.md with:
- [List specific additions]

Or mark Step 6 as N/A if no public API changes?"

**This check is MANDATORY** - can't proceed to done-done without addressing Step 6

---

## Final Step: Done-Done-Done (Git Operations)

**After Step 6 verification and user approves**:

**Project is done-done** (code + tests + ADRs + documentation)

**Next**: Git commit and tag for done-done-done (published)

**See**: `ai/reports/github-tagging-guide.md` for:
- TXO commit message template (comprehensive pattern)
- Git tagging strategy (annotated tags)
- Examples from actual refactorings

**AI can help**:
```
"Generate git commit message from ai/reports/release-notes_v3.3.md
 following TXO pattern in github-tagging-guide.md"
```

AI will create comprehensive commit message including:
- What changed (files, features, fixes)
- ADRs created/modified
- Test coverage
- Breaking changes (or none)
- Quality metrics

**Commands**:
```bash
git add .
git commit -m "[AI-generated comprehensive message]"
git tag v3.2 -m "[release summary]"
git push origin main --tags
```

---

## 📚 Documentation Guidance for Refactoring

**Template Examples** (ai/decided/*-example_v3.3.md):
- `readme-example_v3.3.md` and `in-depth-readme-example_v3.3.md`
- **Purpose**: TEMPLATES for Script Creating workflow (not project documentation)
- **Refactoring action**: Update ONLY if patterns shown are outdated/incorrect
- **Leave as-is**: If patterns still valid (don't update just for version number)

**Project README.md** (root):
- Documents the TXO Template project itself (how to use template)
- **Refactoring action**: Update if user-facing template features changed
- **For v3.2**: Optional (internal utils/ refactoring, not user-facing changes)

**Remember**: Script Creating uses templates to generate docs for created scripts, Refactoring updates internal framework

---

**Version**: v3.2
**Type**: Refactoring Workflow
**Format**: Markdown + Inline XML (per ADR-B016)
**Validated**: Successfully used for TXO v3.2 refactoring (16 tasks, 100% completion)
