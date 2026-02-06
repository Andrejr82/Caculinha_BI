"""
Script de Diagnóstico - Autenticação Backend
Verifica todas as configurações necessárias para o login funcionar
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import get_settings
from app.config.security import get_password_hash, verify_password


def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_check(status: bool, message: str):
    """Print check result"""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")


async def check_settings():
    """Verificar configurações"""
    print_header("1. VERIFICANDO CONFIGURAÇÕES (.env)")
    
    try:
        settings = get_settings()
        
        # Database URL
        db_url = str(settings.DATABASE_URL)
        has_db_url = len(db_url) > 0 and "localhost" in db_url
        print_check(has_db_url, f"DATABASE_URL configurado")
        if has_db_url:
            # Mascarar senha na exibição
            safe_url = db_url.split("@")[0].split(":")[0] + ":***@" + db_url.split("@")[1] if "@" in db_url else db_url
            print(f"   URL: {safe_url}")
        
        # Secret Key
        has_secret = len(settings.SECRET_KEY) >= 32
        print_check(has_secret, f"SECRET_KEY configurado (comprimento: {len(settings.SECRET_KEY)} chars)")
        if not has_secret:
            print("   ⚠️  ATENÇÃO: SECRET_KEY deve ter no mínimo 32 caracteres!")
        
        # JWT Settings
        print_check(True, f"ALGORITHM: {settings.ALGORITHM}")
        print_check(True, f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        print_check(True, f"REFRESH_TOKEN_EXPIRE_DAYS: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")
        
        return has_db_url and has_secret
        
    except Exception as e:
        print_check(False, f"Erro ao carregar configurações: {e}")
        return False


async def check_database_connection():
    """Verificar conexão com banco de dados"""
    print_header("2. VERIFICANDO CONEXÃO COM BANCO DE DADOS")
    
    try:
        from app.config.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("SELECT 1"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print_check(True, "Conexão com banco de dados estabelecida")
                
                # Verificar se tabela users existe
                try:
                    result = await db.execute(text(
                        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                        "WHERE TABLE_NAME = 'users'"
                    ))
                    count = result.scalar()
                    
                    if count > 0:
                        print_check(True, "Tabela 'users' existe no banco")
                        
                        # Contar usuários
                        result = await db.execute(text("SELECT COUNT(*) FROM users"))
                        user_count = result.scalar()
                        print_check(True, f"Total de usuários no banco: {user_count}")
                        
                        return True
                    else:
                        print_check(False, "Tabela 'users' NÃO existe")
                        print("   ⚠️  Execute: alembic upgrade head")
                        return False
                        
                except Exception as e:
                    print_check(False, f"Erro ao verificar tabela users: {e}")
                    return False
            else:
                print_check(False, "Falha no teste de conexão")
                return False
                
    except Exception as e:
        print_check(False, f"Erro ao conectar com banco: {e}")
        print(f"   Detalhes: {str(e)}")
        return False


async def check_admin_user():
    """Verificar se usuário admin existe"""
    print_header("3. VERIFICANDO USUÁRIO ADMIN")
    
    try:
        from app.config.database import AsyncSessionLocal
        from app.infrastructure.database.models import User
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            admin = result.scalar_one_or_none()
            
            if admin:
                print_check(True, f"Usuário admin encontrado")
                print(f"   ID: {admin.id}")
                print(f"   Username: {admin.username}")
                print(f"   Email: {admin.email}")
                print(f"   Role: {admin.role}")
                print_check(admin.is_active, f"Usuário ativo: {admin.is_active}")
                print(f"   Criado em: {admin.created_at}")
                
                if admin.last_login:
                    print(f"   Último login: {admin.last_login}")
                else:
                    print(f"   Último login: Nunca")
                
                return admin.is_active
            else:
                print_check(False, "Usuário admin NÃO encontrado")
                print("   ⚠️  Execute: python scripts\\seed_admin.py")
                return False
                
    except Exception as e:
        print_check(False, f"Erro ao verificar admin: {e}")
        return False


async def test_password_hashing():
    """Testar hashing de senhas"""
    print_header("4. TESTANDO HASHING DE SENHAS (bcrypt)")
    
    try:
        test_password = "admin123"
        
        # Gerar hash
        hashed = get_password_hash(test_password)
        print_check(True, "Hash gerado com sucesso")
        print(f"   Hash: {hashed[:50]}...")
        
        # Verificar senha correta
        is_valid = verify_password(test_password, hashed)
        print_check(is_valid, "Verificação de senha correta")
        
        # Verificar senha incorreta
        is_invalid = verify_password("senha_errada", hashed)
        print_check(not is_invalid, "Rejeição de senha incorreta")
        
        return is_valid and not is_invalid
        
    except Exception as e:
        print_check(False, f"Erro ao testar hashing: {e}")
        return False


async def test_jwt_tokens():
    """Testar criação de tokens JWT"""
    print_header("5. TESTANDO TOKENS JWT")
    
    try:
        from app.config.security import create_access_token, create_refresh_token, decode_token
        
        # Dados de teste
        token_data = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "username": "admin",
            "role": "admin"
        }
        
        # Criar access token
        access_token = create_access_token(token_data)
        print_check(True, "Access token criado")
        print(f"   Token: {access_token[:50]}...")
        
        # Criar refresh token
        refresh_token = create_refresh_token(token_data)
        print_check(True, "Refresh token criado")
        
        # Decodificar access token
        decoded = decode_token(access_token)
        print_check(decoded.get("type") == "access", "Access token decodificado corretamente")
        print_check(decoded.get("sub") == token_data["sub"], "Dados do token corretos")
        
        # Decodificar refresh token
        decoded_refresh = decode_token(refresh_token)
        print_check(decoded_refresh.get("type") == "refresh", "Refresh token decodificado corretamente")
        
        return True
        
    except Exception as e:
        print_check(False, f"Erro ao testar JWT: {e}")
        return False


async def test_login_flow():
    """Testar fluxo completo de login"""
    print_header("6. TESTANDO FLUXO DE LOGIN COMPLETO")
    
    try:
        from app.config.database import AsyncSessionLocal
        from app.infrastructure.database.models import User
        from app.config.security import verify_password, create_access_token
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # 1. Buscar usuário
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print_check(False, "Usuário admin não encontrado")
                return False
            
            print_check(True, "Usuário encontrado no banco")
            
            # 2. Verificar senha
            password_valid = verify_password("admin123", user.hashed_password)
            print_check(password_valid, "Senha 'admin123' verificada com sucesso")
            
            if not password_valid:
                print("   ⚠️  A senha hashada no banco não corresponde a 'admin123'")
                return False
            
            # 3. Verificar se está ativo
            print_check(user.is_active, "Usuário está ativo")
            
            if not user.is_active:
                print("   ⚠️  Execute: UPDATE users SET is_active = 1 WHERE username = 'admin'")
                return False
            
            # 4. Criar token
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            }
            access_token = create_access_token(token_data)
            print_check(True, "Token JWT criado com sucesso")
            
            print("\n✅ FLUXO DE LOGIN COMPLETO FUNCIONANDO!")
            print(f"\n   Você pode fazer login com:")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            
            return True
            
    except Exception as e:
        print_check(False, f"Erro no fluxo de login: {e}")
        import traceback
        print(f"\n{traceback.format_exc()}")
        return False


async def main():
    """Executar todos os diagnósticos"""
    print("\n" + "="*60)
    print("  🔍 DIAGNÓSTICO DE AUTENTICAÇÃO - AGENT BI BACKEND")
    print("="*60)
    
    results = []
    
    # 1. Configurações
    results.append(await check_settings())
    
    # 2. Conexão com banco
    results.append(await check_database_connection())
    
    # 3. Usuário admin
    results.append(await check_admin_user())
    
    # 4. Hashing de senhas
    results.append(await test_password_hashing())
    
    # 5. Tokens JWT
    results.append(await test_jwt_tokens())
    
    # 6. Fluxo de login
    results.append(await test_login_flow())
    
    # Resumo
    print_header("RESUMO DO DIAGNÓSTICO")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total de testes: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    
    if all(results):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O sistema de autenticação está configurado corretamente.")
        print("   Você pode fazer login com: admin / admin123")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        print("   Verifique os erros acima e siga as recomendações.")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
