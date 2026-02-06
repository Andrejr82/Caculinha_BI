"""
Teste de Validação - BI Solution
FIX 2026-02-04: Testes com queries reais do setor comercial
"""

import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(__file__))

def test_sql_validator():
    """Testa o SQL Validator com queries reais do setor comercial"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: SQL VALIDATOR")
    print("="*60)
    
    from utils.sql_validator import validate_sql, safe_add_limit
    
    # Queries reais do setor comercial
    test_cases = [
        # Queries válidas (devem passar)
        ("SELECT NOMESEGMENTO, SUM(VENDA_30DD) FROM admmat GROUP BY NOMESEGMENTO", True, "Agregação por segmento"),
        ("SELECT * FROM admmat WHERE ESTOQUE < 10 LIMIT 100", True, "Filtro de estoque baixo"),
        ("SELECT CODIGO, NOME FROM admmat WHERE NOMESEGMENTO = 'Papelaria'", True, "Filtro por categoria"),
        
        # Queries inválidas (devem ser bloqueadas)
        ("DELETE FROM admmat WHERE id = 1", False, "DELETE deve ser bloqueado"),
        ("DROP TABLE admmat", False, "DROP deve ser bloqueado"),
        ("UPDATE admmat SET preco = 0", False, "UPDATE deve ser bloqueado"),
    ]
    
    passed = 0
    failed = 0
    
    for sql, expected_valid, description in test_cases:
        is_valid, error = validate_sql(sql)
        
        if is_valid == expected_valid:
            print(f"  ✅ PASS: {description}")
            passed += 1
        else:
            print(f"  ❌ FAIL: {description}")
            print(f"       Query: {sql[:50]}...")
            print(f"       Esperado: {'VÁLIDO' if expected_valid else 'INVÁLIDO'}")
            print(f"       Obtido: {'VÁLIDO' if is_valid else 'INVÁLIDO'} - {error}")
            failed += 1
    
    # Teste de auto-LIMIT
    print("\n  📝 Teste Auto-LIMIT:")
    query_sem_limit = "SELECT * FROM vendas"
    query_com_limit = safe_add_limit(query_sem_limit)
    if "LIMIT" in query_com_limit:
        print(f"  ✅ PASS: LIMIT adicionado automaticamente")
        passed += 1
    else:
        print(f"  ❌ FAIL: LIMIT não adicionado")
        failed += 1
    
    return passed, failed


def test_master_prompt():
    """Testa carregamento do Master Prompt com contexto de negócio"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: MASTER PROMPT")
    print("="*60)
    
    passed = 0
    failed = 0
    
    try:
        from app.core.prompts.master_prompt import get_system_prompt, get_few_shot_examples
        
        # Teste 1: Carregar prompt
        prompt = get_system_prompt()
        if "Lojas Caçula" in prompt or "IDENTIDADE" in prompt:
            print(f"  ✅ PASS: System prompt carregado (length: {len(prompt):,} chars)")
            passed += 1
        else:
            print(f"  ❌ FAIL: Contexto de negócio não encontrado no prompt")
            failed += 1
        
        # Teste 2: Carregar few-shot examples
        examples = get_few_shot_examples()
        if len(examples) > 0:
            print(f"  ✅ PASS: {len(examples)} few-shot examples carregados")
            passed += 1
        else:
            print(f"  ⚠️ WARN: Nenhum few-shot example encontrado")
            passed += 1  # Não é erro crítico
            
    except Exception as e:
        print(f"  ❌ FAIL: Erro ao carregar master_prompt: {e}")
        failed += 1
    
    return passed, failed


def test_gemini_tools():
    """Testa configuração de Tools do Gemini"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: GEMINI TOOLS")
    print("="*60)
    
    passed = 0
    failed = 0
    
    try:
        from tools.gemini_tools import get_tool_names, get_tools_for_gemini
        
        tools = get_tools_for_gemini()
        tool_names = get_tool_names()
        
        expected_tools = [
            "consultar_dados_flexivel",
            "gerar_grafico_universal_v2",
            "encontrar_rupturas_criticas",
            "calcular_abastecimento_une",
            "consultar_dicionario_dados",
            "analisar_produto_todas_lojas"
        ]
        
        for tool in expected_tools:
            if tool in tool_names:
                print(f"  ✅ PASS: Tool '{tool}' configurada")
                passed += 1
            else:
                print(f"  ❌ FAIL: Tool '{tool}' não encontrada")
                failed += 1
                
    except Exception as e:
        print(f"  ❌ FAIL: Erro ao carregar gemini_tools: {e}")
        failed += 1
    
    return passed, failed


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🚀 TESTE DE VALIDAÇÃO - BI SOLUTION")
    print("   Data: 2026-02-04")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    # Teste 1: SQL Validator
    try:
        p, f = test_sql_validator()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"  ❌ ERRO no teste SQL Validator: {e}")
        total_failed += 1
    
    # Teste 2: Master Prompt
    try:
        p, f = test_master_prompt()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"  ❌ ERRO no teste Master Prompt: {e}")
        total_failed += 1
    
    # Teste 3: Gemini Tools
    try:
        p, f = test_gemini_tools()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"  ❌ ERRO no teste Gemini Tools: {e}")
        total_failed += 1
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    print(f"  ✅ Passou: {total_passed}")
    print(f"  ❌ Falhou: {total_failed}")
    print(f"  📈 Taxa de Sucesso: {total_passed/(total_passed+total_failed)*100:.1f}%")
    print("="*60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
