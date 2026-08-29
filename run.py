#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
विशालवृत्तावलिः (Viśālavṛttāvaliḥ) Application Launcher.

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
    parser = argparse.ArgumentParser(description="Run विशालवृत्तावलिः (Viśālavṛttāvaliḥ) Web Application")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")

    args = parser.parse_args()

    # Check if port is in use and pick next free port
    import socket
    actual_port = args.port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((args.host, actual_port)) == 0:
            for p in [5050, 8080, 8000, 5001]:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                    if s2.connect_ex((args.host, p)) != 0:
                        actual_port = p
                        break

    url = f"http://{args.host}:{actual_port}"
    print("=" * 65)
    print("  विशालवृत्तावलिः (Viśālavṛttāvaliḥ) - Sanskrit Prosody Suite")
    print(f"  Access URL: {url}")
    print("  Press Ctrl+C to stop the server")
    print("=" * 65)

    if not args.no_browser and not args.debug:
        open_browser_later(url)

    app.run(host=args.host, port=actual_port, debug=args.debug)



if __name__ == '__main__':
    main()
