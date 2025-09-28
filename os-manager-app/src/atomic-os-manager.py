#!/usr/bin/env python3
"""
Atomic OS Manager - Image-specific configuration tool for ostree-based systems
Provides tailored options based on the current running image
"""

import gi
import sys
import os
import threading
import subprocess
import json
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
import signal

# Import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deployment_manager import DeploymentManager
from command_executor import CommandExecutor
from rpm_ostree_helper import get_status_json
from ui.confirmation_dialog import ConfirmationDialog


class ImageConfig:
    """Configuration for specific images"""
    
    BAZZITE_CONFIG = {
        "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/bazzite",
        "variants": {
            "bazzite": {
                "name": "Bazzite",
                "gamemode_target": "bazzite-deck",
                "dx_target": "bazzite-dx",
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-nvidia": {
                "name": "Bazzite NVIDIA",
                "gamemode_target": "bazzite-deck-nvidia",
                "dx_target": "bazzite-dx-nvidia",
                "gpu_variants": {
                    "AMD": "",  # Switch back to base bazzite
                    "NVIDIA": "",  # Already nvidia
                    "Intel": ""
                }
            },
            "bazzite-gnome": {
                "name": "Bazzite GNOME", 
                "gamemode_target": "bazzite-deck-gnome",
                "dx_target": "bazzite-dx-gnome",
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-gnome-nvidia": {
                "name": "Bazzite GNOME NVIDIA",
                "gamemode_target": "bazzite-deck-nvidia",  # Switch to deck-nvidia for game mode
                "dx_target": "bazzite-dx-nvidia-gnome",
                "gpu_variants": {
                    "AMD": "",  # Switch back to gnome
                    "NVIDIA": "",  # Already nvidia
                    "Intel": ""
                }
            },
            "bazzite-deck": {
                "name": "Bazzite Deck",
                "gamemode_target": None,  # Already in game mode
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-deck-nvidia": {
                "name": "Bazzite Deck NVIDIA",
                "gamemode_target": None,  # Already in game mode
                "gpu_variants": {
                    "AMD": "",  # Switch back to deck
                    "NVIDIA": "",  # Already nvidia
                    "Intel": ""
                }
            },
            "bazzite-deck-gnome": {
                "name": "Bazzite Deck GNOME",
                "gamemode_target": None,  # Already in game mode
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-asus": {
                "name": "Bazzite ASUS",
                "gamemode_target": "bazzite-deck",
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "",  # ASUS is AMD only
                    "Intel": ""
                }
            },
            "bazzite-dx": {
                "name": "Bazzite DX",
                "gamemode_target": None,  # No game mode for DX
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-dx-nvidia": {
                "name": "Bazzite DX NVIDIA",
                "gamemode_target": None,  # No game mode for DX
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",  # Switch back to dx
                    "NVIDIA": "",  # Already nvidia
                    "Intel": ""
                }
            },
            "bazzite-dx-gnome": {
                "name": "Bazzite DX GNOME",
                "gamemode_target": None,  # No game mode for DX
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bazzite-dx-nvidia-gnome": {
                "name": "Bazzite DX NVIDIA GNOME",
                "gamemode_target": None,  # No game mode for DX
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",  # Switch back to dx-gnome
                    "NVIDIA": "",  # Already nvidia
                    "Intel": ""
                }
            }
        },
        "branches": ["stable", "testing"],
        "features": ["gamemode", "gpu_selection", "branch_selection", "dx_mode"]
    }
    
    BLUEFIN_CONFIG = {
        "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/bluefin",
        "variants": {
            "bluefin": {
                "name": "Bluefin",
                "dx_target": "bluefin-dx",
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "bluefin-dx": {
                "name": "Bluefin DX",
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            }
        },
        "branches": ["stable", "latest", "gts"],
        "features": ["dx_mode", "gpu_selection", "branch_selection"]
    }
    
    AURORA_CONFIG = {
        "base_url": "ostree-image-signed:docker://ghcr.io/ublue-os/aurora",
        "variants": {
            "aurora": {
                "name": "Aurora",
                "dx_target": "aurora-dx",
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            },
            "aurora-dx": {
                "name": "Aurora DX",
                "dx_target": None,  # Already DX
                "gpu_variants": {
                    "AMD": "",
                    "NVIDIA": "-nvidia",
                    "Intel": ""
                }
            }
        },
        "branches": ["stable", "latest", "gts"],
        "features": ["dx_mode", "gpu_selection", "branch_selection"]
    }
    
    SILVERBLUE_CONFIG = {
        "base_url": "ostree-image-signed:docker://quay.io/fedora/fedora-silverblue",
        "variants": {
            "silverblue": {
                "name": "Fedora Silverblue",
                "gpu_variants": None  # No GPU variants for Fedora
            }
        },
        "branches": ["41", "40", "rawhide"],
        "features": ["branch_selection"]
    }
    
    KINOITE_CONFIG = {
        "base_url": "ostree-image-signed:docker://quay.io/fedora/fedora-kinoite",
        "variants": {
            "kinoite": {
                "name": "Fedora Kinoite",
                "gpu_variants": None  # No GPU variants for Fedora
            }
        },
        "branches": ["41", "40", "rawhide"],
        "features": ["branch_selection"]
    }


# Update tool configuration
UPDATE_TOOLS = [
    {
        "name": "uupd",
        "command": ["flatpak-spawn", "--host", "pkexec", "uupd", "--json"],
        "check_command": "uupd",
        "reboot_indicators": ["(R)eboot", "(r)eboot", "restart required", "Reboot required", "System restart required"],
        "json_output": True,  # Using JSON for structured progress data
        "needs_tty": False,
    },
    {
        "name": "ujust",
        "command": ["flatpak-spawn", "--host", "ujust", "update"],
        "check_command": "ujust",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
        "json_output": False,
    },
    {
        "name": "bootc",
        "command": ["flatpak-spawn", "--host", "pkexec", "bootc", "upgrade"],
        "check_command": "bootc",
        "reboot_indicators": ["(R)eboot", "(r)eboot", "restart required", "Reboot required"],
        "json_output": False,
    },
    {
        "name": "rpm-ostree",
        "command": ["flatpak-spawn", "--host", "rpm-ostree", "upgrade"],
        "check_command": "rpm-ostree",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
        "json_output": False,
    }
]


class AtomicOSManager(Adw.Application):
    """Main application class for OS Manager"""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.ublue.OSManager',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        
    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            self.window = OSManagerWindow(application=self)
        self.window.present()
    
    def do_shutdown(self):
        """Called when the application is shutting down"""
        # Clean up any running processes in the window
        if self.window:
            self.window.cleanup_on_shutdown()
        # Call parent shutdown
        Adw.Application.do_shutdown(self)
        
    def do_startup(self):
        """Called when the application starts up"""
        Adw.Application.do_startup(self)


class OSManagerWindow(Adw.ApplicationWindow):
    """Main window for the OS Manager"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Atomic OS Manager", **kwargs)
        
        self.deployment_manager = DeploymentManager()
        self.command_executor = CommandExecutor()
        self.pending_changes = {}
        self.is_system_update = False
        self.update_process = None
        
        self.set_default_size(700, -1)  # Width only, let height be natural
        
        # Detect current image
        self.detect_current_image()
        
        # Setup UI
        self.setup_ui()
        
    def detect_current_image(self):
        """Detect the currently running image and its configuration"""
        deployment = self.deployment_manager.get_current_deployment()
        
        if not deployment:
            self.current_config = None
            self.current_variant = None
            self.current_image_name = None
            self.current_branch = "stable"
            self.current_gpu = "AMD"
            return
            
        origin = deployment.origin.lower()
        
        # Detect image type and variant
        if "bazzite" in origin:
            self.current_config = ImageConfig.BAZZITE_CONFIG
            self.current_image_name = "bazzite"
            # Order matters - check most specific first
            if "dx-nvidia-gnome" in origin:
                self.current_variant = "bazzite-dx-nvidia-gnome"
            elif "dx-gnome" in origin:
                self.current_variant = "bazzite-dx-gnome"
            elif "dx-nvidia" in origin:
                self.current_variant = "bazzite-dx-nvidia"
            elif "dx" in origin:
                self.current_variant = "bazzite-dx"
            elif "deck-gnome" in origin:
                self.current_variant = "bazzite-deck-gnome"
            elif "deck-nvidia" in origin:
                self.current_variant = "bazzite-deck-nvidia"
            elif "deck" in origin:
                self.current_variant = "bazzite-deck"
            elif "gnome-nvidia" in origin:
                self.current_variant = "bazzite-gnome-nvidia"
            elif "gnome" in origin:
                self.current_variant = "bazzite-gnome"
            elif "nvidia" in origin:
                self.current_variant = "bazzite-nvidia"
            elif "asus" in origin:
                self.current_variant = "bazzite-asus"
            else:
                self.current_variant = "bazzite"
        elif "bluefin" in origin:
            self.current_config = ImageConfig.BLUEFIN_CONFIG
            self.current_image_name = "bluefin"
            if "dx" in origin:
                self.current_variant = "bluefin-dx"
            else:
                self.current_variant = "bluefin"
        elif "aurora" in origin:
            self.current_config = ImageConfig.AURORA_CONFIG
            self.current_image_name = "aurora"
            if "dx" in origin:
                self.current_variant = "aurora-dx"
            else:
                self.current_variant = "aurora"
        elif "silverblue" in origin:
            self.current_config = ImageConfig.SILVERBLUE_CONFIG
            self.current_image_name = "silverblue"
            self.current_variant = "silverblue"
        elif "kinoite" in origin:
            self.current_config = ImageConfig.KINOITE_CONFIG
            self.current_image_name = "kinoite"
            self.current_variant = "kinoite"
        else:
            self.current_config = None
            self.current_variant = None
            self.current_image_name = None
            
        # Detect current branch
        if ":testing" in origin or "-testing" in origin:
            self.current_branch = "testing"
        elif ":gts" in origin or "-gts" in origin:
            self.current_branch = "gts"
        elif ":latest" in origin:
            self.current_branch = "latest"
        elif ":rawhide" in origin:
            self.current_branch = "rawhide"
        elif ":41" in origin:
            self.current_branch = "41"
        elif ":40" in origin:
            self.current_branch = "40"
        else:
            self.current_branch = "stable"
            
        # Detect GPU variant
        if "nvidia" in origin:
            self.current_gpu = "NVIDIA"
        else:
            self.current_gpu = "AMD"  # Default to AMD
            
    def setup_ui(self):
        """Setup the user interface"""
        # Header bar
        header_bar = Adw.HeaderBar()
        
        # Main content box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)
        main_box.append(header_bar)
        
        # Create stack for different views
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)
        
        # Configuration view
        self.create_config_view()
        
        # Progress view
        self.create_progress_view()
        
        main_box.append(self.stack)
        self.set_content(main_box)
        
    def create_config_view(self):
        """Create the configuration view"""
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # Content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        
        # Create a clamp to limit maximum width while centering content
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)  # Maximum width for content
        clamp.set_tightening_threshold(600)
        clamp.set_child(self.content_box)
        
        # System Settings section at the top (for Universal Blue images)
        if self.current_image_name in ["bazzite", "bluefin", "aurora"]:
            self.create_system_settings_section()
        
        # Current system info
        self.create_system_info_section()
        
        # Configuration options
        if self.current_config:
            self.create_configuration_section()
        else:
            self.create_unsupported_section()
            
        scrolled.set_child(clamp)
        self.stack.add_named(scrolled, "config")
        self.stack.set_visible_child_name("config")
        
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
        self.progress_label.set_text("Applying configuration changes...")
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
        self.log_frame.set_size_request(700, 400)
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
        
        # Set up log buffer with tag for better visibility
        self.log_buffer = self.log_view.get_buffer()
        self.log_tag = self.log_buffer.create_tag("log", font="monospace")
        
        scrolled_log.set_child(self.log_view)
        self.log_frame.set_child(scrolled_log)
        progress_box.append(self.log_frame)
        
        # Button box
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.button_box.set_halign(Gtk.Align.CENTER)
        self.button_box.set_margin_top(12)
        
        # Back button (hidden initially, left side when visible)
        self.back_button = Gtk.Button()
        self.back_button.set_label("Back to Configuration")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.back_button.set_visible(False)
        self.button_box.append(self.back_button)
        
        # Cancel button (right side)
        self.cancel_button = Gtk.Button()
        self.cancel_button.set_label("Cancel")
        self.cancel_button.add_css_class("destructive-action")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.button_box.append(self.cancel_button)
        
        # Reboot button (hidden initially)
        self.reboot_button = Gtk.Button()
        self.reboot_button.set_label("Reboot Now")
        self.reboot_button.add_css_class("suggested-action")
        self.reboot_button.connect("clicked", self.on_reboot_clicked)
        self.reboot_button.set_visible(False)
        self.button_box.append(self.reboot_button)
        
        # Close button (hidden initially)
        self.close_button = Gtk.Button()
        self.close_button.set_label("Close")
        self.close_button.connect("clicked", lambda w: self.get_application().quit())
        self.close_button.set_visible(False)
        self.button_box.append(self.close_button)
        
        progress_box.append(self.button_box)
        
        self.stack.add_named(progress_box, "progress")
        
    def create_system_info_section(self):
        """Create the current system information section"""
        info_group = Adw.PreferencesGroup()
        info_group.set_title("Current System")
        
        # Image info
        if self.current_config and self.current_variant:
            variant_info = self.current_config["variants"].get(self.current_variant, {})
            image_name = variant_info.get("name", "Unknown")
            
            info_row = Adw.ActionRow()
            info_row.set_title(image_name)
            info_row.set_subtitle(f"Branch: {self.current_branch} • GPU: {self.current_gpu}")
            info_group.add(info_row)
        else:
            info_row = Adw.ActionRow()
            info_row.set_title("Unsupported Image")
            info_row.set_subtitle("This tool does not support your current image")
            info_group.add(info_row)
            
        self.content_box.append(info_group)
        
    def create_configuration_section(self):
        """Create the configuration options section"""
        config_group = Adw.PreferencesGroup()
        config_group.set_title("Configuration Options")
        config_group.set_description("Select the desired configuration for your system")
        
        # Game Mode option (Bazzite only)
        if "gamemode" in self.current_config.get("features", []):
            self.create_gamemode_option(config_group)
            
        # DX Mode option (Bluefin/Aurora only)
        if "dx_mode" in self.current_config.get("features", []):
            self.create_dx_mode_option(config_group)
            
        # Branch selection
        if "branch_selection" in self.current_config.get("features", []):
            self.create_branch_selection(config_group)
            
        # GPU selection
        if "gpu_selection" in self.current_config.get("features", []):
            self.create_gpu_selection(config_group)
            
        self.content_box.append(config_group)
        
        # Apply button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        self.apply_button = Gtk.Button()
        self.apply_button.set_label("Apply Changes")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.set_sensitive(False)
        self.apply_button.connect("clicked", self.on_apply_clicked)
        button_box.append(self.apply_button)
        
        self.content_box.append(button_box)
        
        # Status bar at bottom
        self.status_bar = Gtk.Label()
        self.status_bar.set_margin_top(12)
        self.status_bar.add_css_class("dim-label")
        self.status_bar.set_text("Ready")
        self.content_box.append(self.status_bar)
        
    def create_gamemode_option(self, parent):
        """Create game mode toggle option"""
        gamemode_row = Adw.ActionRow()
        gamemode_row.set_title("Game Mode")
        gamemode_row.set_subtitle("Enable Steam Deck-like gaming experience")
        
        self.gamemode_switch = Gtk.Switch()
        self.gamemode_switch.set_valign(Gtk.Align.CENTER)
        
        # Check if already in game mode
        is_deck = "deck" in self.current_variant
        self.gamemode_switch.set_active(is_deck)
        
        # Only enable if there's a target to switch to
        variant_info = self.current_config["variants"].get(self.current_variant, {})
        has_target = variant_info.get("gamemode_target") is not None
        self.gamemode_switch.set_sensitive(has_target)
        
        self.gamemode_switch.connect("notify::active", self.on_gamemode_toggled)
        gamemode_row.add_suffix(self.gamemode_switch)
        
        parent.add(gamemode_row)
        
    def create_dx_mode_option(self, parent):
        """Create DX mode toggle option"""
        self.dx_row = Adw.ActionRow()
        self.dx_row.set_title("Developer Experience")
        self.dx_row.set_subtitle("Enable additional developer tools and features")
        
        self.dx_check = Gtk.CheckButton()
        self.dx_check.set_valign(Gtk.Align.CENTER)
        
        # Check if already in DX mode
        is_dx = "dx" in self.current_variant
        self.dx_check.set_active(is_dx)
        
        # Only enable if there's a target to switch to
        variant_info = self.current_config["variants"].get(self.current_variant, {})
        has_target = variant_info.get("dx_target") is not None
        self.dx_check.set_sensitive(has_target)
        
        self.dx_check.connect("toggled", self.on_dx_toggled)
        self.dx_row.add_suffix(self.dx_check)
        
        parent.add(self.dx_row)
        
        # Update initial visibility
        self.update_dx_visibility()
        
    def create_branch_selection(self, parent):
        """Create branch selection options"""
        branch_row = Adw.ActionRow()
        branch_row.set_title("Update Branch")
        branch_row.set_subtitle("Select the update channel")
        
        # Create dropdown for branches
        branch_options = Gtk.StringList()
        branches = self.current_config.get("branches", [])
        current_index = 0
        
        for i, branch in enumerate(branches):
            branch_options.append(branch)
            if branch == self.current_branch:
                current_index = i
                
        self.branch_dropdown = Gtk.DropDown()
        self.branch_dropdown.set_model(branch_options)
        self.branch_dropdown.set_valign(Gtk.Align.CENTER)
        self.branch_dropdown.set_selected(current_index)
        
        # Connect change signal
        self.branch_dropdown.connect("notify::selected", self.on_branch_dropdown_changed)
        
        branch_row.add_suffix(self.branch_dropdown)
        parent.add(branch_row)
        
    def create_gpu_selection(self, parent):
        """Create GPU selection dropdown"""
        gpu_row = Adw.ActionRow()
        gpu_row.set_title("GPU Type")
        gpu_row.set_subtitle("Select your graphics hardware")
        
        # Create dropdown
        gpu_options = Gtk.StringList()
        for gpu in ["AMD", "NVIDIA", "Intel"]:
            gpu_options.append(gpu)
            
        self.gpu_dropdown = Gtk.DropDown()
        self.gpu_dropdown.set_model(gpu_options)
        self.gpu_dropdown.set_valign(Gtk.Align.CENTER)
        
        # Set current selection
        if self.current_gpu == "NVIDIA":
            self.gpu_dropdown.set_selected(1)
        elif self.current_gpu == "Intel":
            self.gpu_dropdown.set_selected(2)
        else:
            self.gpu_dropdown.set_selected(0)  # AMD
            
        self.gpu_dropdown.connect("notify::selected", self.on_gpu_changed)
        
        gpu_row.add_suffix(self.gpu_dropdown)
        parent.add(gpu_row)
        
    def create_unsupported_section(self):
        """Create section for unsupported images"""
        unsupported_group = Adw.PreferencesGroup()
        unsupported_group.set_title("Unsupported Image")
        unsupported_group.set_description(
            "This tool currently supports:\n"
            "• Bazzite (Gaming-focused)\n"
            "• Bluefin (Developer-focused GNOME)\n"
            "• Aurora (Developer-focused KDE)\n"
            "• Fedora Silverblue\n"
            "• Fedora Kinoite"
        )
        
        self.content_box.append(unsupported_group)
        
    def create_system_settings_section(self):
        """Create system settings section for Universal Blue images"""
        system_group = Adw.PreferencesGroup()
        system_group.set_title("System Maintenance")
        system_group.set_description("Update your system and installed applications")
        
        # System update button
        update_row = Adw.ActionRow()
        update_row.set_title("System Update")
        update_row.set_subtitle("Update system, Flatpaks, and containers")
        
        self.update_button = Gtk.Button()
        self.update_button.set_label("Check for Updates")
        self.update_button.set_valign(Gtk.Align.CENTER)
        self.update_button.add_css_class("suggested-action")
        self.update_button.connect("clicked", self.on_update_clicked)
        update_row.add_suffix(self.update_button)
        
        system_group.add(update_row)
        self.content_box.append(system_group)
        
        
    def on_gamemode_toggled(self, switch, param):
        """Handle game mode toggle"""
        self.pending_changes["gamemode"] = switch.get_active()
        self.update_apply_button()
        # Update DX visibility based on new target variant
        self.update_dx_visibility()
        
    def on_dx_toggled(self, checkbox):
        """Handle DX mode toggle"""
        is_active = checkbox.get_active()
        variant_info = self.current_config["variants"].get(self.current_variant, {})
        is_currently_dx = "dx" in self.current_variant
        
        # Only add to pending changes if it's actually a change
        if is_active != is_currently_dx:
            self.pending_changes["dx_mode"] = is_active
        elif "dx_mode" in self.pending_changes:
            del self.pending_changes["dx_mode"]
            
        self.update_apply_button()
        
    def on_update_clicked(self, button):
        """Handle system update button click"""
        # Disable button during update
        button.set_sensitive(False)
        button.set_label("Checking...")
        
        # Kill any existing update process before starting a new one
        if self.update_process:
            self.cleanup_update_process()
            
        # Switch to progress view
        self.stack.set_visible_child_name("progress")
        self.spinner.start()
        self.cancel_button.set_sensitive(True)  # Allow cancelling system updates
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
        self.progress_label.set_text("Running system update...")
        
        # Set flag to indicate we're doing a system update
        self.is_system_update = True
        
        # Run update in a thread
        thread = threading.Thread(target=self.run_system_update)
        thread.daemon = True
        thread.start()
    
    def update_dx_visibility(self):
        """Update DX checkbox visibility based on current selections"""
        if not hasattr(self, 'dx_row'):
            return
            
        # Start with current variant
        target_variant = self.current_variant
        variant_info = self.current_config["variants"].get(target_variant, {})
        
        # Check if gamemode is toggled
        if hasattr(self, 'gamemode_switch') and "gamemode" in self.pending_changes:
            if self.pending_changes["gamemode"]:
                # Switching to game mode
                gamemode_target = variant_info.get("gamemode_target")
                if gamemode_target:
                    target_variant = gamemode_target
                    variant_info = self.current_config["variants"][target_variant]
            else:
                # Switching from game mode - need to determine base variant
                if "deck" in target_variant:
                    # Remove deck from variant name to get base
                    target_variant = target_variant.replace("-deck", "").replace("deck-", "")
                    variant_info = self.current_config["variants"].get(target_variant, {})
        
        # Check if the target variant has a DX option
        has_dx_target = variant_info.get("dx_target") is not None
        self.dx_row.set_visible(has_dx_target)
        
        # If hiding DX row and it was selected, remove from pending changes
        if not has_dx_target and "dx_mode" in self.pending_changes:
            del self.pending_changes["dx_mode"]
            self.dx_check.set_active(False)
            self.update_apply_button()
        
    def on_branch_changed(self, radio, branch):
        """Handle branch selection change (legacy radio button handler)"""
        if radio.get_active():
            if branch != self.current_branch:
                self.pending_changes["branch"] = branch
            elif "branch" in self.pending_changes:
                del self.pending_changes["branch"]
            self.update_apply_button()
    
    def on_branch_dropdown_changed(self, dropdown, param):
        """Handle branch selection change from dropdown"""
        selected_index = dropdown.get_selected()
        branches = self.current_config.get("branches", [])
        
        if 0 <= selected_index < len(branches):
            branch = branches[selected_index]
            if branch != self.current_branch:
                self.pending_changes["branch"] = branch
            elif "branch" in self.pending_changes:
                del self.pending_changes["branch"]
            self.update_apply_button()
            
    def on_gpu_changed(self, dropdown, param):
        """Handle GPU selection change"""
        gpu_map = {0: "AMD", 1: "NVIDIA", 2: "Intel"}
        selected_gpu = gpu_map[dropdown.get_selected()]
        
        if selected_gpu != self.current_gpu:
            self.pending_changes["gpu"] = selected_gpu
        elif "gpu" in self.pending_changes:
            del self.pending_changes["gpu"]
        self.update_apply_button()
        
    def update_apply_button(self):
        """Update apply button state"""
        has_changes = len(self.pending_changes) > 0
        self.apply_button.set_sensitive(has_changes)
        
        # Update status text
        if has_changes:
            count = len(self.pending_changes)
            self.status_bar.set_text(f"{count} pending change{'s' if count > 1 else ''}")
        else:
            self.status_bar.set_text("Ready")
        
    def generate_rebase_url(self):
        """Generate the rebase URL based on pending changes"""
        if not self.current_config or not self.current_variant:
            return None
            
        # Start with current variant
        target_variant = self.current_variant
        variant_info = self.current_config["variants"][target_variant]
        
        # Apply game mode change
        if self.pending_changes.get("gamemode"):
            gamemode_target = variant_info.get("gamemode_target")
            if gamemode_target:
                target_variant = gamemode_target
                variant_info = self.current_config["variants"][target_variant]
                
        # Apply DX mode change
        if self.pending_changes.get("dx_mode"):
            dx_target = variant_info.get("dx_target")
            if dx_target:
                target_variant = dx_target
                variant_info = self.current_config["variants"][target_variant]
                
        # Build base URL - start fresh from config base
        base_url = self.current_config["base_url"]
        
        # For Bazzite, handle the complex variant naming
        if "bazzite" in base_url:
            gpu = self.pending_changes.get("gpu", self.current_gpu)
            
            # Debug output
            print(f"  - Target variant: {target_variant}")
            print(f"  - GPU: {gpu}")
            
            # Map target variant to URL suffix
            variant_to_suffix = {
                "bazzite": "",
                "bazzite-nvidia": "-nvidia",
                "bazzite-gnome": "-gnome",
                "bazzite-gnome-nvidia": "-gnome-nvidia",
                "bazzite-deck": "-deck",
                "bazzite-deck-nvidia": "-deck-nvidia",
                "bazzite-deck-gnome": "-deck-gnome",
                "bazzite-asus": "-asus",
                "bazzite-dx": "-dx",
                "bazzite-dx-nvidia": "-dx-nvidia",
                "bazzite-dx-gnome": "-dx-gnome",
                "bazzite-dx-nvidia-gnome": "-dx-nvidia-gnome",
            }
            
            # Get the base suffix for the variant
            suffix = variant_to_suffix.get(target_variant, "")
            
            # Apply GPU override if switching GPU
            if gpu == "NVIDIA" and "-nvidia" not in suffix:
                # Need to add nvidia to the variant
                if suffix == "-deck-gnome":
                    suffix = "-deck-nvidia-gnome"
                elif suffix == "-deck":
                    suffix = "-deck-nvidia"
                elif suffix == "-gnome":
                    suffix = "-gnome-nvidia"
                elif suffix == "-dx-gnome":
                    suffix = "-dx-nvidia-gnome"
                elif suffix == "-dx":
                    suffix = "-dx-nvidia"
                elif suffix == "":
                    suffix = "-nvidia"
            elif gpu == "AMD" and "-nvidia" in suffix:
                # Need to remove nvidia from the variant
                suffix = suffix.replace("-nvidia", "")
                
            base_url += suffix
            print(f"  - Final suffix: {suffix}")
            print(f"  - Full URL: {base_url}")
            
        elif "bluefin" in base_url:
            if target_variant == "bluefin-dx":
                base_url += "-dx"
            # Add GPU suffix for bluefin
            gpu = self.pending_changes.get("gpu", self.current_gpu)
            if variant_info.get("gpu_variants") and gpu in variant_info["gpu_variants"]:
                gpu_suffix = variant_info["gpu_variants"][gpu]
                if gpu_suffix:
                    base_url += gpu_suffix
                    
        elif "aurora" in base_url:
            if target_variant == "aurora-dx":
                base_url += "-dx"
            # Add GPU suffix for aurora
            gpu = self.pending_changes.get("gpu", self.current_gpu)
            if variant_info.get("gpu_variants") and gpu in variant_info["gpu_variants"]:
                gpu_suffix = variant_info["gpu_variants"][gpu]
                if gpu_suffix:
                    base_url += gpu_suffix
                
        # Add branch
        branch = self.pending_changes.get("branch", self.current_branch)
        base_url += f":{branch}"
        
        print(f"  - Current variant: {self.current_variant}")
        print(f"  - Target variant: {target_variant}")
        print(f"  - GPU: {gpu}")
        print(f"  - Branch: {branch}")
        
        return base_url
        
    def on_apply_clicked(self, button):
        """Handle apply button click"""
        # Kill any running update process before applying changes
        if self.update_process:
            self.cleanup_update_process()
            
        # Disable the apply button immediately
        button.set_sensitive(False)
        self.status_bar.set_text("Preparing changes...")
        
        # Check if we have changes that need rebase
        needs_rebase = any(key in self.pending_changes for key in ["gamemode", "dx_mode", "branch", "gpu"])
        
        if needs_rebase:
            rebase_url = self.generate_rebase_url()
            
            if not rebase_url:
                self.show_error("Unable to generate rebase URL")
                button.set_sensitive(True)
                self.status_bar.set_text("Ready")
                return
        else:
            rebase_url = None
            
        # Build change summary
        changes = []
        if self.pending_changes.get("gamemode"):
            changes.append("• Enable Game Mode")
        if self.pending_changes.get("dx_mode"):
            changes.append("• Enable Developer Experience (DX)")
        if "branch" in self.pending_changes:
            changes.append(f"• Switch to {self.pending_changes['branch']} branch")
        if "gpu" in self.pending_changes:
            changes.append(f"• Switch to {self.pending_changes['gpu']} GPU variant")
            
        # Use simple Adw.MessageDialog for confirmation
        dialog = Adw.MessageDialog()
        dialog.set_transient_for(self)
        dialog.set_title("Apply Configuration Changes?")
        
        if rebase_url:
            body_text = (
                f"This will apply the following changes:\n\n" + "\n".join(changes) + 
                f"\n\nTarget image: {rebase_url}\n\n"
                "You will need to reboot for changes to take effect."
            )
        else:
            body_text = (
                f"This will apply the following changes:\n\n" + "\n".join(changes) + 
                "\n\nThese changes will take effect immediately."
            )
            
        dialog.set_body(body_text)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("apply", "Apply")
        dialog.set_default_response("apply")
        dialog.set_close_response("cancel")
        
        dialog.connect("response", self.on_apply_dialog_response, rebase_url)
        dialog.present()
        
    def on_apply_dialog_response(self, dialog, response, rebase_url):
        """Handle apply dialog response"""
        dialog.close()
        
        if response == "apply":
            # Update status and show progress immediately
            self.status_bar.set_text("Applying changes...")
            
            if rebase_url:
                # Execute rebase
                self.execute_rebase(rebase_url)
        else:
            # Re-enable button if user cancelled
            self.apply_button.set_sensitive(True)
            self.status_bar.set_text("No changes made - ready when you are!")
            
    def execute_rebase(self, image_url):
        """Execute the rebase operation"""
        # Force switch to progress view
        self.stack.set_visible_child_name("progress")
        
        # Force UI update - ensure view switch happens
        # In GTK4, we don't have events_pending/main_iteration
        # The stack switch should happen immediately
        
        self.spinner.start()
        self.cancel_button.set_sensitive(True)
        self.back_button.set_visible(False)
        
        # Reset progress
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.status_label.set_text("")
        
        # Hide log by default
        self.log_frame.set_visible(False)
        self.toggle_log_button.set_label("Show Details")
        
        # Set flag to indicate we're doing a rebase (not system update)
        self.is_system_update = False
        
        # Clear log
        self.log_buffer.set_text("")
        
        # Update progress label
        self.progress_label.set_text(f"Applying configuration changes...")
        
        
        def append_log_line(line):
            """Append a line to the log view"""
            def add_line():
                # Use the main append_log_line method which includes progress parsing
                self.append_log_line(line)
                return False
            
            GLib.idle_add(add_line)
        
        # Add initial log lines
        append_log_line(f"=== Applying Configuration Changes ===")
        append_log_line(f"Target image: {image_url}")
        append_log_line("="*60)
        append_log_line("")
        append_log_line("Starting rebase operation...")
        append_log_line("")
        
        def run_rebase():
            """Run rebase in background thread"""
            print("DEBUG: Starting rebase thread")
            # First run cleanup
            append_log_line("Cleaning up any pending deployments...")
            try:
                if 'FLATPAK_ID' in os.environ:
                    cleanup_cmd = ["flatpak-spawn", "--host", "rpm-ostree", "cleanup", "-p"]
                else:
                    cleanup_cmd = ["rpm-ostree", "cleanup", "-p"]
                
                subprocess.run(cleanup_cmd, capture_output=True, text=True)
                append_log_line("Cleanup complete")
                append_log_line("")
            except Exception as e:
                append_log_line(f"Cleanup warning: {e}")
            
            # Now run the rebase
            append_log_line("Executing rebase command...")
            append_log_line(f"Command: rpm-ostree rebase {image_url}")
            append_log_line("")
            
            print(f"DEBUG: Calling command_executor.execute_rebase({image_url})")
            result = self.command_executor.execute_rebase(image_url, append_log_line)
            print(f"DEBUG: Rebase result: {result}")
            GLib.idle_add(self.rebase_complete, result)
        
        # Start rebase in background thread
        thread = threading.Thread(target=run_rebase, daemon=True)
        thread.start()
        
    def on_cancel_clicked(self, button):
        """Handle cancel button click"""
        # Append cancellation message
        self.append_log_line("\n" + "="*60)
        self.append_log_line("⚠️  Cancelling operation...")
        button.set_sensitive(False)
        
        # If this is a system update, kill the update process
        if self.is_system_update and self.update_process:
            self.cleanup_update_process()
            # Update UI to show cancellation
            self.progress_label.set_text("Update cancelled")
            self.spinner.stop()
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("")
            self.status_label.set_text("You can safely go back to configuration.")
            self.cancel_button.set_visible(False)
            self.back_button.set_visible(True)
        else:
            # Cancel the current command execution
            self.command_executor.cancel_current_execution()
            
            # Also run rpm-ostree cancel to cancel the transaction
            try:
                subprocess.run(["flatpak-spawn", "--host", "rpm-ostree", "cancel"], 
                             capture_output=True, text=True)
                self.append_log_line("✅ Operation cancelled successfully")
                self.append_log_line("\nYou can safely go back to make different changes.")
            except Exception as e:
                self.append_log_line(f"⚠️  Note: {e}")
                self.append_log_line("The operation may have already completed or been cancelled.")
            
            # Update UI to show cancellation was successful
            self.progress_label.set_text("Operation cancelled")
            self.spinner.stop()
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("")
            self.status_label.set_text("You can safely go back to make different changes.")
            self.cancel_button.set_visible(False)
            self.back_button.set_visible(True)
        
    def rebase_complete(self, result):
        """Handle rebase completion"""
        self.spinner.stop()
        self.cancel_button.set_visible(False)
        self.back_button.set_visible(True)
        
        if result['success']:
            self.progress_label.set_text("Configuration changes applied successfully!")
            
            # Add success message to log
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, "\n" + "="*60 + "\n")
            self.log_buffer.insert(self.log_buffer.get_end_iter(), "✅ Configuration changes applied successfully!\n")
            self.log_buffer.insert(self.log_buffer.get_end_iter(), "Please reboot your system for the changes to take effect.\n")
            
            # Clear pending changes
            self.pending_changes.clear()
            self.update_apply_button()
            
            # Show success dialog
            dialog = Adw.MessageDialog()
            dialog.set_transient_for(self)
            dialog.set_title("Changes Applied")
            dialog.set_body(
                "Configuration changes have been applied successfully!\n\n"
                "Please reboot your system for the changes to take effect."
            )
            dialog.add_response("ok", "OK")
            dialog.set_default_response("ok")
            dialog.present()
        else:
            self.progress_label.set_text("Configuration change failed")
            error_msg = result.get('error', 'Unknown error')
            
            # Determine if it was cancelled or failed
            if "cancelled" in error_msg.lower() or "cancel" in error_msg.lower():
                self.status_label.set_text("The operation was cancelled.")
                # Don't show an error dialog for cancellation - the UI already shows the status
            else:
                # For actual errors, show a simplified message
                self.status_label.set_text("The configuration change could not be completed.")
                
                # Show simplified error dialog
                dialog = Adw.MessageDialog()
                dialog.set_transient_for(self)
                dialog.set_title("Configuration Change Failed")
                dialog.set_body(
                    "The configuration change could not be completed.\n\n"
                    "This may be due to network issues or other system constraints."
                )
                dialog.add_response("ok", "OK")
                dialog.set_default_response("ok")
                dialog.add_css_class("error")
                dialog.present()
            
    def on_back_clicked(self, button):
        """Handle back button click"""
        # Switch back to config view
        self.stack.set_visible_child_name("config")
        
        # Reset system update flag
        self.is_system_update = False
            
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
        
            
    def on_toggle_log(self, button):
        """Toggle log view visibility"""
        if self.log_frame.get_visible():
            self.log_frame.set_visible(False)
            button.set_label("Show Details")
            # Let window shrink back to natural size
            self.set_default_size(-1, -1)
        else:
            self.log_frame.set_visible(True)
            button.set_label("Hide Details")
            # Expand window to show log
            self.set_default_size(800, 700)
    
    def _parse_uupd_json(self, line):
        """Parse JSON output from uupd and update progress"""
        try:
            # Try to parse as JSON
            data = json.loads(line)
            
            # Check if it's a progress update
            if isinstance(data, dict):
                # Look for overall progress percentage
                if "overall" in data:
                    overall = int(data["overall"])
                    self.progress_bar.set_fraction(overall / 100.0)
                    self.progress_bar.set_text(f"{overall}%")
                
                # Update status from description
                if "description" in data:
                    desc = data["description"]
                    self.status_label.set_text(desc)
                
                # Log message if present
                if "msg" in data:
                    msg = data["msg"]
                    # Return the message to be logged
                    return msg
                
                # Alternative progress field
                if "progress" in data and isinstance(data["progress"], (int, float)):
                    # This might be step number, not percentage
                    pass
                
                # Step progress (0.0 to 1.0)
                if "step_progress" in data:
                    step_prog = float(data["step_progress"])
                    if step_prog > 0:
                        # Use step progress if no overall progress
                        if "overall" not in data:
                            percent = int(step_prog * 100)
                            self.progress_bar.set_fraction(step_prog)
                            self.progress_bar.set_text(f"{percent}%")
                
                # Return empty string to suppress JSON from log
                return ""
            
            # If it's a simple string in JSON, return it
            if isinstance(data, str):
                return data
                
        except json.JSONDecodeError:
            # Not JSON, return as-is
            pass
        except Exception as e:
            print(f"[DEBUG] Error parsing JSON: {e}")
        
        return None
    
    def _parse_progress_line(self, line):
        """Parse progress information from log line"""
        import re
        
        # Look for ostree chunk fetching (e.g., "[0/48] Fetching ostree chunk 180fde2153970ba7d4a (26.4 MB)...done")
        chunk_match = re.search(r'\[(\d+)/(\d+)\]\s*Fetching ostree chunk', line)
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
        
        # Look for simple percentage patterns (e.g., "95%", "Progress: 50%")
        simple_percent = re.search(r'(?:progress[:\s]*)?(\d+)\s*%', line, re.IGNORECASE)
        if simple_percent:
            percent = int(simple_percent.group(1))
            self.progress_bar.set_fraction(percent / 100.0)
            self.progress_bar.set_text(f"{percent}%")
            return
        
        # Look for uupd's specific progress format - "overall" is the percentage
        uupd_overall = re.search(r'overall:\s*(\d+)', line)
        if uupd_overall:
            overall = int(uupd_overall.group(1))
            self.progress_bar.set_fraction(overall / 100.0)
            self.progress_bar.set_text(f"{overall}%")
            return
            
        uupd_step_progress = re.search(r'step_progress:\s*(\d+(?:\.\d+)?)', line)
        if uupd_step_progress:
            step_progress = float(uupd_step_progress.group(1))
            # step_progress appears to be 0-1 range
            percent = int(step_progress * 100)
            self.progress_bar.set_fraction(step_progress)
            self.progress_bar.set_text(f"{percent}%")
            return
        
        # Update status based on uupd description
        if "description:" in line:
            desc_match = re.search(r'description:\s*(.+)', line)
            if desc_match:
                description = desc_match.group(1).strip()
                self.status_label.set_text(description)
        
        # Look for specific stages
        if "Scanning metadata" in line:
            self.status_label.set_text("Scanning metadata...")
        elif "Pulling manifest" in line:
            self.status_label.set_text("Pulling manifest...")
        elif "Fetching ostree chunk" in line and "done" in line:
            # Individual chunk completed, don't change status
            pass
        elif "Importing" in line:
            self.status_label.set_text("Importing layers...")
        elif "Checking out tree" in line:
            self.status_label.set_text("Checking out files...")
            # When we start checking out the tree, we're essentially done downloading
            # Set progress to 100%
            if "done" in line:
                self.progress_bar.set_fraction(1.0)
                self.progress_bar.set_text("100%")
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
        # uupd-specific progress patterns
        elif "Checking for updates" in line.lower():
            self.status_label.set_text("Checking for updates...")
        elif "System update" in line and "available" in line:
            self.status_label.set_text("System update available")
        elif "Updating system" in line.lower():
            self.status_label.set_text("Updating system...")
            # Estimate progress based on stage
            self.progress_bar.set_fraction(0.3)
            self.progress_bar.set_text("30%")
        elif "Downloading" in line and ("MB" in line or "GB" in line or "KB" in line):
            self.status_label.set_text("Downloading updates...")
            # Look for download progress in format like "10.5MB/50MB"
            download_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]B)\s*/\s*(\d+(?:\.\d+)?)\s*([KMG]B)', line)
            if download_match:
                current_val = float(download_match.group(1))
                current_unit = download_match.group(2)
                total_val = float(download_match.group(3))
                total_unit = download_match.group(4)
                
                # Convert to same unit
                if current_unit == total_unit:
                    fraction = current_val / total_val
                    percent = int(fraction * 100)
                    self.progress_bar.set_fraction(fraction)
                    self.progress_bar.set_text(f"{percent}%")
        elif "Installing" in line and "update" in line.lower():
            self.status_label.set_text("Installing updates...")
            # Estimate 60% when installing
            self.progress_bar.set_fraction(0.6)
            self.progress_bar.set_text("60%")
        elif "Updating flatpaks" in line.lower() or "flatpak" in line.lower() and "updat" in line.lower():
            self.status_label.set_text("Updating Flatpak applications...")
            # Estimate 70% for flatpaks
            self.progress_bar.set_fraction(0.7)
            self.progress_bar.set_text("70%")
        elif "Updating containers" in line.lower() or "container" in line.lower() and "updat" in line.lower():
            self.status_label.set_text("Updating containers...")
            # Estimate 80% for containers
            self.progress_bar.set_fraction(0.8)
            self.progress_bar.set_text("80%")
        elif "brew" in line.lower() and "updat" in line.lower():
            self.status_label.set_text("Updating Brew packages...")
            # Estimate 85% for brew
            self.progress_bar.set_fraction(0.85)
            self.progress_bar.set_text("85%")
        elif "distrobox" in line.lower() and "updat" in line.lower():
            self.status_label.set_text("Updating Distrobox containers...")
            # Estimate 90% for distrobox
            self.progress_bar.set_fraction(0.9)
            self.progress_bar.set_text("90%")
        elif "Starting" in line and "update" in line.lower():
            self.status_label.set_text("Starting update process...")
            # Starting = 10%
            self.progress_bar.set_fraction(0.1)
            self.progress_bar.set_text("10%")
        elif "Completed" in line.lower() or "Complete" in line:
            self.status_label.set_text("Update complete")
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("100%")
        elif "Failed" in line or "Error" in line:
            self.status_label.set_text("Update failed - check logs")
            
    def append_log_line(self, line):
        """Append a line to the log buffer and update progress"""
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, line + "\n")
        
        # Auto-scroll to bottom
        mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_mark_onscreen(mark)
        self.log_buffer.delete_mark(mark)
        
        # Parse progress information
        self._parse_progress_line(line)
        
    def run_system_update(self):
        """Run system update using ujust update or appropriate command"""
        def append_log(message):
            GLib.idle_add(lambda: self.append_log_line(message))
            
        def update_ui(progress_text=None, finished=False, success=True, updates_found=False):
            def ui_update():
                if progress_text:
                    self.progress_label.set_text(progress_text)
                    
                if finished:
                    self.spinner.stop()
                    
                    if success and updates_found:
                        # Show reboot/close/back buttons when updates were found
                        self.cancel_button.set_visible(False)
                        self.back_button.set_visible(True)
                        self.reboot_button.set_visible(True)
                        self.close_button.set_visible(True)
                    else:
                        # Show only back button if no updates or failed
                        self.cancel_button.set_visible(False)
                        self.back_button.set_visible(True)
                        self.reboot_button.set_visible(False)
                        self.close_button.set_visible(False)
                    
                    # Force UI refresh
                    self.button_box.queue_draw()
                    
                    # Re-enable update button
                    self.update_button.set_sensitive(True)
                    self.update_button.set_label("Check for Updates")
                    
                return False
                
            GLib.idle_add(ui_update)
            
        append_log("Starting system update...")
        append_log("=" * 50)
        
        # Find first available update tool
        selected_tool = None
        for tool in UPDATE_TOOLS:
            check_cmd = ["flatpak-spawn", "--host", "which", tool["check_command"]]
            check_result = subprocess.run(check_cmd, capture_output=True)
            
            if check_result.returncode == 0:
                selected_tool = tool
                append_log(f"Found {tool['name']}")
                break
            else:
                append_log(f"{tool['name']} not found, checking next tool...")
        
        if not selected_tool:
            # No update tools available
            append_log("✗ No update tool found (uupd, ujust, bootc, or rpm-ostree)")
            append_log("Please ensure at least one update tool is installed on your system.")
            update_ui("No update tool available", finished=True, success=False)
            return
        
        # Use the selected tool
        append_log(f"Using {selected_tool['name']} for system update...")
        update_cmd = selected_tool["command"]
        is_json_output = selected_tool.get("json_output", False)
        
        # Create JSON-aware logging function
        def append_log_json_aware(line):
            if is_json_output and selected_tool["name"] == "uupd":
                # Try to parse as JSON first
                json_result = self._parse_uupd_json(line)
                if json_result is not None:
                    if json_result:  # Only log if there's a message
                        append_log(json_result)
                else:
                    # JSON parsing failed, log as-is
                    append_log(line)
            else:
                # Not JSON output, log normally
                append_log(line)
            
            # Debug logging
            if line and len(output_lines) < 20:
                print(f"[DEBUG] uupd output: {line[:200]}")
        
        try:
                
            # Run the update command
            self.update_process = subprocess.Popen(
                update_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create new process group for proper cleanup
            )
            
            # Track if we need to show action buttons
            show_action_buttons = False
            output_lines = []
            start_time = datetime.now()
            timeout_triggered = False
            
            # Read output line by line with timeout check
            while True:
                if self.update_process is None:
                    # Process was cancelled
                    append_log("\n[Update cancelled by user]")
                    update_ui("Update cancelled", finished=True, success=False, updates_found=False)
                    return
                    
                line = self.update_process.stdout.readline()
                if not line:
                    # Check if process is still running
                    if self.update_process.poll() is not None:
                        break
                    # Check for 30 second timeout
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > 30 and not timeout_triggered:
                        append_log("\n[Auto-showing action buttons after 30 seconds]")
                        show_action_buttons = True
                        timeout_triggered = True
                    # Small sleep to prevent busy waiting
                    import time
                    time.sleep(0.1)
                    continue
                    
                line_stripped = line.rstrip()
                append_log_json_aware(line_stripped)
                output_lines.append(line_stripped)
                
                # Check for reboot indicators from selected tool
                for indicator in selected_tool["reboot_indicators"]:
                    if indicator in line_stripped:
                        append_log(f"[Reboot prompt detected: '{indicator}' - showing action buttons]")
                        show_action_buttons = True
                        # Immediately show buttons when detected
                        update_ui("Updates staged - Action required", finished=True, success=True, updates_found=True)
                        break
                    
            if self.update_process:
                self.update_process.wait()
                returncode = self.update_process.returncode
            else:
                # Process was cancelled
                returncode = -1
            
            if returncode == 0:
                append_log("=" * 50)
                if show_action_buttons:
                    append_log("✓ System update completed successfully!")
                    append_log("Updates have been staged. Please choose an action:")
                    update_ui("Updates staged - Action required", finished=True, success=True, updates_found=True)
                else:
                    append_log("✓ System update check completed!")
                    update_ui("Update check complete", finished=True, success=True, updates_found=False)
            else:
                append_log("=" * 50)
                append_log("✗ System update failed or was cancelled")
                update_ui("Update failed", finished=True, success=False, updates_found=False)
                
        except Exception as e:
            append_log(f"✗ Error running system update: {str(e)}")
            update_ui("Update error", finished=True, success=False, updates_found=False)
        finally:
            # Clean up process reference
            self.update_process = None
    
    def on_reboot_clicked(self, button):
        """Handle reboot button click"""
        # Use systemctl reboot through flatpak-spawn
        try:
            subprocess.run(["flatpak-spawn", "--host", "systemctl", "reboot"], check=True)
        except subprocess.CalledProcessError as e:
            # If systemctl fails, try loginctl
            try:
                subprocess.run(["flatpak-spawn", "--host", "loginctl", "reboot"], check=True)
            except subprocess.CalledProcessError:
                # Show error dialog
                error_dialog = Adw.MessageDialog(
                    heading="Reboot Failed",
                    body="Unable to reboot the system. Please reboot manually.",
                    transient_for=self
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
    
    def on_back_clicked(self, button):
        """Return to configuration view"""
        # Kill any running update process when leaving the view
        if self.update_process:
            self.cleanup_update_process()
            
        # Reset button visibility
        self.cancel_button.set_visible(True)
        self.back_button.set_visible(False)
        self.reboot_button.set_visible(False)
        self.close_button.set_visible(False)
        
        # Hide log if it's visible and reset window size
        if self.log_frame.get_visible():
            self.log_frame.set_visible(False)
            self.toggle_log_button.set_label("Show Details")
        
        # Reset window to natural size for config view
        self.set_default_size(-1, -1)
        
        # Switch back to config view
        self.stack.set_visible_child_name("config")
        
        # Clear the system update flag
        self.is_system_update = False
    
    def cleanup_update_process(self):
        """Properly terminate the update process and all child processes"""
        if self.update_process:
            try:
                # Kill the entire process group to ensure topgrade and other children are terminated
                os.killpg(os.getpgid(self.update_process.pid), signal.SIGTERM)
                # Give processes time to terminate gracefully
                import time
                time.sleep(0.5)
                # Force kill if still running
                if self.update_process.poll() is None:
                    os.killpg(os.getpgid(self.update_process.pid), signal.SIGKILL)
            except Exception as e:
                print(f"Error cleaning up update process: {e}")
                # Try direct kill as fallback
                try:
                    self.update_process.kill()
                except:
                    pass
            finally:
                self.update_process = None
                
        # Also kill any orphaned topgrade processes
        self.kill_orphaned_topgrade()
    
    def cleanup_on_shutdown(self):
        """Clean up when application is closing"""
        # Clean up any running update process
        if self.update_process:
            self.cleanup_update_process()
        # Also kill any orphaned topgrade processes
        self.kill_orphaned_topgrade()
    
    def kill_orphaned_topgrade(self):
        """Kill any topgrade processes that might be running"""
        try:
            # Use pkill to kill topgrade processes
            subprocess.run(["flatpak-spawn", "--host", "pkill", "-f", "topgrade"], 
                         capture_output=True, timeout=2)
        except:
            # If pkill fails, try killall
            try:
                subprocess.run(["flatpak-spawn", "--host", "killall", "topgrade"], 
                             capture_output=True, timeout=2)
            except:
                pass
        
        
def main():
    """Main entry point"""
    app = AtomicOSManager()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())