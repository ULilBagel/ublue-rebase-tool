#!/usr/bin/env python3
"""
Unit tests for HistoryManager
Tests command history storage, retrieval, and pruning
"""

import unittest
import tempfile
import shutil
import os
import json
import time
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from history_manager import HistoryManager, HistoryEntry


class TestHistoryEntry(unittest.TestCase):
    """Test cases for HistoryEntry data class"""
    
    def test_history_entry_creation(self):
        """Test creating a history entry"""
        entry = HistoryEntry(
            command="rpm-ostree rebase test:latest",
            timestamp=1234567890.0,
            success=True,
            image_name="test:latest",
            operation_type="rebase"
        )
        
        self.assertEqual(entry.command, "rpm-ostree rebase test:latest")
        self.assertEqual(entry.timestamp, 1234567890.0)
        self.assertTrue(entry.success)
        self.assertEqual(entry.image_name, "test:latest")
        self.assertEqual(entry.operation_type, "rebase")
        
    def test_to_dict(self):
        """Test converting entry to dictionary"""
        entry = HistoryEntry(
            command="test command",
            timestamp=1234567890.0,
            success=False,
            image_name="image",
            operation_type="rollback"
        )
        
        data = entry.to_dict()
        self.assertEqual(data['command'], "test command")
        self.assertEqual(data['timestamp'], 1234567890.0)
        self.assertFalse(data['success'])
        self.assertEqual(data['image_name'], "image")
        self.assertEqual(data['operation_type'], "rollback")
        
    def test_from_dict(self):
        """Test creating entry from dictionary"""
        data = {
            'command': "test command",
            'timestamp': 1234567890.0,
            'success': True,
            'image_name': "test:latest",
            'operation_type': "rebase"
        }
        
        entry = HistoryEntry.from_dict(data)
        self.assertEqual(entry.command, "test command")
        self.assertEqual(entry.timestamp, 1234567890.0)
        self.assertTrue(entry.success)
        
    def test_get_formatted_time(self):
        """Test formatted time output"""
        entry = HistoryEntry(
            command="test",
            timestamp=1234567890.0,  # 2009-02-13 23:31:30
            success=True,
            image_name="",
            operation_type="unknown"
        )
        
        formatted = entry.get_formatted_time()
        self.assertIn("2009", formatted)
        self.assertIn("02", formatted)
        self.assertIn("13", formatted)


class TestHistoryManager(unittest.TestCase):
    """Test cases for HistoryManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock GLib to return our temp directory
        self.glib_patcher = patch('history_manager.GLib')
        mock_glib = self.glib_patcher.start()
        mock_glib.get_user_data_dir.return_value = self.temp_dir
        
        # Create manager instance
        self.manager = HistoryManager()
        
    def tearDown(self):
        """Clean up after tests"""
        self.glib_patcher.stop()
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_directory_creation(self):
        """Test that data directory is created"""
        expected_dir = os.path.join(self.temp_dir, "ublue-image-manager")
        self.assertTrue(os.path.exists(expected_dir))
        
    def test_add_entry(self):
        """Test adding entries to history"""
        # Add an entry
        self.manager.add_entry(
            command="rpm-ostree rebase test:latest",
            success=True,
            image_name="test:latest",
            operation_type="rebase"
        )
        
        # Verify it was saved
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].command, "rpm-ostree rebase test:latest")
        self.assertTrue(entries[0].success)
        
    def test_multiple_entries(self):
        """Test adding multiple entries"""
        # Add several entries
        for i in range(5):
            self.manager.add_entry(
                command=f"command {i}",
                success=i % 2 == 0,
                image_name=f"image{i}",
                operation_type="rebase"
            )
            
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 5)
        
        # Verify order (newest first)
        self.assertEqual(entries[0].command, "command 4")
        self.assertEqual(entries[4].command, "command 0")
        
    def test_get_recent_entries_with_limit(self):
        """Test retrieving limited number of entries"""
        # Add 10 entries
        for i in range(10):
            self.manager.add_entry(
                command=f"command {i}",
                success=True,
                image_name="test",
                operation_type="rebase"
            )
            
        # Get only 5
        entries = self.manager.get_recent_entries(limit=5)
        self.assertEqual(len(entries), 5)
        self.assertEqual(entries[0].command, "command 9")
        
    def test_automatic_pruning(self):
        """Test that old entries are pruned automatically"""
        # Add more than MAX_ENTRIES
        for i in range(60):
            self.manager.add_entry(
                command=f"command {i}",
                success=True,
                image_name="test",
                operation_type="rebase"
            )
            
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), HistoryManager.MAX_ENTRIES)
        
        # Verify oldest entries were removed
        commands = [e.command for e in entries]
        self.assertNotIn("command 0", commands)
        self.assertNotIn("command 9", commands)
        self.assertIn("command 59", commands)
        
    def test_prune_old_entries(self):
        """Test manual pruning"""
        # Create a custom history file with too many entries
        entries_data = []
        for i in range(70):
            entries_data.append({
                'command': f"command {i}",
                'timestamp': time.time(),
                'success': True,
                'image_name': "test",
                'operation_type': "rebase"
            })
            
        with open(self.manager.history_file, 'w') as f:
            json.dump(entries_data, f)
            
        # Prune entries
        removed = self.manager.prune_old_entries()
        self.assertEqual(removed, 20)  # 70 - 50
        
        # Verify only 50 remain
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 50)
        
    def test_clear_history(self):
        """Test clearing all history"""
        # Add some entries
        for i in range(5):
            self.manager.add_entry(f"command {i}", True)
            
        # Clear history
        self.manager.clear_history()
        
        # Verify empty
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 0)
        
    def test_get_entries_by_type(self):
        """Test filtering by operation type"""
        # Add mixed entries
        self.manager.add_entry("rebase 1", True, operation_type="rebase")
        self.manager.add_entry("rollback 1", True, operation_type="rollback")
        self.manager.add_entry("rebase 2", True, operation_type="rebase")
        
        # Get only rebase entries
        rebase_entries = self.manager.get_entries_by_type("rebase")
        self.assertEqual(len(rebase_entries), 2)
        
        # Get only rollback entries
        rollback_entries = self.manager.get_entries_by_type("rollback")
        self.assertEqual(len(rollback_entries), 1)
        
    def test_get_successful_and_failed_entries(self):
        """Test filtering by success status"""
        # Add mixed entries
        self.manager.add_entry("success 1", True)
        self.manager.add_entry("fail 1", False)
        self.manager.add_entry("success 2", True)
        self.manager.add_entry("fail 2", False)
        
        # Get successful entries
        successful = self.manager.get_successful_entries()
        self.assertEqual(len(successful), 2)
        self.assertTrue(all(e.success for e in successful))
        
        # Get failed entries
        failed = self.manager.get_failed_entries()
        self.assertEqual(len(failed), 2)
        self.assertTrue(all(not e.success for e in failed))
        
    def test_export_history(self):
        """Test exporting history to file"""
        # Add some entries
        self.manager.add_entry("command 1", True, "image1", "rebase")
        self.manager.add_entry("command 2", False, "image2", "rollback")
        
        # Export to file
        export_file = os.path.join(self.temp_dir, "export.json")
        result = self.manager.export_history(export_file)
        self.assertTrue(result)
        
        # Verify export file
        self.assertTrue(os.path.exists(export_file))
        with open(export_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['command'], "command 2")
            
    def test_corrupted_history_file(self):
        """Test handling of corrupted history file"""
        # Write invalid JSON
        with open(self.manager.history_file, 'w') as f:
            f.write("invalid json {]}")
            
        # Should return empty list
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 0)
        
        # Should still be able to add new entries
        self.manager.add_entry("new command", True)
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 1)
        
    def test_malformed_entry_skipping(self):
        """Test that malformed entries are skipped"""
        # Create history with one good and one bad entry
        data = [
            {
                'command': "good command",
                'timestamp': time.time(),
                'success': True,
                'image_name': "test",
                'operation_type': "rebase"
            },
            {
                # Missing required fields
                'command': "bad command"
            }
        ]
        
        with open(self.manager.history_file, 'w') as f:
            json.dump(data, f)
            
        # Should load only the good entry
        entries = self.manager.get_recent_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].command, "good command")
        
    def test_no_glib_fallback(self):
        """Test fallback when GLib is not available"""
        # Stop current patcher
        self.glib_patcher.stop()
        
        # Mock GLib as None
        with patch('history_manager.GLib', None):
            # Test with XDG_DATA_HOME set
            with patch.dict(os.environ, {'XDG_DATA_HOME': self.temp_dir}):
                manager = HistoryManager()
                expected = os.path.join(self.temp_dir, "ublue-image-manager")
                self.assertEqual(manager.history_dir, expected)
                
            # Test without XDG_DATA_HOME
            with patch.dict(os.environ, {}, clear=True):
                with patch('os.path.expanduser') as mock_expand:
                    mock_expand.return_value = self.temp_dir
                    manager = HistoryManager()
                    expected = os.path.join(self.temp_dir, ".local", "share", "ublue-image-manager")
                    self.assertEqual(manager.history_dir, expected)


if __name__ == '__main__':
    unittest.main()