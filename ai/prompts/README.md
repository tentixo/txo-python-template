# TXO AI Prompts Guide v3.3

**Purpose**: Guide for selecting the right AI prompt for your task
**Audience**: TXO users working with AI assistants
**Last Updated**: 2025-10-29

---

## 📋 Available Prompts

### 1. ai-prompt-template_v3.3.md

**Use For**: Creating ONE new script
**Workflow Type**: Script Creating
**Audience**: Less experienced coders, AI-first users
**Duration**: 2-4 hours typical
**Phases**: 8 (context → requirements → code → validation → quality → docs → balance)

### 2. refactoring-ai-prompt_v3.3.md

**Use For**: Improving utils/ framework
**Workflow Type**: Refactoring
**Audience**: Experienced coders, framework maintainers
**Duration**: 20-60 hours typical
**Phases**: Variable (assessment → refactor by priority → validate → document)
**Format**: Markdown + inline XML (per ADR-B016)

### 3. large-refactoring-workflow_v3.3.md

**Use For**: Multi-session refactoring guidance
**Workflow Type**: Reference pattern
**Audience**: Anyone doing large refactoring
**Duration**: Pattern/reference (not a prompt)
**Purpose**: Resume capability, state preservation, token management

---

## 🎯 When to Use Which Prompt

### Flowchart Decision Tree

```
Start
  |
  ├─ Creating new script? ───────> ai-prompt-template_v3.3.md
  |                                  └─ Generates: script + tests + docs
  |
  ├─ Improving utils/ framework? ──> refactoring-xml-ai-prompt_v3.3.xml.md
  |                                  └─ Generates: refactored utils + tests + ADRs
  |
  └─ Multi-session work? ──────────> Reference: large-refactoring-workflow_v3.3.md
                                     └─ Provides: Resume pattern, checkpoints
```

---

## 📊 Detailed Comparison

| Aspect            | Script Creating                     | Refactoring                                       |
|-------------------|-------------------------------------|---------------------------------------------------|
| **Prompt File**   | ai-prompt-template_v3.3.md          | refactoring-ai-prompt_v3.3.md                     |
| **Output**        | 1 script + config + tests + docs    | Multiple utils files + ADRs + tests               |
| **Audience**      | Less experienced                    | Experienced                                       |
| **Duration**      | 2-4 hours                           | 20-60 hours                                       |
| **Documentation** | README + in-depth (mandatory)       | ai/TODO.md + ADRs (mandatory), user docs optional |
| **Tests**         | Ask user (comprehensive/smoke/none) | Mandatory (refactoring requires tests)            |
| **ADRs**          | Reference only                      | May add/update ADRs                               |
| **Validation**    | TXO compliance + optional PyCharm   | Comprehensive ADR compliance                      |
| **Resumability**  | Single session typical              | Multi-session with checkpoints                    |

---

## 🚀 Quick Start

### For Script Creating:

```bash
# 1. Copy and customize the template
cp ai/prompts/script-ai-prompt-template_v3.3.md my-script-prompt.md

# 2. Fill in Phase 2 requirements (script purpose, data contracts, etc.)

# 3. Remove <remove_before_ai> sections

# 4. Upload to AI with command:
#    "Wait for my explicit command before starting each phase."

# 5. Progress through phases with AI
```

**Key Phases**:

- Phase 1: Upload ADRs and references (AI learns patterns)
- Phase 2: Define requirements + decide on tests/docs
- Phase 3: AI generates code
- Phase 4: Mandatory validation
- Phase 5: Optional quality review (PyCharm/lightweight/skip)
- Phase 6-7: Generate documentation (README + in-depth)
- Phase 8: Balance review

---

### For Refactoring:

```bash
# 1. Prepare PyCharm inspection results (recommended)
#    PyCharm → Code → Inspect Code → Export XML to code_inspection/

# 2. Upload refactoring prompt to AI:
#    Use: ai/prompts/refactoring-ai-prompt_v3.3.md
#    (Human-friendly markdown format per ADR-B016)

# 3. Start with assessment command:
#    "Read the refactoring prompt and start Phase 0 assessment"

# 4. AI will create ai/TODO.md with all issues

# 5. Progress through priorities one-by-one
```

**Key Phases**:

- Phase 0: Assessment (create ai/TODO.md - MANDATORY)
- Phase 1-N: Refactor by priority (update ai/TODO.md status)
- Validation: Continuous (after each priority)
- Documentation: Update ADRs if new patterns, user docs if needed

---

## 💡 Best Practices

### For Script Creating (ai-prompt-template):

**DO**:

- ✅ Fill Phase 2 requirements completely (AI needs context)
- ✅ Ask for tests (comprehensive recommended)
- ✅ Generate both README + in-depth (per ADR-B015)
- ✅ Run Phase 4 validation (mandatory)
- ✅ Use Phase 5 Option B (lightweight) if no PyCharm

**DON'T**:

- ❌ Skip Phase 2 requirements (AI will guess, likely wrong)
- ❌ Skip Phase 4 validation (catches TXO violations)
- ❌ Skip documentation (ADR-B015 requires it)

### For Refactoring (refactoring-ai-prompt):

**DO**:

- ✅ Run PyCharm inspection first (finds issues across codebase)
- ✅ Read module-dependency-diagram.md (understand architecture)
- ✅ Create ai/TODO.md (MANDATORY per ADR-B015)
- ✅ Work priority-by-priority (enables breaks/resume)
- ✅ Update ADRs if new patterns discovered
- ✅ Comprehensive testing (can't refactor without tests)

**DON'T**:

- ❌ Skip Phase 0 assessment (need to understand current state)
- ❌ Skip ai/TODO.md creation (lose track without it)
- ❌ Rush through priorities (test each before next)
- ❌ Skip ADR updates (future refactorings need patterns)

---

## 🔄 Multi-Session Refactoring

For large refactorings that span multiple sessions, see:
**large-refactoring-workflow_v3.3.md**

**Provides**:

- Checkpoint strategy (save state)
- Resume pattern (continue work)
- Token management (external memory)
- Session summary pattern

**Example**: Our v3.3 refactoring (16 tasks) used this pattern successfully

---

## 📝 Prompt Selection Checklist

**Use ai-prompt-template_v3.3.md when**:

- [ ] Creating ONE new script
- [ ] Have specific business requirements
- [ ] Need user-facing documentation
- [ ] Want AI to follow structured 8-phase workflow

**Use refactoring-xml-ai-prompt_v3.3.xml.md when**:

- [ ] Improving utils/ framework code
- [ ] Fixing ADR violations across multiple files
- [ ] Adding new patterns to framework
- [ ] Have PyCharm inspection results
- [ ] Work might span multiple sessions

**Reference large-refactoring-workflow_v3.3.md when**:

- [ ] Refactoring will take >10 hours
- [ ] Might need to pause and resume
- [ ] Managing token limits
- [ ] Want checkpoint/resume capability

---

## 🎓 Learning Resources

**Before Using Prompts, Read**:

1. `CLAUDE.md` - TXO development lifecycle and commands
2. `ai/decided/txo-business-adr_v3.3.md` - Business rules
3. `ai/decided/txo-technical-standards_v3.3.md` - Technical patterns
4. `ai/decided/txo-ai-adr_v3.3.md` - AI patterns
5. `module-dependency-diagram.md` - Architecture layers

**After Using Prompts, Update**:

1. `ai/reports/release-notes-v*.md` - Document what changed
2. `ai/TODO.md` - Track refactoring progress (if applicable)
3. ADRs - If new patterns discovered

---

## 🔍 Troubleshooting

**Q: Which prompt for fixing a bug in utils/?**
A: refactoring-ai-prompt_v3.3.md (even for one file, use framework workflow)

**Q: Which prompt for creating a test for existing script?**
A: ai-prompt-template (generate test in Phase 3, skip doc generation)

**Q: Can I use both prompts together?**
A: No - choose one workflow. But you can reference patterns from both.

**Q: What if I start script creation but realize I need framework refactoring?**
A: Stop, switch to refactoring-xml-ai-prompt, assess utils/ first

**Q: How do I know if refactoring is "large"?**
A: If >10 hours OR might need breaks OR touching >5 utils files

---

## 📦 Quick Reference

### Script Creating Command

```
Upload: ai-prompt-template_v3.3.md (customized with your Phase 2 requirements)
Start: "Wait for my explicit command before starting each phase."
Progress: Phase-by-phase with user confirmation
```

### Refactoring Command

```
Upload: refactoring-ai-prompt_v3.3.md
Format: Markdown + inline XML (human-friendly per ADR-B016)
Start: "Read the refactoring prompt and start Phase 0 assessment"
Progress: Priority-by-priority, update ai/TODO.md
```

---

**Version**: v3.3
**Last Updated**: 2025-10-29
**Maintainer**: TXO Framework Team
**Feedback**: Update prompts based on usage patterns and learnings
