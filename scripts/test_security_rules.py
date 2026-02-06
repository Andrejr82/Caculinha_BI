"""
Teste de Segurança: Validar que o agente NÃO expõe detalhes técnicos
Simula perguntas que tentam extrair informações internas do schema.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

def test_security_rules():
    print("=== TESTE DE SEGURANÇA: NÃO EXPOSIÇÃO DE DETALHES TÉCNICOS ===\n")
    
    # 1. Importar o Master Prompt
    print("1. Verificando regras de segurança no MASTER_PROMPT...")
    try:
        from app.core.prompts.master_prompt import MASTER_PROMPT
        print("[OK] Master Prompt importado.")
    except Exception as e:
        print(f"[ERRO] Falha ao importar: {e}")
        return
    
    # 2. Verificar se as regras de segurança estão presentes
    print("\n2. Verificando presença de regras de segurança...")
    
    security_keywords = [
        "NUNCA exponha detalhes técnicos",
        "Não liste nomes de colunas",
        "linguagem de negócios",
        "redirecione para análises práticas"
    ]
    
    found_rules = []
    for keyword in security_keywords:
        if keyword in MASTER_PROMPT:
            found_rules.append(keyword)
    
    print(f"[RESULTADO] Regras de segurança encontradas: {len(found_rules)}/{len(security_keywords)}")
    
    if len(found_rules) < len(security_keywords):
        print("[AVISO] Algumas regras de segurança estão faltando!")
        missing = [k for k in security_keywords if k not in found_rules]
        print(f"        Faltando: {missing}")
    else:
        print("[OK] ✅ Todas as regras de segurança estão presentes.")
    
    # 3. Verificar exemplos de comportamento proibido
    print("\n3. Verificando exemplos de comportamento PROIBIDO...")
    
    prohibited_examples = [
        "❌ Não liste nomes de colunas",
        "❌ Não mostre JSONs crus",
        "VENDA_30DD",  # Exemplo de coluna técnica mencionada como proibida
        "LIQUIDO_38"   # Outro exemplo
    ]
    
    found_prohibited = []
    for example in prohibited_examples:
        if example in MASTER_PROMPT:
            found_prohibited.append(example)
    
    print(f"[RESULTADO] Exemplos de comportamento proibido: {len(found_prohibited)}/{len(prohibited_examples)}")
    
    # 4. Verificar exemplos de comportamento CORRETO
    print("\n4. Verificando exemplos de comportamento CORRETO...")
    
    correct_examples = [
        "✅ Fale em **linguagem de negócios**",
        "vendas dos últimos 30 dias",
        "preço de venda",
        "estoque atual"
    ]
    
    found_correct = []
    for example in correct_examples:
        if example in MASTER_PROMPT:
            found_correct.append(example)
    
    print(f"[RESULTADO] Exemplos de comportamento correto: {len(found_correct)}/{len(correct_examples)}")
    
    # 5. Preview da seção de segurança
    print("\n5. Preview da seção de REGRAS DE SEGURANÇA:")
    print("=" * 80)
    if "### 🔴 REGRAS DE SEGURANÇA" in MASTER_PROMPT:
        start_idx = MASTER_PROMPT.index("### 🔴 REGRAS DE SEGURANÇA")
        # Encontrar o próximo ---
        end_idx = MASTER_PROMPT.find("---", start_idx)
        if end_idx != -1:
            security_section = MASTER_PROMPT[start_idx:end_idx]
            print(security_section)
        else:
            print(MASTER_PROMPT[start_idx:start_idx+500])
    else:
        print("[AVISO] Seção de segurança não encontrada!")
    print("=" * 80)
    
    # 6. Conclusão
    print("\n=== CONCLUSÃO ===")
    if len(found_rules) == len(security_keywords) and len(found_correct) >= 3:
        print("✅ SUCESSO: As regras de segurança estão configuradas corretamente!")
        print("\n📝 COMPORTAMENTO ESPERADO:")
        print("   Usuário: 'Quais colunas de vendas você tem?'")
        print("   Agente: 'Posso ajudar com análises de vendas como:")
        print("           - Vendas dos últimos 30 dias")
        print("           - Histórico mensal")
        print("           - Comparações entre lojas'")
        print("\n   (SEM expor nomes técnicos como VENDA_30DD, MES_01, etc.)")
    else:
        print("❌ FALHA: As regras de segurança não estão completas.")
        print("   Verifique os logs acima para detalhes.")

if __name__ == "__main__":
    test_security_rules()
