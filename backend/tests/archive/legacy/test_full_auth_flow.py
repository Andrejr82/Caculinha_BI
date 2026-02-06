"""
Teste completo do fluxo de autenticacao como faria o auth_service.py
"""
import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

from supabase import create_client

url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, anon_key)

print("=" * 80)
print("TESTE COMPLETO DE AUTENTICACAO - SIMULANDO auth_service.py")
print("=" * 80)

TEST_EMAIL = "user@agentbi.com"
TEST_PASSWORD = "user123"

print(f"\n1. Fazendo login com email: {TEST_EMAIL}")

try:
    response = supabase.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response and response.session:
        user = response.session.user
        user_id = str(user.id)
        
        print(f"   [OK] Login bem-sucedido!")
        print(f"   User ID: {user_id}")
        print(f"   Email: {user.email}")
        
        # Simular logica do auth_service.py
        role = "user"
        allowed_segments = []
        
        # Recuperar metadata (allowed_segments pode estar aqui)
        user_metadata = user.user_metadata or {}
        print(f"\n2. User Metadata do Supabase Auth:")
        print(f"   {json.dumps(user_metadata, indent=2, default=str)}")
        
        if "allowed_segments" in user_metadata:
            allowed_segments = user_metadata["allowed_segments"]
            print(f"\n   allowed_segments encontrado no metadata: {allowed_segments[:3]}...")
        
        # Consultar user_profiles (sem email - usando id direto)
        print(f"\n3. Consultando user_profiles com id={user_id}...")
        try:
            profile_resp = supabase.table("user_profiles").select("role, username").eq("id", user_id).execute()
            if profile_resp.data:
                role = profile_resp.data[0].get("role", "user")
                username = profile_resp.data[0].get("username", "")
                print(f"   [OK] Perfil encontrado:")
                print(f"   - role: {role}")
                print(f"   - username: {username}")
            else:
                print(f"   [ALERTA] Nenhum perfil encontrado para este ID")
                role = user_metadata.get("role", "user")
        except Exception as e:
            print(f"   [ERRO] Erro ao consultar user_profiles: {e}")
            role = user_metadata.get("role", "user")
        
        # Admin check
        if role == "admin":
            allowed_segments = ["*"]
        
        # Resultado final
        result = {
            "id": user_id,
            "username": user.email.split('@')[0],
            "email": user.email,
            "role": role,
            "is_active": True,
            "allowed_segments": allowed_segments
        }
        
        print(f"\n4. RESULTADO FINAL (como retornaria auth_service.py):")
        print(f"   {json.dumps(result, indent=2, default=str)}")
        
        print("\n\n[SUCESSO] O fluxo de autenticacao funcionou corretamente!")
        print("O usuario pode fazer login e tem permissoes definidas.")
        
    else:
        print("   [ERRO] Login falhou - sem sessao")
        
except Exception as e:
    print(f"   [ERRO] {e}")
    
print("\n" + "=" * 80)
