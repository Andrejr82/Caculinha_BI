#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para liberar portas 8000 e 3000
Mata todos os processos Python/Node rodando nessas portas
"""

import subprocess
import sys
import time


def get_pids_on_port(port: int) -> list:
    """Obtem todos os PIDs usando uma porta especifica"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )

        pids = []
        for line in result.stdout.splitlines():
            if 'LISTENING' in line or 'ESTABLISHED' in line:
                parts = line.split()
                if parts:
                    try:
                        pid = int(parts[-1])
                        if pid > 0 and pid not in pids:
                            pids.append(pid)
                    except (ValueError, IndexError):
                        continue

        return pids
    except Exception as e:
        print(f"[ERRO] Erro ao obter PIDs da porta {port}: {e}")
        return []


def kill_process(pid: int) -> bool:
    """Mata um processo pelo PID"""
    try:
        result = subprocess.run(
            f'taskkill //F //PID {pid}',
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  [OK] Processo {pid} finalizado")
            return True
        else:
            if "nao foi encontrado" in result.stdout or "not found" in result.stdout:
                print(f"  [INFO] Processo {pid} ja nao existe")
                return True
            else:
                print(f"  [ERRO] Falha ao matar {pid}")
                return False
    except Exception as e:
        print(f"  [ERRO] Erro ao matar processo {pid}: {e}")
        return False


def kill_port(port: int, max_attempts: int = 3) -> bool:
    """Mata todos os processos em uma porta (com tentativas)"""
    print(f"\n{'='*60}")
    print(f"[*] Verificando porta {port}...")
    print(f"{'='*60}")

    for attempt in range(1, max_attempts + 1):
        pids = get_pids_on_port(port)

        if not pids:
            print(f"[OK] Porta {port} esta livre!")
            return True

        print(f"\n[*] Tentativa {attempt}/{max_attempts}")
        print(f"    Processos encontrados: {pids}")

        for pid in pids:
            kill_process(pid)

        time.sleep(1)

        remaining_pids = get_pids_on_port(port)
        if not remaining_pids:
            print(f"\n[OK] Porta {port} liberada com sucesso!")
            return True
        else:
            print(f"\n[AVISO] Processos ainda ativos: {remaining_pids}")

    print(f"\n[ERRO] Porta {port} ainda esta ocupada apos {max_attempts} tentativas")
    print(f"        Processos restantes: {get_pids_on_port(port)}")
    return False


def kill_python_processes():
    """Mata todos os processos Python do projeto"""
    print(f"\n{'='*60}")
    print("[*] Procurando processos Python do projeto...")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            'tasklist | findstr python.exe',
            shell=True,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            print("[OK] Nenhum processo Python encontrado")
            return

        print("\n[*] Processos Python encontrados:")
        print(result.stdout[:500])  # Limitar output

        subprocess.run(
            'taskkill //F //IM python.exe //FI "WINDOWTITLE eq *uvicorn*"',
            shell=True,
            capture_output=True
        )
        subprocess.run(
            'taskkill //F //IM python.exe //FI "WINDOWTITLE eq *run.py*"',
            shell=True,
            capture_output=True
        )

        print("[OK] Tentativa de matar processos Python do backend concluida")

    except Exception as e:
        print(f"[AVISO] Erro ao procurar processos Python: {e}")


def main():
    print("\n" + "="*60)
    print("KILL PORTS - Agent Solution BI")
    print("="*60)
    print("   Limpando portas 8000 (Backend) e 3000 (Frontend)")
    print("="*60)

    kill_python_processes()
    time.sleep(1)

    port_8000_freed = kill_port(8000)
    port_3000_freed = kill_port(3000)

    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"   Porta 8000 (Backend): {'[OK] LIVRE' if port_8000_freed else '[ERRO] OCUPADA'}")
    print(f"   Porta 3000 (Frontend): {'[OK] LIVRE' if port_3000_freed else '[ERRO] OCUPADA'}")
    print("="*60)

    if port_8000_freed and port_3000_freed:
        print("\n[OK] Sucesso! Todas as portas foram liberadas.")
        print("     Agora voce pode iniciar o sistema com: python run.py")
        return 0
    else:
        print("\n[AVISO] Algumas portas ainda estao ocupadas!")
        print("        Solucoes:")
        print("        1. Feche manualmente os terminais/shells que estao rodando o backend")
        print("        2. Use o Gerenciador de Tarefas para matar processos Python")
        print("        3. Reinicie o computador se necessario")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Operacao cancelada pelo usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
