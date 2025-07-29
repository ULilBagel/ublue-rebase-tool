# Requirements - Test Fixes

## Overview
Fix failing unit tests in the Universal Blue Rebase Tool to ensure all security validations, command execution, and history management features work correctly.

## Codebase Analysis Summary
- **Existing Components to Leverage:**
  - CommandExecutor service with security validation logic
  - HistoryManager with audit logging functionality
  - Test suite infrastructure already in place
  - Security validation patterns for image URLs and commands
  
- **Integration Points:**
  - Command validation methods need fixes for proper error messages
  - Progress callback handling in execute_with_progress
  - File permissions for history files
  - Polkit authorization return value handling

## Requirements

### Requirement 1: Fix Command Validation Test Failures
**User Story:** As a developer, I want the command validation tests to pass correctly, so that I can ensure command validation logic works as expected.

#### Acceptance Criteria
1. WHEN validate_command is called with shell metacharacters THEN the system SHALL return error message containing "dangerous character"
2. WHEN validate_command is called with a valid rpm-ostree command THEN the system SHALL return True with no error
3. IF a command contains dangerous characters in arguments THEN the system SHALL reject it with appropriate error message

### Requirement 2: Fix Image URL Validation Test Failures
**User Story:** As a security engineer, I want image URL validation to properly enforce all security rules, so that only safe image URLs are accepted.

#### Acceptance Criteria
1. WHEN _validate_image_url is called with an allowed registry and valid path THEN the system SHALL return True
2. IF an image URL contains suspicious patterns THEN the system SHALL return error message containing "suspicious pattern"
3. IF an image URL exceeds 512 characters THEN the system SHALL return error message containing "too long"
4. WHEN an image URL uses an invalid path for a registry THEN the system SHALL include the allowed paths in the error message

### Requirement 3: Fix Command Execution Progress Callback
**User Story:** As a developer, I want the progress callback to be invoked correctly during command execution, so that UI can show real-time progress.

#### Acceptance Criteria
1. WHEN execute_with_progress runs a command THEN the progress_callback SHALL be called for each output line
2. IF GLib.idle_add is used THEN the callback SHALL be invoked in the main thread
3. WHEN a command produces multiple lines of output THEN each line SHALL trigger a separate callback invocation

### Requirement 4: Fix History File Permissions
**User Story:** As a security administrator, I want history files to have secure permissions, so that sensitive command history is protected.

#### Acceptance Criteria
1. WHEN a history file is created THEN it SHALL have permissions 0600 (read/write for owner only)
2. IF the history file already exists THEN its permissions SHALL be preserved or set to 0600
3. WHEN checking file permissions in tests THEN the test SHALL correctly validate that group/other permissions are not set

### Requirement 5: Fix Polkit Authorization Return Values
**User Story:** As a developer, I want polkit authorization tests to handle return values correctly, so that authorization logic works properly.

#### Acceptance Criteria
1. WHEN request_elevated_privileges succeeds THEN it SHALL return tuple (True, "")
2. WHEN request_elevated_privileges fails THEN it SHALL return tuple (False, error_message)
3. IF the test mocks polkit responses THEN it SHALL match the expected return value structure

### Requirement 6: Fix Rollback Command Generation
**User Story:** As a user, I want rollback commands to be generated correctly, so that I can roll back to previous deployments.

#### Acceptance Criteria
1. WHEN generate_rollback_command is called for a previous deployment THEN it SHALL return a valid rpm-ostree deploy command
2. IF the deployment has a specific commit THEN the command SHALL include the commit hash
3. WHEN formatting deployment info THEN pinned deployments SHALL be marked appropriately

### Requirement 7: Fix Command Executor Callback Handling
**User Story:** As a developer, I want confirmation callbacks to work correctly, so that UI can handle user confirmations properly.

#### Acceptance Criteria
1. WHEN execute_with_confirmation is called and user confirms THEN the confirm_callback SHALL be called with success status
2. IF the user rejects confirmation THEN the callback SHALL be called with (False, "")
3. WHEN execution completes THEN the callback SHALL include both success status and error type

## Success Criteria
- All 93 unit tests pass without failures or errors
- No regression in existing functionality
- Code changes maintain existing security patterns
- All test assertions match actual implementation behavior

## Technical Constraints
- Must maintain compatibility with existing GTK/GLib infrastructure
- Must preserve existing security validation patterns
- Cannot modify test logic, only fix implementation to match test expectations
- Must handle both GTK and non-GTK environments (for testing)

## Out of Scope
- Adding new features or tests
- Refactoring test structure
- Changing security policies or validation rules
- Modifying UI components

---

Do the requirements look good? If so, we can move on to the design.