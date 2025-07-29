#!/usr/bin/env python3
"""
Unit tests for ProgressTracker
Tests real-time output streaming and JavaScript injection
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import time
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from progress_tracker import ProgressTracker


class TestProgressTracker(unittest.TestCase):
    """Test cases for ProgressTracker functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock API with execute_js method
        self.mock_api = Mock()
        self.mock_api.execute_js = Mock()
        
        # Create tracker instance
        self.tracker = ProgressTracker(self.mock_api)
        
        # Mock GLib.idle_add to execute functions immediately
        self.glib_patcher = patch('progress_tracker.GLib.idle_add', side_effect=lambda func, *args: func(*args))
        self.glib_patcher.start()
        
    def tearDown(self):
        """Clean up after tests"""
        self.glib_patcher.stop()
        
    def test_start_tracking(self):
        """Test initialization of progress tracking"""
        operation_name = "Test Operation"
        
        # Start tracking
        self.tracker.start_tracking(operation_name)
        
        # Verify state
        self.assertEqual(self.tracker.operation_name, operation_name)
        self.assertIsNotNone(self.tracker.start_time)
        self.assertTrue(self.tracker.is_tracking)
        self.assertEqual(len(self.tracker.output_buffer), 0)
        
        # Verify JavaScript execution
        self.mock_api.execute_js.assert_called_once()
        js_call = self.mock_api.execute_js.call_args[0][0]
        self.assertIn('initializeProgress', js_call)
        self.assertIn(operation_name, js_call)
        
    def test_update_output_single_line(self):
        """Test updating output with a single complete line"""
        self.tracker.start_tracking("Test")
        self.mock_api.execute_js.reset_mock()
        
        # Add a complete line
        self.tracker.update_output("Test output line\n")
        
        # Verify buffer
        self.assertEqual(len(self.tracker.output_buffer), 1)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Test output line")
        
        # Verify JavaScript execution
        self.assertEqual(self.mock_api.execute_js.call_count, 1)
        js_call = self.mock_api.execute_js.call_args[0][0]
        self.assertIn('updateProgress', js_call)
        self.assertIn('Test output line', js_call)
        
    def test_update_output_partial_lines(self):
        """Test handling of partial lines and buffering"""
        self.tracker.start_tracking("Test")
        self.mock_api.execute_js.reset_mock()
        
        # Add partial lines
        self.tracker.update_output("Part 1 ")
        self.tracker.update_output("Part 2 ")
        self.tracker.update_output("Part 3\n")
        
        # Should only have one complete line
        self.assertEqual(len(self.tracker.output_buffer), 1)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Part 1 Part 2 Part 3")
        
    def test_update_output_multiple_lines(self):
        """Test handling multiple lines in one update"""
        self.tracker.start_tracking("Test")
        self.mock_api.execute_js.reset_mock()
        
        # Add multiple lines at once
        multi_line = "Line 1\nLine 2\nLine 3\n"
        self.tracker.update_output(multi_line)
        
        # Should have three lines
        self.assertEqual(len(self.tracker.output_buffer), 3)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Line 1")
        self.assertEqual(self.tracker.output_buffer[1]['text'], "Line 2")
        self.assertEqual(self.tracker.output_buffer[2]['text'], "Line 3")
        
        # Should have three JS calls
        self.assertEqual(self.mock_api.execute_js.call_count, 3)
        
    def test_ansi_code_removal(self):
        """Test removal of ANSI escape codes"""
        # Test various ANSI codes
        test_cases = [
            ("\x1b[31mRed text\x1b[0m", "Red text"),
            ("\x1b[1;32mBold green\x1b[0m", "Bold green"),
            ("\x1b[2J\x1b[H", ""),  # Clear screen
            ("Normal \x1b[33mYellow\x1b[0m text", "Normal Yellow text"),
        ]
        
        for input_text, expected in test_cases:
            cleaned = self.tracker._clean_ansi_codes(input_text)
            self.assertEqual(cleaned, expected)
            
    def test_complete_success(self):
        """Test successful completion of operation"""
        self.tracker.start_tracking("Test Operation")
        self.tracker.update_output("Some output\n")
        self.mock_api.execute_js.reset_mock()
        
        # Complete successfully
        self.tracker.complete(success=True, message="Custom success message")
        
        # Verify state
        self.assertFalse(self.tracker.is_tracking)
        
        # Verify JavaScript execution
        self.mock_api.execute_js.assert_called_once()
        js_call = self.mock_api.execute_js.call_args[0][0]
        self.assertIn('completeProgress', js_call)
        self.assertIn('"success": true', js_call)
        self.assertIn('Custom success message', js_call)
        
    def test_complete_failure(self):
        """Test failed completion of operation"""
        self.tracker.start_tracking("Test Operation")
        self.mock_api.execute_js.reset_mock()
        
        # Complete with failure
        self.tracker.complete(success=False, message="Error occurred")
        
        # Verify JavaScript execution
        js_call = self.mock_api.execute_js.call_args[0][0]
        self.assertIn('"success": false', js_call)
        self.assertIn('Error occurred', js_call)
        
    def test_complete_flushes_buffer(self):
        """Test that completion flushes any remaining buffer"""
        self.tracker.start_tracking("Test")
        self.mock_api.execute_js.reset_mock()
        
        # Add partial line
        self.tracker.update_output("Partial line without newline")
        
        # Should not be in buffer yet
        self.assertEqual(len(self.tracker.output_buffer), 0)
        
        # Complete operation
        self.tracker.complete(success=True)
        
        # Now should be flushed to buffer
        self.assertEqual(len(self.tracker.output_buffer), 1)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Partial line without newline")
        
    def test_get_full_output(self):
        """Test retrieving complete output as string"""
        self.tracker.start_tracking("Test")
        
        # Add multiple lines
        self.tracker.update_output("Line 1\n")
        self.tracker.update_output("Line 2\n")
        self.tracker.update_output("Line 3\n")
        
        # Get full output
        full_output = self.tracker.get_full_output()
        expected = "Line 1\nLine 2\nLine 3"
        self.assertEqual(full_output, expected)
        
    def test_clear(self):
        """Test clearing tracker state"""
        # Set up some state
        self.tracker.start_tracking("Test")
        self.tracker.update_output("Some output\n")
        
        # Clear
        self.tracker.clear()
        
        # Verify cleared state
        self.assertIsNone(self.tracker.operation_name)
        self.assertIsNone(self.tracker.start_time)
        self.assertEqual(len(self.tracker.output_buffer), 0)
        self.assertEqual(self.tracker.line_buffer, "")
        self.assertFalse(self.tracker.is_tracking)
        
    def test_create_progress_callback(self):
        """Test creation of subprocess callback"""
        self.tracker.start_tracking("Test")
        
        # Create callback
        callback = self.tracker.create_progress_callback()
        
        # Test callback
        callback("Test output\n")
        
        # Verify output was processed
        self.assertEqual(len(self.tracker.output_buffer), 1)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Test output")
        
    def test_output_buffer_limit(self):
        """Test that output buffer respects maxlen limit"""
        self.tracker.start_tracking("Test")
        
        # Add more than 1000 lines (the limit)
        for i in range(1100):
            self.tracker.update_output(f"Line {i}\n")
            
        # Should only have last 1000 lines
        self.assertEqual(len(self.tracker.output_buffer), 1000)
        
        # First line should be Line 100 (0-99 were dropped)
        self.assertEqual(self.tracker.output_buffer[0]['text'], "Line 100")
        
        # Last line should be Line 1099
        self.assertEqual(self.tracker.output_buffer[-1]['text'], "Line 1099")
        
    def test_not_tracking_ignores_updates(self):
        """Test that updates are ignored when not tracking"""
        # Don't start tracking
        self.tracker.update_output("Should be ignored\n")
        
        # Nothing should happen
        self.assertEqual(len(self.tracker.output_buffer), 0)
        self.mock_api.execute_js.assert_not_called()


if __name__ == '__main__':
    unittest.main()