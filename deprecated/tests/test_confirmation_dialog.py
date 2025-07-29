#!/usr/bin/env python3
"""
Unit tests for ConfirmationDialog
Tests dialog creation, responses, and cancellation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock GTK/Adw before importing
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()

# Create mock classes
class MockMessageDialog:
    def __init__(self):
        self.parent = None
        self.title = None
        self.heading = None
        self.body = None
        self.body_use_markup = False
        self.responses = {}
        self.response_appearances = {}
        self.default_response = None
        self.response_callback = None
        
    @classmethod
    def new(cls, parent, title, heading):
        dialog = cls()
        dialog.parent = parent
        dialog.title = title
        dialog.heading = heading
        return dialog
    
    def set_body(self, body):
        self.body = body
    
    def set_body_use_markup(self, use_markup):
        self.body_use_markup = use_markup
    
    def add_response(self, response_id, label):
        self.responses[response_id] = label
    
    def set_response_appearance(self, response_id, appearance):
        self.response_appearances[response_id] = appearance
    
    def set_default_response(self, response_id):
        self.default_response = response_id
    
    def connect(self, signal, callback):
        if signal == "response":
            self.response_callback = callback
    
    def present(self):
        pass
    
    def simulate_response(self, response_id):
        """Test helper to simulate user response"""
        if self.response_callback:
            self.response_callback(self, response_id)

# Apply mocks
sys.modules['gi.repository'].Adw = MagicMock()
sys.modules['gi.repository'].Adw.MessageDialog = MockMessageDialog
sys.modules['gi.repository'].Adw.ResponseAppearance = MagicMock()
sys.modules['gi.repository'].Adw.ResponseAppearance.SUGGESTED = "suggested"
sys.modules['gi.repository'].Adw.ResponseAppearance.DESTRUCTIVE = "destructive"
sys.modules['gi.repository'].GLib = MagicMock()
sys.modules['gi.repository'].GLib.markup_escape_text = lambda x: x

# Now import after mocks are set up
from ui.confirmation_dialog import ConfirmationDialog


class TestConfirmationDialog(unittest.TestCase):
    """Test cases for ConfirmationDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parent_window = MagicMock()
        self.dialog = ConfirmationDialog(self.parent_window)
        self.callback_result = None
        
        # Patch MessageDialog.new to return our mock
        self.patcher = patch('ui.confirmation_dialog.Adw.MessageDialog.new')
        self.mock_dialog_class = self.patcher.start()
        self.mock_dialog = MockMessageDialog()
        self.mock_dialog_class.return_value = self.mock_dialog
        
    def tearDown(self):
        """Clean up"""
        self.patcher.stop()
    
    def callback(self, confirmed):
        """Test callback to capture response"""
        self.callback_result = confirmed
    
    def test_show_rebase_confirmation_structure(self):
        """Test rebase confirmation dialog structure"""
        # Show dialog
        self.dialog.show_rebase_confirmation(
            "Bluefin",
            "rpm-ostree rebase ghcr.io/ublue-os/bluefin:latest",
            self.callback
        )
        
        # Verify dialog creation
        self.mock_dialog_class.assert_called_once_with(
            self.parent_window,
            "Rebase to Bluefin?",
            "This will execute the following command:\n\n"
            "<tt>rpm-ostree rebase ghcr.io/ublue-os/bluefin:latest</tt>"
        )
        
        # Verify body contains safety warnings
        self.assertIn("Important Safety Information", self.mock_dialog.body)
        self.assertIn("system restart will be required", self.mock_dialog.body)
        self.assertIn("administrator privileges", self.mock_dialog.body)
        self.assertTrue(self.mock_dialog.body_use_markup)
        
        # Verify buttons
        self.assertIn("cancel", self.mock_dialog.responses)
        self.assertIn("execute", self.mock_dialog.responses)
        
        # Verify execute button is suggested (blue)
        self.assertEqual(
            self.mock_dialog.response_appearances.get("execute"),
            "suggested"
        )
        
        # Verify default is cancel
        self.assertEqual(self.mock_dialog.default_response, "cancel")
    
    def test_show_rebase_confirmation_execute(self):
        """Test rebase confirmation with execute response"""
        # Show dialog
        self.dialog.show_rebase_confirmation(
            "Aurora",
            "rpm-ostree rebase ghcr.io/ublue-os/aurora:latest",
            self.callback
        )
        
        # Simulate user clicking Execute
        self.mock_dialog.simulate_response("execute")
        
        # Verify callback was called with True
        self.assertTrue(self.callback_result)
    
    def test_show_rebase_confirmation_cancel(self):
        """Test rebase confirmation with cancel response"""
        # Show dialog
        self.dialog.show_rebase_confirmation(
            "Bazzite",
            "rpm-ostree rebase ghcr.io/ublue-os/bazzite:latest",
            self.callback
        )
        
        # Simulate user clicking Cancel
        self.mock_dialog.simulate_response("cancel")
        
        # Verify callback was called with False
        self.assertFalse(self.callback_result)
    
    def test_show_rollback_confirmation_structure(self):
        """Test rollback confirmation dialog structure"""
        deployment_info = {
            'image_name': 'Universal Blue - Aurora',
            'version': '40.20240715.0',
            'timestamp': '2024-07-15 14:20:00',
            'id': 'abc123def456',
            'status': ['Pinned']
        }
        
        # Show dialog
        self.dialog.show_rollback_confirmation(
            deployment_info,
            "rpm-ostree rollback",
            self.callback
        )
        
        # Verify dialog creation
        self.mock_dialog_class.assert_called_once_with(
            self.parent_window,
            "Rollback to Universal Blue - Aurora?",
            "This will execute the following command:\n\n"
            "<tt>rpm-ostree rollback</tt>"
        )
        
        # Verify body contains deployment details
        self.assertIn("Version: 40.20240715.0", self.mock_dialog.body)
        self.assertIn("Deployed: 2024-07-15 14:20:00", self.mock_dialog.body)
        self.assertIn("ID: abc123def456", self.mock_dialog.body)
        self.assertIn("Status: Pinned", self.mock_dialog.body)
        self.assertIn("revert to a previous system state", self.mock_dialog.body)
        
        # Verify buttons
        self.assertIn("cancel", self.mock_dialog.responses)
        self.assertIn("rollback", self.mock_dialog.responses)
        
        # Verify rollback button is destructive (red)
        self.assertEqual(
            self.mock_dialog.response_appearances.get("rollback"),
            "destructive"
        )
        
        # Verify default is cancel
        self.assertEqual(self.mock_dialog.default_response, "cancel")
    
    def test_show_rollback_confirmation_minimal_info(self):
        """Test rollback confirmation with minimal deployment info"""
        deployment_info = {
            'image_name': 'Previous Deployment'
        }
        
        # Show dialog
        self.dialog.show_rollback_confirmation(
            deployment_info,
            "rpm-ostree deploy fedcba098765",
            self.callback
        )
        
        # Should handle gracefully
        self.assertIn("No additional details available", self.mock_dialog.body)
    
    def test_show_rollback_confirmation_rollback(self):
        """Test rollback confirmation with rollback response"""
        deployment_info = {'image_name': 'Test Image'}
        
        # Show dialog
        self.dialog.show_rollback_confirmation(
            deployment_info,
            "rpm-ostree rollback",
            self.callback
        )
        
        # Simulate user clicking Rollback
        self.mock_dialog.simulate_response("rollback")
        
        # Verify callback was called with True
        self.assertTrue(self.callback_result)
    
    def test_show_rollback_confirmation_cancel(self):
        """Test rollback confirmation with cancel response"""
        deployment_info = {'image_name': 'Test Image'}
        
        # Show dialog
        self.dialog.show_rollback_confirmation(
            deployment_info,
            "rpm-ostree rollback",
            self.callback
        )
        
        # Simulate user clicking Cancel
        self.mock_dialog.simulate_response("cancel")
        
        # Verify callback was called with False
        self.assertFalse(self.callback_result)
    
    def test_get_user_response(self):
        """Test get_user_response method"""
        # Should return None (method is for compatibility)
        self.assertIsNone(self.dialog.get_user_response())
    
    def test_show_error_dialog(self):
        """Test error dialog creation"""
        self.dialog.show_error_dialog("Error Title", "Error message")
        
        # Verify dialog creation
        self.mock_dialog_class.assert_called_with(
            self.parent_window,
            "Error Title",
            "Error message"
        )
        
        # Verify OK button
        self.assertIn("ok", self.mock_dialog.responses)
        self.assertEqual(self.mock_dialog.default_response, "ok")
    
    def test_show_info_dialog(self):
        """Test info dialog creation"""
        self.dialog.show_info_dialog("Info Title", "Info message")
        
        # Verify dialog creation
        self.mock_dialog_class.assert_called_with(
            self.parent_window,
            "Info Title",
            "Info message"
        )
        
        # Verify OK button
        self.assertIn("ok", self.mock_dialog.responses)
        self.assertEqual(self.mock_dialog.default_response, "ok")
    
    def test_callback_cleared_after_response(self):
        """Test that callback is cleared after use"""
        # Show dialog
        self.dialog.show_rebase_confirmation(
            "Test",
            "test command",
            self.callback
        )
        
        # Verify callback is set
        self.assertIsNotNone(self.dialog.response_callback)
        
        # Simulate response
        self.mock_dialog.simulate_response("cancel")
        
        # Verify callback is cleared
        self.assertIsNone(self.dialog.response_callback)


if __name__ == '__main__':
    unittest.main()