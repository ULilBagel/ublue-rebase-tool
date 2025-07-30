#!/usr/bin/env python3
"""
Atomic Rebase Tool - Standalone rebase utility for ostree-based systems
Extracted from Atomic Image Manager
"""

import gi
import sys
import os
import threading
import time
import subprocess
import json
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gio, GLib, WebKit, Pango

# Import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deployment_manager import DeploymentManager
from command_executor import CommandExecutor
from rpm_ostree_helper import get_status_json
from ui.simple_confirmation_dialog import ConfirmationDialog


class AtomicRebaseTool(Adw.Application):
    """Standalone rebase tool for atomic systems"""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.ublue.AtomicRebaseTool',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self.deployment_manager = DeploymentManager()
        self.command_executor = CommandExecutor()
        
    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            self.window = RebaseWindow(application=self)
        self.window.present()
        
    def do_startup(self):
        """Called when the application starts up"""
        Adw.Application.do_startup(self)
        

class RebaseWindow(Adw.ApplicationWindow):
    """Main window for the rebase tool"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Atomic Rebase Tool", **kwargs)
        
        self.deployment_manager = DeploymentManager()
        self.command_executor = CommandExecutor()
        
        self.set_default_size(900, 700)
        
        # Define available images
        self.available_images = [
            {
                "name": "Fedora Silverblue",
                "base_url": "ostree-image-signed:docker://quay.io/fedora/fedora-silverblue",
                "description": "Official Fedora atomic desktop with GNOME",
                "variants": [
                    {"name": "Latest", "suffix": ":latest", "desc": "Latest stable version"},
                    {"name": "41", "suffix": ":41", "desc": "Fedora 41"},
                    {"name": "40", "suffix": ":40", "desc": "Fedora 40"},
                    {"name": "Rawhide", "suffix": ":rawhide", "desc": "Development version"}
                ]
            },
            {
                "name": "Fedora Kinoite", 
                "base_url": "ostree-image-signed:docker://quay.io/fedora/fedora-kinoite",
                "description": "Official Fedora atomic desktop with KDE Plasma",
                "variants": [
                    {"name": "Latest", "suffix": ":latest", "desc": "Latest stable version"},
                    {"name": "41", "suffix": ":41", "desc": "Fedora 41"},
                    {"name": "40", "suffix": ":40", "desc": "Fedora 40"},
                    {"name": "Rawhide", "suffix": ":rawhide", "desc": "Development version"}
                ]
            },
            {
                "name": "Bazzite",
                "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/bazzite",
                "description": "Gaming-focused Universal Blue image",
                "variants": [
                    {"name": "Default", "suffix": "", "desc": "Base gaming image"},
                    {"name": "GNOME", "suffix": "-gnome", "desc": "GNOME desktop"},
                    {"name": "Deck", "suffix": "-deck", "desc": "Steam Deck-like experience"},
                    {"name": "Deck GNOME", "suffix": "-deck-gnome", "desc": "Steam Deck with GNOME"},
                    {"name": "DX", "suffix": "-dx", "desc": "Developer edition"},
                    {"name": "NVIDIA", "suffix": "-nvidia", "desc": "NVIDIA GPU support"},
                    {"name": "ASUS", "suffix": "-asus", "desc": "ASUS hardware optimized"}
                ]
            },
            {
                "name": "Bluefin",
                "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/bluefin",
                "description": "Developer-focused Universal Blue image",
                "variants": [
                    {"name": "Default", "suffix": "", "desc": "Base developer image"},
                    {"name": "DX", "suffix": "-dx", "desc": "Developer experience edition"},
                    {"name": "NVIDIA", "suffix": "-nvidia", "desc": "NVIDIA GPU support"},
                    {"name": "DX NVIDIA", "suffix": "-dx-nvidia", "desc": "DX with NVIDIA"}
                ]
            },
            {
                "name": "Aurora",
                "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/aurora",
                "description": "Developer-focused KDE image from Universal Blue",
                "variants": [
                    {"name": "Default", "suffix": "", "desc": "Base KDE developer image"},
                    {"name": "DX", "suffix": "-dx", "desc": "Developer experience edition"},
                    {"name": "NVIDIA", "suffix": "-nvidia", "desc": "NVIDIA GPU support"},
                    {"name": "DX NVIDIA", "suffix": "-dx-nvidia", "desc": "DX with NVIDIA"}
                ]
            }
        ]
        
        # Setup UI
        self.setup_ui()
        
        # Initial status refresh
        self.refresh_system_status()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Header bar
        header_bar = Adw.HeaderBar()
        
        # Refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh system status")
        refresh_button.connect("clicked", lambda w: self.refresh_system_status())
        header_bar.pack_end(refresh_button)
        
        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Add header bar to main box
        main_box.append(header_bar)
        
        # Create stack for different views
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Image selection view
        self.create_image_selection_view()
        
        # Progress view
        self.create_progress_view()
        
        main_box.append(self.stack)
        
        self.set_content(main_box)
        
    def create_image_selection_view(self):
        """Create the image selection view"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        # Current system info
        self.system_group = Adw.PreferencesGroup()
        self.system_group.set_title("Current System")
        
        self.system_row = Adw.ActionRow()
        self.system_group.add(self.system_row)
        
        content_box.append(self.system_group)
        
        # Available images
        images_group = Adw.PreferencesGroup()
        images_group.set_title("Available Images")
        images_group.set_description("Select an image to rebase your system")
        
        # Create rows for each image
        for image in self.available_images:
            row = self.create_image_row(image)
            images_group.add(row)
        
        content_box.append(images_group)
        
        # Custom URL section
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title("Custom Image")
        custom_group.set_description("Rebase to a custom OCI image URL")
        
        # Custom URL entry row
        self.custom_url_row = Adw.EntryRow()
        self.custom_url_row.set_title("Image URL")
        self.custom_url_row.set_text("")
        custom_group.add(self.custom_url_row)
        
        # Custom rebase button
        custom_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        custom_button_box.set_margin_top(6)
        custom_button_box.set_halign(Gtk.Align.END)
        
        custom_rebase_btn = Gtk.Button()
        custom_rebase_btn.set_label("Rebase to Custom Image")
        custom_rebase_btn.add_css_class("suggested-action")
        custom_rebase_btn.connect("clicked", self.on_custom_rebase_clicked)
        custom_button_box.append(custom_rebase_btn)
        
        custom_group.add(custom_button_box)
        content_box.append(custom_group)
        
        scrolled.set_child(content_box)
        self.stack.add_named(scrolled, "selection")
        
    def create_progress_view(self):
        """Create the progress view"""
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        progress_box.set_valign(Gtk.Align.CENTER)
        progress_box.set_halign(Gtk.Align.CENTER)
        progress_box.set_margin_top(24)
        progress_box.set_margin_bottom(24)
        progress_box.set_margin_start(24)
        progress_box.set_margin_end(24)
        
        # Progress spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        progress_box.append(self.spinner)
        
        # Progress label
        self.progress_label = Gtk.Label()
        self.progress_label.set_text("Preparing rebase operation...")
        self.progress_label.add_css_class("title-2")
        progress_box.append(self.progress_label)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(400, -1)
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("")
        self.progress_bar.set_fraction(0.0)
        progress_box.append(self.progress_bar)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_text("")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_margin_top(6)
        progress_box.append(self.status_label)
        
        # Toggle log button
        self.toggle_log_button = Gtk.Button()
        self.toggle_log_button.set_label("Show Details")
        self.toggle_log_button.set_margin_top(12)
        self.toggle_log_button.connect("clicked", self.on_toggle_log)
        progress_box.append(self.toggle_log_button)
        
        # Log view (initially hidden)
        self.log_frame = Gtk.Frame()
        self.log_frame.set_size_request(600, 300)
        self.log_frame.set_visible(False)
        self.log_frame.set_margin_top(12)
        
        scrolled_log = Gtk.ScrolledWindow()
        scrolled_log.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_margin_top(6)
        self.log_view.set_margin_bottom(6)
        self.log_view.set_margin_start(6)
        self.log_view.set_margin_end(6)
        
        self.log_buffer = self.log_view.get_buffer()
        
        scrolled_log.set_child(self.log_view)
        self.log_frame.set_child(scrolled_log)
        progress_box.append(self.log_frame)
        
        # Button box
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.button_box.set_halign(Gtk.Align.CENTER)
        self.button_box.set_margin_top(12)
        
        # Back button (initially hidden)
        self.back_button = Gtk.Button()
        self.back_button.set_label("Back to Image Selection")
        self.back_button.connect("clicked", lambda w: self.stack.set_visible_child_name("selection"))
        self.back_button.set_visible(False)
        self.button_box.append(self.back_button)
        
        # Cancel button
        self.cancel_button = Gtk.Button()
        self.cancel_button.set_label("Cancel")
        self.cancel_button.add_css_class("destructive-action")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.button_box.append(self.cancel_button)
        
        progress_box.append(self.button_box)
        
        self.stack.add_named(progress_box, "progress")
        
    def create_image_row(self, image):
        """Create a row for an image"""
        expander = Adw.ExpanderRow()
        expander.set_title(image["name"])
        expander.set_subtitle(image["description"])
        
        # Add variants
        for variant in image["variants"]:
            variant_row = Adw.ActionRow()
            variant_row.set_title(variant["name"])
            variant_row.set_subtitle(variant["desc"])
            
            # Rebase button
            rebase_btn = Gtk.Button()
            rebase_btn.set_label("Rebase")
            rebase_btn.set_valign(Gtk.Align.CENTER)
            rebase_btn.add_css_class("suggested-action")
            
            # Store image info in button
            rebase_btn.image_url = f"{image['base_url']}{variant['suffix']}:stable"
            rebase_btn.image_name = f"{image['name']} {variant['name']}"
            rebase_btn.connect("clicked", self.on_rebase_clicked)
            
            variant_row.add_suffix(rebase_btn)
            expander.add_row(variant_row)
        
        return expander
        
    def refresh_system_status(self):
        """Refresh the current system status"""
        deployment = self.deployment_manager.get_current_deployment()
        
        if deployment:
            image_name = self._extract_image_name(deployment.origin)
            self.system_row.set_title(image_name)
            self.system_row.set_subtitle(f"Version: {deployment.version} • Deployed: {deployment.timestamp}")
        else:
            self.system_row.set_title("Unknown System")
            self.system_row.set_subtitle("Unable to determine current deployment")
            
    def on_rebase_clicked(self, button):
        """Handle rebase button click"""
        image_url = button.image_url
        image_name = button.image_name
        
        dialog = ConfirmationDialog(
            self,
            "Rebase System?",
            f"This will rebase your system to:\n{image_name}\n\n"
            "This operation will download a new system image.\n"
            "You will need to reboot for changes to take effect.\n\n"
            "Current running applications and data will not be affected.",
            "Rebase"
        )
        
        if dialog.run():
            self.execute_rebase(image_url)
            
    def on_custom_rebase_clicked(self, button):
        """Handle custom rebase button click"""
        custom_url = self.custom_url_row.get_text().strip()
        
        if not custom_url:
            self.show_error("Please enter a valid image URL")
            return
            
        # Validate URL format
        is_valid, error_msg = self.command_executor._validate_image_url(custom_url)
        if not is_valid:
            self.show_error(f"Invalid image URL:\n{error_msg}")
            return
            
        dialog = ConfirmationDialog(
            self,
            "Rebase to Custom Image?",
            f"This will rebase your system to:\n{custom_url}\n\n"
            "⚠️ Warning: Custom images are not verified.\n"
            "Only use images from trusted sources.\n\n"
            "You will need to reboot for changes to take effect.",
            "Rebase"
        )
        
        if dialog.run():
            self.execute_rebase(custom_url)
            
    def execute_rebase(self, image_url):
        """Execute the rebase operation"""
        # Switch to progress view
        self.stack.set_visible_child_name("progress")
        self.spinner.start()
        
        # Reset button visibility
        self.cancel_button.set_sensitive(True)
        self.cancel_button.set_visible(True)
        self.back_button.set_visible(False)
        
        # Reset progress
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.status_label.set_text("")
        
        # Hide log by default
        self.log_frame.set_visible(False)
        self.toggle_log_button.set_label("Show Details")
        
        # Clear log
        self.log_buffer.set_text("")
        
        # Update progress label
        display_url = image_url.split("docker://")[-1] if "docker://" in image_url else image_url
        self.progress_label.set_text(f"Rebasing to {display_url}...")
        
        def append_log_line(line):
            """Append a line to the log view and update progress"""
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, line + "\n")
            
            # Auto-scroll to bottom
            self.log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
            
            # Parse progress information
            self._parse_progress_line(line)
        
        def run_rebase():
            """Run rebase in background thread"""
            result = self.command_executor.execute_rebase(image_url, append_log_line)
            GLib.idle_add(self.rebase_complete, result)
        
        # Start rebase in background thread
        thread = threading.Thread(target=run_rebase, daemon=True)
        thread.start()
        
    def on_cancel_clicked(self, button):
        """Handle cancel button click"""
        # Append cancellation message
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, "\n=== Cancelling operation ===\n")
        
        button.set_sensitive(False)
        
        # Cancel the current command execution
        self.command_executor.cancel_current_execution()
        
        # Also run rpm-ostree cancel to cancel the transaction
        try:
            subprocess.run(["flatpak-spawn", "--host", "rpm-ostree", "cancel"], 
                         capture_output=True, text=True)
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, "Operation cancelled by user\n")
        except Exception as e:
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, f"Error during cancel: {e}\n")
        
        # Update UI
        self.spinner.stop()
        self.progress_label.set_text("Rebase cancelled")
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.status_label.set_text("You can safely return to image selection.")
        self.cancel_button.set_visible(False)
        self.back_button.set_visible(True)
            
    def on_toggle_log(self, button):
        """Toggle log view visibility"""
        if self.log_frame.get_visible():
            self.log_frame.set_visible(False)
            button.set_label("Show Details")
        else:
            self.log_frame.set_visible(True)
            button.set_label("Hide Details")
    
    def _parse_progress_line(self, line):
        """Parse progress information from log line"""
        import re
        
        # Look for ostree chunk fetching (e.g., "[0/48] Fetching ostree chunk 180fde2153970ba7d4a (26.4 MB)...done")
        # Also matches "Fetching layer" for the final chunk
        chunk_match = re.search(r'\[(\d+)/(\d+)\]\s*Fetching (?:ostree chunk|layer)', line)
        if chunk_match:
            current = int(chunk_match.group(1))
            total = int(chunk_match.group(2))
            
            if total > 0:
                percent = int((current / total) * 100)
                self.progress_bar.set_fraction(current / total)
                self.progress_bar.set_text(f"{percent}% ({current}/{total})")
                
                # Update status based on progress
                if current == 0:
                    self.status_label.set_text("Starting download...")
                else:
                    self.status_label.set_text(f"Fetching chunks...")
            return
        
        # Look for other progress patterns (e.g., "Receiving objects: 95% (190/200)")
        percent_match = re.search(r'(\d+)%\s*\((\d+)/(\d+)\)', line)
        if percent_match:
            percent = int(percent_match.group(1))
            current = int(percent_match.group(2))
            total = int(percent_match.group(3))
            
            self.progress_bar.set_fraction(percent / 100.0)
            self.progress_bar.set_text(f"{percent}% ({current}/{total})")
            return
        
        # Look for specific stages
        if "Scanning metadata" in line:
            self.status_label.set_text("Scanning metadata...")
        elif "Pulling manifest" in line:
            self.status_label.set_text("Pulling manifest...")
        elif ("Fetching ostree chunk" in line or "Fetching layer" in line) and "done" in line:
            # Individual chunk/layer completed, don't change status
            pass
        elif "Importing" in line:
            self.status_label.set_text("Importing layers...")
        elif "Checking out tree" in line:
            self.status_label.set_text("Checking out files...")
        elif "Writing objects" in line:
            self.status_label.set_text("Writing objects...")
        elif "Staging deployment" in line:
            self.status_label.set_text("Staging deployment...")
        elif "Transaction complete" in line:
            self.status_label.set_text("Finalizing...")
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("100%")
        elif "Receiving objects" in line:
            self.status_label.set_text("Downloading objects...")
        elif "Receiving deltas" in line:
            self.status_label.set_text("Processing deltas...")
        elif "Resolving deltas" in line:
            self.status_label.set_text("Resolving deltas...")
    
    def rebase_complete(self, result):
        """Handle rebase completion"""
        self.spinner.stop()
        self.cancel_button.set_visible(False)
        self.back_button.set_visible(True)
        
        if result['success']:
            self.progress_label.set_text("Rebase completed successfully!")
            
            # Show success dialog
            dialog = Adw.MessageDialog.new(
                self,
                "Rebase Complete",
                "System rebase completed successfully!\n\n"
                "Please reboot your system to boot into the new image."
            )
            dialog.add_response("ok", "OK")
            dialog.set_default_response("ok")
            dialog.present()
            
            # Switch back to selection view
            dialog.connect("response", lambda d, r: self.stack.set_visible_child_name("selection"))
            
            # Refresh system status
            self.refresh_system_status()
        else:
            self.progress_label.set_text("Rebase failed")
            error_msg = result.get('error', 'Unknown error')
            
            # Determine if it was cancelled or failed
            if "cancelled" in error_msg.lower() or "cancel" in error_msg.lower():
                self.status_label.set_text("The operation was cancelled.")
                # Don't show an error dialog for cancellation - the UI already shows the status
            else:
                # For actual errors, show a simplified message
                self.status_label.set_text("The rebase could not be completed.")
                
                # Show simplified error dialog
                dialog = Adw.MessageDialog.new(
                    self,
                    "Rebase Failed",
                    "The rebase operation could not be completed.\n\n"
                    "This may be due to network issues or other system constraints."
                )
                dialog.add_response("ok", "OK")
                dialog.set_default_response("ok")
                dialog.add_css_class("error")
                dialog.present()
            
    def show_error(self, message):
        """Show error dialog"""
        dialog = Adw.MessageDialog.new(
            self,
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.add_css_class("error")
        dialog.present()
        
    def _extract_image_name(self, origin):
        """Extract a user-friendly name from the origin URL"""
        if "ghcr.io/ublue-os/" in origin:
            parts = origin.split("/")
            if len(parts) >= 3:
                image_tag = parts[-1]
                image_name = image_tag.split(":")[0]
                
                # Clean up common suffixes
                for suffix in ["-nvidia", "-dx", "-deck", "-gnome", "-asus"]:
                    if image_name.endswith(suffix):
                        variant = suffix[1:].upper()
                        base = image_name[:-len(suffix)]
                        return f"{base.title()} {variant}"
                
                return image_name.title()
        
        elif "quay.io/fedora" in origin:
            parts = origin.split("/")
            if len(parts) >= 2:
                image_tag = parts[-1]
                image_name = image_tag.split(":")[0]
                image_name = image_name.replace("fedora-", "").replace("-", " ").title()
                return f"Fedora {image_name}"
        
        return origin.split("/")[-1]


def main():
    """Main entry point"""
    app = AtomicRebaseTool()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())