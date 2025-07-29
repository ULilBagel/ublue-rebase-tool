#!/usr/bin/env python3
"""
Universal Blue Image Management GUI
A modern GTK4/libadwaita application for managing Universal Blue custom images
Following Universal Blue development best practices and community standards
"""

import os
import sys
import json
import subprocess
import threading

# Test GTK imports first
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    gi.require_version('WebKit', '6.0')
    from gi.repository import Gtk, Adw, WebKit, GLib, Gio
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1 gir1.2-webkit-6.0")
    sys.exit(1)


class UBlueImageAPI:
    """Backend API following Universal Blue portal integration patterns"""
    
    def __init__(self):
        self.current_operation = None
        self.webview = None
        
    def set_webview(self, webview):
        """Set webview reference for JavaScript communication"""
        self.webview = webview
        
    def execute_js(self, script):
        """Execute JavaScript in webview with error handling"""
        if self.webview:
            try:
                # evaluate_javascript was removed from WebKitGTK 4.0; use run_javascript
                self.webview.run_javascript(script, None, None, None)
            except Exception as e:
                print(f"JavaScript execution error: {e}")
    
    def get_system_status(self):
        """Get current deployment status - supports both real and demo modes"""
        try:
            # Try to get real rpm-ostree status
            result = subprocess.run(
                ['rpm-ostree', 'status', '--json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                current_deployment = None
                
                for deployment in status_data.get('deployments', []):
                    if deployment.get('booted', False):
                        current_deployment = deployment
                        break
                
                if current_deployment:
                    status = {
                        'success': True,
                        'currentImage': current_deployment.get('origin', 'Unknown'),
                        'osVersion': current_deployment.get('version', 'Unknown'),
                        'deploymentId': current_deployment.get('checksum', '')[:8],
                        'isUniversalBlue': 'ublue-os' in current_deployment.get('origin', ''),
                        'type': 'real'
                    }
                else:
                    status = {'success': False, 'error': 'No current deployment found'}
            else:
                # Fallback to demo data
                status = {
                    'success': True,
                    'currentImage': 'Demo: Not on rpm-ostree system',
                    'osVersion': 'Testing Environment',
                    'deploymentId': 'demo123',
                    'isUniversalBlue': False,
                    'type': 'demo'
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # Demo data for testing
            status = {
                'success': True,
                'currentImage': 'Demo: Testing Environment',
                'osVersion': 'Ubuntu 24.04 LTS (Testing)',
                'deploymentId': 'test456',
                'isUniversalBlue': False,
                'type': 'demo'
            }
        
        # Update web interface
        js_script = f"""
        if (typeof updateSystemStatus === 'function') {{
            updateSystemStatus({json.dumps(status)});
        }}
        """
        GLib.idle_add(self.execute_js, js_script)
        return status
    
    def guide_rebase(self, image_url, options=""):
        """Guide user through proper rebasing procedure - UB guidance pattern"""
        instructions = {
            'success': True,
            'action': 'guide',
            'title': 'Universal Blue Rebase Instructions',
            'instructions': [
                "⚠️  IMPORTANT: This application provides guidance only",
                "1. Open a terminal application",
                f"2. Run: rpm-ostree rebase {image_url}",
                "3. Wait for the operation to complete", 
                "4. Reboot your system when prompted",
                "5. Use this tool to verify the new deployment"
            ],
            'command': f"rpm-ostree rebase {image_url}",
            'imageUrl': image_url,
            'safetyNote': 'Following Universal Blue guidance patterns - manual execution required for safety'
        }
        
        js_script = f"""
        if (typeof showRebaseInstructions === 'function') {{
            showRebaseInstructions({json.dumps(instructions)});
        }}
        """
        GLib.idle_add(self.execute_js, js_script)
        return instructions
    
    def get_available_images(self):
        """Get list of available Universal Blue images"""
        images = [
            {
                'name': 'Bluefin (GNOME)',
                'url': 'ghcr.io/ublue-os/bluefin:latest',
                'description': 'Developer-focused GNOME desktop with modern tooling'
            },
            {
                'name': 'Aurora (KDE)',
                'url': 'ghcr.io/ublue-os/aurora:latest', 
                'description': 'Polished KDE Plasma desktop experience'
            },
            {
                'name': 'Bazzite (Gaming)',
                'url': 'ghcr.io/ublue-os/bazzite:latest',
                'description': 'Gaming-optimized desktop with Steam and drivers'
            },
            {
                'name': 'Silverblue Main',
                'url': 'ghcr.io/ublue-os/silverblue-main:latest',
                'description': 'Clean GNOME experience based on Fedora Silverblue'
            }
        ]
        
        result = {'success': True, 'images': images}
        js_script = f"""
        if (typeof showAvailableImages === 'function') {{
            showAvailableImages({json.dumps(result)});
        }}
        """
        GLib.idle_add(self.execute_js, js_script)
        return result


class UBlueImageWindow(Adw.ApplicationWindow):
    """Main application window using libadwaita widgets per UB guide"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Universal Blue Image Manager")
        self.set_default_size(1200, 800)
        
        # Create API instance
        self.api = UBlueImageAPI()
        
        # Set up AdwHeaderBar as recommended
        self.header_bar = Adw.HeaderBar()
        self.set_titlebar(self.header_bar)
        
        # Add header bar controls
        self.create_header_controls()
        
        # Create main content with AdwToastOverlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        
        # Create content
        self.create_content()
        
        # Load system status on startup
        GLib.timeout_add(1000, self.load_initial_status)
        
    def create_header_controls(self):
        """Create header bar controls following UB patterns"""
        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name("view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Refresh System Status")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        self.header_bar.pack_start(refresh_btn)
        
        # Menu button
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text("Application Menu")
        self.header_bar.pack_end(menu_btn)
        
        # Create menu
        menu = Gio.Menu()
        menu.append("About", "app.about")
        menu_btn.set_menu_model(menu)
    
    def create_content(self):
        """Create main content area"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.set_spacing(0)
        
        # Create sidebar
        sidebar = self.create_sidebar()
        main_box.append(sidebar)
        
        # Create separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(separator)
        
        # Create main content area with web interface
        main_content = self.create_main_content()
        main_box.append(main_content)
        
        self.toast_overlay.set_child(main_box)
    
    def create_sidebar(self):
        """Create sidebar with system information using AdwActionRows"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(350, -1)
        sidebar_box.add_css_class("sidebar")
        
        # Add some padding
        sidebar_box.set_margin_top(12)
        sidebar_box.set_margin_bottom(12)
        sidebar_box.set_margin_start(12)
        sidebar_box.set_margin_end(12)
        
        # System status group
        status_group = Adw.PreferencesGroup()
        status_group.set_title("System Status")
        status_group.set_description("Current deployment information")
        
        # Current image row
        self.current_image_row = Adw.ActionRow()
        self.current_image_row.set_title("Current Image")
        self.current_image_row.set_subtitle("Loading...")
        status_group.add(self.current_image_row)
        
        # OS version row
        self.os_version_row = Adw.ActionRow()
        self.os_version_row.set_title("OS Version")
        self.os_version_row.set_subtitle("Loading...")
        status_group.add(self.os_version_row)
        
        # Deployment ID row
        self.deployment_row = Adw.ActionRow()
        self.deployment_row.set_title("Deployment")
        self.deployment_row.set_subtitle("Loading...")
        status_group.add(self.deployment_row)
        
        sidebar_box.append(status_group)
        
        # Available images group
        images_group = Adw.PreferencesGroup()
        images_group.set_title("Available Images")
        images_group.set_description("Universal Blue image variants")
        
        # Add image options
        images = self.api.get_available_images()['images']
        for image in images:
            image_row = Adw.ActionRow()
            image_row.set_title(image['name'])
            image_row.set_subtitle(image['description'])
            
            # Add guide button
            guide_btn = Gtk.Button()
            guide_btn.set_label("Guide")
            guide_btn.add_css_class("suggested-action")
            guide_btn.connect("clicked", lambda btn, url=image['url']: self.on_guide_clicked(url))
            image_row.add_suffix(guide_btn)
            
            images_group.add(image_row)
        
        sidebar_box.append(images_group)
        
        return sidebar_box
    
    def create_main_content(self):
        """Create main content area with web interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_hexpand(True)
        
        # Create web view for hybrid interface
        self.webview = WebKit.WebView()
        self.api.set_webview(self.webview)
        
        # Configure web view
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(True)
        settings.set_enable_write_console_messages_to_stdout(True)
        
        # Set up JavaScript bridge
        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("ublueAPI")
        content_manager.connect("script-message-received::ublueAPI", self.on_script_message)
        
        # Inject API bridge
        self.inject_api_bridge()
        
        # Load web interface
        self.load_web_interface()
        
        main_box.append(self.webview)
        return main_box
    
    def inject_api_bridge(self):
        """Inject JavaScript API bridge following UB patterns"""
        api_bridge_script = """
        window.ublueImageAPI = {
            getSystemStatus: function() {
                webkit.messageHandlers.ublueAPI.postMessage({method: 'get_system_status'});
            },
            guideRebase: function(imageUrl, options) {
                webkit.messageHandlers.ublueAPI.postMessage({
                    method: 'guide_rebase',
                    args: [imageUrl, options || '']
                });
            },
            getAvailableImages: function() {
                webkit.messageHandlers.ublueAPI.postMessage({method: 'get_available_images'});
            }
        };
        """
        
        script = WebKit.UserScript(
            api_bridge_script,
            WebKit.UserContentInjectedFrames.TOP_FRAME,
            WebKit.UserScriptInjectionTime.START,
            None,
            None
        )
        content_manager = self.webview.get_user_content_manager()
        content_manager.add_script(script)
    
    def load_web_interface(self):
        """Load web interface with proper path resolution"""
        html_file = self.get_html_file_path()
        if html_file and os.path.exists(html_file):
            self.webview.load_uri(f"file://{html_file}")
        else:
            self.load_fallback_interface()
    
    def get_html_file_path(self):
        """Get HTML file path with UB-compliant locations"""
        if os.environ.get('FLATPAK_ID'):
            return '/app/share/ublue-image-manager/index.html'
        else:
            # Check current directory and data directory
            current_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'web', 'index.html')
            if os.path.exists(current_dir):
                return os.path.abspath(current_dir)
            
            # Check if web directory exists in current working directory
            cwd_web = os.path.join(os.getcwd(), 'data', 'web', 'index.html')
            if os.path.exists(cwd_web):
                return os.path.abspath(cwd_web)
                
            return None
    
    def load_fallback_interface(self):
        """Load fallback interface with libadwaita styling"""
        fallback_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Universal Blue Image Manager</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: system-ui, -apple-system, sans-serif; 
                    background: #fafafa;
                    color: #2e3436;
                    padding: 20px;
                    line-height: 1.5;
                }
                .container { max-width: 800px; margin: 0 auto; }
                .card { 
                    background: white;
                    border: 1px solid #d5d5d5;
                    border-radius: 12px;
                    padding: 24px; 
                    margin: 16px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .header { 
                    font-size: 1.5em; 
                    font-weight: bold; 
                    margin-bottom: 16px;
                    color: #1a5fb4;
                }
                .button { 
                    background: #3584e4;
                    color: white;
                    border: none; 
                    border-radius: 6px;
                    padding: 8px 16px; 
                    margin: 4px;
                    cursor: pointer; 
                    font-weight: 500;
                    font-size: 14px;
                }
                .button:hover { background: #2379d1; }
                .warning { 
                    background: #fdf6e3;
                    color: #b58900;
                    padding: 12px; 
                    border-radius: 6px; 
                    margin: 8px 0;
                    border-left: 4px solid #f1c40f;
                }
                .info { 
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 12px; 
                    border-radius: 6px; 
                    margin: 8px 0;
                    border-left: 4px solid #2196f3;
                }
                .status { font-family: monospace; background: #f5f5f5; padding: 4px 8px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="header">🚀 Universal Blue Image Manager</div>
                    <p>Modern libadwaita-compliant interface for managing Universal Blue images</p>
                    
                    <div class="warning">
                        ⚠️ <strong>Universal Blue Guidance Pattern:</strong> This application follows UB best practices by providing guidance rather than direct system modifications.
                    </div>
                    
                    <button class="button" onclick="refreshStatus()">🔄 Refresh Status</button>
                    <button class="button" onclick="showImages()">📋 Show Available Images</button>
                </div>
                
                <div class="card">
                    <div class="header">📊 System Status</div>
                    <div id="systemStatus">
                        <p>Current Image: <span class="status" id="currentImage">Loading...</span></p>
                        <p>OS Version: <span class="status" id="osVersion">Loading...</span></p>
                        <p>Deployment: <span class="status" id="deploymentId">Loading...</span></p>
                    </div>
                </div>
                
                <div class="card" id="instructionsCard" style="display: none;">
                    <div class="header">📋 Instructions</div>
                    <div id="instructionsContent"></div>
                </div>
            </div>
            
            <script>
                function updateSystemStatus(status) {
                    document.getElementById('currentImage').textContent = status.currentImage;
                    document.getElementById('osVersion').textContent = status.osVersion;
                    document.getElementById('deploymentId').textContent = status.deploymentId;
                    
                    if (status.type === 'demo') {
                        document.getElementById('systemStatus').innerHTML += 
                            '<div class="info">ℹ️ Running in demo mode - not on an rpm-ostree system</div>';
                    } else if (status.isUniversalBlue) {
                        document.getElementById('systemStatus').innerHTML += 
                            '<div class="info">✅ Universal Blue system detected</div>';
                    }
                }
                
                function showRebaseInstructions(instructions) {
                    const card = document.getElementById('instructionsCard');
                    const content = document.getElementById('instructionsContent');
                    
                    content.innerHTML = `
                        <div class="warning">${instructions.safetyNote}</div>
                        <h3>${instructions.title}</h3>
                        <ol style="margin-left: 20px; margin-top: 12px;">
                            ${instructions.instructions.map(inst => `<li style="margin: 8px 0;">${inst}</li>`).join('')}
                        </ol>
                        <p style="margin-top: 12px;"><strong>Command:</strong> <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 4px;">${instructions.command}</code></p>
                    `;
                    
                    card.style.display = 'block';
                    card.scrollIntoView({ behavior: 'smooth' });
                }
                
                function refreshStatus() {
                    window.ublueImageAPI.getSystemStatus();
                }
                
                function showImages() {
                    window.ublueImageAPI.getAvailableImages();
                }
                
                // Initialize
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(refreshStatus, 500);
                });
            </script>
        </body>
        </html>
        """
        self.webview.load_html(fallback_html, None)
    
    def on_script_message(self, content_manager, message):
        """Handle JavaScript messages with proper error handling"""
        try:
            data = message.get_js_value().to_json()
            message_data = json.loads(data)
            
            method = message_data.get('method')
            args = message_data.get('args', [])
            
            if hasattr(self.api, method):
                def execute_api_call():
                    try:
                        func = getattr(self.api, method)
                        result = func(*args)
                        
                        # Show toast notification for operations
                        if result.get('success'):
                            if result.get('action') == 'guide':
                                toast = Adw.Toast.new("Instructions provided")
                            else:
                                toast = Adw.Toast.new("Operation completed")
                            self.toast_overlay.add_toast(toast)
                        else:
                            toast = Adw.Toast.new(f"Error: {result.get('error', 'Unknown error')}")
                            self.toast_overlay.add_toast(toast)
                            
                    except Exception as e:
                        error_toast = Adw.Toast.new(f"API Error: {str(e)}")
                        self.toast_overlay.add_toast(error_toast)
                
                threading.Thread(target=execute_api_call, daemon=True).start()
                
        except Exception as e:
            print(f"Error handling script message: {e}")
    
    def load_initial_status(self):
        """Load initial system status"""
        self.api.get_system_status()
        return False  # Don't repeat
    
    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.api.get_system_status()
        toast = Adw.Toast.new("Refreshing system status...")
        self.toast_overlay.add_toast(toast)
        
    def on_guide_clicked(self, image_url):
        """Handle guide button click from sidebar"""
        self.api.guide_rebase(image_url)


class UBlueImageApplication(Adw.Application):
    """Main application class following UB patterns"""
    
    def __init__(self):
        super().__init__(application_id="io.github.ublue.RebaseTool")
        self.create_actions()
    
    def create_actions(self):
        """Create application actions"""
        # About action  
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
    
    def do_activate(self):
        """Activate the application"""
        window = UBlueImageWindow(self)
        window.present()
    
    def on_about(self, action, param):
        """Show about dialog"""
        about = Adw.AboutWindow()
        about.set_application_name("Universal Blue Image Manager")
        about.set_application_icon("io.github.ublue.RebaseTool")
        about.set_version("2.0.0")
        about.set_developer_name("Universal Blue Community")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments("Modern GUI for managing Universal Blue custom images following UB best practices")
        about.set_website("https://github.com/universal-blue")
        about.present()


def main():
    """Main application entry point"""
    app = UBlueImageApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
