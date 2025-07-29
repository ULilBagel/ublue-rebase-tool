# Tasks - Fix Remaining Tests

## Overview
Implementation tasks to fix all 31 failing tests and achieve 100% test pass rate without breaking existing functionality.

## Task Breakdown

### Phase 1: Dialog Callback Fixes

#### Task 1: Refactor execute_rebase for Callback Pattern
**Description:** Modify execute_rebase method to use async callback pattern with confirmation dialog
**Requirements:** Requirement 1, Requirement 6
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- execute_rebase uses callback with show_rebase_confirmation
- Method handles both confirmed and cancelled responses
- Async execution flow is maintained
- All rebase-related tests pass

**Implementation Details:**
- Modify execute_rebase in ublue-image-manager.py
- Create handle_rebase_confirmation callback function
- Move execution logic into callback
- Ensure proper error handling in callback

---

#### Task 2: Refactor execute_rollback for Callback Pattern
**Description:** Modify execute_rollback method to use async callback pattern with confirmation dialog
**Requirements:** Requirement 1, Requirement 6
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- execute_rollback uses callback with show_rollback_confirmation
- Method handles both confirmed and cancelled responses
- Async execution flow is maintained
- All rollback-related tests pass

**Implementation Details:**
- Modify execute_rollback in ublue-image-manager.py
- Create handle_rollback_confirmation callback function
- Move execution logic into callback
- Ensure proper error handling in callback

---

### Phase 2: API Method Exposure

#### Task 3: Add on_script_message Proxy to API
**Description:** Add proxy method to UBlueImageAPI that delegates to window's on_script_message
**Requirements:** Requirement 2
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- API object has on_script_message method
- Method delegates to window when available
- Method handles direct calls in tests
- WebKit bridge tests pass

**Implementation Details:**
- Add on_script_message method to UBlueImageAPI
- Check if window exists and has the method
- Implement fallback for test scenarios
- Handle message processing logic

---

#### Task 4: Implement Direct Message Handler
**Description:** Create _handle_script_message_directly for test scenarios
**Requirements:** Requirement 2
**Priority:** Medium
**Estimated Effort:** Small

**Acceptance Criteria:**
- Direct handler processes messages without window
- Same message format as window handler
- Proper error handling
- Tests can mock message objects

**Implementation Details:**
- Add _handle_script_message_directly method
- Parse message data
- Route to appropriate handlers
- Return expected response format

---

### Phase 3: GTK Mock Resolution

#### Task 5: Create GTK Mock Utilities Module
**Description:** Create tests/mock_gtk.py with proper GTK mock helpers
**Requirements:** Requirement 3
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Module provides GTK-compatible mock objects
- Mocks work with Adw.Application
- Mocks work with Adw.ApplicationWindow
- No GTK initialization required

**Implementation Details:**
- Create tests/mock_gtk.py file
- Implement create_mock_gtk_application function
- Implement create_mock_gtk_window function
- Add proper type compatibility

---

#### Task 6: Update UI Test Setup Methods
**Description:** Modify all UI test setUp methods to use GTK mock utilities
**Requirements:** Requirement 3
**Priority:** High
**Estimated Effort:** Large

**Acceptance Criteria:**
- All UI tests use proper mock objects
- No "Cannot spec a Mock object" errors
- No "could not convert value" errors
- All 19 UI component tests pass

**Implementation Details:**
- Update test_ui_components.py setUp methods
- Replace Mock() with GTK-compatible mocks
- Ensure all test classes are updated
- Verify each test class individually

---

### Phase 4: Async and Demo Fixes

#### Task 7: Add Demo Mode Feedback
**Description:** Implement proper demo mode blocking with user feedback
**Requirements:** Requirement 5
**Priority:** Medium
**Estimated Effort:** Small

**Acceptance Criteria:**
- Demo mode shows toast notification
- Operations return demo_mode flag
- execute_js is called with feedback
- Demo mode tests pass

**Implementation Details:**
- Add demo mode check in execute_rebase
- Add demo mode check in execute_rollback
- Call execute_js with toast message
- Return appropriate response object

---

#### Task 8: Fix Progress Callback Invocation
**Description:** Ensure progress callbacks are invoked during command execution
**Requirements:** Requirement 4
**Priority:** Medium
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Progress callbacks called for each output line
- GLib.idle_add works in tests
- Callbacks execute synchronously in tests
- Progress tracking tests pass

**Implementation Details:**
- Add test mode detection in command_executor.py
- Modify GLib.idle_add usage for tests
- Ensure callbacks are invoked
- Maintain thread safety in production

---

#### Task 9: Implement Test Synchronization
**Description:** Add async operation synchronization for tests
**Requirements:** Requirement 6
**Priority:** Medium
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Tests can wait for async operations
- Operations complete within timeout
- No race conditions in tests
- Non-blocking execution tests pass

**Implementation Details:**
- Add _test_mode flag to API
- Add operation completion tracking
- Implement wait mechanism for tests
- Ensure production code unaffected

---

### Phase 5: Final Validation

#### Task 10: Run Test Categories Individually
**Description:** Verify each category of tests passes after fixes
**Requirements:** All requirements
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- Integration tests: 0 failures, 0 errors
- UI component tests: 0 failures, 0 errors
- All other tests remain passing
- Document any issues found

**Implementation Details:**
- Run: python -m unittest tests.test_integration -v
- Run: python -m unittest tests.test_ui_components -v
- Run other test files individually
- Fix any remaining issues

---

#### Task 11: Verify Full Test Suite
**Description:** Run complete test suite and ensure 100% pass rate
**Requirements:** All requirements
**Priority:** High
**Estimated Effort:** Small

**Acceptance Criteria:**
- All 130 tests pass
- 0 failures, 0 errors
- Execution time < 10 seconds
- Generate test report

**Implementation Details:**
- Run: python tests/run_all_tests.py
- Verify test count is 130
- Check execution time
- Document final results

---

#### Task 12: Manual Application Testing
**Description:** Verify application functionality hasn't regressed
**Requirements:** All requirements
**Priority:** High
**Estimated Effort:** Medium

**Acceptance Criteria:**
- Application launches correctly
- Rebase operations work
- Rollback operations work
- UI remains responsive
- No production regressions

**Implementation Details:**
- Test application startup
- Test rebase with confirmation
- Test rollback with confirmation
- Test demo mode behavior
- Test progress display

## Execution Order

1. **Phase 1** - Tasks 1-2 (Dialog Callbacks)
2. **Phase 2** - Tasks 3-4 (API Methods)
3. **Phase 3** - Tasks 5-6 (GTK Mocks)
4. **Phase 4** - Tasks 7-9 (Async/Demo)
5. **Phase 5** - Tasks 10-12 (Validation)

## Dependencies

- Task 2 can be done in parallel with Task 1
- Task 4 depends on Task 3
- Task 6 depends on Task 5
- Tasks 7-9 can be done in parallel
- Tasks 10-12 must be done sequentially after all others

## Risk Mitigation

- **Risk:** Callback changes break production flow
  - **Mitigation:** Careful testing of dialog interactions
  
- **Risk:** GTK mocks cause unexpected behavior
  - **Mitigation:** Minimal mock implementation, test thoroughly
  
- **Risk:** Async changes create race conditions
  - **Mitigation:** Proper synchronization primitives

## Success Metrics

- ✅ 130/130 tests passing (100% pass rate)
- ✅ 0 test failures
- ✅ 0 test errors
- ✅ No production functionality broken
- ✅ Application works correctly in manual testing

---

Do the tasks look good? If so, would you like me to:
1. Generate task commands for automated execution, or
2. Proceed directly to implementing the fixes?