
import psutil
import sys

def kill_process_on_port(port):
    print(f"🔍 Procurando processo na porta {port}...")
    killed = False
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            try:
                proc = psutil.Process(conn.pid)
                print(f"⚠️ Encontrado: PID {proc.pid} ({proc.name()})")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                    print(f"✅ Processo {proc.pid} terminado com sucesso.")
                except psutil.TimeoutExpired:
                    proc.kill()
                    print(f"✅ Processo {proc.pid} morto à força.")
                killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"❌ Erro ao terminar processo: {e}")
    
    if not killed:
        print(f"ℹ️ Nenhum processo encontrado na porta {port}.")

if __name__ == "__main__":
    kill_process_on_port(8000)
