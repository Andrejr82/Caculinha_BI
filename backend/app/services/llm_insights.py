
import logging
import json
from typing import List, Dict, Any
from backend.app.core.llm_factory import LLMFactory
from backend.app.services.data_aggregation import DataAggregationService

logger = logging.getLogger(__name__)

class LLMInsightsService:
    """
    Serviço coordenador para gerar insights de varejo usando LLM (Gemini/Groq)
    baseado em dados reais agregados.
    """
    
    @staticmethod
    async def generate_proactive_insights(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Orquestra o fluxo:
        1. Obtém resumo dos dados (DataAggregationService)
        2. Monta prompt com dados reais
        3. Chama LLM via SmartLLM
        4. Trata e retorna JSON
        """
        try:
            # 1. Coleta Dados
            data_summary = DataAggregationService.get_retail_summary(filters=filters)
            
            # Se houver erro na coleta, retornar fallback seguro ou erro tratado
            if "error" in data_summary:
                logger.warning(f"Falha na coleta de dados para insights: {data_summary['error']}")
                return _get_fallback_insights()

            # 2. Prepara Prompt
            
            # Ajuste de contexto por segmento
            contexto_segmento = "CONTEXTO: Análise Global da Loja"
            if filters and filters.get("segments"):
                segs = ", ".join(filters["segments"])
                contexto_segmento = f"CONTEXTO ESPECÍFICO: Você está analisando APENAS o(s) segmento(s): {segs}. Adapte seus insights para este nicho de mercado."

            # Context7 Style: Gestor de Varejo focado em AÇÕES URGENTES
            system_instruction = (
                "Você é um GESTOR DE VAREJO SÊNIOR especializado em identificar AÇÕES URGENTES para maximizar vendas e reduzir perdas.\\n"
                f"{contexto_segmento}\\n\\n"
                "MISSÃO: Gerar 4 insights PRIORIZADOS POR URGÊNCIA que o gestor deve AGIR IMEDIATAMENTE ao fazer login.\\n\\n"
                
                "PRIORIZAÇÃO (do mais para o menos urgente):\\n"
                "1. RUPTURAS CRÍTICAS (severity: high) - Produtos vendendo MAS SEM ESTOQUE = PERDA DE VENDA AGORA\\n"
                "2. PRODUTOS DE ALTO GIRO (severity: medium) - Risco de ruptura em breve, reabastecer preventivamente\\n"
                "3. ESTOQUE PARADO (severity: medium) - Capital imobilizado, criar promoção/liquidação\\n"
                "4. OPORTUNIDADES (severity: low) - Produtos com potencial de crescimento\\n\\n"
                
                "TÉCNICAS DE VAREJO A APLICAR:\\n"
                "- Ruptura = Reposição URGENTE (calcular demanda de 15-30 dias)\\n"
                "- Alto Giro = Aumentar ponto de pedido, negociar com fornecedor\\n"
                "- Estoque Parado = Promoção relâmpago, bundle, desconto progressivo\\n"
                "- Sazonalidade = Antecipar demanda, ajustar mix de produtos\\n\\n"
                
                "FORMATO OBRIGATÓRIO DO INSIGHT:\\n"
                "- Title: '[URGÊNCIA] Problema - Impacto R$' (máx 80 chars)\\n"
                "  Exemplos: '[CRÍTICO] Ruptura TNT Preto - Perda R$ 18K/mês'\\n"
                "           '[ATENÇÃO] Papel A4 - Risco ruptura em 5 dias'\\n"
                "           '[AÇÃO] 500K em estoque parado - Liquidar'\\n\\n"
                
                "REGRAS ANTI-GENÉRICAS (CRÍTICO):\\n"
                "1. PROIBIDO dizer 'Identificamos produtos...' ou 'Vários itens...'.\\n"
                "2. VOCÊ DEVE CITAR O NOME EXATO DO PRODUTO (Top 1 da lista). Ex: 'O produto CANETA BIC AZUL está em falta'.\\n"
                "3. Se a lista de 'Stockouts' não estiver vazia, o Insight #1 OBRIGATORIAMENTE deve ser sobre o primeiro produto dessa lista.\\n"
                "4. Use NÚMEROS REAIS do JSON. Não arredonde excessivamente nem invente.\\n\\n"

                "- Description: Estrutura OBRIGATÓRIA:\\n"
                "  1. PRODUTO: Nome completo (CÓDIGO: XXXXX)\\n"
                "  2. SITUAÇÃO ATUAL: Vendas 30d, Estoque atual, Valor unitário\\n"
                "  3. IMPACTO: Perda/Oportunidade em R$ (calcular!)\\n"
                "  4. URGÊNCIA: Por que agir AGORA (dias para ruptura, % de perda, etc)\\n\\n"
                
                "- Category:\\n"
                "  'alert' = Rupturas e riscos iminentes\\n"
                "  'sales' = Oportunidades de crescimento\\n"
                "  'inventory' = Estoque parado ou excesso\\n\\n"
                
                "- Severity:\\n"
                "  'high' = CRÍTICO - Agir nas próximas 24h (rupturas, perdas >R$10K/mês)\\n"
                "  'medium' = IMPORTANTE - Agir esta semana (riscos, R$5K-10K)\\n"
                "  'low' = MONITORAR - Agir este mês (oportunidades, <R$5K)\\n\\n"
                
                "- Recommendation: AÇÃO ESPECÍFICA em 3 partes:\\n"
                "  1. O QUE fazer (ex: 'Repor estoque', 'Criar promoção')\\n"
                "  2. QUANTO (ex: '300 unidades', '30% desconto')\\n"
                "  3. QUANDO (ex: 'Hoje', 'Esta semana', 'Próximos 3 dias')\\n"
                "  4. RESULTADO ESPERADO (ex: 'Evitar perda de R$ 15K', 'Liberar R$ 50K em capital')\\n\\n"
                
                "EXEMPLO PERFEITO:\\n"
                "[\\n"
                "  {\\n"
                '    "title": "[CRÍTICO] Ruptura TNT Preto - Perda R$ 2.7K/dia",\\n'
                '    "description": "PRODUTO: TNT 40GRS 100%O LG 1.40 034 PRETO (CÓDIGO: 369946)\\n\\nSITUAÇÃO: Vendeu 1.247 unidades (R$ 18.500) nos últimos 30 dias. Estoque atual: -85 unidades (Zero). Preço: R$ 14,85. Demanda: 42/dia.\\n\\nIMPACTO: Perda de R$ 2.700/dia. Cliente não encontra o produto principal.\\n\\nURGÊNCIA: Imediata. Ruptura já existente.",\\n'
                '    "category": "alert",\\n'
                '    "severity": "high",\\n'
                '    "recommendation": "AÇÃO: Comprar 1.500 un urgente via fornecedor X."\\n'
                "  }\\n"
                "]\\n\\n"
                
                "IMPORTANTE: Retorne APENAS o JSON (array). Sem markdown, sem texto extra. SEJA ESPECÍFICO!"
            )
            
            user_message = f"""
            IMPORTANTE: Use os dados abaixo para fundamentar seus insights. Cite nomes e valores exatos.
            
            DADOS DA LOJA (Últimos 30 dias):
            
            [DATA] TOTAIS GERAIS:
            {json.dumps(data_summary.get('general_stats', {}), indent=2)}
            
            🔥 TOP 5 PRODUTOS MAIS VENDIDOS:
            {json.dumps(data_summary.get('top_performing_products', [])[:5], indent=2)}
            
            [WARNING] RUPTURAS CRÍTICAS (Vendendo sem estoque):
            {json.dumps(data_summary.get('critical_measurements', {}).get('stockouts', [])[:5], indent=2)}
            
            💤 ESTOQUE PARADO (Zero vendas, alto estoque):
            {json.dumps(data_summary.get('critical_measurements', {}).get('dead_stock', [])[:5], indent=2)}
            
            TAREFA: Gere 4 insights PRIORIZADOS POR URGÊNCIA.
            
            ORDEM DE PRIORIDADE:
            1. RUPTURAS (severity: high) - CRÍTICO, agir hoje
            2. RISCO DE RUPTURA em produtos de alto giro (severity: medium)
            3. ESTOQUE PARADO com alto valor imobilizado (severity: medium)
            4. OPORTUNIDADES de crescimento (severity: low)
            
            FOCO: Insights que o GESTOR precisa VER IMEDIATAMENTE ao fazer login para AGIR HOJE.
            """
            
            # 3. Chama LLM
            # Usa o provider configurado em settings (google/groq/mock)
            from backend.app.config.settings import settings
            llm = LLMFactory.get_adapter(provider=settings.LLM_PROVIDER, use_smart=True)
            
            # Configura system prompt
            if hasattr(llm, 'system_instruction'):
                llm.system_instruction = system_instruction
           
            # Reforçando que queremos apenas JSON
            user_message_final = user_message + "\n\nRESPOSTA (APENAS JSON):"

            response_text = await llm.generate_response(user_message_final)
            logger.info(f"LLM Raw Response ({settings.LLM_PROVIDER}): {response_text[:200]}...") # Log parcial
            
            # 4. Parse e Limpeza
            return _parse_llm_response(response_text)

        except Exception as e:
            logger.error(f"Erro fatal gerando insights LLM: {e}")
            return _get_fallback_insights(str(e))

def _parse_llm_response(text: str) -> List[Dict[str, Any]]:
    """Tenta extrair JSON de texto com possíveis sujos (markdown, etc)"""
    try:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        data = json.loads(clean_text)
        
        # Normalizar estrutura se necessário
        if isinstance(data, dict) and "insights" in data:
            data = data["insights"]
        
        if not isinstance(data, list):
            return _get_fallback_insights("Formato JSON inválido - não é uma lista")
        
        # Mapear campos alternativos que o Gemini pode usar (PT/EN/Case-insensitive)
        def get_val(d, keys, default=None):
            if not isinstance(d, dict): return default
            # Busca exata
            for k in keys:
                if k in d: return d[k]
            # Busca case-insensitive
            d_lower = {k.lower(): v for k, v in d.items()}
            for k in keys:
                if k.lower() in d_lower: return d_lower[k.lower()]
            return default

        normalized_insights = []
        for item in data:
            # Busca flexível de campos
            title = get_val(item, ["title", "titulo", "título", "insight", "problema"], "Insight Varejo")
            desc = get_val(item, ["description", "descricao", "descrição", "resumo", "situacao", "detalhes", "texto"], "")
            rec = get_val(item, ["recommendation", "recomendacao", "recomendação", "acao", "oportunidade", "sugestao", "action"], "")
            sev = get_val(item, ["severity", "severidade", "urgencia", "prioridade", "impacto"], "medium")
            cat = get_val(item, ["category", "categoria", "tipo", "area"], "alert")
            
            # Normalizar valores de severidade
            sev = str(sev).lower()
            if any(x in sev for x in ["high", "alt", "crít", "crit", "urgent"]): 
                sev = "high"
            elif any(x in sev for x in ["low", "bai", "monit"]): 
                sev = "low"
            else: 
                sev = "medium"

             # Normalizar categorias para ícones do frontend
            cat = str(cat).lower()
            if any(x in cat for x in ["rupt", "ale", "risk"]): cat = "alert"
            elif any(x in cat for x in ["ven", "sal", "oport", "grow"]): cat = "sales"
            elif any(x in cat for x in ["inv", "est", "parado"]): cat = "inventory"
            else: cat = "info"

            normalized = {
                "title": str(title)[:100], 
                "description": str(desc),
                "category": cat,
                "severity": sev,
                "recommendation": str(rec)
            }
            normalized_insights.append(normalized)
        
        return normalized_insights
        
    except json.JSONDecodeError as e:
        logger.error(f"Falha parseando JSON LLM: {text[:100]}...")
        return _get_fallback_insights(f"JSON Error: {str(e)}")

def _get_fallback_insights(error_msg: str = "") -> List[Dict[str, Any]]:
    """Retorna um insight genérico em caso de falha total, para não quebrar a UI"""
    desc = "Não foi possível gerar análises precisas no momento."
    if error_msg:
        desc += f" (Erro: {error_msg})"
        
    return [
        {
            "title": "Sistema de Insights em Manutenção",
            "description": desc,
            "category": "alert",
            "severity": "low",
            "recommendation": "Tente novamente em breve."
        }
    ]
