"""
Script para testar login do admin via Supabase
"""
import asyncio
from app.core.auth_service import auth_service

async def test_admin_login():
    print("\n=== TESTE DE LOGIN DO ADMIN ===\n")

    # Testar login
    print("[1] Testando autenticacao do admin...")
    user_data = await auth_service.authenticate_user(
        username="admin",
        password="admin123",
        db=None  # USE_SQL_SERVER=false
    )

    if not user_data:
        print("[ERRO] Login falhou! Credenciais incorretas ou usuario nao existe.")
        return False

    print("[OK] Login bem-sucedido!")
    print(f"\n[2] Dados do usuario retornados pelo AuthService:")
    print(f"  ID: {user_data.get('id')}")
    print(f"  Username: {user_data.get('username')}")
    print(f"  Email: {user_data.get('email')}")
    print(f"  Role: {user_data.get('role')}")
    print(f"  Is Active: {user_data.get('is_active')}")
    print(f"  Allowed Segments: {user_data.get('allowed_segments')}")

    # Validar dados
    print(f"\n[3] Validando dados...")

    success = True

    if user_data.get("role") != "admin":
        print(f"  [ERRO] Role incorreto: '{user_data.get('role')}' (esperado: 'admin')")
        success = False
    else:
        print(f"  [OK] Role correto: 'admin'")

    if user_data.get("allowed_segments") != ["*"]:
        print(f"  [ERRO] Allowed segments incorreto: {user_data.get('allowed_segments')} (esperado: ['*'])")
        success = False
    else:
        print(f"  [OK] Allowed segments correto: ['*']")

    if not user_data.get("is_active"):
        print(f"  [ERRO] Usuario inativo")
        success = False
    else:
        print(f"  [OK] Usuario ativo")

    # Simular criacao de token JWT
    print(f"\n[4] Simulando criacao de token JWT...")
    from app.config.security import create_access_token

    token_data = {
        "sub": user_data["id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "allowed_segments": user_data["allowed_segments"]
    }

    access_token = create_access_token(token_data)
    print(f"  [OK] Token JWT criado com sucesso!")
    print(f"  Token (primeiros 50 chars): {access_token[:50]}...")

    # Decodificar token para verificar payload
    import jwt
    from app.config.settings import get_settings
    settings = get_settings()

    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print(f"\n[5] Payload do token JWT:")
    print(f"  Username: {payload.get('username')}")
    print(f"  Role: {payload.get('role')}")
    print(f"  Allowed Segments: {payload.get('allowed_segments')}")

    # Validar payload
    if payload.get("role") != "admin":
        print(f"  [ERRO] Token tem role incorreto: '{payload.get('role')}'")
        success = False
    else:
        print(f"  [OK] Token tem role correto: 'admin'")

    if payload.get("allowed_segments") != ["*"]:
        print(f"  [ERRO] Token tem allowed_segments incorreto: {payload.get('allowed_segments')}")
        success = False
    else:
        print(f"  [OK] Token tem allowed_segments correto: ['*']")

    print("\n" + "="*50)
    if success:
        print("RESULTADO: TODOS OS TESTES PASSARAM!")
        print("="*50)
        print("\nPROXIMOS PASSOS:")
        print("1. Reinicie o backend (Ctrl+C e execute 'start.bat')")
        print("2. Limpe o cache do navegador (localStorage.clear())")
        print("3. Faca login com admin/admin")
        print("4. Verifique se o console mostra role='admin' e allowed_segments=['*']")
    else:
        print("RESULTADO: ALGUNS TESTES FALHARAM!")
        print("="*50)
        print("\nVERIFIQUE:")
        print("- Perfil do admin no Supabase (tabela user_profiles)")
        print("- Configuracoes no .env (USE_SUPABASE_AUTH=true, USE_SQL_SERVER=false)")

    return success

if __name__ == "__main__":
    result = asyncio.run(test_admin_login())
    exit(0 if result else 1)
