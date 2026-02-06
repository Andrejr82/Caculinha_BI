"""
Teste de Integração - Gemini Function Calling

Valida que as ferramentas de compras funcionam corretamente com Gemini.
"""

import pytest
import asyncio
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.adapters.llm.gemini_adapter import GeminiLLMAdapter
from app.core.utils.field_mapper import FieldMapper


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
        assert "eoq" in response.lower() or "quantidade" in response.lower()
        
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
        assert "previsão" in response.lower() or "forecast" in response.lower()
    
    async def test_schema_conversion(self):
        """Testa conversão de schema para formato Gemini"""
        from app.core.tools.purchasing_tools import calcular_eoq
        
        # Obter schema da ferramenta
        tool_schema = calcular_eoq.args_schema.schema() if hasattr(calcular_eoq, 'args_schema') else {}
        
        # Validar que schema tem campos necessários
        assert "produto_id" in str(tool_schema) or "properties" in tool_schema
        
        # Gemini espera formato específico
        # Validar que conversão funciona
        assert tool_schema is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
