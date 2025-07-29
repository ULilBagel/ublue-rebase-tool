# Requirements - Fix Remaining Tests

## Overview
Fix the remaining 31 test failures (5 failures + 26 errors) in the Universal Blue Rebase Tool test suite to achieve 100% test pass rate. The goal is to ensure ALL tests pass without breaking any existing functionality.

## Codebase Analysis Summary
- **Total tests**: 130 (all now running after import fix)
- **Current state**: 5 failures, 26 errors
- **Main issues identified**:
  - Callback parameter mismatch in confirmation dialogs
  - Missing method `on_script_message` in API (exists in Window class)
  - Mock object initialization issues in UI tests
  - Progress tracking callback not being invoked
  - Demo mode detection issues
  
- **Reusable components**:
  - Existing ConfirmationDialog class (needs parameter alignment)
  - Progress tracking infrastructure (needs callback fixes)
  - WebKit bridge implementation (needs method exposure)
  - Mock patterns from passing tests

## Requirements

### Requirement 1: Fix Confirmation Dialog Callback Issues
**User Story:** As a developer, I want all confirmation dialog calls to use the correct method signature, so that tests can properly verify user interactions.

#### Acceptance Criteria
1. WHEN show_rebase_confirmation is called THEN it SHALL receive 3 parameters: image_name, command, and callback
2. WHEN show_rollback_confirmation is called THEN it SHALL receive 3 parameters: deployment_info, command, and callback
3. IF a dialog is shown without proper callback THEN the system SHALL handle the response asynchronously
4. WHEN tests mock confirmation dialogs THEN they SHALL be able to simulate user responses

### Requirement 2: Fix WebKit Bridge Method Access
**User Story:** As a test engineer, I want to test the JavaScript bridge functionality, so that I can verify WebKit integration works correctly.

#### Acceptance Criteria
1. WHEN tests access on_script_message THEN it SHALL be available on the API object
2. IF on_script_message is called THEN it SHALL properly handle JavaScript messages
3. WHEN bridge methods are tested THEN they SHALL process mock messages correctly
4. IF an error occurs in bridge handling THEN it SHALL be properly reported

### Requirement 3: Fix UI Component Mock Initialization
**User Story:** As a QA engineer, I want UI component tests to properly initialize mocked GTK objects, so that component behavior can be tested without a display.

#### Acceptance Criteria
1. WHEN creating Mock objects for GTK components THEN they SHALL be compatible with GTK type system
2. IF a Mock is used as a GtkApplication THEN it SHALL be properly wrapped or substituted
3. WHEN UI tests run THEN they SHALL not require actual GTK initialization
4. IF mock initialization fails THEN tests SHALL provide clear error messages

### Requirement 4: Fix Progress Tracking Callbacks
**User Story:** As a developer, I want progress callbacks to be invoked during command execution, so that UI updates can be tested.

#### Acceptance Criteria
1. WHEN a command is executed with progress tracking THEN callbacks SHALL be invoked for each output line
2. IF GLib.idle_add is mocked THEN it SHALL properly invoke the callback function
3. WHEN progress is updated THEN the UI SHALL receive the updates on the main thread
4. IF no progress occurs THEN the test SHALL still pass without callbacks

### Requirement 5: Fix Demo Mode Detection
**User Story:** As a user, I want demo mode to properly prevent actual system changes, so that I can safely explore the application.

#### Acceptance Criteria
1. WHEN in demo mode THEN execute operations SHALL be blocked
2. IF demo mode is active THEN appropriate user feedback SHALL be provided
3. WHEN tests check demo mode THEN they SHALL verify the blocking behavior
4. IF real mode is active THEN operations SHALL proceed normally

### Requirement 6: Fix Execute Method Synchronization
**User Story:** As a developer, I want asynchronous operations to be properly synchronized in tests, so that test assertions work reliably.

#### Acceptance Criteria
1. WHEN execute_rebase is called THEN it SHALL handle both synchronous and asynchronous flows
2. IF a callback-based dialog is shown THEN the execution SHALL wait for user response
3. WHEN tests verify execution state THEN they SHALL account for async operations
4. IF threading is involved THEN proper synchronization SHALL be maintained

## Success Criteria
- **ALL 130 tests pass without ANY failures or errors** (100% pass rate)
- **Zero regression** - previously passing tests must continue to pass
- No breaking changes to existing functionality
- Test execution time remains reasonable (< 10 seconds)
- All mock objects properly simulate real components
- Code coverage maintained or improved
- Application continues to function correctly in production use

## Technical Constraints
- Must maintain compatibility with GTK 4.0 and libadwaita
- Cannot modify test framework or test structure
- Must work with existing WebKit integration
- Should maintain thread safety for UI operations
- Must preserve existing API contracts

## Out of Scope
- Adding new tests
- Refactoring test architecture
- Changing application functionality
- Modifying external dependencies
- Performance optimizations

---

Do the requirements look good? If so, we can move on to the design.