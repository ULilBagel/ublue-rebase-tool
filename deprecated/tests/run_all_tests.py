#!/usr/bin/env python3
"""
Test runner script for comprehensive test suite
Runs all unit tests, integration tests, and generates coverage report
"""

import sys
import os
import unittest
import argparse
from io import StringIO

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def discover_and_run_tests(test_dir=None, pattern='test*.py', verbosity=2):
    """
    Discover and run all tests
    
    Args:
        test_dir: Directory containing tests (default: current directory)
        pattern: Pattern for test files (default: 'test*.py')
        verbosity: Test output verbosity (0-2)
        
    Returns:
        TestResult object
    """
    if test_dir is None:
        test_dir = os.path.dirname(__file__)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


def run_with_coverage():
    """Run tests with coverage reporting"""
    try:
        import coverage
    except ImportError:
        print("Coverage.py not installed. Install with: pip install coverage")
        return
    
    # Configure coverage
    cov = coverage.Coverage(source=['../src'])
    cov.start()
    
    # Run tests
    test_dir = os.path.dirname(__file__)
    result = discover_and_run_tests(test_dir)
    
    # Stop coverage
    cov.stop()
    cov.save()
    
    # Generate report
    print("\n" + "="*70)
    print("COVERAGE REPORT")
    print("="*70)
    
    # Console report
    cov.report()
    
    # HTML report
    html_dir = os.path.join(test_dir, 'htmlcov')
    cov.html_report(directory=html_dir)
    print(f"\nDetailed HTML coverage report generated in: {html_dir}")
    
    return result


def test_requirement_mapping():
    """Generate a mapping of tests to requirements"""
    print("\n" + "="*70)
    print("REQUIREMENTS COVERAGE MAPPING")
    print("="*70)
    
    requirements_map = {
        "Requirement 1: System Status Display": [
            "test_integration.TestRequirementsCoverage.test_requirement_1_system_status_display",
            "test_ublue_image_manager.TestSystemStatus",
        ],
        "Requirement 2: Image Variant Selection": [
            "test_integration.TestFullExecutionFlow.test_rebase_execution_flow_success",
            "test_ublue_image_manager.TestImageSelection",
        ],
        "Requirement 3: Rebase Execution": [
            "test_integration.TestFullExecutionFlow.test_rebase_execution_flow_success",
            "test_command_executor.TestCommandExecution",
            "test_confirmation_dialog.TestConfirmationDialog",
        ],
        "Requirement 4: Command History": [
            "test_history_manager.TestHistoryManager",
            "test_integration.TestRequirementsCoverage.test_requirement_4_history_tracking",
        ],
        "Requirement 5: Clipboard Integration": [
            "test_ublue_image_manager.TestClipboardIntegration",
        ],
        "Requirement 6: System Compatibility": [
            "test_integration.TestRequirementsCoverage.test_requirement_6_demo_mode",
            "test_ublue_image_manager.TestDemoMode",
        ],
        "Requirement 7: Responsive UI": [
            "test_integration.TestUIResponsiveness",
        ],
        "Requirement 8: Rollback Management": [
            "test_integration.TestFullExecutionFlow.test_rollback_execution_flow_success",
            "test_deployment_manager.TestDeploymentManager",
            "test_integration.TestRequirementsCoverage.test_requirement_8_rollback_management",
        ],
        "Security Requirements": [
            "test_security_validations.TestSecurityValidations",
            "test_security_validations.TestAuditLogging",
        ],
    }
    
    for req, tests in requirements_map.items():
        print(f"\n{req}:")
        for test in tests:
            print(f"  - {test}")


def generate_test_summary():
    """Generate a summary of all available tests"""
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    
    test_files = {
        "test_command_executor.py": "Tests for safe command execution service",
        "test_confirmation_dialog.py": "Tests for libadwaita confirmation dialogs",
        "test_deployment_manager.py": "Tests for rpm-ostree deployment management",
        "test_error_handling.py": "Tests for error handling and recovery",
        "test_history_manager.py": "Tests for command history tracking",
        "test_progress_tracker.py": "Tests for real-time progress tracking",
        "test_security_validations.py": "Tests for security validations and injection prevention",
        "test_integration.py": "Integration tests for full execution flow",
    }
    
    for file, description in test_files.items():
        print(f"\n{file}:")
        print(f"  {description}")
        
        # Count tests in file
        try:
            loader = unittest.TestLoader()
            suite = loader.discover(os.path.dirname(__file__), pattern=file)
            test_count = suite.countTestCases()
            print(f"  Test cases: {test_count}")
        except:
            pass


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Run Universal Blue Rebase Tool test suite')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--mapping', action='store_true', help='Show requirements mapping')
    parser.add_argument('--summary', action='store_true', help='Show test suite summary')
    parser.add_argument('--pattern', default='test*.py', help='Test file pattern')
    parser.add_argument('--verbosity', type=int, default=2, choices=[0, 1, 2],
                        help='Test output verbosity')
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    if args.summary:
        generate_test_summary()
        return
    
    if args.mapping:
        test_requirement_mapping()
        return
    
    print("Universal Blue Rebase Tool - Comprehensive Test Suite")
    print("="*70)
    
    if args.coverage:
        result = run_with_coverage()
    else:
        result = discover_and_run_tests(pattern=args.pattern, verbosity=args.verbosity)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()