"""
Script para verificar a estrutura da tabela user_profiles no Supabase
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from supabase import create_client

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, service_key)

print("=" * 80)
print("VERIFICANDO ESTRUTURA DA TABELA user_profiles")
print("=" * 80)

# Obter todos os registros para ver as colunas
try:
    response = supabase.table("user_profiles").select("*").limit(10).execute()
    
    if response.data:
        print("\nColunas existentes na tabela user_profiles:")
        columns = response.data[0].keys()
        for col in columns:
            print(f"   - {col}")
        
        print("\nRegistros existentes:")
        for row in response.data:
            print(f"\n   ID: {row.get('id', 'N/A')}")
            for k, v in row.items():
                print(f"      {k}: {v}")
    else:
        print("Tabela vazia ou nao existe")
        
except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
