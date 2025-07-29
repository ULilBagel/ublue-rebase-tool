#!/usr/bin/env python3
"""
Test suite for error handling and recovery functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_executor import CommandExecutor


class TestCommandExecutorErrorHandling(unittest.TestCase):
    """Test CommandExecutor error detection and handling"""
    
    def setUp(self):
        self.executor = CommandExecutor()
        self.progress_callback = Mock()
    
    def test_network_error_detection(self):
        """Test detection of network-related errors"""
        network_errors = [
            "Error: Unable to connect to registry.example.com",
            "curl: (6) Could not resolve host: ghcr.io",
            "error: While pulling ghcr.io/ublue-os/bluefin:latest: dial tcp: lookup ghcr.io: no such host",
            "Network timeout while downloading manifest",
            "Connection refused: Cannot reach image registry"
        ]
        
        for error_msg in network_errors:
            error_type = self.executor._analyze_error_type(error_msg, 1)
            self.assertEqual(error_type, 'network', f"Failed to detect network error in: {error_msg}")
    
    def test_authentication_error_detection(self):
        """Test detection of authentication errors"""
        auth_errors = [
            "Error: Permission denied",
            "Authentication failed for user",
            "polkit: Authorization failed",
            "error: unauthorized: authentication required",
            "Access denied: insufficient privileges"
        ]
        
        for error_msg in auth_errors:
            error_type = self.executor._analyze_error_type(error_msg, 1)
            self.assertEqual(error_type, 'auth', f"Failed to detect auth error in: {error_msg}")
    
    def test_rpm_ostree_busy_detection(self):
        """Test detection of rpm-ostree busy state"""
        busy_errors = [
            "error: Transaction already in use",
            "rpm-ostree: Another transaction is running",
            "error: rpm-ostree daemon is busy with another transaction"
        ]
        
        for error_msg in busy_errors:
            error_type = self.executor._analyze_error_type(error_msg, 1)
            self.assertEqual(error_type, 'busy', f"Failed to detect busy error in: {error_msg}")
    
    def test_not_found_error_detection(self):
        """Test detection of not found errors"""
        not_found_errors = [
            "error: rpm-ostree: No such deployment",
            "rpm-ostree: Deployment not found",
            "error: No such image: ghcr.io/ublue-os/invalid:latest"
        ]
        
        for error_msg in not_found_errors:
            error_type = self.executor._analyze_error_type(error_msg, 1)
            self.assertEqual(error_type, 'not_found', f"Failed to detect not found error in: {error_msg}")
    
    @patch('subprocess.Popen')
    def test_timeout_handling(self, mock_popen):
        """Test command timeout handling"""
        # Mock a process that times out
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.stdout.readline.side_effect = subprocess.TimeoutExpired('cmd', 30)
        mock_popen.return_value = mock_process
        
        success, output, error_type = self.executor.execute_with_progress(
            ['rpm-ostree', 'rebase', 'test'],
            self.progress_callback
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, 'timeout')
        self.assertIn('timed out', output)
        mock_process.kill.assert_called_once()
    
    @patch('gi.repository.GLib.idle_add', side_effect=lambda func, *args: func(*args))
    @patch('subprocess.Popen')
    def test_successful_execution(self, mock_popen, mock_idle_add):
        """Test successful command execution"""
        # Mock a successful process
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, 0]  # Process finishes successfully
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Starting operation...\n",
            "Progress: 50%\n",
            ""  # EOF
        ]
        mock_process.communicate.return_value = ("Done!\n", None)
        mock_popen.return_value = mock_process
        
        success, output, error_type = self.executor.execute_with_progress(
            ['rpm-ostree', 'status'],
            self.progress_callback
        )
        
        self.assertTrue(success)
        self.assertEqual(error_type, '')
        self.assertIn('Starting operation', output)
        self.assertIn('Done!', output)
        self.assertEqual(self.progress_callback.call_count, 3)  # Called for each line
    
    def test_command_validation(self):
        """Test command validation for security"""
        # Valid commands
        valid_commands = [
            ['rpm-ostree', 'status'],
            ['rpm-ostree', 'rebase', 'ghcr.io/ublue-os/bluefin:latest'],
            ['rpm-ostree', 'rollback']
        ]
        
        for cmd in valid_commands:
            is_valid, error = self.executor.validate_command(cmd)
            self.assertTrue(is_valid, f"Valid command rejected: {cmd}")
            self.assertIsNone(error)
        
        # Invalid commands
        invalid_commands = [
            [],  # Empty command
            ['rm', '-rf', '/'],  # Dangerous command
            ['rpm-ostree', 'rebase', 'http://evil.com/image:latest'],  # Invalid registry
        ]
        
        for cmd in invalid_commands:
            is_valid, error = self.executor.validate_command(cmd)
            self.assertFalse(is_valid, f"Invalid command accepted: {cmd}")
            self.assertIsNotNone(error)
    
    @patch('gi.repository.Gio.DBusProxy.new_for_bus_sync')
    def test_polkit_authentication_retry(self, mock_dbus):
        """Test polkit authentication with retry"""
        # Mock polkit responses
        mock_authority = Mock()
        mock_dbus.return_value = mock_authority
        
        # First two attempts fail, third succeeds
        mock_authority.CheckAuthorization.side_effect = [
            ((False, False), ),  # First attempt fails
            ((False, False), ),  # Second attempt fails
            ((True, False), ),   # Third attempt succeeds
        ]
        
        is_authorized, error = self.executor.request_elevated_privileges(max_retries=3)
        
        self.assertTrue(is_authorized)
        self.assertEqual(error, '')
        self.assertEqual(mock_authority.CheckAuthorization.call_count, 3)
    
    def test_concurrent_execution_prevention(self):
        """Test that concurrent executions are prevented"""
        # Set executor as busy
        self.executor.is_executing = True
        
        success, output, error_type = self.executor.execute_with_progress(
            ['rpm-ostree', 'status'],
            self.progress_callback
        )
        
        self.assertFalse(success)
        self.assertEqual(error_type, 'general')
        self.assertIn('already executing', output)


class TestErrorMessageFormatting(unittest.TestCase):
    """Test user-friendly error message formatting"""
    
    def setUp(self):
        # We'll test the error formatting logic directly
        pass
    
    def test_network_error_message(self):
        """Test network error user message"""
        from ublue_image_manager import UBlueImageAPI
        api = UBlueImageAPI()
        
        message = api._get_user_friendly_error('network', 'Connection refused')
        self.assertIn('Network error', message)
        self.assertIn('internet connection', message)
    
    def test_auth_error_message(self):
        """Test authentication error user message"""
        from ublue_image_manager import UBlueImageAPI
        api = UBlueImageAPI()
        
        message = api._get_user_friendly_error('auth', 'Permission denied')
        self.assertIn('Authentication failed', message)
        self.assertIn('permissions', message)
    
    def test_generic_error_extraction(self):
        """Test extraction of relevant error from output"""
        from ublue_image_manager import UBlueImageAPI
        api = UBlueImageAPI()
        
        output = """
        Starting operation...
        Processing...
        error: Failed to parse manifest: invalid format
        Operation aborted
        """
        
        message = api._get_user_friendly_error('general', output)
        self.assertIn('Failed to parse manifest', message)


if __name__ == '__main__':
    unittest.main()