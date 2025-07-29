#!/usr/bin/env python3
"""
ConfirmationDialog using libadwaita
Display operation details and safety warnings before execution
Following Universal Blue patterns for user confirmation
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from typing import Callable, Optional, Dict, Any


class ConfirmationDialog:
    """Confirmation dialog for rebase and rollback operations using Adw.MessageDialog"""
    
    def __init__(self, parent_window):
        """
        Initialize confirmation dialog
        
        Args:
            parent_window: Parent GTK window for the dialog
        """
        self.parent_window = parent_window
        self.response_callback: Optional[Callable[[bool], None]] = None
        
    def show_rebase_confirmation(self, image_name: str, command: str, 
                                 callback: Callable[[bool], None]) -> None:
        """
        Show rebase confirmation dialog with command and warnings
        
        Args:
            image_name: Name of the image to rebase to
            command: The exact command that will be executed
            callback: Function to call with user's decision (True/False)
        """
        self.response_callback = callback
        
        # Create dialog using Adw.MessageDialog for modern libadwaita styling
        dialog = Adw.MessageDialog.new(
            self.parent_window,
            f"Rebase to {image_name}?",
            f"This will execute the following command:\n\n"
            f"<tt>{GLib.markup_escape_text(command)}</tt>"
        )
        
        # Set detailed body with safety warnings
        dialog.set_body(
            "⚠️  <b>Important Safety Information:</b>\n\n"
            "• This operation will change your system image\n"
            "• A system restart will be required\n"
            "• Ensure you have saved all work before proceeding\n"
            "• Your data and home directory will be preserved\n"
            "• You can rollback to the current deployment if needed\n\n"
            "The operation requires administrator privileges."
        )
        
        # Enable markup for formatted text
        dialog.set_body_use_markup(True)
        
        # Add response buttons following libadwaita patterns
        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("execute", "_Execute")
        
        # Style the execute button as suggested (blue)
        dialog.set_response_appearance("execute", Adw.ResponseAppearance.SUGGESTED)
        
        # Set default response to cancel for safety
        dialog.set_default_response("cancel")
        
        # Connect response handler
        dialog.connect("response", self._on_rebase_response)
        
        # Show the dialog
        dialog.present()
    
    def show_rollback_confirmation(self, deployment_info: Dict[str, Any], 
                                   command: str, callback: Callable[[bool], None]) -> None:
        """
        Show rollback confirmation dialog with deployment info
        
        Args:
            deployment_info: Dictionary with deployment details
            command: The exact command that will be executed
            callback: Function to call with user's decision (True/False)
        """
        self.response_callback = callback
        
        # Format deployment title
        title = f"Rollback to {deployment_info.get('image_name', 'Previous Deployment')}?"
        
        # Create dialog
        dialog = Adw.MessageDialog.new(
            self.parent_window,
            title,
            f"This will execute the following command:\n\n"
            f"<tt>{GLib.markup_escape_text(command)}</tt>"
        )
        
        # Build deployment details
        details = []
        if deployment_info.get('version'):
            details.append(f"• Version: {deployment_info['version']}")
        if deployment_info.get('timestamp'):
            details.append(f"• Deployed: {deployment_info['timestamp']}")
        if deployment_info.get('id'):
            details.append(f"• ID: {deployment_info['id']}")
        
        status_badges = deployment_info.get('status', [])
        if status_badges:
            details.append(f"• Status: {', '.join(status_badges)}")
        
        deployment_details = '\n'.join(details) if details else "No additional details available"
        
        # Set body with deployment info and warnings
        dialog.set_body(
            f"<b>Deployment Details:</b>\n{deployment_details}\n\n"
            f"⚠️  <b>Important:</b>\n\n"
            f"• This will revert to a previous system state\n"
            f"• A system restart will be required\n"
            f"• Your personal data will not be affected\n"
            f"• Current deployment will remain available\n\n"
            f"The operation requires administrator privileges."
        )
        
        dialog.set_body_use_markup(True)
        
        # Add response buttons
        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("rollback", "_Rollback")
        
        # Style rollback button as destructive (red) since it changes system state
        dialog.set_response_appearance("rollback", Adw.ResponseAppearance.DESTRUCTIVE)
        
        # Default to cancel for safety
        dialog.set_default_response("cancel")
        
        # Connect response handler
        dialog.connect("response", self._on_rollback_response)
        
        # Show the dialog
        dialog.present()
    
    def get_user_response(self) -> Optional[bool]:
        """
        Get the last user response (for compatibility/testing)
        
        Returns:
            True if user confirmed, False if cancelled, None if no response yet
        """
        # This is primarily for testing - actual responses go through callbacks
        return None
    
    def _on_rebase_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        """
        Handle rebase dialog response
        
        Args:
            dialog: The message dialog
            response: Response ID ("cancel" or "execute")
        """
        confirmed = response == "execute"
        
        # Call the callback with user's decision
        if self.response_callback:
            self.response_callback(confirmed)
            self.response_callback = None
        
        # Dialog is automatically destroyed
    
    def _on_rollback_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        """
        Handle rollback dialog response
        
        Args:
            dialog: The message dialog
            response: Response ID ("cancel" or "rollback")
        """
        confirmed = response == "rollback"
        
        # Call the callback with user's decision
        if self.response_callback:
            self.response_callback(confirmed)
            self.response_callback = None
        
        # Dialog is automatically destroyed
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """
        Show an error dialog (utility method)
        
        Args:
            title: Error title
            message: Error message
        """
        dialog = Adw.MessageDialog.new(
            self.parent_window,
            title,
            message
        )
        
        dialog.add_response("ok", "_OK")
        dialog.set_default_response("ok")
        
        dialog.present()
    
    def show_info_dialog(self, title: str, message: str) -> None:
        """
        Show an information dialog (utility method)
        
        Args:
            title: Info title
            message: Info message
        """
        dialog = Adw.MessageDialog.new(
            self.parent_window,
            title,
            message
        )
        
        dialog.add_response("ok", "_OK")
        dialog.set_default_response("ok")
        
        dialog.present()