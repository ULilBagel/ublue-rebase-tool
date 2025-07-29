# Requirements - Fix Dialog Mocking

## Overview
Fix the remaining dialog mocking issues in the integration tests to achieve a fully passing test suite. The current implementation has mixed patching strategies that are causing test failures due to improper mocking of the ConfirmationDialog class.

## Codebase Analysis Summary

### Current Issues Identified
1. **Mixed Patching Strategies**: Tests use both `patch('ui.confirmation_dialog.ConfirmationDialog')` and `patch.object(ublue_impl, 'ConfirmationDialog')` inconsistently
2. **Import Bridge Complexity**: The hyphenated filename (`ublue-image-manager.py`) requires special import handling via `importlib.util`
3. **Module Loading Order**: The ConfirmationDialog is imported at module level in ublue-image-manager.py, making runtime patching difficult
4. **Type Incompatibility**: Even with mock GTK window, the actual ConfirmationDialog constructor still runs and expects specific GTK types

### Reusable Components
- **mock_gtk.py**: Existing mock utilities for GTK objects (Application, Window, ToastOverlay, WebView)
- **Test Infrastructure**: Existing test setup with GLib.idle_add mocking and test mode support
- **Callback Pattern**: Already implemented callback-based dialog handling in the main code

### Current Test Patterns
- **test_confirmation_dialog.py**: Successfully patches `Adw.MessageDialog.new` directly
- **test_integration.py**: Attempts to patch ConfirmationDialog at various levels with mixed success
- **test_ui_components.py**: Uses mock_gtk utilities for window creation

## Requirements

### Requirement 1: Consistent Dialog Mocking Strategy
**User Story:** As a test engineer, I want a consistent and reliable way to mock ConfirmationDialog across all tests, so that integration tests don't fail due to GTK type errors.

#### Acceptance Criteria
1. WHEN any integration test creates a ConfirmationDialog THEN it SHALL use a mocked version instead of the real implementation
2. IF a test needs to simulate user confirmation THEN the mock SHALL invoke the provided callback with the appropriate response
3. WHEN the mocking strategy is applied THEN it SHALL work consistently across all test files
4. IF the ublue-image-manager module is imported THEN the ConfirmationDialog mock SHALL already be in place

### Requirement 2: Early Mock Injection
**User Story:** As a developer, I want dialog mocks to be injected before module imports, so that the mocking takes effect regardless of import order.

#### Acceptance Criteria
1. WHEN test modules import ublue-image-manager THEN ConfirmationDialog SHALL already be mocked
2. IF ConfirmationDialog is imported at module level THEN the mock SHALL be injected before the import occurs
3. WHEN multiple tests run in sequence THEN each test SHALL have isolated mock instances
4. IF a test needs specific dialog behavior THEN it SHALL be able to configure the mock per test

### Requirement 3: Simplified Test Setup
**User Story:** As a test author, I want a simple helper function or decorator to handle dialog mocking, so that I don't need to understand the complex import mechanics.

#### Acceptance Criteria
1. WHEN writing a new integration test THEN there SHALL be a simple way to enable dialog mocking
2. IF a test uses the helper THEN it SHALL automatically handle all dialog mocking setup
3. WHEN the helper is used THEN it SHALL not interfere with other mocks or patches
4. IF dialog mocking is enabled THEN the test SHALL be able to verify dialog interactions

### Requirement 4: Backward Compatibility
**User Story:** As a maintainer, I want the new mocking approach to work with existing tests, so that we don't need to rewrite all test files.

#### Acceptance Criteria
1. WHEN the new mocking strategy is implemented THEN existing tests SHALL continue to pass
2. IF a test already has working mocks THEN the new approach SHALL not break them
3. WHEN tests are migrated to the new approach THEN they SHALL be cleaner and more maintainable
4. IF both old and new approaches coexist temporarily THEN they SHALL not conflict

### Requirement 5: Clear Error Messages
**User Story:** As a developer debugging test failures, I want clear error messages when dialog mocking fails, so that I can quickly identify and fix issues.

#### Acceptance Criteria
1. WHEN dialog mocking fails THEN the error message SHALL clearly indicate the mocking issue
2. IF a GTK type error occurs THEN the error SHALL suggest using the dialog mock helper
3. WHEN mock configuration is incorrect THEN the error SHALL show the expected configuration
4. IF import order causes issues THEN the error SHALL explain the proper setup sequence

## Success Criteria
- All 130 tests pass without any dialog-related TypeErrors
- Integration tests can reliably mock dialog interactions
- No changes required to production code
- Test setup is simplified and consistent
- New developers can easily write tests with dialog mocking

## Technical Constraints
- Must work with Python's import system and module caching
- Cannot modify the production ublue-image-manager.py file structure
- Must maintain compatibility with existing test infrastructure
- Should work with both unittest.mock and direct patching approaches

## Out of Scope
- Modifying the production ConfirmationDialog implementation
- Changing the hyphenated filename convention
- Refactoring the entire test suite architecture
- Modifying the GTK/Adwaita library behavior

---

Do the requirements look good? If so, we can move on to the design.