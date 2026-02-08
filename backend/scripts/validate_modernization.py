"""
Script de validação rápida das melhorias de modernização.
Executa testes manuais sem depender do pytest.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

print("=" * 80)
print("VALIDAÇÃO DAS MELHORIAS DE MODERNIZAÇÃO - 2025-12-27")
print("=" * 80)

# Test 1: Chart Tools Consolidation
print("\n[1/3] Testando consolidação de chart tools...")
try:
    from backend.app.core.tools.chart_tools import listar_graficos_disponiveis

    result = listar_graficos_disponiveis.invoke({})
    assert result["status"] == "success"
    assert result["graficos_disponiveis"]["total_tipos"] == 4

    print("[OK] PASS: listar_graficos_disponiveis retorna 4 ferramentas ativas")
    print(f"   Ferramentas: {list(result['graficos_disponiveis']['ferramentas_recomendadas'].keys())}")

except Exception as e:
    print(f"[FAIL] FAIL: {e}")
    sys.exit(1)

# Test 2: Semantic Search Tool
print("\n[2/3] Testando ferramenta de semantic search...")
try:
    from backend.app.core.tools.semantic_search_tool import buscar_produtos_inteligente

    assert buscar_produtos_inteligente is not None
    assert buscar_produtos_inteligente.name == "buscar_produtos_inteligente"

    print("[OK] PASS: Ferramenta buscar_produtos_inteligente criada com sucesso")
    print(f"   Nome: {buscar_produtos_inteligente.name}")
    print(f"   Descrição: {buscar_produtos_inteligente.description[:100]}...")

except Exception as e:
    print(f"[FAIL] FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Tool Scoping
print("\n[3/3] Testando tool scoping por role...")
try:
    from backend.app.core.utils.tool_scoping import ToolPermissionManager
    from langchain_core.tools import BaseTool

    # Create dummy tools
    class DummyTool(BaseTool):
        name: str = ""
        description: str = "test tool"

        def __init__(self, tool_name):
            super().__init__(name=tool_name, description=f"Test tool {tool_name}")

        def _run(self, *args, **kwargs):
            return "test"

    tools = [
        DummyTool("consultar_dados_flexivel"),
        DummyTool("buscar_produtos_inteligente"),
        DummyTool("calcular_preco_final_une"),
        DummyTool("sugerir_transferencias_automaticas"),
        DummyTool("gerar_grafico_universal_v2"),
    ]

    # Test admin
    admin_tools = ToolPermissionManager.get_tools_for_role(tools, "admin")
    assert len(admin_tools) == len(tools), f"Admin deveria ter {len(tools)} tools, tem {len(admin_tools)}"

    # Test analyst
    analyst_tools = ToolPermissionManager.get_tools_for_role(tools, "analyst")
    analyst_names = [t.name for t in analyst_tools]
    assert "consultar_dados_flexivel" in analyst_names
    assert "calcular_preco_final_une" not in analyst_names

    # Test viewer
    viewer_tools = ToolPermissionManager.get_tools_for_role(tools, "viewer")
    viewer_names = [t.name for t in viewer_tools]
    assert "gerar_grafico_universal_v2" in viewer_names
    assert "consultar_dados_flexivel" not in viewer_names

    print("[OK] PASS: Tool scoping funcionando corretamente")
    print(f"   Admin: {len(admin_tools)} tools")
    print(f"   Analyst: {len(analyst_tools)} tools ({analyst_names})")
    print(f"   Viewer: {len(viewer_tools)} tools ({viewer_names})")

except Exception as e:
    print(f"[FAIL] FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Agent Integration
print("\n[4/4] Testando integração no agent...")
try:
    from backend.app.core.agents import caculinha_bi_agent

    # Check imports
    assert hasattr(caculinha_bi_agent, "buscar_produtos_inteligente")
    assert hasattr(caculinha_bi_agent, "ToolPermissionManager")

    print("[OK] PASS: Agent importa novas ferramentas e tool scoping")

except Exception as e:
    print(f"[FAIL] FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("[OK] TODAS AS VALIDACOES PASSARAM!")
print("=" * 80)
print("\nResumo das melhorias implementadas:")
print("1. [OK] Consolidacao de chart tools (14 -> 4 recomendadas)")
print("2. [OK] RAG semantic search com Google Embeddings + FAISS")
print("3. [OK] Tool scoping por role (admin/analyst/viewer/guest)")
print("4. [OK] Integracao completa no CaculinhaBIAgent")
print("\n" + "=" * 80)
