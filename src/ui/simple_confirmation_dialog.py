#!/usr/bin/env python3
"""
Simple confirmation dialog for the rebase tool
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class ConfirmationDialog:
    """Simple confirmation dialog using Adw.MessageDialog"""
    
    def __init__(self, parent, title, message, action_text="Confirm"):
        self.dialog = Adw.MessageDialog.new(parent, title, message)
        self.dialog.add_response("cancel", "Cancel")
        self.dialog.add_response("confirm", action_text)
        self.dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        self.dialog.set_default_response("cancel")
        self.result = False
        
    def run(self):
        """Show dialog and return True if confirmed, False if cancelled"""
        self.dialog.connect("response", self._on_response)
        self.dialog.present()
        # For GTK4, we need to use a different approach
        # This is a simplified synchronous version
        import time
        from gi.repository import GLib
        context = GLib.MainContext.default()
        while self.dialog.get_visible():
            context.iteration(False)
            time.sleep(0.01)
        return self.result
        
    def _on_response(self, dialog, response):
        self.result = (response == "confirm")
        dialog.destroy()