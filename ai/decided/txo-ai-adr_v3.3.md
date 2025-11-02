# TXO AI Workflow Architecture Decision Records v3.2

**Purpose**: AI-specific workflow patterns, document lifecycle, and meta-task management
**Audience**: AI assistants, framework maintainers
**Scope**: How AI works with TXO projects, not business/technical decisions
**Last Updated**: 2025-10-29

---

## ADR-AI001: Dual Document Naming Convention

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

AI assistants create numerous documents during development: task trackers, status reports, session summaries, drafts, and analysis. Without clear naming conventions, these proliferate with inconsistent names (AI-CONTEXT-BRIEF.md, DOCUMENTATION-AUDIT-COMPLETE.md, etc.), confusing beginners and cluttering the project.

Users need visual signals to distinguish:
- Permanent documentation (read these, maintain these)
- AI working documents (temporary scaffolding)

### Decision

**Use dual naming convention with visual distinction**:

**kebab-case_v{version}.md** - Long-term, permanent, human-maintained:
- Examples: `release-notes_v3.3.md`, `adr-gap-analysis_v3.3.md`
- Characteristics: Versioned, archived when superseded, human-editable
- Survive to production, referenced in future work

**UPPERCASE.md** - AI working documents, temporary, meta-scaffolding:
- Examples: `TODO.md`, `PROJECT-STATUS.md`, `AI-CONTEXT-BRIEF.md`
- Characteristics: No version, deleted after done-done, AI-centric
- Purpose: Track progress, enable resume, optimize tokens

### Visual Signal Benefit

**Beginners see**:
- `UPPERCASE.md` → "AI is working, I can skip these"
- `kebab-case_v3.3.md` → "Important permanent docs, I should read"

**Clear separation**: Production docs vs working scaffolding

### Implementation

**Location Rules**:
- **Permanent docs**: ai/decided/, ai/prompts/, ai/reports/
- **Working docs**: ai/ (root) or ai/working/
- **Convention**: UPPERCASE in ai/working/, kebab-case in subdirectories

**Examples**:
```
✅ ai/TODO.md (working, granular tasks)
✅ ai/PROJECT-STATUS.md (working, high-level status)
✅ ai/working/SESSION-SUMMARY_2025-10-29.md (temporary)
✅ ai/reports/release-notes_v3.3.md (permanent)
✅ ai/decided/txo-business-adr_v3.3.md (permanent)

❌ ai/AI-CONTEXT-BRIEF_v3.3.md (working docs don't get versions)
❌ ai/reports/ASSESSMENT-REPORT.md (permanent docs use kebab-case)
```

### Consequences

**Positive**:
- Instant visual understanding of document purpose
- Beginners not overwhelmed (can ignore UPPERCASE initially)
- Clear lifecycle (UPPERCASE temporary, kebab-case permanent)
- Reduces document clutter (UPPERCASE deleted after done-done)

**Negative**:
- Mixed convention (but intentional, purposeful)
- AI must remember which format for which purpose
- Unconventional (but uniquely effective)

**Mitigation**: Document standard clearly, include in AI prompts, enforce in ADR

---

## ADR-AI002: Archive and old/ Directory Handling

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

Projects accumulate superseded versions of documents over time. These old versions are valuable for historical reference but MUST NOT be used by AI as current guidance. AI reading outdated patterns causes incorrect code generation.

### Decision

**AI MUST ignore all old/ subdirectories in ALL locations.**

**old/ directories may exist anywhere**:
- Project root: `/old/`
- AI directories: `ai/old/`, `ai/decided/old/`, `ai/prompts/old/`, `ai/reports/old/`
- Any subdirectory: `*/old/`

**Also applies to**: archive/ (legacy naming) - treat same as old/

### AI Behavior Rules

**NEVER**:
- ❌ Read files in old/ directories (unless explicitly instructed)
- ❌ Reference patterns from old/ directories
- ❌ Apply outdated versions of ADRs, patterns, or guidelines
- ❌ Use old/ files as examples or templates

**ALWAYS**:
- ✅ Read current version files (highest version number)
- ✅ Ignore superseded versions if newer exists
- ✅ Ask user if uncertain which version is current

**EXCEPTION**: User explicitly instructs "check old/ for..." or "compare with old version"

### Advanced Control

**For pro users**: Create `.claudeignore` file in project root for additional ignore patterns (like .gitignore for AI).

**Example .claudeignore**:
```
# Archives
**/old/
**/archive/

# Specific old versions
*_v3.0.md
*_v3.1.md

# Working drafts
ai/working/DRAFT-*.md
```

### Consequences

**Positive**:
- AI always uses current patterns
- No confusion from outdated ADRs
- Users can keep historical reference safely
- Simple rule (ignore old/)

**Negative**:
- AI can't automatically compare versions (must ask user)
- Users must manually archive (no auto-move)

**Mitigation**: Clear documentation, consistent naming, user control over archival

---

## ADR-AI003: AI Working Directory (ai/working/)

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

AI creates temporary scaffolding documents during development: drafts, session notes, assessment reports, checklists. These clutter ai/ root and mix with permanent documents.

### Decision

**Use ai/working/ for all UPPERCASE temporary documents.**

### Directory Structure

```
ai/
├── TODO.md                          # Exception: Root (high visibility)
├── PROJECT-STATUS.md                # Exception: Root (high visibility)
├── AI-CONTEXT-BRIEF.md             # Exception: Root (quick access)
│
└── working/                         # Temporary scaffolding
    ├── SESSION-SUMMARY_2025-10-29.md
    ├── ASSESSMENT-DRAFT.md
    ├── COMPLETION-CHECKLIST.md
    ├── DECISIONS-LOG.md
    └── old/                         # User archives completed sessions
```

**Root vs working/ Decision**:
- **ai/ root**: High-visibility working docs (TODO, STATUS, BRIEF)
- **ai/working/**: Session-specific and draft documents

### Standard Working Documents

**ai/TODO.md** (ai/ root):
- Granular task tracking (Priority 1.1, 1.2, etc.)
- Status: pending/in-progress/completed
- Enables resume at task level
- MANDATORY for Refactoring workflow (ADR-B015)

**ai/PROJECT-STATUS.md** (ai/ root):
- High-level progress (Code done, Meta-work 75%)
- Done vs Done-Done tracking
- Hygiene checklist
- User-facing status summary

**ai/AI-CONTEXT-BRIEF.md** (ai/ root):
- Resume helper (multi-session, token optimization)
- Key decisions condensed
- What to read, what to ignore
- Current version and status

**ai/working/SESSION-SUMMARY_DATE.md**:
- One per work session
- What was accomplished
- Decisions made
- Issues encountered
- Content captured in Version History footers
- User deletes or archives after done-done

### Lifecycle

1. **Created**: AI generates during work
2. **Updated**: AI maintains throughout session
3. **Finalized**: Key content moved to permanent docs
4. **Cleanup**: User manually deletes or moves to old/

**User decides**: Delete (if captured elsewhere) or archive (for reference)

### Consequences

**Positive**:
- Clear organization (root vs working/)
- UPPERCASE documents grouped together
- Easy to find temporary vs permanent
- User controls cleanup

**Negative**:
- Slight complexity (root + working/)
- User must manually clean up

**Mitigation**: Clear rules, user decides when to archive/delete

---

## ADR-AI004: Session Summary to Version History

**Status:** RECOMMENDED
**Date:** 2025-10-29

### Context

Multi-session work generates session summaries that capture decisions, issues, and progress. These are valuable context but create document proliferation. Long-term documents need historical context.

### Decision

**Condense SESSION-SUMMARY content into Version History footers** of permanent documents.

### Implementation

**During session**: Maintain ai/working/SESSION-SUMMARY_DATE.md

**After session**: Add condensed entry to relevant permanent docs

**Example**:

SESSION-SUMMARY_2025-10-29.md contains:
```
Refactored logger with strict mode parameter. Key decision: Logger is
infrastructure (Layer 2 per module-dependency-diagram.md), infrastructure
exception justified. Added ADR-T011 (memory optimization), ADR-T012
(library boundaries). Implemented AsyncOperationResult wrapper.
```

Becomes in release-notes_v3.3.md Version History:
```markdown
## Version History

**Session 2025-10-29**: Refactored logger (strict mode infrastructure
exception), adaptive rate limiter, AsyncOperationResult wrapper. Key
decision: Logger Layer 2 exception per architecture analysis.
```

**After capture**: User deletes SESSION-SUMMARY or moves to ai/working/old/

### Benefits

- Permanent docs have decision history
- Session summaries can be deleted (no information loss)
- Condensed history is readable
- Full details in permanent docs if needed

---

## ADR-AI005: Meta-Task Completion Tracking

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

Projects have two completion levels:
- **Done**: Code works, tests pass
- **Done-Done**: Meta-tasks complete (docs, versions, hygiene, commit/tag)

Without tracking meta-tasks, projects feel "finished" when code works, but lack completeness (documentation gaps, version mismatches, no git tag).

### Decision

**Use two-level tracking**: TODO.md (tactical) + PROJECT-STATUS.md (strategic)

### Structure

**ai/TODO.md** - Tactical (get to "done"):
```markdown
## PHASE 2: Implementation
- [x] Priority 1: Logger refactoring
- [x] Priority 2: Rate limiter
...

## PHASE 3: Validation
- [x] Run all tests
- [x] ADR compliance check
```

**ai/PROJECT-STATUS.md** - Strategic (done → done-done):
```markdown
## Code Work: ✅ DONE
[Summary]

## Meta-Work: 🔄 IN PROGRESS
- ✅ ADRs updated
- 🔄 Version synchronization
- ⏳ Example docs review
- ⏳ CLAUDE.md update
- ⏳ Git commit/tag

## Hygiene Checklist
- [ ] TXO 10-step lifecycle steps 6-10
- [ ] All version numbers synchronized
- [ ] Archive old documents
- [ ] Clean up TODO comments
```

### Benefits

- Clear visibility into both levels
- Can't forget meta-tasks (PROJECT-STATUS tracks them)
- High-level status for stakeholders
- Detailed tasks for execution

### Three Levels of Completion

**Done → Done-Done → Done-Done-Done**:

1. **Done** (Code Level):
   - Code works, tests pass
   - Syntax validation clean
   - Functionality demonstrated
   - Tracked in: ai/TODO.md

2. **Done-Done** (Meta Level):
   - All code complete
   - Documentation updated
   - ADRs enhanced
   - Versions synchronized
   - Hygiene complete
   - Tracked in: ai/PROJECT-STATUS.md (should show 100%)

3. **Done-Done-Done** (Published Level):
   - Git commit (comprehensive message)
   - Git tag (annotated, versioned)
   - Pushed to remote (if applicable)
   - UPPERCASE files archived/deleted
   - Guided by: ai/reports/github-tagging-guide.md

**Final Step**: After PROJECT-STATUS.md shows 100% done-done:
```bash
# See comprehensive guide
cat ai/reports/github-tagging-guide.md

# AI can generate commit message
# "Generate git commit message from release-notes_v{X}.md"

# Commit and tag
git add .
git commit -m "[comprehensive TXO pattern message]"
git tag v{X} -m "[release summary]"
```

---

## ADR-AI006: Version Synchronization Requirements

**Status:** MANDATORY
**Date:** 2025-10-29

### Context

TXO projects use semantic versioning. Per ADR-B013, "all documentation in a project should use the same version number as the git tag/release version."

**Problem**: Files often have mixed versions (_v3.1, _v3.1.1, _v3.2) creating confusion.

### Decision

**Before marking project done-done, synchronize ALL document versions**.

**Version Synchronization Rules**:

1. **Rename files** to match project version (not just internal version)
   - If project = v3.2, rename: `doc_v3.1.md` → `doc_v3.3.md`

2. **Update internal version numbers**:
   - **Version:** v3.2 (in footer)
   - **Last Updated:** 2025-10-29

3. **Update cross-references**:
   - Change `utils-quick-reference_v3.1.md` → `utils-quick-reference_v3.3.md`
   - Find/replace all _v3.1 references with _v3.2

4. **Check for version variants**:
   - Search: `*_v3.1*.md` (catches v3.1, v3.1.1, v3.1.2)
   - Decide: Update to v3.2 or acceptable to keep?

### Meta-Task Checklist

**Before done-done**:
```bash
# Find all version variants
find ai/ -name "*_v3.1*.md"

# Check internal version references
grep -r "v3\.1" ai/decided/ ai/prompts/

# Verify cross-references updated
grep -r "_v3\.1" ai/decided/*.md
```

### Consequences

**Positive**:
- Clean version consistency
- Clear which docs are current
- Follows ADR-B013 requirement
- Easy to identify outdated docs

**Negative**:
- Requires systematic file renaming
- Must update cross-references
- Manual process (not automated)

**Mitigation**: Include as meta-task checklist, AI can assist with find/replace

---

## ADR-AI007: Done/Done-Done/Done-Done-Done Workflow

**Status:** MANDATORY
**Date:** 2025-11-02

### Context

TXO development follows a three-stage completion workflow, but timing was ambiguous for critical tasks like version suffix renaming. Without explicit guidance, developers might:
- Forget to rename version suffixes before git commit
- Update files during done-done causing confusion (referencing wrong version names)
- Miss version synchronization entirely

**Problem**: When should we rename `_v3.2` → `_v3.3` files? During active development or just before git operations?

### Decision

**Formalize three-stage workflow with explicit timing for version management**:

#### **1. Done = Code Complete**
- All code written and functional
- Tests passing
- Script/feature works as intended
- **Files still use current version names** (e.g., _v3.2)

#### **2. Done-Done = Documentation Complete**
- ADRs updated
- Utils reference updated
- Prompts updated
- README and in-depth-readme updated
- Release notes written
- **Work with current _v names throughout** (easier to find files during session)
- **New files** can use new version (e.g., create `script-readme-example_v3.3.md`)

#### **3. Done-Done-Done = Git Operations**
**MANDATORY SEQUENCE** (first action before git commit):

```bash
# Step 1: Bump all version suffixes (MUST be first)
git mv ai/decided/txo-business-adr_v3.2.md ai/decided/txo-business-adr_v3.3.md
git mv ai/decided/utils-quick-reference_v3.2.md ai/decided/utils-quick-reference_v3.2.md
# ... (all _v3.2 → _v3.3 files)

# Step 2: Update all cross-references
sed -i '' 's/_v3\.2\.md/_v3.3.md/g' CLAUDE.md README.md in-depth-readme.md ...

# Step 3: Archive old versions to old/ (if creating new major versions)
mkdir -p ai/decided/old
git mv ai/decided/old-template_v3.2.md ai/decided/old/

# Step 4: Git commit with comprehensive message
git add .
git commit -m "feat(framework): [comprehensive message following TXO pattern]"

# Step 5: Git tag with annotated message
git tag v3.3.0 -m "Version 3.3.0 - [release summary]"

# Step 6: Push to main with tags
git push origin main --tags
```

### Rationale

**Why version bump at START of done-done-done:**

1. **Clear boundary**: Done-done (content) vs done-done-done (git prep)
2. **Explicit checkpoint**: First item on checklist, harder to forget
3. **No confusion during done-done**: Reference files by current names while writing
4. **Safe timing**: All content complete, renaming can't break active work
5. **Before git**: Ensures renamed files in commit, preserves history with `git mv`

**Why NOT during done-done:**
- Confusing to reference files by new names while writing about them
- Easy to miss updating cross-references if scattered across session
- Harder to track which files need updating

### Implementation

**Done-Done-Done Checklist Template**:
```markdown
## Done-Done-Done Checklist

- [ ] 1. Bump all version suffixes using `git mv` (preserves history)
      - txo-business-adr_v3.2.md → _v3.3.md
      - utils-quick-reference_v3.2.md → _v3.3.md
      - script-ai-prompt-template_v3.2.md → _v3.3.md
      - refactoring-ai-prompt_v3.2.md → _v3.3.md
      - (list all files)
- [ ] 2. Update all cross-references from _v3.2 to _v3.3
      - CLAUDE.md
      - README.md
      - in-depth-readme.md
      - All renamed files (internal references)
- [ ] 3. Archive superseded versions to old/ (if applicable)
- [ ] 4. Git commit with comprehensive message
- [ ] 5. Git tag v3.3.0 with annotated message
- [ ] 6. Push to main with --tags
```

### Consequences

**Positive**:
- Clear workflow with explicit timing
- Prevents forgetting version bump before git commit
- Systematic approach reduces errors
- Preserves git history with `git mv`
- Easy to resume if interrupted (checklist-driven)

**Negative**:
- Additional step before git operations
- Must remember to update ALL cross-references
- Manual process (not automated)

**Mitigation**:
- Document in ADR (this document)
- Include in working document templates
- Use sed/grep for bulk cross-reference updates
- Add to done-done-done checklist in all working documents

### Related ADRs

- **ADR-AI006**: Version Synchronization Requirements (when to sync)
- **ADR-B013**: Documentation Version Matching (why versions must match)
- **ADR-AI001**: Dual Document Naming (version suffix convention)

---

## Summary

These AI Workflow ADRs address how AI assistants work WITH the TXO framework, not the framework itself. They complement business ADRs (organizational patterns) and technical ADRs (Python patterns).

**Key Themes**:
1. **Visual clarity**: kebab-case vs UPPERCASE signals purpose
2. **Clean workspace**: old/ ignored, working/ for temporary
3. **Completeness**: PROJECT-STATUS tracks done → done-done
4. **Resumability**: AI-CONTEXT-BRIEF, TODO.md, session summaries
5. **Version discipline**: Synchronize before done-done
6. **Workflow timing**: Version bump at start of done-done-done (ADR-AI007)

---

## Version History

### v3.2 (Current)
- Initial creation of AI Workflow ADRs
- Established dual naming convention (kebab-case vs UPPERCASE)
- Defined old/ ignore rules
- Documented working directory structure
- Created meta-task tracking pattern
- Defined version synchronization requirements

---

**Version:** v3.2
**Domain:** AI Workflow
**Purpose:** How AI assistants work with TXO projects
**Relationship:** Complements business ADRs and technical ADRs
