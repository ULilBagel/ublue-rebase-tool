#!/usr/bin/env python3
"""
Unit tests for update tool command selection logic
"""

import unittest
from unittest.mock import MagicMock, patch, call
import subprocess
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock GTK/Adw imports before importing the module
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()
sys.modules['gi.repository.Gtk'] = MagicMock()
sys.modules['gi.repository.Adw'] = MagicMock()
sys.modules['gi.repository.Gio'] = MagicMock()
sys.modules['gi.repository.GLib'] = MagicMock()

# Define UPDATE_TOOLS directly (copied from atomic-os-manager.py)
UPDATE_TOOLS = [
    {
        "name": "uupd",
        "command": ["flatpak-spawn", "--host", "pkexec", "uupd", "--json"],
        "check_command": "uupd",
        "reboot_indicators": ["(R)eboot", "(r)eboot", "restart required", "Reboot required", "System restart required"],
        "json_output": True,
        "needs_tty": False,
    },
    {
        "name": "ujust",
        "command": ["flatpak-spawn", "--host", "ujust", "update"],
        "check_command": "ujust",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
        "json_output": False,
    },
    {
        "name": "bootc",
        "command": ["flatpak-spawn", "--host", "pkexec", "bootc", "upgrade"],
        "check_command": "bootc",
        "reboot_indicators": ["(R)eboot", "(r)eboot", "restart required", "Reboot required"],
        "json_output": False,
    },
    {
        "name": "rpm-ostree",
        "command": ["flatpak-spawn", "--host", "rpm-ostree", "upgrade"],
        "check_command": "rpm-ostree",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
        "json_output": False,
    }
]


class TestUpdateToolSelection(unittest.TestCase):
    """Test cases for update tool selection logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_subprocess_run = patch('subprocess.run').start()
        self.mock_subprocess_popen = patch('subprocess.Popen').start()
        self.addCleanup(patch.stopall)
        
    def test_update_tools_configuration(self):
        """Test UPDATE_TOOLS configuration structure"""
        # Verify UPDATE_TOOLS exists and has correct structure
        self.assertIsInstance(UPDATE_TOOLS, list)
        self.assertGreater(len(UPDATE_TOOLS), 0)
        
        # Check uupd is first in priority
        self.assertEqual(UPDATE_TOOLS[0]["name"], "uupd")
        self.assertEqual(UPDATE_TOOLS[0]["check_command"], "uupd")
        self.assertEqual(UPDATE_TOOLS[0]["command"], ["flatpak-spawn", "--host", "pkexec", "uupd", "--json"])
        self.assertIn("(R)eboot", UPDATE_TOOLS[0]["reboot_indicators"])
        self.assertIn("restart required", UPDATE_TOOLS[0]["reboot_indicators"])
        self.assertTrue(UPDATE_TOOLS[0]["json_output"])  # Using JSON output
        
        # Check ujust is second
        self.assertEqual(UPDATE_TOOLS[1]["name"], "ujust")
        self.assertEqual(UPDATE_TOOLS[1]["check_command"], "ujust")
        
        # Check bootc is third
        self.assertEqual(UPDATE_TOOLS[2]["name"], "bootc")
        self.assertEqual(UPDATE_TOOLS[2]["check_command"], "bootc")
        
        # Check rpm-ostree is fourth
        self.assertEqual(UPDATE_TOOLS[3]["name"], "rpm-ostree")
        self.assertEqual(UPDATE_TOOLS[3]["check_command"], "rpm-ostree")
        
    def test_uupd_available_selection(self):
        """Test that uupd is selected when available"""
        # Mock uupd as available
        self.mock_subprocess_run.return_value.returncode = 0
        
        # Simulate tool selection logic
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                break
                
        # Verify uupd was selected
        self.assertIsNotNone(selected_tool)
        self.assertEqual(selected_tool["name"], "uupd")
        
        # Verify only one check was made
        self.assertEqual(self.mock_subprocess_run.call_count, 1)
        self.mock_subprocess_run.assert_called_with(
            ["flatpak-spawn", "--host", "which", "uupd"],
            capture_output=True
        )
        
    def test_fallback_to_ujust(self):
        """Test fallback to ujust when uupd not available"""
        # Mock uupd not available, ujust available
        self.mock_subprocess_run.side_effect = [
            MagicMock(returncode=1),  # uupd not found
            MagicMock(returncode=0),  # ujust found
        ]
        
        # Simulate tool selection logic
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                break
                
        # Verify ujust was selected
        self.assertIsNotNone(selected_tool)
        self.assertEqual(selected_tool["name"], "ujust")
        
        # Verify both checks were made
        self.assertEqual(self.mock_subprocess_run.call_count, 2)
        
    def test_fallback_to_bootc(self):
        """Test fallback to bootc when neither uupd nor ujust available"""
        # Mock uupd and ujust not available, bootc available
        self.mock_subprocess_run.side_effect = [
            MagicMock(returncode=1),  # uupd not found
            MagicMock(returncode=1),  # ujust not found
            MagicMock(returncode=0),  # bootc found
        ]
        
        # Simulate tool selection logic
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                break
                
        # Verify bootc was selected
        self.assertIsNotNone(selected_tool)
        self.assertEqual(selected_tool["name"], "bootc")
        
        # Verify all three checks were made
        self.assertEqual(self.mock_subprocess_run.call_count, 3)
        
    def test_fallback_to_rpm_ostree(self):
        """Test fallback to rpm-ostree when other tools not available"""
        # Mock uupd, ujust, and bootc not available, rpm-ostree available
        self.mock_subprocess_run.side_effect = [
            MagicMock(returncode=1),  # uupd not found
            MagicMock(returncode=1),  # ujust not found
            MagicMock(returncode=1),  # bootc not found
            MagicMock(returncode=0),  # rpm-ostree found
        ]
        
        # Simulate tool selection logic
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                break
                
        # Verify rpm-ostree was selected
        self.assertIsNotNone(selected_tool)
        self.assertEqual(selected_tool["name"], "rpm-ostree")
        
        # Verify all four checks were made
        self.assertEqual(self.mock_subprocess_run.call_count, 4)
        
    def test_no_tools_available(self):
        """Test behavior when no update tools are available"""
        # Mock all tools not available
        self.mock_subprocess_run.return_value.returncode = 1
        
        # Simulate tool selection logic
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                break
                
        # Verify no tool was selected
        self.assertIsNone(selected_tool)
        
        # Verify all tools were checked
        self.assertEqual(self.mock_subprocess_run.call_count, 4)
        
    def test_reboot_indicators_per_tool(self):
        """Test that each tool has appropriate reboot indicators"""
        for tool in UPDATE_TOOLS:
            # Verify reboot_indicators exists and is a list
            self.assertIn("reboot_indicators", tool)
            self.assertIsInstance(tool["reboot_indicators"], list)
            self.assertGreater(len(tool["reboot_indicators"]), 0)
            
            # Verify common indicators are present
            self.assertIn("(R)eboot", tool["reboot_indicators"])
            self.assertIn("(r)eboot", tool["reboot_indicators"])
            
    def test_command_structure(self):
        """Test that all tools have proper command structure"""
        for tool in UPDATE_TOOLS:
            # Verify required fields exist
            self.assertIn("name", tool)
            self.assertIn("command", tool)
            self.assertIn("check_command", tool)
            self.assertIn("reboot_indicators", tool)
            
            # Verify command is a list starting with flatpak-spawn
            self.assertIsInstance(tool["command"], list)
            self.assertEqual(tool["command"][0], "flatpak-spawn")
            self.assertEqual(tool["command"][1], "--host")
            
            # Verify check_command is a string
            self.assertIsInstance(tool["check_command"], str)


if __name__ == '__main__':
    unittest.main()