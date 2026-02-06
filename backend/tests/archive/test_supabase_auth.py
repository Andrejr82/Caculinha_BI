"""
Teste completo de autenticação Supabase
Verifica se o admin pode logar e recebe role='admin' e allowed_segments=['*']
"""
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Carrega env
load_dotenv(Path(__file__).parent / ".env")

from app.core.auth_service import auth_service

async def test_login():
    print("="*60)
    print("TESTE DE AUTENTICACAO SUPABASE")
    print("="*60)
    print()
    
    # Testa login com admin
    username = "admin"
    password = "admin123"  # Senha configurada no Supabase
    
    print(f"Tentando login com: {username} / {password}")
    print()
    
    result = await auth_service.authenticate_user(username, password, db=None)
    
    if result:
        print("[SUCESSO] Login realizado!")
        print()
        print("Dados do usuario:")
        print(f"  ID: {result.get('id')}")
        print(f"  Username: {result.get('username')}")
        print(f"  Email: {result.get('email')}")
        print(f"  Role: {result.get('role')}")
        print(f"  Allowed Segments: {result.get('allowed_segments')}")
        print(f"  Is Active: {result.get('is_active')}")
        print()
        
        # Verifica se tem acesso global
        segments = result.get('allowed_segments', [])
        if '*' in segments:
            print("[OK] Admin tem ACESSO GLOBAL (allowed_segments=['*'])")
        else:
            print(f"[PROBLEMA] Admin NAO tem acesso global!")
            print(f"           allowed_segments = {segments}")
            print()
            print("Para corrigir, garanta que na tabela user_profiles do Supabase:")
            print("  - O usuario admin tenha role='admin'")
            print("  - O codigo ja garante allowed_segments=['*'] para role='admin'")
    else:
        print("[ERRO] Login falhou!")
        print()
        print("Possiveis causas:")
        print("  1. Usuario nao existe no Supabase Auth")
        print("  2. Senha incorreta no Supabase") 
        print("  3. Problema de conexao com Supabase")
        print()
        print("Verifique os logs do backend para mais detalhes")

if __name__ == "__main__":
    asyncio.run(test_login())
