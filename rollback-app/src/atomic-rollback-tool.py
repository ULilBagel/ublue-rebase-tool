#!/usr/bin/env python3
"""
Atomic Rollback Tool - Standalone rollback utility for ostree-based systems
Extracted from Atomic Image Manager
"""

import gi
import sys
import os
import threading
import time
import subprocess
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gio, GLib, WebKit, Pango

# Import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deployment_manager import DeploymentManager
from registry_manager import RegistryManager
from command_executor import CommandExecutor
from rpm_ostree_helper import get_status_json
from ui.confirmation_dialog import ConfirmationDialog


class AtomicRollbackTool(Adw.Application):
    """Standalone rollback tool for atomic systems"""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.ublue.RollbackTool',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self.deployment_manager = DeploymentManager()
        self.registry_manager = RegistryManager()
        self.command_executor = CommandExecutor()
        
    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            self.window = RollbackWindow(application=self)
        self.window.present()
        
    def do_startup(self):
        """Called when the application starts up"""
        Adw.Application.do_startup(self)
        

class RollbackWindow(Adw.ApplicationWindow):
    """Main window for the rollback tool"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Atomic Rollback Tool", **kwargs)
        
        self.deployment_manager = DeploymentManager()
        self.registry_manager = RegistryManager()
        self.command_executor = CommandExecutor()
        
        self.set_default_size(900, 700)
        
        # Setup UI
        self.setup_ui()
        
        # Initial status refresh
        self.refresh_deployments()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Header bar
        header_bar = Adw.HeaderBar()
        
        # Refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh deployments")
        refresh_button.connect("clicked", lambda w: self.refresh_deployments())
        header_bar.pack_end(refresh_button)
        
        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Add header bar to main box
        main_box.append(header_bar)
        
        # Create scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        
        # Create sections
        self.create_deployment_sections()
        
        scrolled.set_child(self.content_box)
        main_box.append(scrolled)
        
        self.set_content(main_box)
        
    def create_deployment_sections(self):
        """Create the deployment sections UI"""
        # Current & System Deployments section
        current_group = Adw.PreferencesGroup()
        current_group.set_title("System Deployments")
        current_group.set_description("Current and available system deployments")
        
        self.current_deployments_list = Gtk.ListBox()
        self.current_deployments_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.current_deployments_list.add_css_class("boxed-list")
        current_group.add(self.current_deployments_list)
        
        self.content_box.append(current_group)
        
        # Pinned deployments section
        self.pinned_group = Adw.PreferencesGroup()
        self.pinned_group.set_title("Pinned Deployments")
        self.pinned_group.set_description("Deployments protected from automatic cleanup")
        
        self.pinned_deployments_list = Gtk.ListBox()
        self.pinned_deployments_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pinned_deployments_list.add_css_class("boxed-list")
        self.pinned_group.add(self.pinned_deployments_list)
        
        self.content_box.append(self.pinned_group)
        
        # Historical deployments section
        historical_group = Adw.PreferencesGroup()
        historical_group.set_title("Historical Deployments")
        historical_group.set_description("Available deployments from the last 90 days")
        
        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search deployments...")
        self.search_entry.set_margin_bottom(6)
        self.search_entry.connect("search-changed", self.on_search_changed)
        historical_group.add(self.search_entry)
        
        self.historical_deployments_list = Gtk.ListBox()
        self.historical_deployments_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.historical_deployments_list.add_css_class("boxed-list")
        historical_group.add(self.historical_deployments_list)
        
        self.content_box.append(historical_group)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_margin_top(12)
        self.status_label.add_css_class("dim-label")
        self.content_box.append(self.status_label)
        
    def refresh_deployments(self):
        """Refresh all deployment lists"""
        # Clear existing items
        self.clear_list(self.current_deployments_list)
        self.clear_list(self.pinned_deployments_list)
        self.clear_list(self.historical_deployments_list)
        
        # Get current deployments
        deployments = self.deployment_manager.get_all_deployments()
        
        if not deployments:
            self.status_label.set_text("No deployments found")
            return
            
        # Separate pinned and regular deployments
        pinned_deployments = []
        has_pinned = False
        
        for deployment in deployments:
            if deployment.is_pinned and not deployment.is_booted:
                pinned_deployments.append(deployment)
                has_pinned = True
            
            # Add to current deployments
            row = self.create_deployment_row(deployment)
            self.current_deployments_list.append(row)
        
        # Add pinned deployments
        if has_pinned:
            self.pinned_group.set_visible(True)
            for deployment in pinned_deployments:
                row = self.create_deployment_row(deployment, show_unpin=True)
                self.pinned_deployments_list.append(row)
        else:
            self.pinned_group.set_visible(False)
        
        # Load historical deployments in background
        self.load_historical_deployments(deployments[0] if deployments else None)
        
        # Update status
        self.status_label.set_text(f"Found {len(deployments)} system deployment(s)")
        
    def create_deployment_row(self, deployment, show_unpin=False):
        """Create a row for a deployment"""
        row = Adw.ActionRow()
        
        # Title with image name
        title = self._extract_image_name(deployment.origin)
        if deployment.is_booted:
            title = f"🟢 {title} (Current)"
        elif deployment.is_pinned:
            title = f"📌 {title}"
        row.set_title(title)
        
        # Subtitle with version and date
        subtitle = f"Version: {deployment.version} • Deployed: {deployment.timestamp}"
        row.set_subtitle(subtitle)
        
        # Action buttons
        if not deployment.is_booted:
            if deployment.index == 0:
                # This is a pending deployment
                row.set_subtitle(subtitle + " • ⏳ Pending (reboot required)")
            else:
                # Rollback button
                rollback_btn = Gtk.Button()
                rollback_btn.set_label("Rollback")
                rollback_btn.add_css_class("suggested-action")
                rollback_btn.set_valign(Gtk.Align.CENTER)
                rollback_btn.connect("clicked", lambda w: self.on_rollback_clicked(deployment))
                row.add_suffix(rollback_btn)
        else:
            # Pin button for current deployment
            pin_btn = Gtk.Button()
            pin_btn.set_icon_name("view-pin-symbolic")
            pin_btn.set_tooltip_text("Pin deployment")
            pin_btn.set_valign(Gtk.Align.CENTER)
            pin_btn.connect("clicked", lambda w: self.on_pin_deployment(deployment))
            row.add_suffix(pin_btn)
        
        # Unpin button for pinned deployments
        if show_unpin and deployment.is_pinned:
            unpin_btn = Gtk.Button()
            unpin_btn.set_icon_name("edit-delete-symbolic")
            unpin_btn.set_tooltip_text("Unpin deployment")
            unpin_btn.set_valign(Gtk.Align.CENTER)
            unpin_btn.connect("clicked", lambda w: self.on_unpin_deployment(deployment))
            row.add_suffix(unpin_btn)
        
        return row
        
    def load_historical_deployments(self, current_deployment):
        """Load historical deployments from registry"""
        if not current_deployment:
            return
            
        # Check if skopeo is available
        if not self.registry_manager.check_skopeo_available():
            self.status_label.set_text("Skopeo not available - cannot query historical deployments")
            return
            
        # Extract registry info from current deployment
        registry, image_name, current_tag = self.registry_manager.get_image_info_from_deployment(current_deployment)
        
        if not registry or not image_name:
            return
            
        # Query registry in background thread
        def query_registry():
            # Determine branch from current tag
            branch = "stable"
            if "testing" in current_tag:
                branch = "testing"
            elif "rawhide" in current_tag:
                branch = "rawhide"
            
            # Get recent images
            images = self.registry_manager.get_recent_images(registry, image_name, days=90, branch=branch)
            
            # Update UI in main thread
            GLib.idle_add(self.update_historical_deployments, images)
        
        thread = threading.Thread(target=query_registry, daemon=True)
        thread.start()
        
    def update_historical_deployments(self, images):
        """Update historical deployments list"""
        self.clear_list(self.historical_deployments_list)
        
        if not images:
            return
            
        # Store for search
        self.all_historical_images = images
        
        # Add each image
        for image in images:
            if image.age_days is not None:
                row = self.create_historical_deployment_row(image)
                self.historical_deployments_list.append(row)
                
    def create_historical_deployment_row(self, image):
        """Create a row for a historical deployment"""
        row = Adw.ActionRow()
        
        # Title
        title = f"{image.name}:{image.tag}"
        row.set_title(title)
        
        # Subtitle with age
        if image.age_days is not None:
            subtitle = f"{image.age_days} days ago"
            if image.date:
                subtitle += f" • {image.date.strftime('%Y-%m-%d')}"
        else:
            subtitle = "Date unknown"
        row.set_subtitle(subtitle)
        
        # Restore button
        restore_btn = Gtk.Button()
        restore_btn.set_label("Restore")
        restore_btn.set_valign(Gtk.Align.CENTER)
        restore_btn.connect("clicked", lambda w: self.on_restore_historical(image))
        row.add_suffix(restore_btn)
        
        # Store image reference
        row.image_ref = image
        
        return row
        
    def on_search_changed(self, entry):
        """Handle search text changes"""
        search_text = entry.get_text().lower()
        
        if not hasattr(self, 'all_historical_images'):
            return
            
        # Clear and re-add filtered items
        self.clear_list(self.historical_deployments_list)
        
        for image in self.all_historical_images:
            if search_text in image.tag.lower() or search_text in str(image.age_days):
                row = self.create_historical_deployment_row(image)
                self.historical_deployments_list.append(row)
                
    def clear_list(self, listbox):
        """Clear all items from a listbox"""
        while True:
            child = listbox.get_first_child()
            if child:
                listbox.remove(child)
            else:
                break
                
    def on_rollback_clicked(self, deployment):
        """Handle rollback button click"""
        dialog = ConfirmationDialog(
            self,
            "Rollback to Previous Deployment?",
            f"This will rollback your system to:\n{self._extract_image_name(deployment.origin)}\n\n"
            f"Version: {deployment.version}\n"
            f"Deployed: {deployment.timestamp}\n\n"
            "You will need to reboot for changes to take effect.",
            "Rollback"
        )
        
        if dialog.run():
            self.execute_rollback(deployment)
            
    def on_restore_historical(self, image):
        """Handle restore from historical deployment"""
        dialog = ConfirmationDialog(
            self,
            "Restore Historical Deployment?",
            f"This will restore your system to:\n{image.full_ref}\n\n"
            f"This deployment is {image.age_days} days old.\n\n"
            "You will need to reboot for changes to take effect.",
            "Restore"
        )
        
        if dialog.run():
            self.execute_rebase(image.full_ref)
            
    def on_pin_deployment(self, deployment):
        """Handle pinning a deployment"""
        dialog = ConfirmationDialog(
            self,
            "Pin Deployment?",
            f"This will pin the deployment:\n{self._extract_image_name(deployment.origin)}\n\n"
            "Pinned deployments are protected from automatic cleanup.",
            "Pin"
        )
        
        if dialog.run():
            self.execute_pin(deployment)
            
    def on_unpin_deployment(self, deployment):
        """Handle unpinning a deployment"""
        dialog = ConfirmationDialog(
            self,
            "Unpin Deployment?", 
            f"This will unpin the deployment:\n{self._extract_image_name(deployment.origin)}\n\n"
            "The deployment will no longer be protected from cleanup.",
            "Unpin"
        )
        
        if dialog.run():
            self.execute_unpin(deployment)
            
    def execute_rollback(self, deployment):
        """Execute the rollback command"""
        # Create progress dialog
        progress_dialog = Adw.MessageDialog()
        progress_dialog.set_transient_for(self)
        progress_dialog.set_title("Rolling Back...")
        progress_dialog.set_body("Executing rollback operation...")
        progress_dialog.set_modal(True)
        
        # Add spinner
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.set_size_request(32, 32)
        progress_dialog.set_extra_child(spinner)
        
        progress_dialog.present()
        
        def run_rollback():
            if deployment.index == 1:
                result = self.command_executor.execute_rollback(1)
            else:
                # For other deployments, use rebase
                result = self.command_executor.execute_rebase(deployment.origin)
            
            GLib.idle_add(self.rollback_complete, result, progress_dialog)
        
        thread = threading.Thread(target=run_rollback, daemon=True)
        thread.start()
        
    def execute_rebase(self, image_url):
        """Execute rebase to a specific image"""
        # Create progress dialog
        progress_dialog = Adw.MessageDialog()
        progress_dialog.set_transient_for(self)
        progress_dialog.set_title("Restoring Deployment...")
        progress_dialog.set_body(f"Rebasing to {image_url}...")
        progress_dialog.set_modal(True)
        
        # Add spinner
        spinner = Gtk.Spinner()
        spinner.start()
        spinner.set_size_request(32, 32)
        progress_dialog.set_extra_child(spinner)
        
        progress_dialog.present()
        
        def run_rebase():
            result = self.command_executor.execute_rebase(image_url)
            GLib.idle_add(self.rollback_complete, result, progress_dialog)
        
        thread = threading.Thread(target=run_rebase, daemon=True)
        thread.start()
        
    def execute_pin(self, deployment):
        """Execute pin command"""
        try:
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "pkexec", "ostree", "admin", "pin", str(deployment.index)]
            else:
                cmd = ["pkexec", "ostree", "admin", "pin", str(deployment.index)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.show_success("Deployment pinned successfully")
                self.refresh_deployments()
            else:
                self.show_error(f"Failed to pin deployment: {result.stderr}")
        except Exception as e:
            self.show_error(f"Error pinning deployment: {e}")
            
    def execute_unpin(self, deployment):
        """Execute unpin command"""
        try:
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "pkexec", "ostree", "admin", "pin", "--unpin", str(deployment.index)]
            else:
                cmd = ["pkexec", "ostree", "admin", "pin", "--unpin", str(deployment.index)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.show_success("Deployment unpinned successfully")
                self.refresh_deployments()
            else:
                self.show_error(f"Failed to unpin deployment: {result.stderr}")
        except Exception as e:
            self.show_error(f"Error unpinning deployment: {e}")
            
    def rollback_complete(self, result, progress_dialog):
        """Handle rollback completion"""
        progress_dialog.close()
        
        if result['success']:
            self.show_success("Operation completed successfully!\nPlease reboot to apply changes.")
            self.refresh_deployments()
        else:
            self.show_error(f"Operation failed:\n{result.get('error', 'Unknown error')}")
            
    def show_success(self, message):
        """Show success dialog"""
        dialog = Adw.MessageDialog()
        dialog.set_transient_for(self)
        dialog.set_title("Success")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()
        
    def show_error(self, message):
        """Show error dialog"""
        dialog = Adw.MessageDialog()
        dialog.set_transient_for(self)
        dialog.set_title("Error")
        dialog.set_body(message)
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
    app = AtomicRollbackTool()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())