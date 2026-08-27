#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chandojñānam Local Application Launcher.

Usage:
    python run.py
    python run.py --port 8080 --no-browser
"""

import sys
import os
import argparse
import webbrowser
import threading
import time

from app import app


def open_browser_later(url: str, delay: float = 1.0):
    def _open():
        time.sleep(delay)
        print(f"\nOpening browser at {url} ...")
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="Run Chandojñānam Local Web Application")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")

    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("=" * 60)
    print("  Chandojñānam (छन्दोज्ञानम्) - Local Web Application")
    print(f"  Access URL: {url}")
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)

    if not args.no_browser and not args.debug:
        open_browser_later(url)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
