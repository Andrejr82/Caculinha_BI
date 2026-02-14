import requests
import sys
import time
import socket

def check_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except:
        return False

def wait_for_backend(timeout=60):
    print(f"Waiting for backend to be ready (timeout={timeout}s)...")
    start_time = time.time()
    
    # Wait for port first
    print("Checking port 8000...")
    while time.time() - start_time < timeout:
        if check_port("localhost", 8000):
            print("Port 8000 is open!")
            break
        time.sleep(1)
        print(".", end="", flush=True)
    
    # Then check health endpoint
    print("\nChecking /health endpoint...")
    while time.time() - start_time < timeout:
        try:
            r = requests.get("http://localhost:8000/health", timeout=2)
            if r.status_code == 200:
                print("Backend is ready and healthy!")
                sys.exit(0)
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            # print(f"Error checking backend: {e}", file=sys.stderr)
            pass
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nTimeout waiting for backend.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    wait_for_backend()
