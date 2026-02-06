"""
Teste para capturar a resposta RAW do LLM
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

async def test_llm_raw_response():
    print("\n=== TESTE DA RESPOSTA RAW DO LLM ===\n")
    
    try:
        from app.services.data_aggregation import DataAggregationService
        from app.core.llm_factory import LLMFactory
        from app.config.settings import settings
        import json
        
        # 1. Pegar dados
        print("[1/2] Coletando dados...")
        data_summary = DataAggregationService.get_retail_summary()
        print(f"OK - Vendas: {data_summary['general_stats']['total_sales_30d']}")
        
        # 2. Preparar prompt
        system_instruction = (
            "Voce e um Cientista de Dados Senior especializado em Varejo. "
            "Sua tarefa e analisar os dados fornecidos e gerar 3 a 5 insights estrategicos CURIOSOS e ACIONAVEIS.\n"
            "Foque em: Anomalias (Rupturas criticas), Oportunidades (Produtos vendendo muito bem) e Saude do Estoque.\n"
            "IMPORTANTE: Retorne APENAS um JSON valido (lista de objetos). Nao coloque markdown ```json```.\n"
            "Formato esperado:\n"
            "[\n"
            "  {\n"
            '    "title": "Titulo Impactante",\n'
            '    "description": "Explicacao clara do problema ou oportunidade com numeros (ex: Produto X vendendo 2x a media).",\n'
            '    "category": "inventory" | "sales" | "growth" | "alert",\n'
            '    "severity": "high" | "medium" | "low",\n'
            '    "recommendation": "Acao concreta (ex: Comprar X unidades, Verificar exposicao)."\n'
            "  }\n"
            "]"
        )
        
        user_message = f"""
        Aqui estao os dados atuais da loja (Resumo):
        
        Totais:
        {json.dumps(data_summary.get('general_stats', {}), indent=2)}
        
        Top Vendas (Destaques):
        {json.dumps(data_summary.get('top_performing_products', [])[:5], indent=2)}
        
        Rupturas (Critico - Venda sem Estoque):
        {json.dumps(data_summary.get('critical_measurements', {}).get('stockouts', [])[:5], indent=2)}
        
        Estoque Parado (Atencao):
        {json.dumps(data_summary.get('critical_measurements', {}).get('dead_stock', [])[:5], indent=2)}
        
        Gere 4 insights focados nos problemas mais graves ou maiores oportunidades acima.
        Se houver rupturas, priorize-as como severidade 'high'.
        
        RESPOSTA (APENAS JSON):
        """
        
        # 3. Chamar LLM
        print(f"\n[2/2] Chamando LLM ({settings.LLM_PROVIDER})...")
        llm = LLMFactory.get_adapter(provider=settings.LLM_PROVIDER, use_smart=True)
        
        if hasattr(llm, 'system_instruction'):
            llm.system_instruction = system_instruction
        
        response_text = await llm.generate_response(user_message)
        
        print("\n" + "="*60)
        print("RESPOSTA RAW DO LLM:")
        print("="*60)
        print(response_text)
        print("="*60)
        
        # 4. Tentar parsear
        print("\nTentando parsear JSON...")
        try:
            # Limpar markdown
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            print(f"\n[OK] JSON parseado com sucesso!")
            print(f"Tipo: {type(data)}")
            print(f"Numero de insights: {len(data) if isinstance(data, list) else 'N/A'}")
            
            if isinstance(data, list) and len(data) > 0:
                print(f"\nPrimeiro insight:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"\n[ERRO] Falha ao parsear JSON: {e}")
            print(f"Texto limpo tentado:")
            print(clean_text[:500])
            return False
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_raw_response())
    print(f"\nResultado: {'SUCESSO' if success else 'FALHA'}")
