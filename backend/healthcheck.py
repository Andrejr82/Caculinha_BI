#!/usr/bin/env python3
"""
Healthcheck script for Docker container
Checks if the FastAPI app is responding on port 8000
"""
import sys
import socket

def check_health():
    """
    Simple TCP port check - more reliable than HTTP request
    If port 8000 is listening, the app is likely healthy
    """
    try:
        # Try to connect to port 8000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()

        if result == 0:
            # Port is open and accepting connections
            print("[OK] Port 8000 is accepting connections")
            sys.exit(0)
        else:
            print(f"[FAIL] Port 8000 is not accepting connections (code: {result})")
            sys.exit(1)

    except Exception as e:
        print(f"[FAIL] Healthcheck error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
