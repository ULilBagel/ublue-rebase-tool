#!/usr/bin/env python3
"""
GTK Mock Utilities for Testing
Provides mock objects that are compatible with GTK type system
"""

from unittest.mock import Mock, MagicMock

def create_mock_gtk_application():
    """
    Create a mock GTK application that satisfies type requirements
    Returns a mock object with proper GTK application interface
    """
    # Create a mock that has the essential GTK application methods
    mock_app = MagicMock(name='MockGtkApplication')
    
    # Add required application methods
    mock_app.connect = Mock(return_value=1)  # Return connection ID
    mock_app.run = Mock(return_value=0)  # Return success code
    mock_app.quit = Mock()
    mock_app.activate = Mock()
    mock_app.shutdown = Mock()
    mock_app.get_active_window = Mock(return_value=None)
    mock_app.add_window = Mock()
    mock_app.remove_window = Mock()
    
    # Add properties
    mock_app.application_id = 'org.test.mock'
    mock_app.flags = 0
    
    # Make it look like a GTK object
    mock_app.__class__.__name__ = 'Application'
    mock_app.__module__ = 'gi.repository.Adw'
    
    return mock_app


def create_mock_gtk_window():
    """
    Create a mock GTK window that satisfies type requirements
    Returns a mock object with proper GTK window interface
    """
    # Create a mock that has the essential GTK window methods
    mock_window = MagicMock(name='MockGtkWindow')
    
    # Add required window methods
    mock_window.set_application = Mock()
    mock_window.set_default_size = Mock()
    mock_window.set_title = Mock()
    mock_window.set_content = Mock()
    mock_window.present = Mock()
    mock_window.close = Mock()
    mock_window.destroy = Mock()
    mock_window.show = Mock()
    mock_window.hide = Mock()
    mock_window.get_application = Mock(return_value=None)
    
    # Add properties
    mock_window.title = 'Test Window'
    mock_window.default_width = 800
    mock_window.default_height = 600
    mock_window.visible = True
    
    # Make it look like a GTK object
    mock_window.__class__.__name__ = 'Window'
    mock_window.__module__ = 'gi.repository.Gtk'
    
    return mock_window


def create_mock_adw_toast_overlay():
    """Create a mock AdwToastOverlay"""
    mock_overlay = MagicMock(name='MockAdwToastOverlay')
    mock_overlay.add_toast = Mock()
    mock_overlay.set_child = Mock()
    mock_overlay.get_child = Mock(return_value=None)
    
    mock_overlay.__class__.__name__ = 'ToastOverlay'
    mock_overlay.__module__ = 'gi.repository.Adw'
    
    return mock_overlay


def create_mock_webkit_webview():
    """Create a mock WebKit WebView"""
    mock_webview = MagicMock(name='MockWebKitWebView')
    
    # Add WebView methods
    mock_webview.load_uri = Mock()
    mock_webview.load_html = Mock()
    mock_webview.reload = Mock()
    mock_webview.stop_loading = Mock()
    mock_webview.go_back = Mock()
    mock_webview.go_forward = Mock()
    mock_webview.evaluate_javascript = Mock()
    mock_webview.get_settings = Mock()
    mock_webview.get_user_content_manager = Mock()
    
    # Add properties
    mock_webview.is_loading = False
    mock_webview.uri = None
    mock_webview.title = None
    
    mock_webview.__class__.__name__ = 'WebView'
    mock_webview.__module__ = 'gi.repository.WebKit'
    
    return mock_webview


def create_mock_user_content_manager():
    """Create a mock WebKit UserContentManager"""
    mock_manager = MagicMock(name='MockUserContentManager')
    
    # Add UserContentManager methods
    mock_manager.register_script_message_handler = Mock()
    mock_manager.unregister_script_message_handler = Mock()
    mock_manager.add_script = Mock()
    mock_manager.remove_all_scripts = Mock()
    mock_manager.connect = Mock(return_value=1)
    
    mock_manager.__class__.__name__ = 'UserContentManager'
    mock_manager.__module__ = 'gi.repository.WebKit'
    
    return mock_manager


def create_mock_message(method, args=None):
    """
    Create a mock JavaScript message for testing
    
    Args:
        method: The API method to call
        args: Optional list of arguments
    """
    mock_message = MagicMock()
    
    # Create the JSON data
    message_data = {
        'method': method,
        'args': args or []
    }
    
    # Mock the get_js_value chain
    mock_js_value = MagicMock()
    mock_js_value.to_json.return_value = json.dumps(message_data)
    mock_message.get_js_value.return_value = mock_js_value
    
    return mock_message


# Import json for message creation
import json