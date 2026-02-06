"""
Script de teste completo para validar ChatBI modernizado
Testa: Gemini 2.0, ferramenta flexível, integração com agente
"""

import sys
import os

# Adicionar path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_1_imports():
    """Teste 1: Verificar imports"""
    print("\n🧪 TESTE 1: Verificando imports...")
    try:
        from app.core.tools.flexible_query_tool import consultar_dados_flexivel
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from app.config.settings import settings
        print("✅ Todos os imports OK")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False


def test_2_model_config():
    """Teste 2: Verificar configuração do modelo"""
    print("\n🧪 TESTE 2: Verificando configuração do modelo...")
    try:
        from app.config.settings import settings
        model = settings.LLM_MODEL_NAME
        print(f"   Modelo configurado: {model}")
        
        if "gemini-3-flash-preview" in model:
            print("✅ Modelo Gemini 3 Flash Preview configurado corretamente")
            return True
        else:
            print(f"⚠️  Modelo ainda é: {model}")
            print("   Esperado: gemini-3-flash-preview")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar modelo: {e}")
        return False


def test_3_flexible_tool():
    """Teste 3: Testar ferramenta flexível"""
    print("\n🧪 TESTE 3: Testando ferramenta flexível...")
    try:
        from app.core.tools.flexible_query_tool import consultar_dados_flexivel
        
        # Teste simples: buscar dados sem filtros
        result = consultar_dados_flexivel.invoke({"limite": 5})
        
        if isinstance(result, dict) and "resultados" in result:
            total = result.get("total_resultados", 0)
            print(f"   Retornou {total} resultados")
            print("✅ Ferramenta flexível funcionando")
            return True
        else:
            print(f"❌ Resultado inesperado: {type(result)}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar ferramenta: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_agent_tools():
    """Teste 4: Verificar ferramentas do agente"""
    print("\n🧪 TESTE 4: Verificando ferramentas do agente...")
    try:
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from app.core.llm_gemini_adapter import GeminiLLMAdapter
        from app.core.utils.field_mapper import FieldMapper
        
        # Criar instância do agente (sem executar)
        llm = GeminiLLMAdapter()
        field_mapper = FieldMapper()
        agent = CaculinhaBIAgent(llm=llm, code_gen_agent=None, field_mapper=field_mapper)
        
        num_tools = len(agent.bi_tools)
        tool_names = [t.name for t in agent.bi_tools]
        
        print(f"   Total de ferramentas: {num_tools}")
        print(f"   Ferramentas: {', '.join(tool_names)}")
        
        # Verificar se consultar_dados_flexivel está presente
        if "consultar_dados_flexivel" in tool_names:
            print("✅ Ferramenta flexível integrada ao agente")
            return True
        else:
            print("❌ Ferramenta flexível NÃO encontrada no agente")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar agente: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_parquet_config():
    """Teste 5: Verificar configuração do Parquet"""
    print("\n🧪 TESTE 5: Verificando configuração do Parquet...")
    try:
        from app.config.settings import settings
        import os
        
        parquet_path = settings.PARQUET_FILE_PATH
        print(f"   Caminho configurado: {parquet_path}")
        
        # Verificar se arquivo existe
        full_path = os.path.join(os.getcwd(), parquet_path)
        if os.path.exists(full_path):
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"   Arquivo encontrado: {size_mb:.2f} MB")
            print("✅ Configuração do Parquet OK")
            return True
        else:
            print(f"⚠️  Arquivo não encontrado em: {full_path}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar Parquet: {e}")
        return False


def main():
    """Executar todos os testes"""
    print("=" * 60)
    print("🚀 TESTES DO CHATBI MODERNIZADO")
    print("=" * 60)
    
    tests = [
        test_1_imports,
        test_2_model_config,
        test_3_flexible_tool,
        test_4_agent_tools,
        test_5_parquet_config,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Erro fatal no teste: {e}")
            results.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"\nTestes passados: {passed}/{total} ({percentage:.0f}%)")
    
    if percentage == 100:
        print("\n✅ TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
        return 0
    elif percentage >= 80:
        print("\n⚠️  Maioria dos testes passou. Verificar falhas.")
        return 1
    else:
        print("\n❌ Muitos testes falharam. Revisar implementação.")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
