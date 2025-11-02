# V3.3.0 Architecture Decisions

> **Status**: WORKING DOCUMENT (per ADR-AI001)
> **Date**: 2025-11-01
> **Purpose**: Track architectural decisions for v3.3.0 refactoring
> **Lifecycle**: Delete/archive after content moved to permanent docs

---

## Session Context

**Problem Identified**: TXO template supports two distinct workflows but documentation is ambiguous:
1. **Script Creating Workflow**: User creates business script using template
2. **Refactoring Workflow**: User improves the template framework itself

Current templates claim "for Script Creating" but contain framework content, causing confusion.

---

## Three Major Decisions for v3.3.0

### Decision 1: Add ADR-B017 - Directory-Specific UTC Timestamp Rules

**Problem**:
- UTC timestamps were implicit (examples only), not explicit (MANDATORY ADR)
- AI missed UTC timestamps during script generation
- No distinction between output/ (needs UTC) and payloads/ (must not have UTC)

**Solution**:
- Create ADR-B017 with RFC 2119 keywords (MUST/SHOULD/MUST NOT)
- Define rules for 5 directories:
  - `output/` - MUST use UTC
  - `tmp/` - SHOULD use UTC
  - `generated_payloads/` - MUST NOT use UTC (deterministic for human validation)
  - `payloads/` - MUST NOT use UTC (manual workflow)
  - `wsdl/` - MUST NOT use UTC (service versioned)

**File**: `ai/decided/txo-business-adr_v3.3.md` (after line 1683)

---

### Decision 2: Split README Templates 2 → 4

**Problem**:
Current state:
- `readme-example_v3.3.md` - claims "Script Creating" but contains framework benefits
- `in-depth-readme-example_v3.3.md` - claims "Script Creating" but explains TXO architecture

Root cause: Template serves TWO workflows with different documentation needs

**Solution**: Create 4 distinct templates

#### Script Templates (for REPLACEMENT)
When creating business script, developer REPLACES both files:

1. **script-readme-example_v3.3.md**
   - Title: `# [Script Name]` (e.g., "User Sync Script")
   - Content: What THIS SCRIPT does, how to run THIS SCRIPT
   - Audience: Script users (want to use the script, 15 min)
   - No framework architecture

2. **script-in-depth-readme-example_v3.3.md**
   - Title: `# [Script Name] - In-Depth Guide`
   - Content: Script architecture, customization, which TXO features used
   - Audience: Script maintainers (want to extend the script)

#### Refactoring Templates (for UPDATES)
When improving framework, developer UPDATES both files during done-done:

3. **refactoring-readme-example_v3.3.md**
   - Title: `# TXO Python Template`
   - Content: Framework benefits, how to use template to create scripts
   - Audience: Template users (want to create scripts using template, 5 min)
   - Matches current root README.md

4. **refactoring-in-depth-readme-example_v3.3.md**
   - Title: `# TXO Python Template - Framework Architecture`
   - Content: Framework internals, ADR deep dives, extension patterns
   - Audience: Framework maintainers (want to improve the template)
   - Matches current root in-depth-readme.md

#### Archive Old Templates
Move to `ai/decided/old/`:
- `readme-example_v3.3.md` → `old/readme-example_v3.3.md`
- `in-depth-readme-example_v3.3.md` → `old/in-depth-readme-example_v3.3.md`

---

### Decision 3: Document old/ Directory Pattern

**Problem**:
- old/ directories exist but not explained in user-facing docs
- Users don't understand archival workflow

**Solution**:
Add to README.md:
```markdown
## Document Versioning

TXO uses versioned documentation (e.g., `_v3.3.md`). When documents are superseded:
- Old versions move to `ai/decided/old/` directory
- AI assistants ignore `old/` directories automatically (ADR-AI002)
- Historical reference available but not used for current guidance
```

Add to in-depth-readme.md:
```markdown
## Archival Workflow (ADR-AI002)

**User archives manually**:
1. New version created (e.g., `adr_v3.3.md`)
2. User moves old version: `mv adr_v3.3.md old/adr_v3.3.md`
3. AI ignores old/ in future sessions

**Directories with old/ subdirectories**:
- `ai/old/` - Superseded working documents
- `ai/decided/old/` - Superseded ADRs, templates, references
- `ai/prompts/old/` - Superseded prompt templates
- `ai/reports/old/` - Superseded reports

**AI Rule**: MUST ignore all `**/old/` and `**/archive/` directories
```

---

### Decision 4: Requirements Section ADR-B016 Compliance

**Problem**:
`script-ai-prompt-template_v3.3.md` lines 119-215 use pure XML for human-filled requirements:
```xml
<script-requirements>
    <script-metadata>...</script-metadata>
    <org-env-context>...</org-env-context>
    ...
</script-requirements>
```

This violates **ADR-B016**: "Use Markdown For: Instructions and workflows, Explanations and rationale"

Requirements gathering is EXACTLY where humans write prose - should be markdown!

**Solution**: Convert to markdown with minimal XML

**Structure**:
- Minimal XML: Only `<script-metadata>` with 3 fields (script-name, script-purpose, complexity)
- Markdown body: All sections converted to headers + bullet points
- Code blocks for examples: Claude parses these excellently (ADR-B016 verified)

**Benefits**:
- Human-friendly: Easy for developers to fill in requirements
- ADR-B016 compliant: Markdown-first with minimal XML
- AI-parseable: Code blocks + minimal XML provide structure
- Consistent: Matches ADR-B016 philosophy throughout template

**Implementation**: Update lines 119-215 in `script-ai-prompt-template_v3.3.md`

---

## Implementation Plan

### Session 1: Working Doc + 4 Templates (60 min)
- [x] Create `ai/working/V3-3-ARCHITECTURE-DECISIONS.md` (this file)
- [ ] Create `script-readme-example_v3.3.md`
- [ ] Create `script-in-depth-readme-example_v3.3.md`
- [ ] Create `refactoring-readme-example_v3.3.md`
- [ ] Create `refactoring-in-depth-readme-example_v3.3.md`
- [ ] Create `ai/decided/old/` directory
- [ ] Move old templates to `old/`

### Session 2: ADR-B017 + Prompts (30 min)
- [x] Add ADR-B017 to `txo-business-adr_v3.3.md`
- [ ] Update `script-ai-prompt-template_v3.3.md`:
  - Convert requirements section (lines 119-215) from XML to markdown (ADR-B016 compliance)
  - Add directory-specific critical reminders (ADR-B017)
  - Add directory-specific examples section

### Session 3: Reference Docs + Root Files (45 min)
- [ ] Update `utils-quick-reference_v3.3.md` (fix line 476, anti-patterns, new section)
- [ ] Update `README.md` (output files section, old/ info, v3.3.0)
- [ ] Update `in-depth-readme.md` (ADR-B017 deep dive, old/ workflow, v3.3.0)
- [ ] Fix `CLAUDE.md` line 119 reference
- [ ] Fix `in-depth-readme-example` line 599 ADR reference

### Session 4: Validation (20 min)
- [ ] Add `check_directory_specific_timestamps()` to `validate_tko_compliance.py`
- [ ] Test validation on example scripts
- [ ] Update version numbers across all files

---

## Files Modified (12 total)

### Created (5)
1. `ai/working/V3-3-ARCHITECTURE-DECISIONS.md` (this file)
2. `ai/decided/script-readme-example_v3.3.md`
3. `ai/decided/script-in-depth-readme-example_v3.3.md`
4. `ai/decided/refactoring-readme-example_v3.3.md`
5. `ai/decided/refactoring-in-depth-readme-example_v3.3.md`

### Modified (6)
6. `ai/decided/txo-business-adr_v3.3.md` - Add ADR-B017
7. `ai/prompts/script-ai-prompt-template_v3.3.md` - Add directory reminders
8. `ai/decided/utils-quick-reference_v3.3.md` - Add directory patterns
9. `README.md` - Add output files section + old/ info
10. `in-depth-readme.md` - Add ADR-B017 + old/ workflow
11. `utils/validate_tko_compliance.py` - Add ADR-B017 checks

### Moved/Fixed (1)
12. `CLAUDE.md` - Fix line 119 reference

---

## Key Insights Captured

### 1. REPLACE vs UPDATE Pattern
**Script Creating Workflow**:
- Developer REPLACES both README.md and in-depth-readme.md
- New project has script-specific documentation only
- Example: "User Sync Script" replaces "TXO Python Template"

**Refactoring Workflow**:
- Developer UPDATES both README.md and in-depth-readme.md
- Template documentation improves incrementally
- Example: Add ADR-B017 section to existing framework docs

### 2. Current State Analysis
Root files are already refactoring-focused:
- `README.md` = "TXO Python Template v3.1.1" (framework quick start)
- `in-depth-readme.md` = "Framework Architecture" (framework deep dive)

This means:
- Refactoring templates should match current root structure
- During v3.3.0, we UPDATE (not replace) root files

### 3. Version Bump Rationale
v3.3.0 (not v3.2.1) because:
- Architectural change (template split)
- New MANDATORY ADR (ADR-B017)
- Semantic versioning: Minor version for non-breaking enhancements

---

## Post-Implementation Checklist

### Done-Done Requirements
- [ ] All 4 templates created and tested
- [ ] ADR-B017 added with complete examples
- [ ] All documentation updated (README, in-depth, prompts, reference)
- [ ] Compliance validation working
- [ ] Version numbers synchronized to v3.3.0
- [ ] Old templates archived
- [ ] Cross-references updated (CLAUDE.md, prompt references)

### Done-Done-Done Requirements
- [ ] Git commit with comprehensive message
- [ ] Git tag: v3.3.0 with annotated message
- [ ] This working document archived/deleted
- [ ] Release notes updated

---

## Questions Resolved

**Q: Does in-depth-readme.md exist in root?**
A: Yes, it's the "how-to-use-this-template-repo" documentation

**Q: Combine README split + ADR-B017 in one release?**
A: Yes, combined v3.3.0 release (2-3 hours total)

**Q: Working document name?**
A: V3-3-ARCHITECTURE-DECISIONS.md (version-specific per ADR-AI001)

**Q: Does REPLACE vs UPDATE apply to both README files?**
A: Yes, both README.md and in-depth-readme.md follow same pattern

---

## Next Actions

1. Start with Session 1: Create 4 templates
2. Progress through sessions sequentially
3. Use this document to track completion
4. After done-done-done: Archive this document to `ai/working/old/`

---

**Document Status**: ACTIVE - In Progress
**Last Updated**: 2025-11-01
**Delete After**: Content captured in permanent docs + v3.3.0 released
