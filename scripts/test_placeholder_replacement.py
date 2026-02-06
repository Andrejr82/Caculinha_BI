"""
Script de Teste Simplificado: Validação da Substituição do Placeholder
Testa apenas a lógica de substituição sem instanciar o agente completo.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

def test_placeholder_replacement():
    print("=== TESTE: SUBSTITUIÇÃO DO PLACEHOLDER [SCHEMA_INJECTION_POINT] ===\n")
    
    # 1. Importar o Master Prompt
    print("1. Importando MASTER_PROMPT...")
    try:
        from app.core.prompts.master_prompt import MASTER_PROMPT
        print("[OK] Master Prompt importado.")
    except Exception as e:
        print(f"[ERRO] Falha ao importar: {e}")
        return
    
    # 2. Verificar se o placeholder existe
    print("\n2. Verificando presença do placeholder...")
    if "[SCHEMA_INJECTION_POINT]" in MASTER_PROMPT:
        print("[OK] ✅ Placeholder [SCHEMA_INJECTION_POINT] encontrado no MASTER_PROMPT.")
    else:
        print("[FALHA] ❌ Placeholder [SCHEMA_INJECTION_POINT] NÃO encontrado!")
        print("         O prompt precisa conter este placeholder para a injeção funcionar.")
        return
    
    # 3. Simular a injeção de schema (mesma lógica do CaculinhaBIAgent)
    print("\n3. Simulando injeção de schema...")
    try:
        from app.core.data_source_manager import get_data_manager
        
        manager = get_data_manager()
        cols = manager.get_columns()
        
        important_keywords = ['PRODUTO', 'NOME', 'UNE', 'SEGMENTO', 'CATEGORIA', 'VENDA', 'ESTOQUE', 'PRECO', 'CUSTO', 'LIQUIDO', 'MARGEM', 'FABRICANTE']
        priority_cols = [c for c in cols if any(k in c.upper() for k in important_keywords)]
        other_cols = [c for c in cols if c not in priority_cols]
        
        schema_str = f"""Você tem acesso a um banco de dados Parquet com **{len(cols)} colunas**.

**📊 COLUNAS PRIORITÁRIAS ({len(priority_cols)} colunas):**
Use estas colunas preferencialmente para análises. Elas cobrem os principais casos de uso:
{", ".join([f"`{c}`" for c in priority_cols])}

**📁 OUTRAS COLUNAS DISPONÍVEIS ({len(other_cols)} colunas):**
{", ".join([f"`{c}`" for c in other_cols[:30]])}
{f"... (+{len(other_cols)-30} colunas adicionais)" if len(other_cols) > 30 else ""}

**⚠️ IMPORTANTE:**
- Se precisar de TODAS as colunas ou descrições detalhadas, use a ferramenta `consultar_dicionario_dados()`.
- NUNCA invente nomes de colunas. Use APENAS as listadas acima.
- Para histórico de vendas, use: `MES_01` a `MES_12` (vendas mensais) ou `VENDA_30DD` (últimos 30 dias).
- Para preços: `LIQUIDO_38` (preço de venda) e `ULTIMA_ENTRADA_CUSTO_CD` (custo).
"""
        
        # Fazer a substituição
        injected_prompt = MASTER_PROMPT.replace("[SCHEMA_INJECTION_POINT]", schema_str)
        
        print(f"[OK] Schema injetado com sucesso!")
        print(f"     Total de colunas: {len(cols)}")
        print(f"     Colunas prioritárias: {len(priority_cols)}")
        print(f"     Outras colunas: {len(other_cols)}")
        
    except Exception as e:
        print(f"[ERRO] Falha ao simular injeção: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Verificar se a substituição funcionou
    print("\n4. Verificando resultado da substituição...")
    
    if "[SCHEMA_INJECTION_POINT]" in injected_prompt:
        print("[FALHA] ❌ Placeholder ainda presente após substituição!")
        return
    
    # Verificar se as colunas esperadas estão presentes
    expected_columns = ['PRODUTO', 'NOME', 'UNE', 'VENDA_30DD', 'ESTOQUE_UNE', 'LIQUIDO_38']
    found_columns = []
    
    for col in expected_columns:
        if f"`{col}`" in injected_prompt:
            found_columns.append(col)
    
    print(f"[RESULTADO] Colunas esperadas encontradas: {len(found_columns)}/{len(expected_columns)}")
    print(f"            Encontradas: {found_columns}")
    
    # 5. Preview do prompt injetado
    print("\n5. Preview da seção injetada (primeiros 800 caracteres):")
    print("=" * 80)
    # Encontrar a seção de DADOS DISPONÍVEIS
    if "## 🗄️ DADOS DISPONÍVEIS" in injected_prompt:
        start_idx = injected_prompt.index("## 🗄️ DADOS DISPONÍVEIS")
        preview = injected_prompt[start_idx:start_idx+800]
        print(preview)
    else:
        print("[AVISO] Seção '## 🗄️ DADOS DISPONÍVEIS' não encontrada.")
    print("=" * 80)
    
    # 6. Conclusão
    print("\n=== CONCLUSÃO ===")
    if len(found_columns) == len(expected_columns):
        print("✅ SUCESSO: A lógica de injeção de schema está funcionando corretamente!")
        print("   O placeholder foi substituído e as colunas foram injetadas.")
        print("\n📝 PRÓXIMO PASSO:")
        print("   Reinicie o backend para que o agente carregue o novo prompt.")
        print("   Depois, teste perguntando: 'Quais colunas de vendas você tem?'")
    else:
        print("❌ FALHA: Algumas colunas esperadas não foram encontradas.")
        print("   Verifique os logs acima para detalhes.")

if __name__ == "__main__":
    test_placeholder_replacement()
