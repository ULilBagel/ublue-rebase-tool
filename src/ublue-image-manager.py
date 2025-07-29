#!/usr/bin/env python3
"""
Universal Blue Image Management GUI
A GTK4/libadwaita application for managing Universal Blue rpm-ostree deployments
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, GLib, Gio
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Import components
from command_executor import CommandExecutor
from deployment_manager import DeploymentManager
from history_manager import HistoryManager
from ui.simple_confirmation_dialog import ConfirmationDialog


class AtomicImageManager(Adw.Application):
    """Main application class for Atomic Image Manager"""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.ublue.RebaseTool',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        
    def do_activate(self):
        """Activate the application"""
        if not self.window:
            self.window = AtomicImageWindow(self)
        self.window.present()


class AtomicImageWindow(Adw.ApplicationWindow):
    """Main application window for Atomic Image Manager"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Atomic Image Manager")
        self.set_default_size(900, 600)
        # Connect to delete-event to prevent accidental closing
        self.connect('close-request', self._on_close_request)
        
        # Initialize components
        self.command_executor = CommandExecutor()
        self.deployment_manager = DeploymentManager()
        self.history_manager = HistoryManager()
        
        # Check if running on atomic/ostree system
        if not self.check_atomic_system():
            self.show_unsupported_system_dialog()
            return
            
        # Build UI
        self.build_ui()
        
        # Load initial data
        self.refresh_system_status()
        
    def check_atomic_system(self):
        """Check if running on an atomic/ostree system"""
        try:
            # Check for rpm-ostree via D-Bus (works in flatpak)
            try:
                bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
                proxy = Gio.DBusProxy.new_sync(
                    bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    "org.projectatomic.rpmostree1",
                    "/org/projectatomic/rpmostree1/Sysroot",
                    "org.projectatomic.rpmostree1.Sysroot",
                    None
                )
                # If we can connect to rpm-ostree D-Bus, it's available
            except:
                return False
                
            # Check for atomic systems in os-release
            # In flatpak, we need to check the host's os-release
            os_release_paths = ['/run/host/etc/os-release', '/etc/os-release']
            for os_release_path in os_release_paths:
                if os.path.exists(os_release_path):
                    with open(os_release_path, 'r') as f:
                        content = f.read().lower()
                        # Check for known atomic system identifiers
                        atomic_identifiers = [
                            'bazzite', 'bluefin', 'aurora', 'ucore',
                            'universal-blue', 'ublue', 'ublue-os',
                            'silverblue', 'kinoite', 'fedora-silverblue',
                            'fedora-kinoite', 'ostree', 'atomic'
                        ]
                        if any(identifier in content for identifier in atomic_identifiers):
                            return True
                        
            # Check current deployment for atomic systems
            status = subprocess.run(['rpm-ostree', 'status', '--json'],
                                  capture_output=True, text=True)
            if status.returncode == 0:
                data = json.loads(status.stdout)
                deployments = data.get('deployments', [])
                if deployments:
                    # Check origin, base-commit-meta, and other fields
                    deployment = deployments[0]
                    origin = deployment.get('origin', '')
                    
                    # Check for known atomic systems in origin
                    atomic_origins = [
                        'ublue', 'ghcr.io/ublue-os', 'silverblue', 
                        'kinoite', 'quay.io/fedora', 'fedora-silverblue',
                        'fedora-kinoite'
                    ]
                    if any(sys in origin.lower() for sys in atomic_origins):
                        return True
                        
                    # Check base-commit-meta for atomic systems
                    base_meta = deployment.get('base-commit-meta', {})
                    if base_meta:
                        for key, value in base_meta.items():
                            if isinstance(value, str):
                                for sys in atomic_origins:
                                    if sys in value.lower():
                                        return True
                        
        except Exception as e:
            print(f"Error checking system: {e}")
            
        return False
        
    def show_unsupported_system_dialog(self):
        """Show dialog for unsupported systems"""
        dialog = Adw.MessageDialog.new(
            self,
            "Unsupported System",
            "This tool is designed for atomic/ostree-based systems only.\n\n"
            "Supported systems include Fedora Silverblue, Kinoite, and Universal Blue variants."
        )
        dialog.add_response("close", "Close")
        dialog.set_response_appearance("close", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda d, r: (d.destroy(), self.close()))
        dialog.present()
        
    def build_ui(self):
        """Build the main UI"""
        # Create header bar with window controls
        header_bar = Adw.HeaderBar()
        self.set_title("Atomic Image Manager")
        
        # Add refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh system status")
        refresh_button.connect("clicked", lambda b: self.refresh_system_status())
        header_bar.pack_start(refresh_button)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header_bar)
        
        # Create toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)
        
        # Create view stack for sections
        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        
        # Add Rebase section
        rebase_page = self.create_rebase_section()
        self.view_stack.add_titled_with_icon(
            rebase_page, "rebase", "Rebase", "system-software-install-symbolic"
        )
        
        # Add Rollback section  
        rollback_page = self.create_rollback_section()
        self.view_stack.add_titled_with_icon(
            rollback_page, "rollback", "Rollback", "edit-undo-symbolic"
        )
        
        # Create view switcher
        view_switcher = Adw.ViewSwitcherTitle()
        view_switcher.set_property("stack", self.view_stack)
        header_bar.set_title_widget(view_switcher)
        
        # Add stack to toast overlay
        self.toast_overlay.set_child(self.view_stack)
        
        # Set window content
        self.set_content(main_box)
        
    def _on_close_request(self, widget):
        """Handle window close request"""
        # Only close if user explicitly wants to
        dialog = Adw.MessageDialog.new(
            self,
            "Close Application?",
            "Are you sure you want to close the Atomic Image Manager?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("close", "Close")
        dialog.set_response_appearance("close", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        def on_response(d, response):
            if response == "close":
                self.get_application().quit()
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()
        return True  # Prevent default close
        
    def create_rebase_section(self):
        """Create the rebase section UI"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Current deployment info
        self.current_deployment_group = Adw.PreferencesGroup()
        self.current_deployment_group.set_title("Current Deployment")
        box.append(self.current_deployment_group)
        
        # Available images list
        images_group = Adw.PreferencesGroup()
        images_group.set_title("Available Atomic Images")
        images_group.set_description("Select an image to rebase your system")
        
        # Add atomic images
        self.images_list = Gtk.ListBox()
        self.images_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.images_list.add_css_class("boxed-list")
        
        self.populate_images_list()
        
        images_group.add(self.images_list)
        box.append(images_group)
        
        # Wrap in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(box)
        
        return scrolled
        
    def create_rollback_section(self):
        """Create the rollback section UI"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Deployments list
        deployments_group = Adw.PreferencesGroup()
        deployments_group.set_title("System Deployments")
        deployments_group.set_description("All available system deployments")
        
        self.deployments_list = Gtk.ListBox()
        self.deployments_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.deployments_list.add_css_class("boxed-list")
        
        deployments_group.add(self.deployments_list)
        box.append(deployments_group)
        
        # History section
        history_group = Adw.PreferencesGroup()
        history_group.set_title("Deployment History")
        history_group.set_description("Recent system changes")
        
        self.history_list = Gtk.ListBox()
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.history_list.add_css_class("boxed-list")
        
        history_group.add(self.history_list)
        box.append(history_group)
        
        # Wrap in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(box)
        
        return scrolled
        
    def populate_images_list(self):
        """Populate the list of available atomic images"""
        images = [
            {
                "name": "Fedora Silverblue",
                "base_url": "ostree-unverified-registry:quay.io/fedora/fedora-silverblue",
                "description": "Immutable desktop OS with GNOME",
                "variants": [
                    {"name": "Latest", "suffix": ":latest", "desc": "Latest stable release"},
                    {"name": "40", "suffix": ":40", "desc": "Fedora 40"},
                    {"name": "41", "suffix": ":41", "desc": "Fedora 41"},
                    {"name": "Rawhide", "suffix": ":rawhide", "desc": "Development version"}
                ]
            },
            {
                "name": "Fedora Kinoite",
                "base_url": "ostree-unverified-registry:quay.io/fedora/fedora-kinoite",
                "description": "Immutable desktop OS with KDE Plasma",
                "variants": [
                    {"name": "Latest", "suffix": ":latest", "desc": "Latest stable release"},
                    {"name": "40", "suffix": ":40", "desc": "Fedora 40"},
                    {"name": "41", "suffix": ":41", "desc": "Fedora 41"},
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
                    {"name": "DX", "suffix": "-dx", "desc": "Developer edition"},
                    {"name": "NVIDIA", "suffix": "-nvidia", "desc": "NVIDIA GPU support"},
                    {"name": "AMD", "suffix": "-asus", "desc": "ASUS/AMD optimized"}
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
                "description": "KDE-based Universal Blue image",
                "variants": [
                    {"name": "Default", "suffix": "", "desc": "Base KDE image"},
                    {"name": "DX", "suffix": "-dx", "desc": "Developer experience edition"},
                    {"name": "NVIDIA", "suffix": "-nvidia", "desc": "NVIDIA GPU support"},
                    {"name": "DX NVIDIA", "suffix": "-dx-nvidia", "desc": "DX with NVIDIA"}
                ]
            }
        ]
        
        for image in images:
            row = Adw.ActionRow()
            row.set_title(image["name"])
            row.set_subtitle(image["description"])
            
            # Create container for suffix widgets
            suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            suffix_box.set_valign(Gtk.Align.CENTER)
            
            # Variant dropdown
            variant_dropdown = Gtk.DropDown()
            variant_model = Gtk.StringList()
            
            # Populate dropdown with variants
            for variant in image["variants"]:
                variant_model.append(variant["name"])
            
            variant_dropdown.set_model(variant_model)
            variant_dropdown.set_selected(0)  # Default to first option
            
            # Store variant data for later use
            variant_dropdown.variants_data = image["variants"]
            variant_dropdown.base_url = image["base_url"]
            
            suffix_box.append(variant_dropdown)
            
            # Add rebase button
            rebase_button = Gtk.Button()
            rebase_button.set_label("Rebase")
            rebase_button.add_css_class("suggested-action")
            
            # Connect with variant dropdown reference
            rebase_button.connect("clicked", 
                                lambda b, name=image["name"], dropdown=variant_dropdown: 
                                self.on_rebase_variant_clicked(name, dropdown))
            
            suffix_box.append(rebase_button)
            
            # Add suffix box to row
            row.add_suffix(suffix_box)
            self.images_list.append(row)
            
    def refresh_system_status(self):
        """Refresh system status and deployments"""
        def do_refresh():
            try:
                # Get current deployment
                deployments = self.deployment_manager.get_all_deployments()
                
                # Update UI in main thread with proper error handling
                def safe_update():
                    try:
                        if self.get_visible():
                            self.update_current_deployment(deployments)
                            self.update_deployments_list(deployments)
                            self.update_history_list()
                    except Exception as e:
                        print(f"Error updating UI during refresh: {e}")
                        import traceback
                        traceback.print_exc()
                
                GLib.idle_add(safe_update)
                
            except Exception as e:
                print(f"Error in refresh thread: {e}")
                GLib.idle_add(self.show_error, f"Failed to refresh: {str(e)}")
                
        thread = threading.Thread(target=do_refresh, daemon=True)
        thread.start()
        
    def update_current_deployment(self, deployments):
        """Update current deployment display"""
        # For AdwPreferencesGroup, we need to work with its content differently
        # Create a new list box for deployments
        if not hasattr(self, 'current_deployment_list'):
            self.current_deployment_list = Gtk.ListBox()
            self.current_deployment_list.set_selection_mode(Gtk.SelectionMode.NONE)
            self.current_deployment_list.add_css_class("boxed-list")
            self.current_deployment_group.add(self.current_deployment_list)
            
        # Clear existing rows in the list box
        child = self.current_deployment_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.current_deployment_list.remove(child)
            child = next_child
            
        if deployments and len(deployments) > 0:
            current = deployments[0]
            
            row = Adw.ActionRow()
            row.set_title(current.origin)
            row.set_subtitle(f"Version: {current.version} • Deployed: {current.timestamp}")
            
            if current.is_booted:
                status_label = Gtk.Label(label="● Active")
                status_label.add_css_class("success")
                row.add_suffix(status_label)
                
            self.current_deployment_list.append(row)
            
    def update_deployments_list(self, deployments):
        """Update deployments list for rollback"""
        # Clear existing
        child = self.deployments_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.deployments_list.remove(child)
            child = next_child
            
        # Show all deployments (Universal Blue keeps 90-day history)
        for i, deployment in enumerate(deployments):
            row = Adw.ActionRow()
            
            # Format title with deployment info
            if i == 0:
                title = f"Current: {deployment.origin}"
                row.add_css_class("accent")
            else:
                title = f"Previous: {deployment.origin}"
                
            row.set_title(title)
            
            # Add detailed subtitle
            subtitle_parts = [f"Deployed: {deployment.timestamp}"]
            if hasattr(deployment, 'version') and deployment.version:
                subtitle_parts.append(f"Version: {deployment.version}")
            row.set_subtitle(" • ".join(subtitle_parts))
            
            # Add status indicators
            if deployment.is_booted:
                status_label = Gtk.Label(label="● Active")
                status_label.add_css_class("success")
                status_label.set_valign(Gtk.Align.CENTER)
                row.add_suffix(status_label)
            elif i == 0:
                status_label = Gtk.Label(label="● Pending")
                status_label.add_css_class("warning") 
                status_label.set_valign(Gtk.Align.CENTER)
                row.add_suffix(status_label)
                
            # Add rollback button for non-current deployments
            if i > 0:
                rollback_button = Gtk.Button()
                rollback_button.set_label("Rollback")
                rollback_button.set_valign(Gtk.Align.CENTER)
                rollback_button.add_css_class("destructive-action")
                rollback_button.connect("clicked",
                                      lambda b, idx=i: self.on_rollback_clicked(idx))
                row.add_suffix(rollback_button)
            
            self.deployments_list.append(row)
            
        # Add info if limited deployments shown
        if len(deployments) < 4:
            info_row = Adw.ActionRow()
            info_row.set_title("ℹ️ Limited deployment history available")
            info_row.set_subtitle("Universal Blue systems typically maintain 90-day history")
            info_row.add_css_class("dim-label")
            self.deployments_list.append(info_row)
            
    def update_history_list(self):
        """Update history list"""
        # Implementation would load from history manager
        pass
        
    def on_rebase_clicked(self, image_url, image_name):
        """Handle rebase button click"""
        dialog = ConfirmationDialog(
            self,
            f"Rebase to {image_name}?",
            f"This will rebase your system to {image_name}.\n\n"
            "Your current deployment will be preserved and you can rollback if needed.",
            "Rebase"
        )
        
        if dialog.run():
            self.execute_rebase(image_url, image_name)
            
    def on_rebase_variant_clicked(self, base_name, variant_dropdown):
        """Handle rebase button click with variant selection"""
        # Get selected variant
        selected_idx = variant_dropdown.get_selected()
        variant_info = variant_dropdown.variants_data[selected_idx]
        
        # Build full image name and URL
        variant_suffix = variant_info["suffix"]
        # Build display name - remove colon for Fedora variants
        if variant_suffix and variant_suffix.startswith(':'):
            display_suffix = variant_suffix[1:]  # Remove the colon
            full_name = f"{base_name} {display_suffix}"
        else:
            full_name = f"{base_name}{variant_suffix}" if variant_suffix else base_name
        # For Fedora atomic, suffix includes the tag (e.g., :latest, :40)
        # For Universal Blue, we need to add :latest
        if variant_suffix and variant_suffix.startswith(':'):
            # Fedora atomic style - suffix includes the tag
            image_url = f"{variant_dropdown.base_url}{variant_suffix}"
        else:
            # Universal Blue style - add :latest
            image_url = f"{variant_dropdown.base_url}{variant_suffix}:latest"
        
        # Show confirmation with full variant name
        dialog = ConfirmationDialog(
            self,
            f"Rebase to {full_name}?",
            f"This will rebase your system to {base_name} ({variant_info['name']} variant).\n\n"
            f"{variant_info['desc']}\n\n"
            "Your current deployment will be preserved and you can rollback if needed.",
            "Rebase"
        )
        
        if dialog.run():
            self.execute_rebase(image_url, full_name)
            
    def on_rollback_clicked(self, deployment_index):
        """Handle rollback button click"""
        dialog = ConfirmationDialog(
            self,
            "Rollback to previous deployment?",
            "This will rollback your system to the selected deployment.\n\n"
            "Your current configuration will become the alternate deployment.",
            "Rollback"
        )
        
        if dialog.run():
            self.execute_rollback(deployment_index)
            
    def execute_rebase(self, image_url, image_name):
        """Execute rebase operation"""
        # Create progress window
        progress_dialog = Adw.Window()
        progress_dialog.set_title(f"Rebasing to {image_name}")
        progress_dialog.set_default_size(600, 500)
        progress_dialog.set_modal(True)
        progress_dialog.set_transient_for(self)
        
        # Progress content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_markup(f"<b>Rebasing to {image_name}...</b>")
        content_box.append(status_label)
        
        # Progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_bar.set_text("Initializing...")
        content_box.append(progress_bar)
        
        # Log output area
        log_label = Gtk.Label(label="Command Output:")
        log_label.set_halign(Gtk.Align.START)
        log_label.add_css_class("heading")
        content_box.append(log_label)
        
        # Scrolled window for log
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(250)
        
        # Text view for log output
        log_view = Gtk.TextView()
        log_view.set_editable(False)
        log_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        log_view.set_monospace(True)
        log_view.add_css_class("terminal")
        
        log_buffer = log_view.get_buffer()
        scrolled.set_child(log_view)
        content_box.append(scrolled)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)
        
        # Cancel button (disabled during operation)
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.set_sensitive(False)
        cancel_button.add_css_class("destructive-action")
        button_box.append(cancel_button)
        
        # Close button (hidden initially)
        close_button = Gtk.Button(label="Close")
        close_button.set_visible(False)
        close_button.connect("clicked", lambda b: progress_dialog.close())
        button_box.append(close_button)
        
        content_box.append(button_box)
        
        progress_dialog.set_content(content_box)
        progress_dialog.present()
        
        # Variables for progress tracking
        is_downloading = False
        download_progress = 0
        
        def update_progress_from_log(line):
            """Update progress bar based on log output"""
            nonlocal is_downloading, download_progress
            
            # Detect download progress
            if "Downloading" in line or "Pulling" in line:
                is_downloading = True
                progress_bar.set_text("Downloading image layers...")
                # Try to extract percentage
                import re
                percent_match = re.search(r'(\d+)%', line)
                if percent_match:
                    percent = int(percent_match.group(1))
                    progress_bar.set_fraction(percent / 100.0)
            elif "Writing" in line or "Storing" in line:
                progress_bar.set_text("Writing to disk...")
                progress_bar.pulse()
            elif "Staging" in line:
                progress_bar.set_text("Staging deployment...")
                progress_bar.set_fraction(0.8)
            elif "Deployment" in line and "complete" in line:
                progress_bar.set_text("Finalizing...")
                progress_bar.set_fraction(0.95)
            else:
                # Keep pulsing if no specific progress
                if is_downloading:
                    progress_bar.pulse()
        
        def append_log_line(line):
            """Append a line to the log view"""
            try:
                end_iter = log_buffer.get_end_iter()
                log_buffer.insert(end_iter, line + "\n")
                
                # Auto-scroll to bottom
                log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
                
                # Update progress based on content
                update_progress_from_log(line)
            except Exception as e:
                print(f"Error appending log line: {e}")
        
        def do_rebase():
            try:
                # Initial log
                GLib.idle_add(append_log_line, f"Starting rebase to {image_url}")
                GLib.idle_add(append_log_line, "")
                
                # Create a thread-safe progress callback
                def thread_safe_progress(line):
                    GLib.idle_add(append_log_line, line)
                
                # Execute with progress callback
                result = self.command_executor.execute_rebase(image_url, thread_safe_progress)
                
                if result['success']:
                    # Update UI elements in main thread
                    def update_success_ui():
                        try:
                            progress_bar.set_fraction(1.0)
                            progress_bar.set_text("Complete!")
                            status_label.set_markup(f"<b>✓ Successfully rebased to {image_name}</b>")
                            append_log_line("")
                            append_log_line("=== Rebase completed successfully ===")
                            append_log_line("Please reboot your system to boot into the new deployment.")
                            cancel_button.set_visible(False)
                            close_button.set_visible(True)
                            self.show_success(f"Successfully rebased to {image_name}. Please reboot.")
                        except Exception as e:
                            print(f"Error updating success UI: {e}")
                    
                    GLib.idle_add(update_success_ui)
                else:
                    # Update UI elements in main thread
                    def update_failure_ui():
                        try:
                            progress_bar.set_fraction(0)
                            progress_bar.set_text("Failed")
                            status_label.set_markup(f"<b>✗ Failed to rebase to {image_name}</b>")
                            append_log_line("")
                            append_log_line("=== Rebase failed ===")
                            cancel_button.set_visible(False)
                            close_button.set_visible(True)
                            close_button.add_css_class("suggested-action")
                            self.show_error(result.get('error', 'Rebase failed'))
                        except Exception as e:
                            print(f"Error updating failure UI: {e}")
                    
                    GLib.idle_add(update_failure_ui)
                    
            except Exception as e:
                print(f"Exception in do_rebase: {e}")
                import traceback
                traceback.print_exc()
                
                def update_error_ui():
                    try:
                        append_log_line(f"\nError: {str(e)}")
                        progress_bar.set_fraction(0)
                        progress_bar.set_text("Error")
                        cancel_button.set_visible(False)
                        close_button.set_visible(True)
                        self.show_error(str(e))
                    except Exception as ui_error:
                        print(f"Error updating error UI: {ui_error}")
                
                GLib.idle_add(update_error_ui)
                
            finally:
                # Delay the refresh to ensure UI updates complete
                def delayed_refresh():
                    try:
                        if self.get_visible() and not progress_dialog.is_destroyed():
                            self.refresh_system_status()
                    except Exception as e:
                        print(f"Error in delayed refresh: {e}")
                        
                GLib.timeout_add(1000, delayed_refresh)  # 1 second delay
                
                # Clear the progress dialog reference after a delay
                def clear_dialog_ref():
                    if hasattr(self, '_active_progress_dialog'):
                        self._active_progress_dialog = None
                    return False
                    
                GLib.timeout_add(5000, clear_dialog_ref)  # 5 second delay
                
        thread = threading.Thread(target=do_rebase, daemon=True)
        thread.start()
        
    def execute_rollback(self, deployment_index):
        """Execute rollback operation"""
        # Create progress window
        progress_dialog = Adw.Window()
        progress_dialog.set_title("Rolling Back Deployment")
        progress_dialog.set_default_size(600, 400)
        progress_dialog.set_modal(True)
        progress_dialog.set_transient_for(self)
        
        # Progress content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_markup("<b>Rolling back to previous deployment...</b>")
        content_box.append(status_label)
        
        # Progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_bar.set_text("Processing...")
        content_box.append(progress_bar)
        
        # Log output area
        log_label = Gtk.Label(label="Command Output:")
        log_label.set_halign(Gtk.Align.START)
        log_label.add_css_class("heading")
        content_box.append(log_label)
        
        # Scrolled window for log
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(200)
        
        # Text view for log output
        log_view = Gtk.TextView()
        log_view.set_editable(False)
        log_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        log_view.set_monospace(True)
        log_view.add_css_class("terminal")
        
        log_buffer = log_view.get_buffer()
        scrolled.set_child(log_view)
        content_box.append(scrolled)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)
        
        # Cancel button (disabled during operation)
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.set_sensitive(False)
        cancel_button.add_css_class("destructive-action")
        button_box.append(cancel_button)
        
        # Close button (hidden initially)
        close_button = Gtk.Button(label="Close")
        close_button.set_visible(False)
        close_button.connect("clicked", lambda b: progress_dialog.close())
        button_box.append(close_button)
        
        content_box.append(button_box)
        
        progress_dialog.set_content(content_box)
        progress_dialog.present()
        
        def append_log_line(line):
            """Append a line to the log view"""
            end_iter = log_buffer.get_end_iter()
            log_buffer.insert(end_iter, line + "\n")
            
            # Auto-scroll to bottom
            log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
            
            # Update progress based on content
            if "Moving" in line or "Switching" in line:
                progress_bar.set_text("Switching deployments...")
                progress_bar.set_fraction(0.5)
            elif "complete" in line.lower():
                progress_bar.set_fraction(0.9)
        
        def do_rollback():
            try:
                # Initial log
                GLib.idle_add(append_log_line, "Starting rollback operation...")
                GLib.idle_add(append_log_line, "")
                
                # Execute with progress callback
                result = self.command_executor.execute_rollback(deployment_index, append_log_line)
                
                if result['success']:
                    GLib.idle_add(progress_bar.set_fraction, 1.0)
                    GLib.idle_add(progress_bar.set_text, "Complete!")
                    GLib.idle_add(status_label.set_markup, 
                                "<b>✓ Successfully rolled back</b>")
                    GLib.idle_add(append_log_line, "")
                    GLib.idle_add(append_log_line, "=== Rollback completed successfully ===")
                    GLib.idle_add(append_log_line, "Please reboot your system to boot into the previous deployment.")
                    GLib.idle_add(cancel_button.set_visible, False)
                    GLib.idle_add(close_button.set_visible, True)
                    GLib.idle_add(self.show_success,
                                "Successfully rolled back. Please reboot.")
                else:
                    GLib.idle_add(progress_bar.set_fraction, 0)
                    GLib.idle_add(progress_bar.set_text, "Failed")
                    GLib.idle_add(status_label.set_markup, 
                                "<b>✗ Rollback failed</b>")
                    GLib.idle_add(append_log_line, "")
                    GLib.idle_add(append_log_line, "=== Rollback failed ===")
                    GLib.idle_add(cancel_button.set_visible, False)
                    GLib.idle_add(close_button.set_visible, True)
                    GLib.idle_add(close_button.add_css_class, "suggested-action")
                    GLib.idle_add(self.show_error, result.get('error', 'Rollback failed'))
            except Exception as e:
                GLib.idle_add(append_log_line, f"\nError: {str(e)}")
                GLib.idle_add(progress_bar.set_fraction, 0)
                GLib.idle_add(progress_bar.set_text, "Error")
                GLib.idle_add(cancel_button.set_visible, False)
                GLib.idle_add(close_button.set_visible, True)
                GLib.idle_add(self.show_error, str(e))
            finally:
                GLib.idle_add(self.refresh_system_status)
                
        thread = threading.Thread(target=do_rollback)
        thread.start()
        
    def show_success(self, message):
        """Show success toast"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
        
    def show_error(self, message):
        """Show error toast"""
        toast = Adw.Toast.new(f"Error: {message}")
        toast.set_timeout(5)
        self.toast_overlay.add_toast(toast)


def main():
    """Main entry point"""
    app = AtomicImageManager()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())