import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"sys.path: {sys.path}")

try:
    import backend
    print(f"backend found: {backend.__file__}")
except ImportError as e:
    print(f"backend NOT found: {e}")

try:
    from backend import app
    print(f"backend.app found: {app.__file__}")
except ImportError as e:
    print(f"backend.app NOT found: {e}")

try:
    import app
    print(f"app found: {app.__file__}")
except ImportError as e:
    print(f"app NOT found: {e}")
