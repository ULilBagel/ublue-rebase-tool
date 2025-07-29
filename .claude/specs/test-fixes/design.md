# Design - Test Fixes

## Overview
This design document outlines the technical approach to fix failing unit tests in the Universal Blue Rebase Tool. The fixes will address validation logic, callback handling, file permissions, and return value structures.

## Architecture Decisions

### 1. Minimal Code Changes
- Fix only what's necessary to make tests pass
- Maintain existing architecture and patterns
- No refactoring of working code

### 2. Preserve Security Model
- Keep all existing security validations
- Maintain strict input validation
- Preserve audit logging functionality

### 3. Test Compatibility
- Ensure code works in both GTK and non-GTK environments
- Handle mocking scenarios properly
- Maintain test isolation

## Component Design

### CommandExecutor Fixes

#### 1. validate_command Method Enhancement
**Current Issue:** Error messages don't match test expectations

**Solution:**
- Update error message for shell metacharacters to include "dangerous character"
- Ensure consistent error messaging across all validation failures

**Implementation:**
```python
# In validate_command method
if char in arg and not (arg.startswith('"') and arg.endswith('"')):
    return False, f"Potentially dangerous character '{char}' in argument"
```

#### 2. _validate_image_url Method Fixes
**Current Issues:** 
- Missing "suspicious pattern" in error messages
- Missing "too long" in length validation
- Path validation happens before suspicious pattern check

**Solution:**
- Reorder validation checks: suspicious patterns first, then path validation
- Update error messages to match test expectations

**Implementation Flow:**
1. Check registry allowlist
2. Check for suspicious patterns (return "suspicious pattern" error)
3. Check URL length (return "too long" error)
4. Validate paths for registry

#### 3. execute_with_progress Return Value Fix
**Current Issue:** Method returns 2-tuple instead of 3-tuple

**Solution:**
- Change return signature to (success, output, error_type)
- Update all return statements to include error_type

#### 4. execute_with_confirmation Callback Fix
**Current Issue:** Callback expects (success, error_type) but gets (success)

**Solution:**
- Update callback invocation to pass both parameters
- Ensure error_type is empty string on user rejection

### HistoryManager Fixes

#### 1. File Permission Setting
**Current Issue:** History file created without explicit permissions

**Solution:**
- Set file permissions to 0o600 after creation
- Use os.chmod() after file write

**Implementation:**
```python
# After writing history file
os.chmod(self.history_file, 0o600)
```

### DeploymentManager Fixes

#### 1. generate_rollback_command Implementation
**Current Issue:** Method not returning expected command format

**Solution:**
- Return proper rpm-ostree deploy command with commit hash
- Format: ["rpm-ostree", "deploy", commit_hash]

### Progress Tracking Fixes

#### 1. Callback Invocation
**Current Issue:** Progress callbacks not being called

**Solution:**
- Ensure mock compatibility in tests
- Verify GLib.idle_add is properly mocked

## Implementation Strategy

### Phase 1: CommandExecutor Fixes
1. Fix validate_command error messages
2. Fix _validate_image_url validation order and messages
3. Fix execute_with_progress return values
4. Fix execute_with_confirmation callback parameters

### Phase 2: HistoryManager Fixes
1. Add file permission setting after write
2. Ensure atomic file operations preserve permissions

### Phase 3: DeploymentManager Fixes
1. Implement generate_rollback_command properly
2. Fix deployment info formatting

### Phase 4: Test Compatibility
1. Verify all mocking scenarios work
2. Ensure GTK/non-GTK compatibility

## Testing Approach

### Unit Test Verification
- Run each test file individually to verify fixes
- Use pytest with verbose output
- Ensure no regression in passing tests

### Integration Testing
- Run full test suite after each component fix
- Verify no side effects from changes

## Security Considerations

### Input Validation
- Maintain all existing validation rules
- No relaxation of security checks
- Preserve all regex patterns and checks

### File Security
- History files must be owner-readable only (0o600)
- No sensitive data in error messages
- Maintain audit trail integrity

## Error Handling

### Consistent Error Messages
- "dangerous character" for shell metacharacters
- "suspicious pattern" for URL injection attempts
- "too long" for length violations
- Include allowed values in validation errors

### Return Value Consistency
- All execution methods return tuples with consistent structure
- Error types properly categorized
- Empty strings for missing values (not None)

## Code Quality

### Style Guidelines
- Follow existing code style
- Maintain comment patterns
- No unnecessary changes

### Documentation
- Update docstrings if return values change
- Keep inline comments minimal
- Preserve existing documentation

---

Do the design look good? If so, we can move on to creating the task breakdown.