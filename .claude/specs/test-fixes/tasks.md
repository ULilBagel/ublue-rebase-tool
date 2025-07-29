# Tasks - Test Fixes

## Overview
Implementation tasks to fix all failing unit tests in the Universal Blue Rebase Tool.

## Task Breakdown

### Task 1: Fix validate_command error messages
**Description:** Update error messages in validate_command to match test expectations
**Requirements:** Requirement 1
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- Error message includes "dangerous character" for shell metacharacters
- All validate_command tests pass

**Implementation Details:**
- Modify line 259 in command_executor.py
- Change error message from "Potentially dangerous character '{char}' in argument" to include "dangerous character"

---

### Task 2: Fix _validate_image_url validation order and messages
**Description:** Reorder validation checks and update error messages in _validate_image_url
**Requirements:** Requirement 2
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Suspicious pattern check happens before path validation
- Error messages include "suspicious pattern" and "too long"
- All image URL validation tests pass

**Implementation Details:**
- Move suspicious pattern check (lines 327-353) before path validation
- Update length check error message to include "too long"
- Update suspicious pattern error to include "suspicious pattern"

---

### Task 3: Fix execute_with_progress return values
**Description:** Change execute_with_progress to return 3-tuple instead of 2-tuple
**Requirements:** Requirement 3
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Method returns (success, output, error_type)
- All execution tests pass
- No regression in existing functionality

**Implementation Details:**
- Update return statements at lines 83, 87, 92, 94
- Ensure error_type is properly set for all return paths
- Update method documentation

---

### Task 4: Fix execute_with_confirmation callback parameters
**Description:** Update callback invocation to pass both success and error_type
**Requirements:** Requirement 7
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- Callback receives (success, error_type) parameters
- User rejection passes (False, "")
- Confirmation tests pass

**Implementation Details:**
- Modify line 148 to pass error_type to callback
- Update line 152 to pass empty string for error_type

---

### Task 5: Fix history file permissions
**Description:** Set secure permissions on history file after creation
**Requirements:** Requirement 4
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- History file has 0o600 permissions
- File permission test passes
- Permissions preserved on updates

**Implementation Details:**
- Add os.chmod(self.history_file, 0o600) after line 171 in history_manager.py
- Ensure permissions are set after atomic rename

---

### Task 6: Fix polkit authorization return values
**Description:** Update request_elevated_privileges to return tuple format
**Requirements:** Requirement 5
**Priority:** Medium
**Estimated Effort:** Small

**Acceptance Criteria:**
- Success returns (True, "")
- Failure returns (False, error_message)
- Polkit tests pass

**Implementation Details:**
- Current implementation already returns tuples correctly
- Verify test expectations match implementation

---

### Task 7: Implement generate_rollback_command
**Description:** Create generate_rollback_command method in DeploymentManager
**Requirements:** Requirement 6
**Priority:** Medium
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Returns ["rpm-ostree", "deploy", commit_hash] for previous deployments
- Returns None for current deployment
- Rollback command tests pass

**Implementation Details:**
- Add method to deployment_manager.py
- Check if deployment is current (return None)
- Extract commit hash and return proper command format

---

### Task 8: Fix command validation for non-rpm-ostree commands
**Description:** Update validate_command to properly reject non-rpm-ostree commands
**Requirements:** Requirement 1
**Priority:** Medium
**Estimated Effort:** Small

**Acceptance Criteria:**
- Commands not starting with "rpm-ostree" are rejected
- Appropriate error message returned
- Security validation tests pass

**Implementation Details:**
- Add check at beginning of validate_command
- Return error if command[0] != "rpm-ostree"

---

### Task 9: Fix progress callback invocation timing
**Description:** Ensure progress callbacks are called for each output line
**Requirements:** Requirement 3
**Priority:** Medium
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Callback called for each line of output
- Mock compatibility maintained
- Progress tracking tests pass

**Implementation Details:**
- Verify GLib.idle_add is being called correctly
- Ensure callback happens even with mocked GLib

---

### Task 10: Run and verify all tests
**Description:** Execute full test suite and verify all tests pass
**Requirements:** All requirements
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- All 93 tests pass without failures
- No errors reported
- No regression in functionality

**Implementation Details:**
- Run python tests/run_all_tests.py
- Fix any remaining issues
- Document test results

## Execution Order

1. **Phase 1 - CommandExecutor Core Fixes** (Tasks 1, 2, 3, 4, 8)
   - Fix validation messages
   - Fix return values
   - Fix callback parameters

2. **Phase 2 - Storage and Security** (Tasks 5, 6)
   - Fix file permissions
   - Verify polkit handling

3. **Phase 3 - DeploymentManager** (Task 7)
   - Implement rollback command generation

4. **Phase 4 - Progress and Verification** (Tasks 9, 10)
   - Fix progress callbacks
   - Run full test suite

## Dependencies

- Task 10 depends on all other tasks
- Tasks 1-9 can be done independently within their phases
- Phase order should be maintained for logical progression

## Risk Mitigation

- **Risk:** Changes break existing functionality
  - **Mitigation:** Run tests after each task completion
  
- **Risk:** Mock incompatibility
  - **Mitigation:** Test in both GTK and non-GTK environments

- **Risk:** Security regression
  - **Mitigation:** No relaxation of validation rules

---

Do the tasks look good? If so, I can ask if you'd like task commands generated or proceed directly to implementation.