#!/usr/bin/env python3
"""
History Manager for Command Tracking
Stores and manages command execution history with automatic pruning
Following Universal Blue patterns for data persistence
"""

import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path

try:
    from gi.repository import GLib
except ImportError:
    # Fallback for non-GTK environments (e.g., testing)
    GLib = None


@dataclass
class HistoryEntry:
    """Data class representing a command history entry"""
    command: str            # Executed command
    timestamp: float        # Unix timestamp
    success: bool           # Operation result
    image_name: str         # Target image (if rebase)
    operation_type: str     # 'rebase' or 'rollback'
    user_id: Optional[int] = None    # User ID who executed the command
    session_id: Optional[str] = None # Session identifier for audit trail
    error_message: Optional[str] = None  # Error message if command failed
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HistoryEntry':
        """Create HistoryEntry from dictionary"""
        return cls(**data)
    
    def get_formatted_time(self) -> str:
        """Get human-readable timestamp"""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class HistoryManager:
    """Manage command execution history with persistent storage"""
    
    MAX_ENTRIES = 50  # Maximum number of history entries to keep
    HISTORY_FILE = "command_history.json"
    
    def __init__(self):
        """Initialize HistoryManager with proper data directory"""
        self.history_dir = self._get_data_directory()
        self.history_file = os.path.join(self.history_dir, self.HISTORY_FILE)
        self._ensure_directory_exists()
        
    def _get_data_directory(self) -> str:
        """
        Get application data directory following XDG specifications
        
        Returns:
            Path to application data directory
        """
        if GLib:
            # Use GLib for proper XDG directory handling
            data_dir = GLib.get_user_data_dir()
            app_dir = os.path.join(data_dir, "ublue-image-manager")
        else:
            # Fallback to XDG standard paths
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                app_dir = os.path.join(xdg_data_home, "ublue-image-manager")
            else:
                home = os.path.expanduser("~")
                app_dir = os.path.join(home, ".local", "share", "ublue-image-manager")
                
        return app_dir
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the history directory exists"""
        Path(self.history_dir).mkdir(parents=True, exist_ok=True)
        
    def _load_history(self) -> List[HistoryEntry]:
        """
        Load history from JSON file
        
        Returns:
            List of HistoryEntry objects
        """
        if not os.path.exists(self.history_file):
            return []
            
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                entries = []
                for entry_data in data:
                    try:
                        entries.append(HistoryEntry.from_dict(entry_data))
                    except (TypeError, KeyError):
                        # Skip malformed entries
                        continue
                return entries
        except (json.JSONDecodeError, IOError):
            # Return empty list if file is corrupted or unreadable
            return []
    
    def _log_to_journal(self, entry: HistoryEntry) -> None:
        """
        Log command execution to system journal for security audit
        
        Args:
            entry: HistoryEntry to log
        """
        try:
            # Try to use systemd journal if available
            import systemd.journal
            systemd.journal.send(
                f"ublue-image-manager: {entry.operation_type} command executed",
                PRIORITY=systemd.journal.LOG_INFO if entry.success else systemd.journal.LOG_WARNING,
                COMMAND=entry.command,
                OPERATION_TYPE=entry.operation_type,
                SUCCESS=str(entry.success),
                IMAGE_NAME=entry.image_name,
                USER_ID=str(entry.user_id) if entry.user_id else "unknown",
                SESSION_ID=entry.session_id or "unknown",
                ERROR_MESSAGE=entry.error_message or "",
                SYSLOG_IDENTIFIER="ublue-image-manager"
            )
        except ImportError:
            # Fallback to syslog if systemd journal not available
            try:
                import syslog
                priority = syslog.LOG_INFO if entry.success else syslog.LOG_WARNING
                message = (
                    f"ublue-image-manager: {entry.operation_type} "
                    f"{'succeeded' if entry.success else 'failed'} - "
                    f"user={entry.user_id or 'unknown'} "
                    f"session={entry.session_id or 'unknown'} "
                    f"command={entry.command}"
                )
                if entry.error_message:
                    message += f" error={entry.error_message}"
                syslog.syslog(priority, message)
            except ImportError:
                # No system logging available, silently continue
                pass
    
    def _save_history(self, entries: List[HistoryEntry]) -> None:
        """
        Save history to JSON file
        
        Args:
            entries: List of HistoryEntry objects to save
        """
        try:
            # Convert entries to dictionaries
            data = [entry.to_dict() for entry in entries]
            
            # Write to temporary file first for atomic operation
            temp_file = self.history_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Atomic rename
            os.replace(temp_file, self.history_file)
            
            # Set secure permissions (owner read/write only)
            os.chmod(self.history_file, 0o600)
        except IOError as e:
            print(f"Error saving history: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
    
    def add_entry(self, command: str, success: bool, image_name: str = "", 
                  operation_type: str = "unknown", error_message: str = None) -> None:
        """
        Add a new entry to command history with security audit information
        
        Args:
            command: The executed command
            success: Whether the operation succeeded
            image_name: Target image name (for rebase operations)
            operation_type: Type of operation ('rebase', 'rollback', etc.)
            error_message: Error message if operation failed
        """
        # Get security audit information
        user_id = os.getuid() if hasattr(os, 'getuid') else None
        session_id = os.environ.get('XDG_SESSION_ID', os.environ.get('SESSIONID'))
        
        # Create new entry with audit information
        entry = HistoryEntry(
            command=command,
            timestamp=time.time(),
            success=success,
            image_name=image_name,
            operation_type=operation_type,
            user_id=user_id,
            session_id=session_id,
            error_message=error_message
        )
        
        # Log to system journal if available (for security audit)
        self._log_to_journal(entry)
        
        # Load existing history
        entries = self._load_history()
        
        # Add new entry at the beginning
        entries.insert(0, entry)
        
        # Prune if necessary
        if len(entries) > self.MAX_ENTRIES:
            entries = entries[:self.MAX_ENTRIES]
            
        # Save updated history
        self._save_history(entries)
    
    def get_recent_entries(self, limit: int = 50) -> List[HistoryEntry]:
        """
        Retrieve recent history entries
        
        Args:
            limit: Maximum number of entries to return (default: 50)
            
        Returns:
            List of recent HistoryEntry objects
        """
        entries = self._load_history()
        return entries[:limit]
    
    def prune_old_entries(self) -> int:
        """
        Remove entries beyond the maximum limit
        
        Returns:
            Number of entries removed
        """
        entries = self._load_history()
        original_count = len(entries)
        
        if original_count > self.MAX_ENTRIES:
            entries = entries[:self.MAX_ENTRIES]
            self._save_history(entries)
            return original_count - self.MAX_ENTRIES
            
        return 0
    
    def clear_history(self) -> None:
        """Clear all history entries"""
        self._save_history([])
        
    def get_entries_by_type(self, operation_type: str) -> List[HistoryEntry]:
        """
        Get history entries filtered by operation type
        
        Args:
            operation_type: Type of operation to filter by
            
        Returns:
            Filtered list of HistoryEntry objects
        """
        entries = self._load_history()
        return [entry for entry in entries if entry.operation_type == operation_type]
    
    def get_successful_entries(self) -> List[HistoryEntry]:
        """
        Get only successful history entries
        
        Returns:
            List of successful HistoryEntry objects
        """
        entries = self._load_history()
        return [entry for entry in entries if entry.success]
    
    def get_failed_entries(self) -> List[HistoryEntry]:
        """
        Get only failed history entries
        
        Returns:
            List of failed HistoryEntry objects
        """
        entries = self._load_history()
        return [entry for entry in entries if not entry.success]
    
    def export_history(self, output_file: str) -> bool:
        """
        Export history to a file
        
        Args:
            output_file: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entries = self._load_history()
            data = [entry.to_dict() for entry in entries]
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except IOError:
            return False
    
    def generate_security_report(self) -> dict:
        """
        Generate a security audit report from history
        
        Returns:
            Dictionary containing security audit information
        """
        entries = self._load_history()
        
        # Collect statistics
        total_commands = len(entries)
        successful_commands = sum(1 for e in entries if e.success)
        failed_commands = total_commands - successful_commands
        
        # Group by user
        user_stats = {}
        for entry in entries:
            user = str(entry.user_id) if entry.user_id else "unknown"
            if user not in user_stats:
                user_stats[user] = {"total": 0, "success": 0, "failed": 0}
            user_stats[user]["total"] += 1
            if entry.success:
                user_stats[user]["success"] += 1
            else:
                user_stats[user]["failed"] += 1
        
        # Group by operation type
        operation_stats = {}
        for entry in entries:
            op_type = entry.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = {"total": 0, "success": 0, "failed": 0}
            operation_stats[op_type]["total"] += 1
            if entry.success:
                operation_stats[op_type]["success"] += 1
            else:
                operation_stats[op_type]["failed"] += 1
        
        # Find recent failures
        recent_failures = [
            {
                "timestamp": entry.get_formatted_time(),
                "command": entry.command,
                "error": entry.error_message or "Unknown error",
                "user": str(entry.user_id) if entry.user_id else "unknown"
            }
            for entry in entries[:10]
            if not entry.success
        ]
        
        return {
            "report_generated": datetime.now().isoformat(),
            "summary": {
                "total_commands": total_commands,
                "successful": successful_commands,
                "failed": failed_commands,
                "success_rate": f"{(successful_commands/total_commands*100):.1f}%" if total_commands > 0 else "N/A"
            },
            "user_statistics": user_stats,
            "operation_statistics": operation_stats,
            "recent_failures": recent_failures,
            "history_file": self.history_file
        }