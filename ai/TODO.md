# TXO v3.2 Refactoring Todo List

**Status**: In Progress
**Started**: 2025-10-29
**Target Version**: v3.2
**Following**: TXO 10-Step Development Lifecycle

---

## PHASE 1: Planning & ADR Updates

### ✅ Task 1.1: Create Comprehensive Todo Document
**Status**: COMPLETED
**File**: `ai/TODO.md`
**Duration**: 1 hour

This document.

---

### 🔄 Task 1.2: Add Memory Optimization ADR
**Status**: IN PROGRESS
**Priority**: HIGH
**File**: `ai/decided/txo-technical-standards_v3.1.md`
**Estimated**: 2 hours

**Objective**: Formalize the memory optimization strategy for `__slots__` usage

**Current Issue**:
- Inconsistent `__slots__` usage across dataclasses
- Comments in multiple files: "Removed __slots__ because it conflicts with default values"
- Files affected: exceptions.py, url_helpers.py, oauth_helpers.py, rest_api_helpers.py, concurrency.py

**Action**:
- Add ADR-T011: Memory Optimization Strategy
- Document when to use `__slots__` (high-volume objects)
- Document when not to use (flexibility needed, dataclass defaults)
- Provide implementation examples

**Validation**:
- [ ] ADR-T011 added to technical standards
- [ ] Clear decision criteria documented
- [ ] Examples for both use cases provided
- [ ] Version updated to v3.2

---

### ⏳ Task 1.3: Review ADR Gaps
**Status**: PENDING
**Priority**: MEDIUM
**Files**: All ADR documents
**Estimated**: 2 hours

**Objective**: Identify and address any missing ADRs based on codebase analysis

**Actions**:
- Review current code patterns not covered by ADRs
- Update version numbers across ADR documents (v3.1 → v3.2)
- Ensure consistency across business and technical ADRs

**Validation**:
- [ ] All current patterns documented
- [ ] Version numbers consistent
- [ ] No gaps identified

---

## PHASE 2: Execute Refactoring (Priority Order)

### ⏳ Priority 1: Logger Exception Refactoring
**Status**: PENDING
**Priority**: HIGH (Blocking testability)
**Files**: `utils/logger.py`, `utils/exceptions.py`, calling code
**Estimated**: 8 hours
**ADR Violation**: Library code should not call sys.exit()

**Current Issues**:
- **10 sys.exit() violations** in logger.py at lines:
  - Line 71: `_fail()` method
  - Line 363: exception handler
  - Line 395: missing config
  - Line 411: invalid JSON
  - Line 422: file read failure
  - Line 434: invalid structure
  - Line 450: missing sections
  - Line 463: missing TxoApp logger
  - Line 507: configuration apply failure
  - Line 605: `setup_logger()` function

**TXO 10-Step Process**:
1. ✅ **Discuss**: Identified 10 violations blocking testability
2. ✅ **Decision**: Breaking change - replace with exceptions (no compatibility mode)
3. [ ] **Todo**: Mark as in-progress when starting
4. [ ] **Code**:
   - Create `LoggerConfigurationError` in exceptions.py
   - Create `LoggerSecurityError` in exceptions.py
   - Replace all `sys.exit(1)` with `raise LoggerConfigurationError()` or `raise LoggerSecurityError()`
   - Update `setup_logger()` docstring with Raises section
   - Update `script_runner.py` with try/except for logger initialization
   - Update any other calling code
5. [ ] **Validation**:
   - Run: `python -m py_compile utils/logger.py`
   - Run: `PYTHONPATH=. python utils/validate_tko_compliance.py utils/logger.py`
   - Create unit tests for all error paths
   - Verify no sys.exit() remains in utils/
6. [ ] **Utils Reference**: Update setup_logger() documentation
7. [ ] **AI Prompt**: Add logger exception handling pattern
8. [ ] **Documentation**: Update README.md error handling section
9. [ ] **Release Notes**: Add breaking change with migration example
10. [ ] **Leftovers**: Track in roadmap if any issues

**Code Changes**:
```python
# In exceptions.py - ADD
class LoggerConfigurationError(TxoBaseError):
    """Raised when logger configuration is missing or invalid."""
    pass

class LoggerSecurityError(TxoBaseError):
    """Raised when security patterns cannot be loaded."""
    pass

# In logger.py - REPLACE sys.exit(1) with:
raise LoggerConfigurationError(error_msg)
# or
raise LoggerSecurityError(error_msg)

# In script_runner.py - UPDATE calling code:
from utils.exceptions import LoggerConfigurationError, LoggerSecurityError

try:
    logger = setup_logger()
except (LoggerConfigurationError, LoggerSecurityError) as e:
    print(f"Logger initialization failed: {e}", file=sys.stderr)
    sys.exit(1)
```

**Success Criteria**:
- [ ] Zero sys.exit() in utils/logger.py
- [ ] All error paths raise appropriate exceptions
- [ ] Calling code handles exceptions properly
- [ ] Unit tests cover all error paths
- [ ] All existing tests pass
- [ ] Migration guide created

---

### ⏳ Priority 2: Rate Limiter Header Implementation
**Status**: PENDING
**Priority**: HIGH (Missing functionality)
**Files**: `utils/rate_limit_manager.py`
**Estimated**: 4 hours

**Current Issue**:
- `update_from_headers()` is stub implementation (lines 95-111)
- Logs headers but doesn't adjust rate limiter behavior
- No adaptive rate adjustment based on API responses

**TXO 10-Step Process**:
1. ✅ **Discuss**: Stub implementation needs adaptive logic
2. ✅ **Decision**: Implement 4-tier adaptive rate adjustment
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**: Implement adaptive rate adjustment with thresholds:
   - <5% remaining: Emergency slow down (rate * 0.3)
   - <10% remaining: Aggressive slow down (rate * 0.5)
   - <25% remaining: Moderate slow down (rate * 0.75)
   - >75% remaining: Can speed up (rate * 1.25, max original)
5. [ ] **Validation**:
   - Unit tests with mocked headers (all threshold levels)
   - Integration test with simulated rate limit responses
   - Test reset time handling
   - Test retry-after header handling
6. [ ] **Utils Reference**: Update rate limiter documentation
7. [ ] **AI Prompt**: Add rate limit header handling pattern
8. [ ] **Documentation**: Document adaptive rate limiting behavior
9. [ ] **Release Notes**: Note new feature
10. [ ] **Leftovers**: None expected

**Implementation Reference**:
See `ai/reports/refactor_v3.2.md` lines 119-189 for complete implementation

**Success Criteria**:
- [ ] Header parsing works for X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- [ ] Adaptive adjustment at all 4 threshold levels
- [ ] Rate increases when healthy (>75%)
- [ ] Rate decreases when low (<25%, <10%, <5%)
- [ ] Logging at appropriate levels (debug, info, warning)
- [ ] Unit tests cover all thresholds

---

### ⏳ Priority 3: REST API Response Mutation Fix
**Status**: PENDING
**Priority**: HIGH (Fragile pattern)
**Files**: `utils/rest_api_helpers.py`
**Estimated**: 5 hours

**Current Issue**:
- Direct mutation of `response._content` (line 447-448)
- Violates encapsulation
- Fragile implementation that breaks object contracts

**Current Code**:
```python
# Line 447-448
response._content = json.dumps(result).encode('utf-8') if result else b''
response.status_code = 200
```

**TXO 10-Step Process**:
1. ✅ **Discuss**: Direct mutation violates encapsulation
2. ✅ **Decision**: Create AsyncOperationResult dataclass wrapper
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**:
   - Create `AsyncOperationResult` dataclass with data, status_code, original_response
   - Add .json(), .ok, .content properties for compatibility
   - Update `_execute_request()` to return wrapper for async ops (status 202)
   - Update calling code to handle Union[Response, AsyncOperationResult]
5. [ ] **Validation**:
   - Unit tests for async operation handling
   - Test response.json() compatibility
   - Verify backward compatibility with existing code
   - Test timeout scenarios
6. [ ] **Utils Reference**: Document AsyncOperationResult usage
7. [ ] **AI Prompt**: Add async operation pattern
8. [ ] **Documentation**: Update API client usage examples
9. [ ] **Release Notes**: Note internal improvement (non-breaking)
10. [ ] **Leftovers**: None expected

**Implementation Reference**:
See `ai/reports/refactor_v3.2.md` lines 226-287 for complete implementation

**Success Criteria**:
- [ ] No _content mutation anywhere in codebase
- [ ] Async operations return AsyncOperationResult wrapper
- [ ] Wrapper provides .json(), .ok, .content compatibility
- [ ] Backward compatibility maintained
- [ ] All existing async operation tests pass

---

### ⏳ Priority 4: OAuth Config Hard-Fail Fix
**Status**: PENDING
**Priority**: MEDIUM (ADR violation)
**Files**: `utils/script_runner.py`
**Estimated**: 1 hour
**ADR Violation**: ADR-B003 Hard-Fail Configuration Philosophy

**Current Issue**:
- Lines 195-198 use `config.get()` soft-fail for OAuth configuration
- Should hard-fail when `require_token=True`
- Masks configuration errors

**Current Code** (approximate):
```python
# Lines 195-198
oauth_config = config.get("oauth-settings", {})
client_id = oauth_config.get("client-id")
```

**TXO 10-Step Process**:
1. ✅ **Discuss**: Soft-fail on OAuth config when authentication required
2. ✅ **Decision**: Hard-fail with KeyError for required OAuth config
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**:
   - Replace `config.get()` with `config[]` for OAuth settings
   - Let KeyError propagate naturally
   - Add HelpfulError with clear message if needed
5. [ ] **Validation**:
   - Test with missing OAuth config (should raise KeyError)
   - Test with complete config (should work)
   - Run: `PYTHONPATH=. python utils/validate_tko_compliance.py utils/script_runner.py`
6. [ ] **Utils Reference**: No changes needed (pattern already documented)
7. [ ] **AI Prompt**: No changes needed
8. [ ] **Documentation**: No changes needed
9. [ ] **Release Notes**: Note ADR compliance fix
10. [ ] **Leftovers**: None

**Success Criteria**:
- [ ] KeyError raised when OAuth config missing and require_token=True
- [ ] No config.get() for required configuration
- [ ] TXO compliance validator passes
- [ ] Test with incomplete config confirms hard-fail

---

### ⏳ Priority 5: Complex Method Refactoring
**Status**: PENDING
**Priority**: MEDIUM (Maintainability)
**Files**: `utils/logger.py`, `utils/rest_api_helpers.py`, `utils/script_runner.py`
**Estimated**: 10 hours
**ADR Violation**: ADR-T010 Method Complexity Management (target 50 lines, max 100)

**Three Methods to Refactor**:

#### 5.1: logger._setup_logger() - 144 lines
**Location**: lines 374-518
**Target**: Split into 3-4 methods (<50 lines each)
**Complexity**: High nesting, multiple responsibilities

**Refactoring Plan**:
- Extract `_validate_logging_config()` - Config structure validation
- Extract `_configure_handlers()` - Handler setup logic
- Extract `_apply_log_levels()` - Level configuration
- Keep `_setup_logger()` as orchestrator (~30 lines)

#### 5.2: rest_api_helpers._execute_request() - 108 lines
**Location**: lines 396-503
**Target**: Split into 4 methods (<30 lines each)
**Already identified in refactor_v3.2.md**

**Refactoring Plan**:
- Extract `_prepare_request()` - Headers, auth, parameters
- Extract `_send_with_retries()` - Retry logic and circuit breaker
- Extract `_handle_response()` - Response validation and processing
- Keep `_execute_request()` as orchestrator (~25 lines)

#### 5.3: script_runner.acquire_token() - 81 lines
**Location**: lines 166-246
**Target**: Split into 3 methods (<30 lines each)

**Refactoring Plan**:
- Extract `_validate_oauth_config()` - Config validation logic
- Extract `_get_oauth_client()` - Client creation
- Extract `_retrieve_token()` - Token acquisition
- Keep `acquire_token()` as orchestrator (~25 lines)

**TXO 10-Step Process** (per method):
1. ✅ **Discuss**: Method exceeds complexity limits
2. ✅ **Decision**: Extract sub-methods with single responsibilities
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**: Split method following plan above
5. [ ] **Validation**:
   - All tests pass (no behavioral changes)
   - Each new method has single responsibility
   - All methods under 50 lines
   - Run compliance validator
6. [ ] **Utils Reference**: Update if public API changes
7. [ ] **AI Prompt**: No changes (pattern already documented)
8. [ ] **Documentation**: Update in-depth-readme if significant
9. [ ] **Release Notes**: Note refactoring for maintainability
10. [ ] **Leftovers**: None expected

**Success Criteria**:
- [ ] All 3 methods split successfully
- [ ] All sub-methods under 50 lines
- [ ] No behavioral changes verified by tests
- [ ] Improved testability (can test sub-methods independently)
- [ ] Code coverage maintained or improved

---

### ⏳ Priority 6: OAuth Exception Specificity
**Status**: PENDING
**Priority**: MEDIUM (Error handling improvement)
**Files**: `utils/oauth_helpers.py`
**Estimated**: 2 hours

**Current Issue**:
- Line 314: Broad exception catch `except (json.JSONDecodeError, ValueError, AttributeError)`
- Masks different error types with same message
- Harder to debug specific failures

**Current Code**:
```python
# Line 314
except (json.JSONDecodeError, ValueError, AttributeError):
    error_msg = f"{error_msg}: {response.text[:200]}"
```

**TXO 10-Step Process**:
1. ✅ **Discuss**: Broad exception catch reduces diagnostics
2. ✅ **Decision**: Split into specific exception handlers
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**:
   ```python
   except json.JSONDecodeError as e:
       error_msg = f"{error_msg}: Invalid JSON response - {e}"
   except KeyError as e:
       error_msg = f"{error_msg}: Missing field in response - {e}"
   except (ValueError, AttributeError) as e:
       error_msg = f"{error_msg}: Unexpected response format - {e}"
   ```
5. [ ] **Validation**:
   - Unit tests for each error type
   - Verify error messages are specific
   - All existing tests pass
6. [ ] **Utils Reference**: No changes needed
7. [ ] **AI Prompt**: No changes needed
8. [ ] **Documentation**: No changes needed
9. [ ] **Release Notes**: Note error handling improvement
10. [ ] **Leftovers**: None

**Success Criteria**:
- [ ] Specific exception handlers for each type
- [ ] Error messages indicate exact problem
- [ ] Unit tests cover all error paths
- [ ] Better debugging experience

---

### ⏳ Priority 7: Circuit Breaker Enhancement
**Status**: PENDING
**Priority**: LOW (Observability improvement)
**Files**: `utils/api_common.py`
**Estimated**: 3 hours

**Current State**:
- Basic circuit breaker implementation (lines 62-123)
- No detailed state transition logging
- No statistics tracking

**Enhancement Objective**:
- Add state transition logging with context
- Add statistics property (success rate, time in state)
- Improve debugging and monitoring

**TXO 10-Step Process**:
1. ✅ **Discuss**: Add observability for state transitions
2. ✅ **Decision**: Enhance with _change_state() and stats property
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**:
   - Add `__slots__` for tracking: _state_changed_at, _total_requests, _total_failures
   - Create `_change_state(new_state, reason)` method
   - Add `stats` property returning metrics dict
   - Update `record_success()` and `record_failure()` to use _change_state()
5. [ ] **Validation**:
   - Unit tests for state transitions
   - Test statistics calculation
   - Verify logging output
   - No behavioral changes to circuit breaking logic
6. [ ] **Utils Reference**: Update circuit breaker documentation
7. [ ] **AI Prompt**: Add monitoring pattern
8. [ ] **Documentation**: Document metrics available
9. [ ] **Release Notes**: Note observability improvement
10. [ ] **Leftovers**: None expected

**Implementation Reference**:
See `ai/reports/refactor_v3.2.md` lines 519-584 for complete implementation

**Success Criteria**:
- [ ] State transitions logged with context and timing
- [ ] Statistics property returns useful metrics
- [ ] No behavioral changes to circuit breaking
- [ ] Enhanced debugging capability

---

### ⏳ Priority 8: Path Helpers Exception Clarity
**Status**: PENDING
**Priority**: LOW (Error handling improvement)
**Files**: `utils/path_helpers.py`
**Estimated**: 1 hour

**Current Issue**:
- Lines 350-352: Silent OSError swallowing in cleanup
- Doesn't distinguish permission errors from other issues

**Current Code**:
```python
try:
    file_path.unlink()
except OSError as e:
    # Continue processing other files
    pass
```

**TXO 10-Step Process**:
1. ✅ **Discuss**: Silent exception swallowing hides issues
2. ✅ **Decision**: Log specific error types
3. [ ] **Todo**: Mark as in-progress
4. [ ] **Code**:
   ```python
   try:
       file_path.unlink()
       deleted_files.append(file_path)
   except PermissionError as e:
       logger.error(f"Permission denied deleting {file_path}: {e}")
   except OSError as e:
       logger.warning(f"Could not delete {file_path}: {e}")
   ```
5. [ ] **Validation**: Test permission error and other OSError scenarios
6-10. [ ] Complete remaining steps

**Success Criteria**:
- [ ] Specific error types logged appropriately
- [ ] Permission errors distinguished from other issues
- [ ] Cleanup continues but with visibility

---

### ⏳ Priority 9: OAuth Unused Parameters
**Status**: PENDING
**Priority**: LOW (Code clarity)
**Files**: `utils/oauth_helpers.py`
**Estimated**: 30 minutes

**Current Issue**:
- Lines 348-349: Unused parameters not clearly marked
- Uses assignment to `_` instead of parameter prefix

**Current Code**:
```python
def revoke_token(self, token: str, client_id: str,
                 client_secret: str, tenant_id: Optional[str] = None) -> bool:
    _ = token  # Unused
    _ = client_secret  # Unused
```

**Proposed**:
```python
def revoke_token(self, _token: str, client_id: str,
                 _client_secret: str, tenant_id: Optional[str] = None) -> bool:
    # No assignment needed - underscore prefix indicates unused
```

**TXO 10-Step Process** (abbreviated for cosmetic change):
1-3. ✅ Discuss, decide, mark in-progress
4. [ ] **Code**: Prefix unused parameters with underscore
5. [ ] **Validation**: Syntax check only
6-10. [ ] Complete if needed

**Success Criteria**:
- [ ] More Pythonic unused parameter handling
- [ ] Clear intent in function signature

---

### ⏳ Priority 10: Type Hint Improvements
**Status**: PENDING
**Priority**: LOW (Type safety improvement)
**Files**: `utils/concurrency.py`
**Estimated**: 2 hours

**Enhancement Objective**:
- Add generic TypeVar for batch_process return types
- Add proper Iterator type hints for load_csv with chunksize
- Improve IDE autocomplete

**TXO 10-Step Process** (abbreviated):
1-3. ✅ Discuss, decide, mark in-progress
4. [ ] **Code**: Add TypeVar, Generic, Iterator type hints
5. [ ] **Validation**: Type check with mypy
6-10. [ ] Complete remaining steps

**Success Criteria**:
- [ ] Better IDE autocomplete
- [ ] Type checker satisfaction
- [ ] Generic return types properly typed

---

## PHASE 3: Final Validation & Documentation

### ⏳ Task 3.1: Run All Validation Tools
**Status**: PENDING
**Priority**: HIGH
**Estimated**: 2 hours

**Validation Commands**:
```bash
# Compliance validation
for file in utils/*.py; do
    echo "Validating $file..."
    PYTHONPATH=. python utils/validate_tko_compliance.py "$file"
done

# Syntax validation
echo "Checking Python syntax..."
python -m py_compile utils/*.py

# Functional testing
echo "Testing scripts..."
PYTHONPATH=. python src/try_me_script.py demo test
PYTHONPATH=. python tests/test_features.py demo test
```

**Success Criteria**:
- [ ] All compliance validation passes
- [ ] All syntax checks pass
- [ ] All functional tests pass
- [ ] No regression detected

---

### ⏳ Task 3.2: Verify ADR Compliance
**Status**: PENDING
**Priority**: HIGH
**Estimated**: 2 hours

**ADR Checklist**:
- [ ] **ADR-B003**: No config.get() for required configuration
- [ ] **ADR-T001**: Thread-safe patterns maintained
- [ ] **ADR-T004**: Proper exception hierarchy (logger exceptions added)
- [ ] **ADR-T010**: All methods under 100 lines (target <50)
- [ ] **ADR-T011**: Consistent __slots__ strategy per new ADR
- [ ] **ADR-B005**: No print() statements in library code

**Manual Verification**:
```bash
# Check for sys.exit() in utils/ (should be zero)
grep -r "sys.exit" utils/*.py

# Check for config.get() on required config (context dependent)
grep -r "config.get\|config\[" utils/*.py

# Check method lengths (automated in Task 3.5)
```

---

### ⏳ Task 3.3: Update Version Documentation
**Status**: PENDING
**Priority**: HIGH
**Estimated**: 3 hours

**Files to Update to v3.2**:
- [ ] `ai/decided/txo-business-adr_v3.1.md` → potentially v3.2 (if changes made)
- [ ] `ai/decided/txo-technical-standards_v3.1.md` → v3.2 (added ADR-T011)
- [ ] `ai/decided/utils-quick-reference_v3.1.md` → v3.2 (if functions changed)
- [ ] `ai/prompts/ai-prompt-template_v3.1.1.md` → v3.2 (if patterns changed)
- [ ] `README.md` → Update for breaking changes (logger exceptions)
- [ ] `in-depth-readme.md` → Add refactoring details
- [ ] `ai/reports/release-notes-v3.1.1.md` → v3.2 with comprehensive changelog

**Version Update Process**:
1. Review each document for changes needed
2. Update version number in filename and content
3. Update version history section
4. Ensure consistency across all documents

---

### ⏳ Task 3.4: Create Migration Guide
**Status**: PENDING
**Priority**: HIGH
**Estimated**: 2 hours
**File**: `ai/reports/release-notes-v3.2.md`

**Required Sections**:
1. **Breaking Changes**:
   - Logger exception handling (sys.exit → exceptions)
   - How to update calling code
   - Before/after examples

2. **New Features**:
   - Adaptive rate limiting
   - AsyncOperationResult wrapper
   - Circuit breaker statistics

3. **Improvements**:
   - Method complexity reduction
   - Exception specificity
   - Type safety enhancements

4. **Migration Steps**:
   - Update logger initialization code
   - Test with new exception handling
   - Verify no behavior changes

**Example Migration Code**:
```python
# BEFORE (v3.1)
logger = setup_logger()  # Could call sys.exit(1)

# AFTER (v3.2)
from utils.exceptions import LoggerConfigurationError, LoggerSecurityError

try:
    logger = setup_logger()
except (LoggerConfigurationError, LoggerSecurityError) as e:
    print(f"Logger initialization failed: {e}", file=sys.stderr)
    sys.exit(1)
```

---

### ⏳ Task 3.5: Performance Benchmarks
**Status**: PENDING
**Priority**: MEDIUM
**Estimated**: 2 hours

**Benchmarks from refactor_v3.2.md**:
```python
# Rate limiter performance
def benchmark_rate_limiter(iterations=10000):
    limiter = RateLimiter(calls_per_second=1000, burst_size=10)
    start = time.time()
    for _ in range(iterations):
        limiter.wait_if_needed()
    elapsed = time.time() - start
    print(f"Rate limiter: {iterations} calls in {elapsed:.2f}s")
    print(f"Average: {elapsed/iterations*1000:.3f}ms per call")

# Logger initialization
def benchmark_logger_init():
    start = time.time()
    for _ in range(100):
        setup_logger()  # Should use cached instance
    elapsed = time.time() - start
    print(f"Logger init: 100 calls in {elapsed:.2f}s")
```

**Expected Results**:
- [ ] Rate limiter: <0.001ms per call
- [ ] Logger init (cached): <0.01ms per call
- [ ] Circuit breaker: <0.001ms overhead
- [ ] No regression >5% vs baseline

---

### ⏳ Task 3.6: Test Coverage Report
**Status**: PENDING
**Priority**: MEDIUM
**Estimated**: 1 hour

**Coverage Targets**:
- Current: ~75% (from refactor_v3.2.md)
- Target: >85%
- Focus: Changed code must have >90% coverage

**Actions**:
- [ ] Run coverage tool on utils/ directory
- [ ] Verify new error paths covered (logger, OAuth, rate limiter)
- [ ] Document coverage by file
- [ ] Identify any gaps

---

## Summary Statistics

**Total Tasks**: 16 major tasks (3 planning + 10 refactoring + 3 validation)
**Estimated Time**: 55-60 hours
**Target Timeline**: 2-3 weeks
**Current Status**: 1/16 completed (6%)

### By Priority:
- **HIGH**: 6 tasks (Planning + Logger + Rate Limiter + REST API + OAuth + Validation)
- **MEDIUM**: 5 tasks (Complex methods + OAuth exceptions + Documentation)
- **LOW**: 5 tasks (Circuit breaker + Path helpers + Unused params + Type hints + Benchmarks)

### By Phase:
- **PHASE 1** (Planning): 3 tasks, ~4 hours
- **PHASE 2** (Refactoring): 10 tasks, ~45-50 hours
- **PHASE 3** (Validation): 3 tasks, ~8 hours

---

## Next Steps

1. ✅ Create this todo document
2. 🔄 Add Memory Optimization ADR (ADR-T011)
3. ⏳ Review ADR gaps
4. ⏳ Begin Priority 1: Logger exception refactoring

---

**Last Updated**: 2025-10-29
**Version**: v3.2 (target)
**Document Status**: Living document - update after each task completion
