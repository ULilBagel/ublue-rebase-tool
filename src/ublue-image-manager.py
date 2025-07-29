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
from registry_manager import RegistryManager
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
        self.registry_manager = RegistryManager()
        
        # Initialize search state
        self.history_search_text = ""
        
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
        
        # System deployments section (combines current and all deployments)
        deployments_group = Adw.PreferencesGroup()
        deployments_group.set_title("System Deployments")
        deployments_group.set_description("All local deployments available on your system")
        
        self.deployments_list = Gtk.ListBox()
        self.deployments_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.deployments_list.add_css_class("boxed-list")
        
        deployments_group.add(self.deployments_list)
        box.append(deployments_group)
        
        # Pinned deployments section
        self.pinned_group = Adw.PreferencesGroup()
        self.pinned_group.set_title("Pinned Deployments")
        self.pinned_group.set_description("Deployments that are protected from automatic cleanup")
        self.pinned_group.set_visible(False)  # Hidden by default
        
        self.pinned_list = Gtk.ListBox()
        self.pinned_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pinned_list.add_css_class("boxed-list")
        
        self.pinned_group.add(self.pinned_list)
        box.append(self.pinned_group)
        
        # Historical deployments section (90 days)
        history_group = Adw.PreferencesGroup()
        history_group.set_title("Historical Deployments")
        history_group.set_description("Browse available images from the registry")
        
        # Add expander for historical deployments
        history_expander = Adw.ExpanderRow()
        history_expander.set_title("Show Historical Deployments")
        history_expander.set_subtitle("Search and browse images from the last 90 days")
        
        # Container for search and history list
        history_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        history_container.set_margin_top(6)
        
        # Add search entry
        self.history_search_entry = Gtk.SearchEntry()
        self.history_search_entry.set_placeholder_text("Search deployments (e.g., 'stable', '20240722', 'testing')...")
        self.history_search_entry.set_margin_start(12)
        self.history_search_entry.set_margin_end(12)
        self.history_search_entry.set_margin_bottom(6)
        self.history_search_entry.connect("search-changed", self.on_history_search_changed)
        history_container.append(self.history_search_entry)
        
        # Scrolled window for history list
        history_scrolled = Gtk.ScrolledWindow()
        history_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        history_scrolled.set_min_content_height(200)
        history_scrolled.set_max_content_height(400)
        
        self.history_list = Gtk.ListBox()
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.history_list.add_css_class("boxed-list")
        self.history_list.set_filter_func(self.history_filter_func)
        
        history_scrolled.set_child(self.history_list)
        history_container.append(history_scrolled)
        
        history_expander.add_row(history_container)
        history_group.add(history_expander)
        box.append(history_group)
        
        # Add refresh button at the bottom
        refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        refresh_box.set_halign(Gtk.Align.CENTER)
        refresh_box.set_margin_top(12)
        
        refresh_button = Gtk.Button()
        refresh_button.set_label("Refresh Deployments")
        refresh_button.add_css_class("pill")
        refresh_button.connect("clicked", lambda b: self.refresh_rollback_deployments())
        refresh_box.append(refresh_button)
        
        box.append(refresh_box)
        
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
                    {"name": "41", "suffix": ":41", "desc": "Fedora 41"},
                    {"name": "40", "suffix": ":40", "desc": "Fedora 40"},
                    {"name": "Rawhide", "suffix": ":rawhide", "desc": "Development version"}
                ]
            },
            {
                "name": "Fedora Kinoite",
                "base_url": "ostree-unverified-registry:quay.io/fedora/fedora-kinoite",
                "description": "Immutable desktop OS with KDE Plasma",
                "variants": [
                    {"name": "Latest", "suffix": ":latest", "desc": "Latest stable release"},
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
        """Update deployment lists"""
        # Separate pinned deployments
        pinned_deployments = [d for d in deployments if d.is_pinned]
        
        # Update combined deployments list
        self._update_combined_deployments_list(deployments)
        
        # Update pinned deployments list
        self._update_pinned_deployments_list(pinned_deployments)
        
        # Update historical deployments from registry (not local deployments)
        self._update_historical_deployments_list(deployments)
    
    def _update_combined_deployments_list(self, deployments):
        """Update the combined deployments list"""
        # Clear existing
        child = self.deployments_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.deployments_list.remove(child)
            child = next_child
        
        for i, deployment in enumerate(deployments):
            row = Adw.ActionRow()
            
            # Determine deployment status
            is_pending = i == 0 and not deployment.is_booted
            is_current = deployment.is_booted
            is_previous = not is_pending and not is_current
            
            # Set icon based on status
            if is_current:
                icon_name = "emblem-default-symbolic"
            elif is_pending:
                icon_name = "view-refresh-symbolic"
            else:
                icon_name = "document-open-recent-symbolic"
            
            icon = Gtk.Image.new_from_icon_name(icon_name)
            row.add_prefix(icon)
            
            # Extract clean image name
            image_name = self._extract_image_name(deployment.origin)
            
            # Build title with status
            if is_current:
                title = f"{image_name} (Current)"
            elif is_pending:
                title = f"{image_name} (Pending)"
            else:
                title = image_name
            
            row.set_title(title)
            
            # Build subtitle
            subtitle_parts = []
            if deployment.version:
                subtitle_parts.append(f"v{deployment.version}")
            subtitle_parts.append(deployment.timestamp)
            
            row.set_subtitle(" • ".join(subtitle_parts))
            
            # Add status indicator
            if is_current:
                status_label = Gtk.Label(label="● Active")
                status_label.add_css_class("success")
                status_label.set_valign(Gtk.Align.CENTER)
                row.add_suffix(status_label)
                row.add_css_class("accent")
                
                # Add pin button for current deployment if not already pinned
                if not deployment.is_pinned:
                    pin_button = Gtk.Button()
                    pin_button.set_icon_name("view-pin-symbolic")
                    pin_button.set_tooltip_text("Pin this deployment")
                    pin_button.set_valign(Gtk.Align.CENTER)
                    pin_button.add_css_class("flat")
                    pin_button.connect("clicked",
                                     lambda b, d=deployment: self.on_pin_deployment(d))
                    row.add_suffix(pin_button)
            elif is_pending:
                status_label = Gtk.Label(label="● Pending Reboot")
                status_label.add_css_class("warning")
                status_label.set_valign(Gtk.Align.CENTER)
                row.add_suffix(status_label)
            
            # Add rollback button only for previous deployments (not current or pending)
            if is_previous:
                rollback_button = Gtk.Button()
                rollback_button.set_label("Rollback")
                rollback_button.set_valign(Gtk.Align.CENTER)
                rollback_button.add_css_class("suggested-action")
                rollback_button.connect("clicked",
                                      lambda b, idx=i: self.on_rollback_clicked(idx))
                row.add_suffix(rollback_button)
            
            self.deployments_list.append(row)
    
    def _update_pinned_deployments_list(self, pinned_deployments):
        """Update the pinned deployments list"""
        # Clear existing
        child = self.pinned_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.pinned_list.remove(child)
            child = next_child
        
        # Show/hide the section based on whether there are pinned deployments
        if pinned_deployments:
            self.pinned_group.set_visible(True)
            
            for deployment in pinned_deployments:
                row = Adw.ActionRow()
                
                # Set icon for pinned deployments
                icon = Gtk.Image.new_from_icon_name("view-pin-symbolic")
                row.add_prefix(icon)
                
                # Extract clean image name
                image_name = self._extract_image_name(deployment.origin)
                row.set_title(image_name)
                
                # Build subtitle
                subtitle_parts = []
                if deployment.version:
                    subtitle_parts.append(f"v{deployment.version}")
                subtitle_parts.append(deployment.timestamp)
                subtitle_parts.append("Protected from cleanup")
                
                row.set_subtitle(" • ".join(subtitle_parts))
                
                # Add unpin button
                unpin_button = Gtk.Button()
                unpin_button.set_icon_name("edit-delete-symbolic")
                unpin_button.set_tooltip_text("Unpin this deployment")
                unpin_button.set_valign(Gtk.Align.CENTER)
                unpin_button.add_css_class("flat")
                unpin_button.connect("clicked",
                                   lambda b, d=deployment: self.on_unpin_deployment(d))
                row.add_suffix(unpin_button)
                
                # Add rollback button if not current
                if not deployment.is_booted:
                    rollback_button = Gtk.Button()
                    rollback_button.set_label("Rollback")
                    rollback_button.set_valign(Gtk.Align.CENTER)
                    rollback_button.add_css_class("suggested-action")
                    # Find the deployment index
                    for i, d in enumerate(self.deployment_manager.get_all_deployments()):
                        if d.id == deployment.id:
                            rollback_button.connect("clicked",
                                                  lambda b, idx=i: self.on_rollback_clicked(idx))
                            break
                    row.add_suffix(rollback_button)
                
                self.pinned_list.append(row)
        else:
            self.pinned_group.set_visible(False)
    
    def _update_historical_deployments_list(self, deployments):
        """Update the historical deployments list with 90-day registry history"""
        # Clear existing
        child = self.history_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.history_list.remove(child)
            child = next_child
        
        # Check if skopeo is available
        if not self.registry_manager.check_skopeo_available():
            info_row = Adw.ActionRow()
            info_row.set_title("Historical images unavailable")
            info_row.set_subtitle("Install skopeo to browse historical images")
            info_row.add_css_class("dim-label")
            self.history_list.append(info_row)
            return
        
        # Get current deployment to determine registry and image
        current_deployment = self.deployment_manager.get_current_deployment()
        if not current_deployment:
            return
        
        # Extract registry info from current deployment
        registry, image_name, current_tag = self.registry_manager.get_image_info_from_deployment(current_deployment)
        
        if not registry or not image_name:
            # Can't determine registry info
            info_row = Adw.ActionRow()
            info_row.set_title("Historical images unavailable")
            info_row.set_subtitle("Unable to determine current image registry")
            self.history_list.append(info_row)
            return
        
        # Show loading state
        loading_row = Adw.ActionRow()
        loading_row.set_title("Loading historical images...")
        loading_row.set_subtitle(f"Querying {registry}/{image_name}")
        spinner = Gtk.Spinner()
        spinner.start()
        loading_row.add_suffix(spinner)
        self.history_list.append(loading_row)
        
        # Fetch historical images in background
        def fetch_historical():
            try:
                # Determine branch from current tag
                branch = "stable"
                if "testing" in current_tag:
                    branch = "testing"
                elif current_tag in ["stable", "testing"]:
                    branch = current_tag
                
                # Get images from last 90 days
                historical_images = self.registry_manager.get_recent_images(
                    registry, image_name, days=90, branch=branch
                )
                
                # Update UI in main thread
                GLib.idle_add(self._populate_historical_list, historical_images, registry, image_name)
                
            except Exception as e:
                print(f"Error fetching historical images: {e}")
                GLib.idle_add(self._show_historical_error, str(e))
        
        # Start background thread
        threading.Thread(target=fetch_historical, daemon=True).start()
    
    def _populate_historical_list(self, images, registry, image_name):
        """Populate the historical list with fetched images"""
        # Clear loading state
        child = self.history_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.history_list.remove(child)
            child = next_child
        
        if not images:
            empty_row = Adw.ActionRow()
            empty_row.set_title("No historical images found")
            empty_row.set_subtitle("No images available from the last 90 days")
            self.history_list.append(empty_row)
            return
        
        # Group by time periods
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        for img in images:
            row = Adw.ActionRow()
            
            # Format the title
            clean_name = image_name.replace("-", " ").title()
            row.set_title(f"{clean_name} - {img.tag}")
            
            # Calculate time description
            time_desc = ""
            if img.date:
                days_ago = (today - img.date.date()).days
                
                if days_ago == 0:
                    time_desc = "Released today"
                elif days_ago == 1:
                    time_desc = "Released yesterday"
                elif days_ago < 7:
                    time_desc = f"Released {days_ago} days ago"
                elif days_ago < 30:
                    weeks = days_ago // 7
                    time_desc = f"Released {weeks} week{'s' if weeks > 1 else ''} ago"
                else:
                    months = days_ago // 30
                    time_desc = f"Released {months} month{'s' if months > 1 else ''} ago"
                
                # Add date to subtitle
                date_str = img.date.strftime("%Y-%m-%d")
                row.set_subtitle(f"{time_desc} • {date_str}")
            else:
                row.set_subtitle(f"Tag: {img.tag}")
            
            # Add rebase button
            rebase_button = Gtk.Button()
            rebase_button.set_label("Rebase")
            rebase_button.set_valign(Gtk.Align.CENTER)
            rebase_button.add_css_class("suggested-action")
            
            # Determine the full image reference based on current deployment protocol
            current_deployment = self.deployment_manager.get_current_deployment()
            if current_deployment and "ostree-unverified-registry:" in current_deployment.origin:
                full_ref = f"ostree-unverified-registry:{img.full_ref}"
            else:
                full_ref = f"ostree-image-signed:docker://{img.full_ref}"
            
            rebase_button.connect("clicked",
                                lambda b, ref=full_ref, name=f"{clean_name} {img.tag}": 
                                self.on_rebase_clicked(ref, name))
            row.add_suffix(rebase_button)
            
            self.history_list.append(row)
    
    def _show_historical_error(self, error_msg):
        """Show error in historical list"""
        # Clear existing
        child = self.history_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.history_list.remove(child)
            child = next_child
        
        error_row = Adw.ActionRow()
        error_row.set_title("Failed to load historical images")
        error_row.set_subtitle(f"Error: {error_msg}")
        error_row.add_css_class("error")
        self.history_list.append(error_row)
    
    def _extract_image_name(self, origin):
        """Extract a clean image name from the origin URL"""
        if "ghcr.io/ublue-os/" in origin:
            parts = origin.split("/")
            if len(parts) >= 3:
                image_tag = parts[-1]
                image_name = image_tag.split(":")[0]
                # Clean up the name
                image_name = image_name.replace("-", " ").title()
                return image_name
        elif "quay.io/fedora/" in origin:
            parts = origin.split("/")
            if len(parts) >= 3:
                image_tag = parts[-1]
                image_name = image_tag.split(":")[0]
                # Clean up Fedora names
                image_name = image_name.replace("fedora-", "").replace("-", " ").title()
                return f"Fedora {image_name}"
        
        # Fallback: just show the last part of the origin
        return origin.split("/")[-1]
    
    def refresh_rollback_deployments(self):
        """Refresh just the rollback deployments"""
        self.refresh_system_status()
    
    def on_historical_rollback_clicked(self, deployment):
        """Handle rollback for historical deployments"""
        # For historical deployments, we need to use the deployment ID
        # This would require enhancing the command executor to support
        # rpm-ostree deploy <commit-id>
        dialog = ConfirmationDialog(
            self,
            "Restore Historical Deployment?",
            f"This will restore your system to:\n{deployment.origin}\n"
            f"Version: {deployment.version}\n"
            f"Deployed: {deployment.timestamp}\n\n"
            "This is an advanced operation. Continue?",
            "Restore"
        )
        
        if dialog.run():
            self.show_error("Historical rollback not yet implemented")
            # TODO: Implement historical rollback using deployment.id
    
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
            # Execute pin command
            try:
                if 'FLATPAK_ID' in os.environ:
                    cmd = ["flatpak-spawn", "--host", "pkexec", "ostree", "admin", "pin", str(deployment.index)]
                else:
                    cmd = ["pkexec", "ostree", "admin", "pin", str(deployment.index)]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.show_success("Deployment pinned successfully")
                    self.refresh_system_status()
                else:
                    self.show_error(f"Failed to pin deployment: {result.stderr}")
            except Exception as e:
                self.show_error(f"Error pinning deployment: {str(e)}")
    
    def on_unpin_deployment(self, deployment):
        """Handle unpinning a deployment"""
        dialog = ConfirmationDialog(
            self,
            "Unpin Deployment?",
            f"This will unpin the deployment:\n{self._extract_image_name(deployment.origin)}\n\n"
            "The deployment will no longer be protected from automatic cleanup.",
            "Unpin"
        )
        
        if dialog.run():
            # Execute unpin command
            try:
                if 'FLATPAK_ID' in os.environ:
                    cmd = ["flatpak-spawn", "--host", "pkexec", "ostree", "admin", "pin", "--unpin", str(deployment.index)]
                else:
                    cmd = ["pkexec", "ostree", "admin", "pin", "--unpin", str(deployment.index)]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.show_success("Deployment unpinned successfully")
                    self.refresh_system_status()
                else:
                    self.show_error(f"Failed to unpin deployment: {result.stderr}")
            except Exception as e:
                self.show_error(f"Error unpinning deployment: {str(e)}")
    
    def on_history_search_changed(self, search_entry):
        """Handle search text changes in historical deployments"""
        # Invalidate filter to trigger re-filtering
        self.history_list.invalidate_filter()
    
    def history_filter_func(self, row):
        """Filter function for historical deployments search"""
        search_text = self.history_search_entry.get_text().lower()
        
        if not search_text:
            return True
        
        # Get the row's title and subtitle
        if hasattr(row, 'get_title'):
            title = row.get_title() or ""
            subtitle = row.get_subtitle() or ""
            
            # Search in both title and subtitle
            combined_text = f"{title} {subtitle}".lower()
            
            # Check if search text matches
            return search_text in combined_text
        
        return True
            
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
        # For Fedora atomic, suffix includes the tag (e.g., :40, :41)
        # For Universal Blue, we need to add :stable for variants without explicit tags
        if variant_suffix and variant_suffix.startswith(':'):
            # Fedora atomic style - suffix includes the tag
            image_url = f"{variant_dropdown.base_url}{variant_suffix}"
        else:
            # Universal Blue style - add :stable as the default
            image_url = f"{variant_dropdown.base_url}{variant_suffix}:stable"
        
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
        
        # Now that append_log_line is defined, we can set up the cancel button
        def on_cancel_clicked(button):
            """Handle cancel button click"""
            append_log_line("\n=== Cancelling operation ===")
            button.set_sensitive(False)
            
            # Cancel the current command execution
            self.command_executor.cancel_current_execution()
            
            # Also run rpm-ostree cancel to cancel the transaction
            try:
                subprocess.run(["flatpak-spawn", "--host", "rpm-ostree", "cancel"], 
                             capture_output=True, text=True)
                append_log_line("Operation cancelled by user")
            except Exception as e:
                append_log_line(f"Error during cancel: {e}")
            
            cancel_button.set_visible(False)
            close_button.set_visible(True)
            progress_bar.set_text("Cancelled")
            status_label.set_markup("<b>Operation cancelled</b>")
        
        # Connect the cancel button handler and enable it
        cancel_button.connect("clicked", on_cancel_clicked)
        cancel_button.set_sensitive(True)
        
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
        
        # Connect cancel button handler after append_log_line is defined
        def on_cancel_clicked(button):
            """Handle cancel button click"""
            append_log_line("\n=== Cancelling operation ===")
            button.set_sensitive(False)
            
            # Cancel the current command execution
            self.command_executor.cancel_current_execution()
            
            # Also run rpm-ostree cancel to cancel the transaction
            try:
                subprocess.run(["flatpak-spawn", "--host", "rpm-ostree", "cancel"], 
                             capture_output=True, text=True)
                append_log_line("Operation cancelled by user")
            except Exception as e:
                append_log_line(f"Error during cancel: {e}")
            
            # Update UI
            progress_bar.set_fraction(0)
            progress_bar.set_text("Cancelled")
            status_label.set_markup("<b>Operation cancelled</b>")
            cancel_button.set_visible(False)
            close_button.set_visible(True)
            close_button.add_css_class("suggested-action")
        
        cancel_button.connect("clicked", on_cancel_clicked)
        cancel_button.set_sensitive(True)  # Enable cancel button
        
        def do_rollback():
            try:
                # Initial log
                GLib.idle_add(append_log_line, "Starting rollback operation...")
                GLib.idle_add(append_log_line, "")
                
                # Execute with progress callback
                def thread_safe_callback(line):
                    GLib.idle_add(append_log_line, line)
                
                result = self.command_executor.execute_rollback(deployment_index, thread_safe_callback)
                
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
                
        thread = threading.Thread(target=do_rollback, daemon=True)
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