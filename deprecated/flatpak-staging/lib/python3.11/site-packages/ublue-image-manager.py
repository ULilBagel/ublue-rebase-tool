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

# Import new components for execution functionality
from command_executor import CommandExecutor
from deployment_manager import DeploymentManager
from progress_tracker import ProgressTracker
from history_manager import HistoryManager
from ui.confirmation_dialog import ConfirmationDialog


class UBlueImageAPI:
    """Backend API following Universal Blue portal integration patterns"""
    
    def __init__(self):
        self.current_operation = None
        self.webview = None
        self.window = None
        
        # Test mode support
        self._test_mode = False
        self._operation_complete = threading.Event()
        self._operation_result = None
        
        # Initialize new components for execution
        self.command_executor = CommandExecutor()
        self.deployment_manager = DeploymentManager()
        self.progress_tracker = ProgressTracker(self)
        self.history_manager = HistoryManager()
        
    def set_webview(self, webview):
        """Set webview reference for JavaScript communication"""
        self.webview = webview
        
    def set_window(self, window):
        """Set window reference for dialog display"""
        self.window = window
        
    def on_script_message(self, content_manager, message):
        """Proxy to window's on_script_message for testing"""
        if self.window and hasattr(self.window, 'on_script_message'):
            return self.window.on_script_message(content_manager, message)
        # Handle case where window isn't set (in tests)
        return self._handle_script_message_directly(content_manager, message)
        
    def execute_js(self, script):
        """Execute JavaScript in webview with error handling"""
        if self.webview:
            try:
                self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
            except Exception as e:
                print(f"JavaScript execution error: {e}")
    
    def _handle_script_message_directly(self, content_manager, message):
        """Handle script messages directly for testing"""
        try:
            # Extract message data
            data = message.get_js_value().to_json()
            message_data = json.loads(data)
            
            method = message_data.get('method')
            args = message_data.get('args', [])
            
            # Call the API method if it exists
            if hasattr(self, method):
                func = getattr(self, method)
                result = func(*args)
                return result
            else:
                print(f"Method {method} not found on API")
                return {'success': False, 'error': f'Method {method} not found'}
                
        except Exception as e:
            print(f"Error handling script message: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self):
        """Get current deployment status - supports both real and demo modes with enhanced compatibility checking"""
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
                    # Enhanced status with more system information
                    origin = current_deployment.get('origin', 'Unknown')
                    is_ublue = 'ublue-os' in origin or 'ghcr.io/ublue-os' in origin
                    
                    # Detect specific Universal Blue variants
                    variant = 'Unknown'
                    if 'bluefin' in origin.lower():
                        variant = 'Bluefin'
                    elif 'aurora' in origin.lower():
                        variant = 'Aurora'
                    elif 'bazzite' in origin.lower():
                        variant = 'Bazzite'
                    elif 'silverblue' in origin.lower():
                        variant = 'Silverblue'
                    elif is_ublue:
                        variant = 'Universal Blue Custom'
                    
                    status = {
                        'success': True,
                        'currentImage': origin,
                        'osVersion': current_deployment.get('version', 'Unknown'),
                        'deploymentId': current_deployment.get('checksum', '')[:8],
                        'isUniversalBlue': is_ublue,
                        'variant': variant,
                        'type': 'real',
                        'capabilities': {
                            'canRebase': True,
                            'canRollback': True,
                            'hasPortalSupport': self._check_portal_support(),
                            'hasPolkitSupport': self._check_polkit_support()
                        },
                        'systemInfo': {
                            'kernel': current_deployment.get('kernel-args', ''),
                            'packages': len(current_deployment.get('packages', [])),
                            'layeredPackages': len(current_deployment.get('requested-packages', [])),
                            'timestamp': current_deployment.get('timestamp', '')
                        }
                    }
                else:
                    status = {'success': False, 'error': 'No current deployment found'}
            else:
                # Enhanced demo mode with system detection
                system_info = self._detect_system_info()
                
                status = {
                    'success': True,
                    'currentImage': f'Demo: {system_info["distribution"]}',
                    'osVersion': system_info['version'],
                    'deploymentId': 'demo123',
                    'isUniversalBlue': False,
                    'variant': 'Not rpm-ostree',
                    'type': 'demo',
                    'capabilities': {
                        'canRebase': False,
                        'canRollback': False,
                        'hasPortalSupport': self._check_portal_support(),
                        'hasPolkitSupport': self._check_polkit_support()
                    },
                    'systemInfo': {
                        'actualSystem': system_info['distribution'],
                        'message': 'Running in demo mode - rpm-ostree not available',
                        'recommendation': 'This tool is designed for Universal Blue and rpm-ostree systems'
                    }
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            # Enhanced error handling with system detection
            system_info = self._detect_system_info()
            
            status = {
                'success': True,
                'currentImage': f'Demo: {system_info["distribution"]}',
                'osVersion': system_info['version'],
                'deploymentId': 'test456',
                'isUniversalBlue': False,
                'variant': 'Not rpm-ostree',
                'type': 'demo',
                'capabilities': {
                    'canRebase': False,
                    'canRollback': False,
                    'hasPortalSupport': self._check_portal_support(),
                    'hasPolkitSupport': self._check_polkit_support()
                },
                'systemInfo': {
                    'actualSystem': system_info['distribution'],
                    'message': f'Demo mode: {str(e)}',
                    'recommendation': 'Install on a Universal Blue system for full functionality'
                }
            }
        
        # Update web interface
        js_script = f"""
        if (typeof updateSystemStatus === 'function') {{
            updateSystemStatus({json.dumps(status)});
        }}
        """
        GLib.idle_add(self.execute_js, js_script)
        
        # Update window UI if available
        if self.window and hasattr(self.window, 'update_system_status'):
            GLib.idle_add(self.window.update_system_status, status)
        
        return status
    
    def _detect_system_info(self):
        """Detect system information for demo mode"""
        system_info = {
            'distribution': 'Unknown Linux',
            'version': 'Unknown'
        }
        
        try:
            # Try to read os-release
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
                for line in os_release.split('\n'):
                    if line.startswith('PRETTY_NAME='):
                        system_info['distribution'] = line.split('=')[1].strip('"')
                    elif line.startswith('VERSION='):
                        system_info['version'] = line.split('=')[1].strip('"')
        except:
            # Try lsb_release as fallback
            try:
                result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True)
                if result.returncode == 0:
                    system_info['distribution'] = result.stdout.replace('Description:', '').strip()
            except:
                pass
        
        return system_info
    
    def _check_portal_support(self):
        """Check if XDG Desktop Portal is available"""
        try:
            result = subprocess.run(
                ['busctl', '--user', 'list'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'org.freedesktop.portal' in result.stdout
        except:
            return False
    
    def _check_polkit_support(self):
        """Check if polkit is available for authentication"""
        try:
            result = subprocess.run(
                ['which', 'pkexec'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def enable_test_mode(self):
        """Enable test mode for synchronous operation in tests"""
        self._test_mode = True
        # Also set test mode on GLib for command executor
        GLib._test_mode = True
    
    def wait_for_operation(self, timeout=5):
        """Wait for async operation to complete in test mode"""
        if self._test_mode:
            return self._operation_complete.wait(timeout=timeout)
        return True
    
    def get_operation_result(self):
        """Get the result of the last operation in test mode"""
        return self._operation_result
    
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
    
    def execute_rebase(self, image_url):
        """Execute rebase operation with confirmation and progress tracking"""
        # Check if we're in demo mode
        status = self.get_system_status()
        if status.get('type') == 'demo':
            # Show toast notification for demo mode
            js_script = """
            if (typeof showToast === 'function') {
                showToast("Demo mode: Command would execute but is blocked", "info");
            }
            """
            GLib.idle_add(self.execute_js, js_script)
            
            # Show error message for demo mode
            error_msg = {
                'success': False,
                'error': 'Cannot execute rebase in demo mode',
                'message': 'This operation requires an rpm-ostree-based system',
                'demo_mode': True
            }
            js_script = f"""
            if (typeof showExecutionError === 'function') {{
                showExecutionError({json.dumps(error_msg)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_msg
        
        # Generate the rebase command as a list to prevent injection
        command = ["rpm-ostree", "rebase", image_url]
        
        # Validate command before proceeding
        is_valid, error_msg = self.command_executor.validate_command(command)
        if not is_valid:
            error_response = {
                'success': False,
                'error': 'Invalid command',
                'message': error_msg
            }
            js_script = f"""
            if (typeof showExecutionError === 'function') {{
                showExecutionError({json.dumps(error_response)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_response
        
        # Show confirmation dialog
        if self.window:
            dialog = ConfirmationDialog(self.window)
            command_str = " ".join(command)  # For display only
            
            # Define callback to handle confirmation response
            def handle_rebase_confirmation(confirmed):
                if not confirmed:
                    # User cancelled
                    js_script = """
                    if (typeof handleRebaseResponse === 'function') {
                        handleRebaseResponse({success: false, cancelled: true});
                    }
                    """
                    GLib.idle_add(self.execute_js, js_script)
                    return
                
                # User confirmed - proceed with execution
                # Start progress tracking
                operation_name = f"Rebase to {image_url.split('/')[-1]}"
                self.progress_tracker.start_tracking(operation_name)
                
                # Execute command with progress callback
                def progress_callback(output):
                    self.progress_tracker.update_output(output)
                
                def execute_thread():
                    try:
                        success, output, error_type = self.command_executor.execute_with_progress(
                            command, 
                            progress_callback
                        )
                        
                        if success:
                            self.progress_tracker.complete(True, "Rebase completed successfully")
                            # Show success toast
                            GLib.idle_add(self._show_success_toast, "Rebase operation completed")
                            # Add to history
                            self.history_manager.add_entry(
                                command=command_str,
                                success=True,
                                image_name=image_url.split('/')[-1],
                                operation_type='rebase'
                            )
                        else:
                            # Handle specific error types
                            error_message = self._get_user_friendly_error(error_type, output)
                            self.progress_tracker.complete(False, error_message)
                            # Show error toast with guidance
                            GLib.idle_add(self._show_error_with_guidance, error_type, error_message)
                            # Add to history
                            self.history_manager.add_entry(
                                command=command_str,
                                success=False,
                                image_name=image_url.split('/')[-1],
                                operation_type='rebase'
                            )
                            
                    except Exception as e:
                        self.progress_tracker.complete(False, f"Error: {str(e)}")
                        GLib.idle_add(self._show_error_toast, f"Execution error: {str(e)}")
                
                # Run in thread to avoid blocking UI
                thread = threading.Thread(target=execute_thread)
                thread.daemon = True
                thread.start()
            
            # Show dialog with callback
            dialog.show_rebase_confirmation(image_url, command_str, handle_rebase_confirmation)
            
            return {'success': True, 'executing': True}
        else:
            return {'success': False, 'error': 'Window not initialized'}
    
    def execute_rollback(self, deployment_id):
        """Execute rollback to a specific deployment with confirmation"""
        # Check if we're in demo mode
        status = self.get_system_status()
        if status.get('type') == 'demo':
            # Show toast notification for demo mode
            js_script = """
            if (typeof showToast === 'function') {
                showToast("Demo mode: Command would execute but is blocked", "info");
            }
            """
            GLib.idle_add(self.execute_js, js_script)
            
            # Show error message for demo mode
            error_msg = {
                'success': False,
                'error': 'Cannot execute rollback in demo mode',
                'message': 'This operation requires an rpm-ostree-based system',
                'demo_mode': True
            }
            js_script = f"""
            if (typeof showExecutionError === 'function') {{
                showExecutionError({json.dumps(error_msg)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_msg
        
        # Get deployment info
        deployments = self.deployment_manager.get_all_deployments()
        target_deployment = None
        for deployment in deployments:
            if deployment.id.startswith(deployment_id):
                target_deployment = deployment
                break
        
        if not target_deployment:
            return {'success': False, 'error': f'Deployment {deployment_id} not found'}
        
        # Generate rollback command
        command = self.deployment_manager.generate_rollback_command(deployment_id)
        
        if not command:
            return {'success': False, 'error': 'Cannot generate rollback command for this deployment'}
        
        # Validate command before proceeding
        is_valid, error_msg = self.command_executor.validate_command(command)
        if not is_valid:
            return {'success': False, 'error': 'Invalid command', 'message': error_msg}
        
        # Show confirmation dialog
        if self.window:
            dialog = ConfirmationDialog(self.window)
            deployment_info = self.deployment_manager.format_deployment_info(target_deployment)
            command_str = " ".join(command)  # For display only
            
            # Define callback to handle confirmation response
            def handle_rollback_confirmation(confirmed):
                if not confirmed:
                    # User cancelled
                    js_script = """
                    if (typeof handleRollbackResponse === 'function') {
                        handleRollbackResponse({success: false, cancelled: true});
                    }
                    """
                    GLib.idle_add(self.execute_js, js_script)
                    return
                
                # User confirmed - proceed with execution
                # Start progress tracking
                operation_name = f"Rollback to {target_deployment.version}"
                self.progress_tracker.start_tracking(operation_name)
                
                # Execute command with progress callback
                def progress_callback(output):
                    self.progress_tracker.update_output(output)
                
                def execute_thread():
                    try:
                        success, output, error_type = self.command_executor.execute_with_progress(
                            command,
                            progress_callback
                        )
                        
                        if success:
                            self.progress_tracker.complete(True, "Rollback completed successfully")
                            GLib.idle_add(self._show_success_toast, "Rollback operation completed")
                            # Add to history
                            self.history_manager.add_entry(
                                command=command_str,
                                success=True,
                                image_name=target_deployment.version,
                                operation_type='rollback'
                            )
                        else:
                            # Handle specific error types
                            error_message = self._get_user_friendly_error(error_type, output)
                            self.progress_tracker.complete(False, error_message)
                            # Show error toast with guidance
                            GLib.idle_add(self._show_error_with_guidance, error_type, error_message)
                            # Add to history
                            self.history_manager.add_entry(
                                command=command_str,
                                success=False,
                                image_name=target_deployment.version,
                                operation_type='rollback'
                            )
                            
                    except Exception as e:
                        self.progress_tracker.complete(False, f"Error: {str(e)}")
                        GLib.idle_add(self._show_error_toast, f"Execution error: {str(e)}")
                
                # Run in thread to avoid blocking UI
                thread = threading.Thread(target=execute_thread)
                thread.daemon = True
                thread.start()
            
            # Show dialog with callback
            dialog.show_rollback_confirmation(deployment_info, command_str, handle_rollback_confirmation)
            
            return {'success': True, 'executing': True}
        else:
            return {'success': False, 'error': 'Window not initialized'}
    
    def get_deployments(self):
        """Get all available deployments and send to web interface"""
        try:
            deployments = self.deployment_manager.get_all_deployments()
            
            # Convert deployments to dict format for JSON
            deployments_data = []
            for deployment in deployments:
                deployments_data.append({
                    'id': deployment.id,
                    'origin': deployment.origin,
                    'version': deployment.version,
                    'timestamp': deployment.timestamp,
                    'is_booted': deployment.is_booted,
                    'is_pinned': deployment.is_pinned,
                    'index': deployment.index
                })
            
            result = {
                'success': True,
                'deployments': deployments_data,
                'current': self.deployment_manager.get_current_deployment()
            }
            
            # Update web interface
            js_script = f"""
            if (typeof showDeployments === 'function') {{
                showDeployments({json.dumps(result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'deployments': []
            }
            
            js_script = f"""
            if (typeof showDeployments === 'function') {{
                showDeployments({json.dumps(error_result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_result
    
    def get_history(self):
        """Get command execution history"""
        try:
            history_entries = self.history_manager.get_recent_entries()
            
            # Convert history entries to dict format for JSON
            history_data = []
            for entry in history_entries:
                history_data.append({
                    'command': entry.command,
                    'timestamp': entry.timestamp,
                    'success': entry.success,
                    'image_name': entry.image_name,
                    'operation_type': entry.operation_type
                })
            
            result = {
                'success': True,
                'history': history_data
            }
            
            # Update web interface
            js_script = f"""
            if (typeof showHistoryResult === 'function') {{
                showHistoryResult({json.dumps(result)});
            }} else if (typeof window.updateAPIResult === 'function') {{
                window.updateAPIResult('get_history', {json.dumps(result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'history': []
            }
            
            js_script = f"""
            if (typeof showHistoryResult === 'function') {{
                showHistoryResult({json.dumps(error_result)});
            }} else if (typeof window.updateAPIResult === 'function') {{
                window.updateAPIResult('get_history', {json.dumps(error_result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_result
    
    def clear_history(self):
        """Clear command execution history"""
        try:
            self.history_manager.clear_history()
            
            result = {
                'success': True,
                'message': 'History cleared successfully'
            }
            
            js_script = f"""
            if (typeof window.updateAPIResult === 'function') {{
                window.updateAPIResult('clear_history', {json.dumps(result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }
            
            js_script = f"""
            if (typeof window.updateAPIResult === 'function') {{
                window.updateAPIResult('clear_history', {json.dumps(error_result)});
            }}
            """
            GLib.idle_add(self.execute_js, js_script)
            return error_result
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard using portal if available"""
        try:
            if self.window:
                # Use GTK clipboard
                clipboard = self.window.get_clipboard()
                clipboard.set(text)
                
                # Show success toast
                GLib.idle_add(self._show_success_toast, "Copied to clipboard")
                
                return {'success': True}
            else:
                return {'success': False, 'error': 'Window not initialized'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _show_success_toast(self, message):
        """Show success toast notification"""
        if self.window and hasattr(self.window, 'toast_overlay'):
            toast = Adw.Toast.new(message)
            self.window.toast_overlay.add_toast(toast)
    
    def _show_error_toast(self, message):
        """Show error toast notification"""
        if self.window and hasattr(self.window, 'toast_overlay'):
            toast = Adw.Toast.new(f"Error: {message}")
            toast.set_timeout(5)  # Show error toasts longer
            self.window.toast_overlay.add_toast(toast)
    
    def _get_user_friendly_error(self, error_type: str, output: str) -> str:
        """Convert technical errors to user-friendly messages"""
        if error_type == 'network':
            return "Network error: Unable to reach the image registry. Please check your internet connection and try again."
        elif error_type == 'auth':
            return "Authentication failed: Please ensure you have the necessary permissions to perform this operation."
        elif error_type == 'timeout':
            return "Operation timed out: The command took too long to complete. Please try again."
        elif error_type == 'busy':
            return "System busy: Another rpm-ostree transaction is in progress. Please wait and try again."
        elif error_type == 'not_found':
            return "Image not found: The specified image or deployment could not be found."
        else:
            # Extract the most relevant part of the error
            lines = output.strip().split('\n')
            if lines:
                # Look for error messages in the last few lines
                for line in reversed(lines[-5:]):
                    if 'error:' in line.lower() or 'failed' in line.lower():
                        return line.strip()
            return "Operation failed. Check the output for details."
    
    def _show_error_with_guidance(self, error_type: str, message: str):
        """Show error toast with specific guidance based on error type"""
        if self.window and hasattr(self.window, 'toast_overlay'):
            # Create main error toast
            toast = Adw.Toast.new(message)
            toast.set_timeout(10)  # Show longer for detailed errors
            
            # Add action button for specific error types
            if error_type == 'network':
                toast.set_button_label("Retry")
                toast.connect("button-clicked", lambda t: self.get_system_status())
            elif error_type == 'auth':
                toast.set_button_label("Help")
                toast.connect("button-clicked", lambda t: self._show_auth_help())
            elif error_type == 'busy':
                toast.set_button_label("Check Status")
                toast.connect("button-clicked", lambda t: self._check_rpm_ostree_status())
            
            self.window.toast_overlay.add_toast(toast)
    
    def _show_auth_help(self):
        """Show authentication help dialog"""
        if self.window:
            dialog = Adw.MessageDialog.new(self.window)
            dialog.set_heading("Authentication Help")
            dialog.set_body(
                "To perform system operations, you need administrator privileges.\n\n"
                "• Ensure you are in the 'wheel' or 'sudo' group\n"
                "• The system will prompt for your password when needed\n"
                "• If using Flatpak, ensure proper permissions are granted"
            )
            dialog.add_response("ok", "OK")
            dialog.set_default_response("ok")
            dialog.choose(None, None, None)
    
    def _check_rpm_ostree_status(self):
        """Check and display rpm-ostree status"""
        def check_status():
            try:
                result = subprocess.run(
                    ['rpm-ostree', 'status', '--json'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    # Check if transaction is in progress
                    if data.get('transaction') is not None:
                        GLib.idle_add(
                            self._show_info_toast,
                            "A system update is in progress. Please wait for it to complete."
                        )
                    else:
                        GLib.idle_add(
                            self._show_info_toast,
                            "No active transactions. You can try again now."
                        )
                else:
                    GLib.idle_add(
                        self._show_error_toast,
                        "Could not check system status"
                    )
            except Exception as e:
                GLib.idle_add(
                    self._show_error_toast,
                    f"Status check failed: {str(e)}"
                )
        
        # Run in thread
        threading.Thread(target=check_status, daemon=True).start()
    
    def _show_info_toast(self, message):
        """Show informational toast notification"""
        if self.window and hasattr(self.window, 'toast_overlay'):
            toast = Adw.Toast.new(message)
            toast.set_timeout(5)
            self.window.toast_overlay.add_toast(toast)


class UBlueImageWindow(Adw.ApplicationWindow):
    """Main application window using libadwaita widgets per UB guide"""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Universal Blue Image Manager")
        self.set_default_size(1200, 800)
        
        # Create API instance
        self.api = UBlueImageAPI()
        self.api.set_window(self)
        
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
        
        # Execution mode controls
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        mode_box.set_spacing(6)
        
        mode_label = Gtk.Label(label="Execute Mode:")
        mode_label.add_css_class("dim-label")
        mode_box.append(mode_label)
        
        self.execute_mode_switch = Gtk.Switch()
        self.execute_mode_switch.set_tooltip_text("Toggle between Guide and Execute modes")
        self.execute_mode_switch.set_active(False)  # Default to Guide mode
        self.execute_mode_switch.connect("notify::active", self.on_execute_mode_changed)
        mode_box.append(self.execute_mode_switch)
        
        self.header_bar.pack_start(mode_box)
        
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
        self.images_group = Adw.PreferencesGroup()
        self.images_group.set_title("Available Images")
        self.images_group.set_description("Universal Blue image variants")
        
        # Add image options
        images = self.api.get_available_images()['images']
        for image in images:
            image_row = Adw.ActionRow()
            image_row.set_title(image['name'])
            image_row.set_subtitle(image['description'])
            
            # Button box for actions
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            button_box.set_spacing(6)
            
            # Add guide button
            guide_btn = Gtk.Button()
            guide_btn.set_label("Guide")
            guide_btn.set_tooltip_text("Show rebase instructions")
            guide_btn.add_css_class("flat")
            guide_btn.connect("clicked", lambda btn, url=image['url']: self.on_guide_clicked(url))
            button_box.append(guide_btn)
            
            # Add execute button
            execute_btn = Gtk.Button()
            execute_btn.set_label("Execute")
            execute_btn.set_tooltip_text("Execute rebase with confirmation")
            execute_btn.add_css_class("suggested-action")
            execute_btn.connect("clicked", lambda btn, url=image['url']: self.on_execute_clicked(url))
            
            # Store button reference for later status updates
            self.execute_buttons = getattr(self, 'execute_buttons', {})
            self.execute_buttons[image['url']] = execute_btn
            
            button_box.append(execute_btn)
            image_row.add_suffix(button_box)
            
            # Set initial visibility based on mode (default to guide mode)
            execute_btn.set_visible(False)
            
            self.images_group.add(image_row)
        
        sidebar_box.append(self.images_group)
        
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
            },
            executeRebase: function(imageUrl) {
                webkit.messageHandlers.ublueAPI.postMessage({
                    method: 'execute_rebase',
                    args: [imageUrl]
                });
            },
            executeRollback: function(deploymentId) {
                webkit.messageHandlers.ublueAPI.postMessage({
                    method: 'execute_rollback',
                    args: [deploymentId]
                });
            },
            getDeployments: function() {
                webkit.messageHandlers.ublueAPI.postMessage({method: 'get_deployments'});
            },
            getHistory: function() {
                webkit.messageHandlers.ublueAPI.postMessage({method: 'get_history'});
            },
            clearHistory: function() {
                webkit.messageHandlers.ublueAPI.postMessage({method: 'clear_history'});
            },
            copyToClipboard: function(text) {
                webkit.messageHandlers.ublueAPI.postMessage({
                    method: 'copy_to_clipboard',
                    args: [text]
                });
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
                            elif result.get('executing'):
                                # Don't show toast for execution start, progress tracker handles it
                                pass
                            else:
                                toast = Adw.Toast.new("Operation completed")
                                self.toast_overlay.add_toast(toast)
                        elif result.get('cancelled'):
                            # User cancelled the operation, no toast needed
                            pass
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
    
    def update_system_status(self, status):
        """Update sidebar with system status"""
        # Update sidebar rows
        self.current_image_row.set_subtitle(status.get('currentImage', 'Unknown'))
        self.os_version_row.set_subtitle(status.get('osVersion', 'Unknown'))
        self.deployment_row.set_subtitle(status.get('deploymentId', 'Unknown')[:12] + '...')
        
        # Check if in demo mode and update UI accordingly
        if status.get('type') == 'demo':
            # Add demo mode indicator
            self.header_bar.set_title_widget(Gtk.Label(label="Universal Blue Image Manager (Demo Mode)"))
            
            # Disable execute buttons in demo mode
            if hasattr(self, 'execute_buttons'):
                for url, button in self.execute_buttons.items():
                    button.set_sensitive(False)
                    button.set_tooltip_text("Execute mode not available in demo mode")
            
            # Disable execute mode switch
            if hasattr(self, 'execute_mode_switch'):
                self.execute_mode_switch.set_sensitive(False)
                self.execute_mode_switch.set_tooltip_text("Execute mode not available in demo mode")
                
            # Show demo mode warning
            toast = Adw.Toast.new("Running in demo mode - execution features disabled")
            toast.set_timeout(0)  # Don't auto-dismiss
            self.toast_overlay.add_toast(toast)
    
    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.api.get_system_status()
        toast = Adw.Toast.new("Refreshing system status...")
        self.toast_overlay.add_toast(toast)
        
    def on_guide_clicked(self, image_url):
        """Handle guide button click from sidebar"""
        self.api.guide_rebase(image_url)
    
    def on_execute_clicked(self, image_url):
        """Handle execute button click from sidebar"""
        self.api.execute_rebase(image_url)
    
    def on_execute_mode_changed(self, switch, pspec):
        """Handle execution mode toggle"""
        execute_mode = switch.get_active()
        
        # Update button visibility based on mode
        # Get first child (the list box) from the preferences group
        list_box = self.images_group.get_first_child()
        if list_box:
            # Iterate through rows
            child = list_box.get_first_child()
            while child:
                if hasattr(child, 'get_suffix'):
                    suffix_widget = child.get_suffix()
                    if suffix_widget and isinstance(suffix_widget, Gtk.Box):
                        # Get buttons from the box
                        guide_btn = suffix_widget.get_first_child()
                        execute_btn = guide_btn.get_next_sibling() if guide_btn else None
                        
                        if guide_btn and execute_btn:
                            if execute_mode:
                                # Execute mode: Hide guide, show execute
                                guide_btn.set_visible(False)
                                execute_btn.set_visible(True)
                            else:
                                # Guide mode: Show guide, hide execute
                                guide_btn.set_visible(True)
                                execute_btn.set_visible(False)
                
                child = child.get_next_sibling()
        
        # Show toast notification
        mode_text = "Execute" if execute_mode else "Guide"
        toast = Adw.Toast.new(f"Switched to {mode_text} mode")
        self.toast_overlay.add_toast(toast)


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
