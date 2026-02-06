
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis do .env
load_dotenv("backend/.env")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("ERRO: Variáveis SUPABASE_URL ou SUPABASE_ANON_KEY não encontradas no .env")
    exit(1)

print(f"Testando conexão com Supabase: {url}")

supabase: Client = create_client(url, key)

async def test_login(email, password):
    print(f"\nTentando login com: {email} ...")
    try:
        # Tenta autenticar
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            print("✅ SUCESSO! Login realizado.")
            print(f"ID do Usuário: {response.user.id}")
            print(f"Email: {response.user.email}")
        else:
            print("❌ FALHA: Resposta vazia.")
            
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")

async def main():
    # Teste 1: Usuário admin simples (comum em setups locais)
    await test_login("admin", "admin123")
    
    # Teste 2: Usuário admin como email (formato Supabase padrão)
    await test_login("admin@agentbi.com", "admin123")

if __name__ == "__main__":
    asyncio.run(main())
