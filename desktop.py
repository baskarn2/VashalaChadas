#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Desktop Application Launcher.

Runs the local backend server in a background thread and opens a native
desktop application window using pywebview (or default browser as fallback).
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import urllib.request

# Ensure resource paths work both in standard Python and PyInstaller bundled mode
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

os.environ['VISHALA_BASE_DIR'] = get_base_dir()

from app import app


def find_free_port(default_port=5000):
    """Find a free port starting from default_port."""
    for port in range(default_port, default_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return default_port


def wait_for_server(url, timeout=10.0):
    """Wait until the Flask server is responding."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status in (200, 302, 301):
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def start_flask_server(host, port):
    """Start Flask server in production-ready quiet mode."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)


def main():
    host = '127.0.0.1'
    port = find_free_port(5000)
    url = f"http://{host}:{port}"

    # Start Flask server thread
    server_thread = threading.Thread(target=start_flask_server, args=(host, port), daemon=True)
    server_thread.start()

    print("=" * 60)
    print("  विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Desktop Mode")
    print(f"  Local Server: {url}")
    print("=" * 60)

    # Wait for server to become live
    wait_for_server(url)

    # Try launching native desktop window with pywebview
    has_webview = False
    try:
        import webview
        has_webview = True
    except ImportError:
        has_webview = False

    if has_webview:
        try:
            window = webview.create_window(
                title='विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Sanskrit Prosody & Composition Suite',
                url=url,
                width=1280,
                height=850,
                min_size=(900, 600),
                confirm_close=False
            )
            webview.start()
            sys.exit(0)
        except Exception as e:
            print(f"pywebview GUI failed ({e}), opening in default browser...")

    # Fallback: Open in default web browser
    webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping application...")
        sys.exit(0)


if __name__ == '__main__':
    main()
