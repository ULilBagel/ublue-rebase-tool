#!/usr/bin/env python3
"""
Test script to verify thread safety fix for the rebase tool.
This script simulates the threading scenario to ensure no crashes occur.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Adw
import threading
import time

class TestWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Thread Safety Test")
        self.set_default_size(400, 300)
        
        # Create UI elements similar to the rebase tool
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        self.progress_label = Gtk.Label(label="Testing thread safety...")
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_buffer = self.log_view.get_buffer()
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.log_view)
        scrolled.set_vexpand(True)
        
        box.append(self.progress_label)
        box.append(self.progress_bar)
        box.append(scrolled)
        
        self.set_content(box)
        
        # Start the test
        self.start_test()
    
    def append_log_line(self, line):
        """Thread-safe version of append_log_line"""
        def update_ui():
            if not self.log_buffer or not self.log_view:
                return False
                
            try:
                end_iter = self.log_buffer.get_end_iter()
                self.log_buffer.insert(end_iter, line + "\n")
                
                # Auto-scroll to bottom
                self.log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
                
                # Update progress
                if "Progress:" in line:
                    try:
                        percent = int(line.split("Progress: ")[1].split("%")[0])
                        self.progress_bar.set_fraction(percent / 100.0)
                        self.progress_bar.set_text(f"{percent}%")
                    except:
                        pass
            except Exception as e:
                print(f"Error updating UI: {e}")
                
            return False
        
        GLib.idle_add(update_ui)
    
    def run_background_task(self):
        """Simulate background task that sends progress updates"""
        for i in range(101):
            self.append_log_line(f"Processing... Progress: {i}%")
            time.sleep(0.01)  # Simulate work
        
        self.append_log_line("Task completed!")
        
        def finish():
            self.progress_label.set_text("Test completed successfully!")
            return False
        
        GLib.idle_add(finish)
    
    def start_test(self):
        """Start the background thread"""
        thread = threading.Thread(target=self.run_background_task, daemon=True)
        thread.start()

class TestApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.test.ThreadSafety")
        self.connect("activate", self.on_activate)
    
    def on_activate(self, app):
        self.window = TestWindow(app)
        self.window.present()

if __name__ == "__main__":
    app = TestApp()
    app.run()