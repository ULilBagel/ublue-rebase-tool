#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio

class TestApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='io.test.TestApp',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
    def do_activate(self):
        print("do_activate called!")
        window = Adw.ApplicationWindow(application=self, title="Test")
        window.set_default_size(400, 300)
        window.present()

app = TestApp()
app.run(None)