#!/usr/bin/env python3
"""
Unit tests for CommandExecutor service
Tests command execution, validation, and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import threading
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_executor import CommandExecutor


class TestCommandExecutor(unittest.TestCase):
    """Test cases for CommandExecutor service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.executor = CommandExecutor()
        self.progress_lines = []
        
    def progress_callback(self, line):
        """Test progress callback"""
        self.progress_lines.append(line)
    
    def test_validate_command_valid(self):
        """Test validation of valid commands"""
        # Valid rpm-ostree commands
        valid, error = self.executor.validate_command(["rpm-ostree", "status"])
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        valid, error = self.executor.validate_command(
            ["rpm-ostree", "rebase", "ghcr.io/ublue-os/bluefin:latest"]
        )
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_validate_command_invalid(self):
        """Test validation rejects dangerous commands"""
        # Empty command
        valid, error = self.executor.validate_command([])
        self.assertFalse(valid)
        self.assertEqual(error, "Empty command")
        
        # Shell injection attempts
        valid, error = self.executor.validate_command(
            ["rpm-ostree", "status", "; rm -rf /"]
        )
        self.assertFalse(valid)
        self.assertIn("dangerous character", error)
        
        # Invalid registry
        valid, error = self.executor.validate_command(
            ["rpm-ostree", "rebase", "docker.io/malicious/image:latest"]
        )
        self.assertFalse(valid)
        self.assertIn("allowed registry", error)
        
        # Unsupported subcommand
        valid, error = self.executor.validate_command(
            ["rpm-ostree", "uninstall"]
        )
        self.assertFalse(valid)
        self.assertIn("Unsupported", error)
    
    @patch('subprocess.Popen')
    def test_execute_with_progress_success(self, mock_popen):
        """Test successful command execution with progress"""
        # Mock the process
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, None, 0]  # Running, running, then done
        mock_process.stdout.readline.side_effect = [
            "Line 1\n",
            "Line 2\n",
            ""  # EOF
        ]
        mock_process.communicate.return_value = ("Line 3\n", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Execute command
        success, output, error_type = self.executor.execute_with_progress(
            ["echo", "test"],
            self.progress_callback
        )
        
        # Verify results
        self.assertTrue(success)
        self.assertIn("Line 1", output)
        self.assertIn("Line 2", output)
        self.assertIn("Line 3", output)
        
        # Verify subprocess was called correctly
        mock_popen.assert_called_once_with(
            ["echo", "test"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    
    @patch('subprocess.Popen')
    def test_execute_with_progress_failure(self, mock_popen):
        """Test command execution failure handling"""
        # Mock failed process
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 1]  # Running, then failed
        mock_process.stdout.readline.side_effect = [
            "Error: Command failed\n",
            ""
        ]
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        # Execute command
        success, output, error_type = self.executor.execute_with_progress(
            ["false"],
            self.progress_callback
        )
        
        # Verify failure
        self.assertFalse(success)
        self.assertIn("exit code 1", output)
        self.assertIn("Error: Command failed", output)
    
    @patch('subprocess.Popen')
    def test_execute_concurrent_prevention(self, mock_popen):
        """Test that concurrent executions are prevented"""
        # Mock long-running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Keep running
        mock_process.stdout.readline.return_value = "Running...\n"
        mock_popen.return_value = mock_process
        
        # Start first execution in thread
        def first_execution():
            self.executor.execute_with_progress(["sleep", "5"], lambda x: None)
        
        thread = threading.Thread(target=first_execution)
        thread.start()
        
        # Give it a moment to start
        time.sleep(0.1)
        
        # Try second execution - should be rejected
        success, output, error_type = self.executor.execute_with_progress(
            ["echo", "test"],
            self.progress_callback
        )
        
        self.assertFalse(success)
        self.assertIn("already executing", output)
        
        # Clean up
        self.executor.cancel_current_execution()
        thread.join(timeout=1)
    
    @patch('subprocess.Popen')
    def test_cancel_execution(self, mock_popen):
        """Test command cancellation"""
        # Mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        mock_process.terminate = MagicMock()
        mock_popen.return_value = mock_process
        
        # Set up executor state
        self.executor.current_process = mock_process
        self.executor.is_executing = True
        
        # Cancel execution
        cancelled = self.executor.cancel_current_execution()
        
        self.assertTrue(cancelled)
        mock_process.terminate.assert_called_once()
    
    @patch('gi.repository.Gio.DBusProxy.new_for_bus_sync')
    def test_request_elevated_privileges_success(self, mock_dbus):
        """Test successful polkit authorization"""
        # Mock DBus proxy
        mock_authority = MagicMock()
        mock_authority.CheckAuthorization.return_value = [[True], None]
        mock_dbus.return_value = mock_authority
        
        # Request privileges
        authorized, error = self.executor.request_elevated_privileges()
        
        self.assertTrue(authorized)
        mock_authority.CheckAuthorization.assert_called_once()
    
    @patch('gi.repository.Gio.DBusProxy.new_for_bus_sync')
    def test_request_elevated_privileges_denied(self, mock_dbus):
        """Test denied polkit authorization"""
        # Mock DBus proxy
        mock_authority = MagicMock()
        mock_authority.CheckAuthorization.return_value = [[False], None]
        mock_dbus.return_value = mock_authority
        
        # Request privileges
        authorized, error = self.executor.request_elevated_privileges()
        
        self.assertFalse(authorized)
    
    def test_execute_with_confirmation_callback(self):
        """Test confirmation callback mechanism"""
        # Mock callbacks
        confirm_callback = Mock()
        progress_callback = Mock()
        
        # Get confirmation handler
        handler = self.executor.execute_with_confirmation(
            ["echo", "test"],
            "This is a test",
            confirm_callback,
            progress_callback
        )
        
        # Simulate user rejection
        handler(False)
        confirm_callback.assert_called_once_with(False, "")
        
        # Reset and simulate user confirmation
        confirm_callback.reset_mock()
        with patch.object(self.executor, 'execute_with_progress') as mock_execute:
            mock_execute.return_value = (True, "Success", "")
            handler(True)
            # Give thread time to execute
            time.sleep(0.1)
            self.assertTrue(mock_execute.called)


if __name__ == '__main__':
    unittest.main()