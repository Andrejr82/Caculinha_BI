import subprocess
import sys

port = sys.argv[1] if len(sys.argv) > 1 else "8000"

# Find and kill process on port
result = subprocess.run(
    f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
    shell=True,
    capture_output=True,
    text=True
)

if result.stdout:
    # Extract PID (last column)
    for line in result.stdout.strip().split('\n'):
        parts = line.split()
        if parts:
            pid = parts[-1]
            print(f"Killing PID {pid} on port {port}")
            subprocess.run(f'taskkill /F /PID {pid}', shell=True)
else:
    print(f"No process found on port {port}")
