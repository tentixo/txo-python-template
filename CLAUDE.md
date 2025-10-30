# CLAUDE.md - AI Assistant Operating Manual

> **Purpose**: Practical guidance for Claude Code (AI) working with TXO codebase
> **Audience**: AI assistants performing development tasks on this repository
> **Focus**: Commands, tools, workflow, and quick navigation

---

## 🔄 **TXO Development Lifecycle**

**Follow this 10-step process for all TXO development work:**

```
1. Discuss Code/Issue →
2. Decision to ADR/Tech Standard →
3. Create ai/to-do.md for refactoring → 
4. Working Code →
5. Validation (ADR + Tech Standards) →
6. Add Functions to Utils Reference →
7. Adapt AI Prompt →
8. Documentation (README + in-depth) →
9. Release Notes Update →
10. Leftovers and ides for later to ai/reports/roadmap.md
```

### **Step-by-Step Workflow**:

1. **Discuss Code**: Analyze requirements, identify patterns, determine approach
2. **ADR Decision**: Update `ai/decided/txo-business-adr_v3.1.md` or `ai/decided/txo-technical-standards_v3.1.md` if needed
3. **Working Code**: Implement following TXO patterns from `ai/decided/utils-quick-reference_v3.1.md`
4. **Validation**: Run compliance tools and verify against ADRs
5. **Utils Reference**: Update `ai/decided/utils-quick-reference_v3.1.md` if new functions added
6. **Adapt Prompt**: Update `ai/prompts/ai-prompt-template_v3.1.1.md` if new patterns discovered
7. **Documentation**: Update README.md (15-min success) and in-depth-readme.md (maintainer focus)
8. **Release Notes**: Update `ai/reports/release-notes-v3.1.1.md` with changes

---

## 🛠️ **Development Commands**

### **Running Scripts**
```bash
# PyCharm (recommended for development)
# Use Run Configuration with parameters: org_id env_type

# Command line (for AI/testing)
PYTHONPATH=. python src/try_me_script.py demo test
PYTHONPATH=. python src/script_name.py org_id env_type

# Module execution (alternative)
python -m src.try_me_script demo test
```

### **Code Quality & Validation**
```bash
# TXO Compliance validation (mandatory for new scripts)
PYTHONPATH=. python utils/validate_tko_compliance.py src/your_script.py

# Syntax validation
python -m py_compile src/your_script.py utils/module_name.py

# Test functionality
PYTHONPATH=. python tests/test_features.py demo test
```

### **Setup Commands**
```bash
# Install dependencies
pip install uv
uv pip install -r pyproject.toml

# Create config files for testing
cp config/org-env-config_example.json config/demo-test-config.json
cp config/org-env-config-secrets_example.json config/demo-test-config-secrets.json
```

### **Git Operations (Done-Done-Done)**
```bash
# See comprehensive guide:
cat ai/reports/github-tagging-guide.md

# Quick reference (after done-done complete):
git add .
git commit -m "type: summary (see guide for TXO comprehensive template)"
git tag v3.2 -m "annotated tag message"
git push origin main --tags

# AI can generate commit message:
# "Generate git commit message from ai/reports/release-notes_v3.2.md
#  following TXO pattern in github-tagging-guide.md"
```

**Guide**: `ai/reports/github-tagging-guide.md` (commit templates, tagging strategy, examples)

---

## 📁 **Project Navigation for AI**

### **Directory Structure (What Goes Where)**
```
#### Used by code (AI modifies these)
├── src/             # Main scripts and examples
├── utils/           # Core framework (rarely modify)
├── config/          # Configuration files
├── tests/           # Test scripts

#### AI documentation workflow
├── ai/
│   ├── decided/     # ADRs, standards, utils reference (update in steps 2,5)
│   ├── prompts/     # AI prompt templates (update in step 6)
│   └── reports/     # Release notes, refactoring guides (update in step 8)
```

### **Key Files for AI Development**
- **Patterns Reference**: `ai/decided/utils-quick-reference_v3.2.md` (step 3: coding)
- **Business Rules**: `ai/decided/txo-business-adr_v3.2.md` (step 2: decisions)
- **Technical Standards**: `ai/decided/txo-technical-standards_v3.2.md` (step 4: validation)
- **AI Workflow**: `ai/decided/txo-ai-adr_v3.2.md` (NEW - AI document standards)
- **AI Prompts**: `ai/prompts/ai-prompt-template_v3.2.md` (Script Creating), `ai/prompts/refactoring-ai-prompt_v3.2.md` (Refactoring)
- **Documentation Examples**: `ai/decided/readme-example_v3.2.md`, `ai/decided/in-depth-readme-example_v3.2.md` (step 7)

---

## ⚡ **Quick Pattern Reference for AI**

### **Critical TXO Patterns (Immediate Decisions)**
```python
# ✅ ALWAYS USE
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.path_helpers import Dir
from utils.api_factory import create_rest_api

# ✅ Configuration access
config['key']  # Hard-fail

# ✅ File operations
data_handler.save_with_timestamp(data, Dir.OUTPUT, "file.xlsx", add_timestamp=True)

# ✅ Multi-sheet Excel
sheets = {"Summary": df1, "Details": df2}
data_handler.save(sheets, Dir.OUTPUT, "report.xlsx")

# ❌ NEVER USE
import requests  # Use create_rest_api()
config.get('key', default)  # Use config['key']
'output'  # Use Dir.OUTPUT
manual_timestamp = datetime.now()  # Use save_with_timestamp()
```

### **AI Workflow Integration**
- **Phase 1-2**: Reference `ai/decided/` documents for patterns
- **Phase 3**: Use `ai/decided/utils-quick-reference_v3.1.md` patterns
- **Phase 4**: Run validation tools listed above
- **Phase 6-7**: Follow `ai/decided/*example*.md` templates exactly

---

## 🔍 **Validation Pipeline**

### **Step 4: Code Validation Process**
```bash
# 1. TXO compliance check
PYTHONPATH=. python utils/validate_tko_compliance.py src/script.py

# 2. Syntax validation
python -m py_compile src/script.py

# 3. Functional testing
PYTHONPATH=. python src/script.py demo test

# 4. Optional: PyCharm inspection (see ai/prompts/ for instructions)
```

### **Validation Success Criteria**
- ✅ TXO compliance validator passes
- ✅ Script executes without errors
- ✅ Follows patterns from utils-quick-reference
- ✅ ADR principles maintained (hard-fail, type-safe, etc.)

---

## 📋 **File Update Tracking**

### **When Working on TXO Framework**
**Always update these in sequence (steps 5-8)**:
1. `ai/decided/utils-quick-reference_v3.1.md` (if new functions)
2. `ai/prompts/ai-prompt-template_v3.1.1.md` (if new patterns/reminders)
3. `README.md` (15-minute success focus)
4. `in-depth-readme.md` (maintainer deep-dive)
5. `ai/reports/release-notes-v3.1.1.md` (track all changes)

### **Version Management**
- **Major changes**: Increment version across all documents
- **Minor improvements**: Update specific documents only
- **Living documents**: Release notes updated continuously

---

## 🎯 **AI Development Best Practices**

### **Before Starting Any Work**
1. **Read relevant ADRs** from `ai/decided/` directory
2. **Check utils-quick-reference** for existing functions
3. **Review recent release notes** for context

### **During Development**
1. **Follow TXO development flow** (8 steps above)
2. **Validate early and often** with provided tools
3. **Reference example templates** for documentation structure

### **Quality Gates**
- **No ADR violations** (hard-fail, type-safe, etc.)
- **TXO compliance** (validator passes)
- **Documentation separation** (README vs in-depth appropriate content)
- **Pattern consistency** (utils-quick-reference alignment)

---

**For comprehensive technical details, see:**
- **All Functions**: `ai/decided/utils-quick-reference_v3.1.md`
- **Business Rules**: `ai/decided/txo-business-adr_v3.1.md`
- **Technical Standards**: `ai/decided/txo-technical-standards_v3.1.md`
- **Architecture Overview**: `module-dependency-diagram.md`

---

**Version:** v3.1.1
**Last Updated:** 2025-09-29
**Domain:** AI Assistant Operations
**Purpose:** Practical guidance for AI development work on TXO codebase