"""
Script de Teste: Validação da Injeção de Schema no Agente
Verifica se o CaculinhaBIAgent recebe corretamente as colunas do banco de dados.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

def test_schema_injection():
    print("=== TESTE: INJEÇÃO DE SCHEMA NO AGENTE ===\n")
    
    # 1. Importar dependências
    print("1. Importando CaculinhaBIAgent...")
    try:
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from app.core.llm_genai_adapter import GeminiLLMAdapter
        from app.core.utils.field_mapper import FieldMapper
        print("[OK] Imports bem-sucedidos.")
    except Exception as e:
        print(f"[ERRO] Falha ao importar: {e}")
        return
    
    # 2. Criar instância do agente (sem CodeGenAgent para simplificar)
    print("\n2. Criando instância do CaculinhaBIAgent...")
    try:
        # Mock LLM adapter (não vamos chamar a API)
        llm = GeminiLLMAdapter(api_key="fake_key_for_testing")
        field_mapper = FieldMapper()
        
        # Criar agente (CodeGenAgent pode ser None para este teste)
        agent = CaculinhaBIAgent(
            llm=llm,
            code_gen_agent=None,
            field_mapper=field_mapper,
            user_role="analyst",
            enable_rag=False  # Desabilitar RAG para simplificar
        )
        print("[OK] Agente criado com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao criar agente: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Verificar se o system_prompt contém as colunas
    print("\n3. Verificando injeção de schema no system_prompt...")
    
    # Verificar se o placeholder foi substituído
    if "[SCHEMA_INJECTION_POINT]" in agent.system_prompt:
        print("[FALHA] ❌ Placeholder [SCHEMA_INJECTION_POINT] ainda presente no prompt!")
        print("         A substituição não ocorreu.")
        return
    
    # Verificar se as colunas prioritárias estão presentes
    expected_columns = ['PRODUTO', 'NOME', 'UNE', 'VENDA_30DD', 'ESTOQUE_UNE', 'LIQUIDO_38']
    found_columns = []
    missing_columns = []
    
    for col in expected_columns:
        if f"`{col}`" in agent.system_prompt:
            found_columns.append(col)
        else:
            missing_columns.append(col)
    
    print(f"\n[RESULTADO] Colunas esperadas encontradas: {len(found_columns)}/{len(expected_columns)}")
    print(f"            Encontradas: {found_columns}")
    
    if missing_columns:
        print(f"            ⚠️ Faltando: {missing_columns}")
    
    # Verificar se as instruções importantes estão presentes
    print("\n4. Verificando instruções importantes no prompt...")
    important_phrases = [
        "COLUNAS PRIORITÁRIAS",
        "NUNCA invente nomes de colunas",
        "consultar_dicionario_dados",
        "MES_01",
        "LIQUIDO_38"
    ]
    
    found_phrases = []
    for phrase in important_phrases:
        if phrase in agent.system_prompt:
            found_phrases.append(phrase)
    
    print(f"[RESULTADO] Instruções encontradas: {len(found_phrases)}/{len(important_phrases)}")
    print(f"            Encontradas: {found_phrases}")
    
    # 5. Mostrar preview do prompt injetado
    print("\n5. Preview do System Prompt (primeiros 1000 caracteres):")
    print("=" * 80)
    print(agent.system_prompt[:1000])
    print("=" * 80)
    
    # 6. Conclusão
    print("\n=== CONCLUSÃO ===")
    if len(found_columns) == len(expected_columns) and len(found_phrases) >= 4:
        print("✅ SUCESSO: A injeção de schema está funcionando corretamente!")
        print("   O agente agora conhece as colunas do banco de dados.")
    else:
        print("❌ FALHA: A injeção de schema não está completa.")
        print("   Verifique os logs acima para detalhes.")

if __name__ == "__main__":
    test_schema_injection()
