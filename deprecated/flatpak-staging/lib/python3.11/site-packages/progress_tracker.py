#!/usr/bin/env python3
"""
Progress Tracker for Real-time Command Output Display
Provides real-time streaming of command output to the web interface
Following Universal Blue patterns for user feedback and transparency
"""

import json
import time
import threading
from typing import Optional, Callable
from collections import deque
from gi.repository import GLib


class ProgressTracker:
    """Track and display real-time command output in the web interface"""
    
    def __init__(self, api_reference):
        """
        Initialize progress tracker with API reference for JS execution
        
        Args:
            api_reference: Reference to UBlueImageAPI for execute_js access
        """
        self.api = api_reference
        self.operation_name = None
        self.start_time = None
        self.output_buffer = deque(maxlen=1000)  # Buffer last 1000 lines
        self.is_tracking = False
        self.line_buffer = ""  # For handling partial lines
        
    def start_tracking(self, operation_name: str) -> None:
        """
        Initialize progress display for a new operation
        
        Args:
            operation_name: Name of the operation (e.g., "Rebase to Bluefin")
        """
        self.operation_name = operation_name
        self.start_time = time.time()
        self.output_buffer.clear()
        self.line_buffer = ""
        self.is_tracking = True
        
        # Initialize progress display in web UI
        js_script = f"""
        if (typeof initializeProgress === 'function') {{
            initializeProgress({{
                'operation': {json.dumps(operation_name)},
                'startTime': {self.start_time}
            }});
        }}
        """
        GLib.idle_add(self.api.execute_js, js_script)
        
    def update_output(self, data: str) -> None:
        """
        Add output data to display, handling line buffering
        
        Args:
            data: Raw output data (may contain partial lines)
        """
        if not self.is_tracking:
            return
            
        # Handle line buffering for clean display
        self.line_buffer += data
        lines = self.line_buffer.split('\n')
        
        # Keep the last incomplete line in the buffer
        if not data.endswith('\n'):
            self.line_buffer = lines[-1]
            lines = lines[:-1]
        else:
            self.line_buffer = ""
            
        # Process complete lines
        for line in lines:
            if line.strip():  # Skip empty lines
                self._add_output_line(line)
                
    def _add_output_line(self, line: str) -> None:
        """
        Add a single line to the output display
        
        Args:
            line: Complete line of output
        """
        # Clean ANSI escape codes for web display
        clean_line = self._clean_ansi_codes(line)
        
        # Add to buffer
        self.output_buffer.append({
            'text': clean_line,
            'timestamp': time.time()
        })
        
        # Update web UI
        js_script = f"""
        if (typeof updateProgress === 'function') {{
            updateProgress({{
                'line': {json.dumps(clean_line)},
                'timestamp': {time.time()}
            }});
        }}
        """
        GLib.idle_add(self.api.execute_js, js_script)
        
    def complete(self, success: bool, message: str = "") -> None:
        """
        Mark operation as complete and display final status
        
        Args:
            success: Whether the operation completed successfully
            message: Optional completion message
        """
        if not self.is_tracking:
            return
            
        # Flush any remaining buffered output
        if self.line_buffer:
            self._add_output_line(self.line_buffer)
            self.line_buffer = ""
            
        self.is_tracking = False
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        # Prepare completion data
        completion_data = {
            'operation': self.operation_name,
            'success': success,
            'message': message or ("Operation completed successfully" if success else "Operation failed"),
            'elapsedTime': elapsed_time,
            'lineCount': len(self.output_buffer)
        }
        
        # Update web UI with completion status
        js_script = f"""
        if (typeof completeProgress === 'function') {{
            completeProgress({json.dumps(completion_data)});
        }}
        """
        GLib.idle_add(self.api.execute_js, js_script)
        
    def get_full_output(self) -> str:
        """
        Get the complete output buffer as a string
        
        Returns:
            Full output text
        """
        return '\n'.join(entry['text'] for entry in self.output_buffer)
        
    def clear(self) -> None:
        """Clear the progress tracker state"""
        self.operation_name = None
        self.start_time = None
        self.output_buffer.clear()
        self.line_buffer = ""
        self.is_tracking = False
        
    @staticmethod
    def _clean_ansi_codes(text: str) -> str:
        """
        Remove ANSI escape codes from text for clean web display
        
        Args:
            text: Text possibly containing ANSI codes
            
        Returns:
            Cleaned text
        """
        import re
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
        
    def create_progress_callback(self) -> Callable[[str], None]:
        """
        Create a callback function for subprocess output streaming
        
        Returns:
            Callback function that can be used with subprocess
        """
        def callback(output: str):
            self.update_output(output)
        return callback