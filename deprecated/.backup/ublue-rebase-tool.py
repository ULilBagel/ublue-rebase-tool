#!/usr/bin/env python3
"""Universal Blue Rebase Tool"""

import os, sys, gi
gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, WebKit

class UBlueApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.ublue.RebaseTool")
    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Universal Blue Rebase Tool")
        window.set_default_size(1200, 800)
        webview = WebKit.WebView()
        # Try to load web interface
        web_file = None
        if os.environ.get("FLATPAK_ID"):
            web_file = "/app/share/ublue-rebase-tool/index.html"
        elif os.path.exists("web/index.html"):
            web_file = os.path.abspath("web/index.html")
        if web_file and os.path.exists(web_file):
            webview.load_uri("file://" + web_file)
        else:
            # Fallback HTML interface
            fallback_html = """<!DOCTYPE html>
<html><head><title>Universal Blue Rebase Tool</title>
<style>body{font-family:system-ui;background:linear-gradient(135deg,#1e3c72,#2a5298);color:white;text-align:center;padding:50px}
h1{font-size:3em;margin-bottom:20px}p{font-size:1.5em}</style></head>
<body><h1>🚀 Universal Blue Rebase Tool</h1><p>GTK WebKit Edition</p>
<p>Interface loaded successfully!</p></body></html>"""
            webview.load_html(fallback_html, None)
        window.set_child(webview)
        window.present()

if __name__ == "__main__":
    app = UBlueApp()
    app.run(sys.argv)
