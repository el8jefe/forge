"""
run.py — FORGE Platform Entry Point
Starts the Flask application server on all interfaces.
Run: python3 run.py
"""

import os
import sys
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from platform.app import create_app

app = create_app()


def _get_lan_ip() -> str:
    """Resolve the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    lan_ip = _get_lan_ip()

    print()
    print("FORGE Platform")
    print("-" * 48)
    print(f"  Local:   http://localhost:{port}")
    print(f"  Network: http://{lan_ip}:{port}")
    print(f"  Admin:   http://localhost:{port}/admin")
    print(f"  Portal:  http://localhost:{port}/portal")
    print(f"  Health:  http://localhost:{port}/health")
    print("-" * 48)
    print()

    app.run(host="0.0.0.0", port=port, debug=False)
