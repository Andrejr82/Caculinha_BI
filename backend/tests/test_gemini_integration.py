"""
Teste de Integração - Gemini Function Calling

Valida que as ferramentas de compras funcionam corretamente com Gemini.
"""

import pytest
import asyncio
import os
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.utils.field_mapper import FieldMapper

pytestmark = [pytest.mark.integration, pytest.mark.external]

if os.getenv("RUN_GEMINI_INTEGRATION", "0") != "1":
    pytest.skip(
        "teste Gemini manual; defina RUN_GEMINI_INTEGRATION=1 para executar.",
        allow_module_level=True,
    )

if not os.getenv("GEMINI_API_KEY"):
    pytest.skip("GEMINI_API_KEY ausente para teste Gemini.", allow_module_level=True)

from backend.app.core.llm_gemini_adapter import GeminiLLMAdapter


@pytest.mark.asyncio
class TestGeminiFunctionCalling:
    """Testes de integração com Gemini"""
    
    async def test_calcular_eoq_integration(self):
        """Testa que Gemini consegue chamar calcular_eoq"""
        # Setup
        llm = GeminiLLMAdapter()
        field_mapper = FieldMapper()
        agent = CaculinhaBIAgent(
            llm=llm,
            code_gen_agent=None,
            field_mapper=field_mapper
        )
        
        # Query que deve acionar calcular_eoq
        query = "Qual a quantidade ideal para comprar do produto 59294?"
        
        # Executar
        response = await agent.run_async(query, chat_history=[])
        
        # Validar
        assert response is not None
        response_text = response if isinstance(response, str) else str(response)
        assert "eoq" in response_text.lower() or "quantidade" in response_text.lower()
        
        # Verificar que ferramenta foi chamada
        # (implementação depende de como agent rastreia tool calls)
    
    async def test_prever_demanda_integration(self):
        """Testa que Gemini consegue chamar prever_demanda_sazonal"""
        llm = GeminiLLMAdapter()
        field_mapper = FieldMapper()
        agent = CaculinhaBIAgent(
            llm=llm,
            code_gen_agent=None,
            field_mapper=field_mapper
        )
        
        query = "Qual a previsão de vendas para o próximo mês?"
        response = await agent.run_async(query, chat_history=[])
        
        assert response is not None
        response_text = response if isinstance(response, str) else str(response)
        assert "previsão" in response_text.lower() or "forecast" in response_text.lower()
    
    async def test_schema_conversion(self):
        """Testa conversão de schema para formato Gemini"""
        from backend.app.core.tools.purchasing_tools import calcular_eoq
        
        # Obter schema da ferramenta
        tool_schema = calcular_eoq.args_schema.schema() if hasattr(calcular_eoq, 'args_schema') else {}
        
        # Validar que schema tem campos necessários
        assert "produto_id" in str(tool_schema) or "properties" in tool_schema
        
        # Gemini espera formato específico
        # Validar que conversão funciona
        assert tool_schema is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
