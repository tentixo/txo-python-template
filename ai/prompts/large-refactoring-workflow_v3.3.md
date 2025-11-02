# Large Refactoring Workflow v3.2

**Purpose**: Pattern for resumable multi-session refactoring
**Based On**: Actual TXO v3.2 refactoring experience (16 tasks, ~16 hours)
**Audience**: Framework maintainers, experienced developers
**Use With**: refactoring-xml-ai-prompt_v3.2.xml.md

---

## Overview

Large refactorings (>10 hours, >5 files, multiple sessions) need special handling for:
- **Resumability**: Can pause and continue later
- **Token Management**: Don't re-read everything on resume
- **State Preservation**: Know what's done, what's pending
- **Context Continuity**: Decisions and rationale preserved

This workflow pattern enables refactorings that span days or weeks.

---

## The Core Pattern: Checkpoint-Resume

### Checkpoint Strategy (Save State)

**Create checkpoints at these milestones**:

1. **Phase 0 Complete** → `ai/TODO.md` created (MANDATORY per ADR-B015)
2. **After each priority** → Update `ai/TODO.md` with status
3. **End of session** → Create `ai/reports/session-summary_YYYY-MM-DD.md`
4. **ADR updates** → Commit ADR changes separately
5. **Major milestones** → Git commits with clear messages

**Checkpoint Documents** (External Memory):
- `ai/TODO.md` - Current task status, what's next
- `ai/reports/refactor_v*.md` - Original plan and analysis
- `ai/reports/adr-gap-analysis_v*.md` - ADR coverage analysis
- `ai/reports/adr-compliance-verification_v*.md` - Compliance status
- `ai/reports/session-summary_DATE.md` - What happened in session
- `ai/reports/release-notes-v*.md` - Changes and migration guide

### Resume Pattern (Continue Work)

**When resuming after a break**:

```
1. AI reads state documents:
   - ai/TODO.md (what's done, what's pending)
   - Latest session summary (decisions made)
   - ADR updates (new patterns added)

2. AI verifies last changes:
   - python -m py_compile utils/*.py (syntax OK?)
   - Check last modified files compile

3. AI asks user:
   - "Continue from Priority X (next pending in ai/TODO.md)?"
   - "Or reassess current state first?"

4. AI proceeds:
   - Update ai/TODO.md status to in-progress
   - Work on task
   - Validate
   - Mark completed
   - Move to next
```

**Resume Command Template**:
```
"I'm resuming the v3.2 refactoring. Please:
1. Read ai/TODO.md to see current status
2. Read ai/reports/session-summary_2025-10-29.md for last session
3. Tell me what's completed and what's next
4. Continue with the next pending priority"
```

---

## 🎯 ai/TODO.md Pattern (Mandatory)

**Per ADR-B015**, framework refactoring MUST create and maintain ai/TODO.md

**Template Structure**:

```markdown
# TXO v3.2 Refactoring Todo List

**Status**: In Progress
**Started**: 2025-10-29
**Target Version**: v3.2

## PHASE 1: Planning & ADR Updates

### ✅ Task 1.1: Create ai/TODO.md
**Status**: COMPLETED
**File**: ai/TODO.md
This document.

### 🔄 Task 1.2: Add Memory Optimization ADR
**Status**: IN PROGRESS
**Files**: ai/decided/txo-technical-standards_v3.3.md
**Objective**: Formalize __slots__ usage strategy
**Actions**:
- Add ADR-T011 content
- Document decision matrix
**Validation**:
- [ ] ADR added
- [ ] Examples provided

### ⏳ Task 1.3: Review ADR Gaps
**Status**: PENDING
...
```

**Key Elements**:
- Status indicators: ✅ completed, 🔄 in-progress, ⏳ pending
- File references with paths
- Line numbers for specific issues
- Validation criteria per task
- Estimated effort

---

## 📝 Session Summary Pattern

**Create at end of each session**: `ai/reports/session-summary_DATE.md`

**Template**:

```markdown
# Refactoring Session Summary - 2025-10-29

## Session Metadata
- Duration: 4 hours
- Tasks Completed: 3/16 (19%)
- Files Modified: 5
- Tests Added: 2

## What Was Accomplished

### Priority 1: Logger Exception Refactoring
- **Completed**: ✅
- **Changes**: Replaced 10 sys.exit() with exceptions
- **Files**: utils/logger.py, utils/exceptions.py, src/try_me_script.py
- **Tests**: Syntax validated, functional test passed

[... repeat for each completed task ...]

## Decisions Made

1. **Logger Infrastructure Exception**: After reviewing module-dependency-diagram.md,
   decided setup_logger() is infrastructure (Layer 2). Added strict parameter instead
   of forcing exception handling everywhere. Rationale: ...

2. **AsyncOperationResult Design**: Chose wrapper pattern over mutation. Reason: ...

## Issues Encountered

1. **Circular Import (logger ↔ path_helpers)**: Fixed with lazy imports
2. **PyCharm False Positive**: openpyxl appears unused but is required

## Next Session

**Start With**:
- Priority 4: OAuth Config Hard-Fail Fix (estimated 30 min)
- Read: ai/TODO.md for current status
- Check: Last commits compile correctly

**Context Preserved In**:
- ai/TODO.md (updated with completed tasks)
- This summary (decisions and issues)
- ADR-T012 (infrastructure exception documented)
```

---

## 🔧 Token Management Strategies

### Problem: AI Context Limits

**Challenge**: Large refactorings require reading many files, can hit token limits

**Solutions**:

#### 1. Use Task Tool for Exploration
```
Instead of: Reading 10 utils files directly in main conversation
Do: "Use Task tool to explore utils/ and report findings"
Benefit: Task tool doesn't consume main context
```

#### 2. Create Summary Documents Frequently
```
After analysis: Create ai/reports/adr-gap-analysis_v3.3.md
After validation: Create ai/reports/adr-compliance-verification_v3.3.md
Benefit: Reference filename instead of re-reading content
```

#### 3. Reference Decisions by Document
```
Instead of: "As we discussed earlier about logger..."
Do: "Per ai/reports/session-summary_2025-10-29.md, logger decision was..."
Benefit: Explicit reference, no context searching
```

#### 4. Progressive Disclosure
```
Phase 0: Read architecture docs (module-dependency-diagram, ADRs)
Phase 1-N: Read specific files only when working on them
Don't: Read entire codebase upfront
```

---

## 📊 Real Example: TXO v3.2 Refactoring

**Scope**: 10 priorities, 16 tasks total
**Duration**: ~16 hours (estimated 40-60, actual much faster with AI)
**Sessions**: Could have been 2-3 sessions with resume

**Checkpoint Documents Created**:
1. `ai/TODO.md` - 16 tasks with status tracking
2. `ai/reports/adr-gap-analysis_v3.3.md` - Initial assessment
3. `ai/reports/adr-compliance-verification_v3.3.md` - Final validation
4. `ai/reports/release-notes-v3.2.md` - Comprehensive changes log
5. ADR updates: ADR-T011, ADR-T012, enhancements to ADR-T004, ADR-B004

**What Enabled Resume**:
- ai/TODO.md showed exactly what was done (15/16 after first session)
- ADR documents preserved decisions
- Git commits had clear messages
- Could resume at any priority boundary

**Hypothetical Resume Scenario**:
```
End of Session 1: Completed Priorities 1-7 (high + medium)
Session 2 Start:
  - Read ai/TODO.md: Shows 8-10 pending (low priority)
  - Read session-summary: Decisions about logger, AsyncOperationResult
  - Continue with Priority 8 (path helpers)
  - No re-analysis needed, jump right in
```

---

## ⚡ Quick Resume Checklist

When resuming refactoring work:

```bash
# 1. Check state
cat ai/TODO.md | grep -A2 "in_progress\|pending" | head -20

# 2. Verify last changes work
python -m py_compile utils/*.py
python -m src.try_me_script demo test  # Quick smoke test

# 3. Read context
cat ai/reports/session-summary_LATEST.md

# 4. Continue
# Tell AI: "Resume refactoring from Priority X per ai/TODO.md"
```

---

## 🎯 Success Criteria (Soft Discussion)

**After refactoring, AI should discuss**:

1. **Achievements**
   - "We fixed 8 ADR violations across 9 files"
   - "Reduced complex code by 60% (200 lines)"
   - "Added 25 test scenarios, all passing"

2. **Trade-offs**
   - "Logger infrastructure exception: practical over purist"
   - "Method complexity: 65-line orchestrator acceptable"
   - "Kept pre-existing cosmetic issues for future"

3. **Questions for User**
   - "100% ADR compliance achieved - acceptable?"
   - "Breaking changes limited to X - proceed with release?"
   - "Test coverage at Y% - sufficient for confidence?"

4. **Future Improvements**
   - "Could add unit tests for new helper methods"
   - "Performance benchmarks recommended before production"
   - "Consider addressing cosmetic issues in v3.3"

**NOT**: Rigid pass/fail metrics
**BUT**: Collaborative assessment of value delivered

---

## 📋 Lessons from v3.2 Refactoring

### What Worked Well

1. **ai/TODO.md tracking** - Essential for managing 16 tasks
2. **Priority ranking** - High→Medium→Low enabled smart breaks
3. **Phase-by-phase approach** - Could validate after each priority
4. **PyCharm inspection** - Found issues we missed manually
5. **Module dependency understanding** - Guided logger infrastructure decision
6. **Soft success discussion** - Enabled pragmatic trade-offs

### What Could Improve

1. **Upfront architecture review** - Should have read module-dependency-diagram.md earlier
2. **PyCharm integration** - Should request inspection results in Phase 0
3. **Test creation timing** - Should create tests immediately after each fix
4. **Documentation updates** - Should update docs progressively, not at end

### Recommendations for Future

1. **Always start with Phase 0** (assessment + ai/TODO.md)
2. **Request PyCharm inspection upfront** (finds cross-cutting issues)
3. **Update ai/TODO.md religiously** (enables resume anywhere)
4. **Create session summaries** (preserve decisions and context)
5. **Test after each priority** (don't batch testing)
6. **Discuss trade-offs explicitly** (better than hiding them)

---

## 🔮 Future Enhancements

**Potential additions to this workflow**:

1. **SKILLS.md integration** (exploring today)
   - Modular refactoring skills
   - Resume from saved state
   - Better context management

2. **Automated checkpoint creation**
   - AI auto-creates session summary
   - Auto-updates ai/TODO.md
   - Git auto-commits at boundaries

3. **Progress dashboards**
   - Visual task completion
   - ADR compliance metrics
   - Test coverage graphs

4. **AI memory optimization**
   - Smart document references
   - Progressive file reading
   - Context compression techniques

---

## 📚 Related Documents

- **Refactoring Prompt**: `ai/prompts/refactoring-xml-ai-prompt_v3.2.xml.md`
- **ADR-B015**: Documentation requirements (includes ai/TODO.md mandate)
- **CLAUDE.md**: TXO development lifecycle
- **module-dependency-diagram.md**: Architecture layers and dependencies

---

**Version**: v3.2
**Created**: 2025-10-29 (from v3.2 refactoring experience)
**Status**: Production-ready pattern
**Validated**: Successfully used for TXO v3.2 refactoring (16 tasks, 100% completion)
