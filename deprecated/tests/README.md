# Universal Blue Rebase Tool - Test Suite Documentation

## Overview

This directory contains a comprehensive test suite for the Universal Blue Rebase Tool, ensuring all components work correctly and meet the specified requirements.

## Test Structure

The test suite is organized into the following categories:

### Unit Tests
- **test_command_executor.py**: Tests for safe command execution service
- **test_confirmation_dialog.py**: Tests for libadwaita confirmation dialogs  
- **test_deployment_manager.py**: Tests for rpm-ostree deployment management
- **test_error_handling.py**: Tests for error handling and recovery
- **test_history_manager.py**: Tests for command history tracking
- **test_progress_tracker.py**: Tests for real-time progress tracking

### Security Tests
- **test_security_validations.py**: Tests for security validations and injection prevention
  - Command sanitization
  - Image URL validation
  - Audit logging
  - Shell injection prevention

### Integration Tests
- **test_integration.py**: Integration tests for full execution flow
  - Complete rebase workflow
  - Complete rollback workflow
  - Error handling scenarios
  - WebKit bridge integration

### UI Tests
- **test_ui_components.py**: Tests for GTK4/libadwaita UI components
  - Responsive layout behavior
  - Accessibility features
  - Toast notifications
  - Dialog interactions

## Running Tests

### Run All Tests
```bash
# Basic test run
python tests/run_all_tests.py

# With coverage report
python tests/run_all_tests.py --coverage

# Show requirements mapping
python tests/run_all_tests.py --mapping

# Show test summary
python tests/run_all_tests.py --summary
```

### Run Specific Test Files
```bash
# Run a single test file
python -m unittest tests.test_command_executor

# Run with verbose output
python -m unittest -v tests.test_security_validations
```

### Using pytest (Alternative)
```bash
# Install pytest and coverage
pip install pytest pytest-cov

# Run all tests with coverage
pytest

# Run specific test markers
pytest -m unit
pytest -m security
pytest -m "not slow"
```

## Test Coverage

The test suite aims for comprehensive coverage of all requirements:

### Requirements Coverage Map

1. **System Status Display (Req. 1)**
   - `test_integration.TestRequirementsCoverage.test_requirement_1_system_status_display`
   - Tests for rpm-ostree status parsing
   - Demo mode detection

2. **Image Variant Selection (Req. 2)**
   - `test_integration.TestFullExecutionFlow`
   - Tests for image selection and display

3. **Rebase Execution (Req. 3)**
   - `test_integration.TestFullExecutionFlow.test_rebase_execution_flow_success`
   - `test_command_executor.TestCommandExecution`
   - `test_confirmation_dialog.TestConfirmationDialog`

4. **Command History (Req. 4)**
   - `test_history_manager.TestHistoryManager`
   - Tests for storage, retrieval, and pruning

5. **Clipboard Integration (Req. 5)**
   - Tests for portal-based clipboard access

6. **System Compatibility (Req. 6)**
   - `test_integration.TestRequirementsCoverage.test_requirement_6_demo_mode`
   - Demo mode behavior tests

7. **Responsive UI (Req. 7)**
   - `test_ui_components.TestResponsiveLayout`
   - `test_integration.TestUIResponsiveness`

8. **Rollback Management (Req. 8)**
   - `test_integration.TestFullExecutionFlow.test_rollback_execution_flow_success`
   - `test_deployment_manager.TestDeploymentManager`

### Security Requirements
- `test_security_validations.TestSecurityValidations`
- `test_security_validations.TestAuditLogging`

## Writing New Tests

When adding new features or fixing bugs, please:

1. **Add corresponding tests** for any new functionality
2. **Follow the existing test patterns** for consistency
3. **Use descriptive test names** that explain what is being tested
4. **Include docstrings** explaining the test purpose
5. **Mock external dependencies** to ensure tests are isolated
6. **Test both success and failure cases**

### Example Test Structure
```python
class TestNewFeature(unittest.TestCase):
    """Test the new feature functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Initialize test objects
        pass
        
    def test_feature_success_case(self):
        """Test that feature works correctly with valid input"""
        # Arrange
        # Act  
        # Assert
        pass
        
    def test_feature_error_handling(self):
        """Test that feature handles errors gracefully"""
        # Test error scenarios
        pass
```

## Continuous Integration

The test suite is designed to be run in CI/CD pipelines:

1. All tests should pass before merging
2. Coverage should not decrease
3. New features require corresponding tests
4. Security tests must pass for all changes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the src directory is in PYTHONPATH
2. **GTK Dependencies**: Some tests mock GTK components for headless testing
3. **Permission Errors**: History tests may need write access to temp directories

### Running Tests in Docker/Flatpak

For testing in isolated environments:

```bash
# Flatpak testing
flatpak-builder --run build-dir io.github.ublue.RebaseTool.yml python tests/run_all_tests.py
```

## Future Improvements

- Add performance benchmarks
- Implement fuzz testing for security validations  
- Add visual regression tests for UI
- Create end-to-end tests with real rpm-ostree systems