"""
Script de sincronizacao de subida:
- Usado por START_SYSTEM_V2026.bat
- Garante que o frontend so sobe depois que o backend estiver pronto

[AJUSTE RAPIDO PARA LEIGO]
Se quiser mudar comportamento, altere apenas estas constantes:
- BACKEND_HOST: host do backend (padrao: localhost)
- BACKEND_PORT: porta do backend (padrao: 8000)
- HEALTH_PATH : endpoint de saude (padrao: /health)
- DEFAULT_TIMEOUT_SECONDS: tempo maximo de espera (padrao: 60s)
"""

import socket
import sys
import time

import requests

# [AJUSTE] Host do backend local
BACKEND_HOST = "localhost"
# [AJUSTE] Porta do backend local
BACKEND_PORT = 8000
# [AJUSTE] Endpoint de saude do backend
HEALTH_PATH = "/health"
# [AJUSTE] Tempo maximo total de espera
DEFAULT_TIMEOUT_SECONDS = 120


def check_port(host: str, port: int) -> bool:
    """Retorna True se a porta TCP estiver aberta no host informado."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except OSError:
        return False


def wait_for_backend(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
    """
    Fluxo de espera:
    1) Aguarda a porta abrir (backend iniciou processo)
    2) Aguarda /health responder 200 (backend realmente pronto)
    """
    print(f"Waiting for backend to be ready (timeout={timeout}s)...")
    start_time = time.monotonic()

    # Wait for port first
    print(f"Checking port {BACKEND_PORT}...")
    while time.monotonic() - start_time < timeout:
        if check_port(BACKEND_HOST, BACKEND_PORT):
            print(f"Port {BACKEND_PORT} is open!")
            break
        time.sleep(1)
        print(".", end="", flush=True)

    # Then check health endpoint
    health_url = f"http://{BACKEND_HOST}:{BACKEND_PORT}{HEALTH_PATH}"
    print(f"\nChecking {HEALTH_PATH} endpoint...")
    while time.monotonic() - start_time < timeout:
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                print("Backend is ready and healthy!")
                sys.exit(0)
        except requests.RequestException:
            pass

        time.sleep(1)
        print(".", end="", flush=True)

    print("\nTimeout waiting for backend.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    wait_for_backend()
