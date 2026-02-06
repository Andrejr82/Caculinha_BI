"""
Script de Teste de Conexão SQL Server (Headless/Sem Navegador)
--------------------------------------------------------------
Este script testa a conexão com o banco de dados SQL Server utilizando
as configurações definidas em app.config.settings, carregadas do arquivo .env.

Não abre browser. Executa apenas no terminal.
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pathlib import Path

# Adiciona o diretório raiz do backend ao PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Tenta carregar as configurações
try:
    from app.config.settings import get_settings
    settings = get_settings()
except ImportError as e:
    print(f"❌ Erro ao importar configurações: {e}")
    sys.exit(1)

async def test_connection():
    print("=" * 60)
    print("TESTE DE CONEXÃO SQL SERVER (HEADLESS)")
    print("=" * 60)
    
    print(f"📂 Diretório Base: {backend_dir}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print(f"🔌 DATABASE_URL (mascarado): {str(settings.DATABASE_URL).replace(settings.DATABASE_URL.split(':')[2].split('@')[0], '******') if ':@' in str(settings.DATABASE_URL) else settings.DATABASE_URL}")
    print(f"🚩 USE_SQL_SERVER: {settings.USE_SQL_SERVER}")
    
    if not settings.USE_SQL_SERVER:
        print("\n⚠️ AVISO: USE_SQL_SERVER está False. O sistema está configurado para usar apenas Parquet/SQLite em memória.")
        print("Para testar o SQL Server, defina USE_SQL_SERVER=True no .env")
        
        # Mesmo assim, vamos tentar testar a string de conexão se ela não for sqlite
        if "sqlite" in str(settings.DATABASE_URL):
            print("⏹️ Configurado para SQLite. Teste encerrado.")
            return
        else:
            print("🔄 Forçando teste de conexão com a URL configurada mesmo com a flag desativada...")

    # Criar engine de teste
    try:
        url = str(settings.DATABASE_URL)
        print(f"\nTentando conectar...")
        
        # Timeout curto para não travar
        engine = create_async_engine(
            url,
            echo=False,
            connect_args={"timeout": 5} 
        )
        
        async with engine.connect() as conn:
            print("✅ Conexão estabelecida com sucesso!")
            
            result = await conn.execute(text("SELECT @@VERSION"))
            version = result.scalar()
            print(f"📊 Versão do SQL Server: {version}")
            
            # Teste de permissão básica
            try:
                await conn.execute(text("SELECT 1"))
                print("✅ Consulta básica (SELECT 1) executada com sucesso.")
            except Exception as e:
                print(f"❌ Erro na consulta básica: {e}")

        await engine.dispose()
        print("\n🎉 Teste concluído com SUCESSO.")
        
    except Exception as e:
        print("\n❌ FALHA NA CONEXÃO:")
        print(f"   Erro: {str(e)}")
        print("\nVerifique:")
        print("   1. Se o servidor SQL Server está rodando")
        print("   2. Se as credenciais no .env estão corretas")
        print("   3. Se o firewall permite conexão na porta 1433")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\nTeste cancelado pelo usuário.")
