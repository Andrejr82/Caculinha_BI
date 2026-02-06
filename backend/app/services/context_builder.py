"""
Context Builder - Formatador de contexto estruturado para LLM.

Arquitetura Metrics-First - Fase 4
Responsável por transformar métricas VALIDADAS em contexto compacto e legível.

Princípios:
- JSON bruto NUNCA é enviado à LLM
- Apenas Markdown estruturado
- Redução de 70% no consumo de tokens
- Hierarquia: Resumo → Métricas → Detalhes → Metadados
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StructuredContext:
    """
    Contexto estruturado para a LLM.
    
    Attributes:
        summary: Resumo executivo (1 linha)
        key_metrics_md: Métricas principais em Markdown
        details_table_md: Tabela de detalhes (opcional)
        metadata_md: Metadados (filtros, período, etc)
        total_tokens: Estimativa de tokens
        raw_metrics: Métricas brutas (para debug)
    """
    summary: str
    key_metrics_md: str
    details_table_md: Optional[str]
    metadata_md: str
    total_tokens: int
    raw_metrics: Dict[str, Any]


class ContextBuilder:
    """
    Construtor de contexto estruturado em Markdown.
    
    Formata métricas validadas em contexto otimizado para LLM:
    - Compacto (economia de tokens)
    - Legível (Markdown bem formatado)
    - Hierárquico (do geral para o específico)
    """
    
    def __init__(self):
        """Inicializa o ContextBuilder"""
        pass
    
    def build(
        self,
        metrics_result: Any,
        intent: Any,
        max_details: int = 10
    ) -> StructuredContext:
        """
        Constrói contexto estruturado com FILTROS PRIMEIRO (Context Engineering 2025).
        
        Args:
            metrics_result: MetricsResult validado
            intent: QueryIntent original
            max_details: Máximo de linhas na tabela de detalhes
        
        Returns:
            StructuredContext pronto para enviar à LLM
        """
        logger.info(f"Construindo contexto para intent: {intent.intent_type}")
        
        # NOVO: Construir seção de filtros PRIMEIRO (Context Engineering 2025)
        filters_md = self._build_filters_section(metrics_result, intent)
        
        # 1. Resumo executivo
        summary = self._build_summary(metrics_result, intent)
        
        # 2. Métricas principais
        key_metrics_md = self._build_key_metrics(metrics_result)
        
        # 3. Tabela de detalhes (se houver dimensões)
        details_table_md = None
        if metrics_result.dimensions:
            details_table_md = self._build_details_table(
                metrics_result.dimensions,
                intent.intent_type,
                max_details
            )
            
        # 3.1 Tabela de segmentos (NOVO)
        segments_table_md = None
        if hasattr(metrics_result, 'segments') and metrics_result.segments:
            segments_table_md = self._build_segments_table(metrics_result.segments)
            if details_table_md:
                details_table_md = f"{segments_table_md}\n\n{details_table_md}"
            else:
                details_table_md = segments_table_md
        
        # 4. Metadados
        metadata_md = self._build_metadata(metrics_result, intent)
        
        # 5. Estimar tokens (aproximado: 1 token ≈ 4 caracteres)
        full_context = f"{filters_md}\n{summary}\n{key_metrics_md}\n{details_table_md or ''}\n{metadata_md}"
        total_tokens = len(full_context) // 4
        
        logger.info(f"Contexto construído: ~{total_tokens} tokens (filtros primeiro)")
        
        return StructuredContext(
            summary=f"{filters_md}\n\n{summary}",  # Filtros + Summary
            key_metrics_md=key_metrics_md,
            details_table_md=details_table_md,
            metadata_md=metadata_md,
            total_tokens=total_tokens,
            raw_metrics=metrics_result.metrics
        )
    
    def _build_filters_section(self, metrics_result: Any, intent: Any) -> str:
        """
        NOVO: Constrói seção de filtros aplicados (SEMPRE PRIMEIRO).
        
        Context Engineering 2025: Filtros no início evitam "Lost in the Middle".
        """
        filters = []
        
        # Extrair filtros do intent
        if hasattr(intent, 'entities') and intent.entities:
            if 'une' in intent.entities:
                filters.append(f"UNE = {intent.entities['une']}")
            if 'segmento' in intent.entities:
                filters.append(f"Segmento = {intent.entities['segmento']}")
            if 'produto' in intent.entities:
                filters.append(f"Produto = {intent.entities['produto']}")
            if 'periodo' in intent.entities:
                filters.append(f"Período = {intent.entities['periodo']}")
        
        # Extrair filtros dos metadados
        if hasattr(metrics_result, 'metadata') and metrics_result.metadata.get('filters'):
            for key, value in metrics_result.metadata['filters'].items():
                filter_str = f"{key} = {value}"
                if filter_str not in filters:
                    filters.append(filter_str)
        
        if not filters:
            return "## ℹ️ Análise Geral\nNenhum filtro específico aplicado. Dados de toda a base."
        
        filters_str = "\n".join([f"- **{f}**" for f in filters])
        
        # Exemplo de menção correta baseado no primeiro filtro
        example_mention = ""
        if 'une' in intent.entities:
            example_mention = f"\n\n**EXEMPLO DE MENÇÃO CORRETA:**\n\"Análise da **UNE {intent.entities['une']}** (conforme solicitado)...\""
        
        return f"""## [WARNING] FILTROS APLICADOS (OBRIGATÓRIO MENCIONAR)

**VOCÊ DEVE mencionar estes filtros explicitamente na sua resposta:**
{filters_str}{example_mention}
"""
    
    def _build_summary(self, metrics_result: Any, intent: Any) -> str:
        """Constrói resumo executivo (1 linha)"""
        intent_labels = {
            "vendas": "Análise de Vendas",
            "estoque": "Análise de Estoque",
            "ruptura": "Análise de Rupturas",
            "comparacao": "Comparação",
            "grafico": "Visualização",
            "chat": "Consulta"
        }
        
        label = intent_labels.get(intent.intent_type, "Análise")
        
        # Adicionar contexto de filtros
        filters_desc = []
        if "une" in intent.entities:
            filters_desc.append(f"Loja {intent.entities['une']}")
        if "segmento" in intent.entities:
            filters_desc.append(intent.entities['segmento'])
        if "periodo" in intent.entities:
            filters_desc.append(f"Período: {intent.entities['periodo']}")
        
        filters_str = " | ".join(filters_desc) if filters_desc else "Geral"
        
        return f"## {label}\n**Contexto:** {filters_str}"
    
    def _build_key_metrics(self, metrics_result: Any) -> str:
        """Constrói seção de métricas principais"""
        if not metrics_result.metrics:
            return "### Métricas Principais\n*Nenhuma métrica disponível*"
        
        lines = ["### Métricas Principais"]
        
        # Formatadores por tipo de métrica
        formatters = {
            "total_vendas": lambda v: f"**Total de Vendas:** R$ {v:,.2f}",
            "preco_medio": lambda v: f"**Preço Médio:** R$ {v:.2f}",
            "qtd_produtos": lambda v: f"**Produtos Ativos:** {int(v):,}",
            "total_estoque": lambda v: f"**Estoque Total:** {v:,.0f} unidades",
            "estoque_medio": lambda v: f"**Estoque Médio:** {v:.1f} unidades",
            "qtd_rupturas": lambda v: f"**Produtos em Ruptura:** {int(v):,}",
            "qtd_lojas": lambda v: f"**Lojas Analisadas:** {int(v)}",
        }
        
        for key, value in metrics_result.metrics.items():
            if key in formatters:
                lines.append(f"- {formatters[key](value)}")
            else:
                # Fallback genérico
                if isinstance(value, float):
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {value:,.2f}")
                else:
                    lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(lines)
    
    def _build_details_table(
        self,
        dimensions: List[Dict[str, Any]],
        intent_type: str,
        max_rows: int
    ) -> str:
        """Constrói tabela de detalhes em Markdown"""
        if not dimensions:
            return None
        
        # Limitar número de linhas
        dimensions = dimensions[:max_rows]
        
        # Tabelas específicas por tipo de intenção
        if intent_type == "vendas":
            return self._build_vendas_table(dimensions)
        elif intent_type == "ruptura":
            return self._build_ruptura_table(dimensions)
        elif intent_type == "comparacao":
            return self._build_comparacao_table(dimensions)
        else:
            return self._build_generic_table(dimensions)
    
    def _build_vendas_table(self, dimensions: List[Dict]) -> str:
        """Tabela de top produtos por vendas"""
        lines = ["### Top Produtos"]
        lines.append("| Produto | Descrição | Vendas | Preço |")
        lines.append("|---------|-----------|--------|-------|")
        
        for item in dimensions:
            produto = item.get('produto', '-')
            descricao = item.get('descricao', '-')[:30]  # Truncar descrição
            vendas = item.get('vendas', 0)
            preco = item.get('preco', 0)
            
            lines.append(
                f"| {produto} | {descricao} | R$ {vendas:,.2f} | R$ {preco:.2f} |"
            )
        
        return "\n".join(lines)
    
    def _build_ruptura_table(self, dimensions: List[Dict]) -> str:
        """Tabela de produtos em ruptura"""
        lines = ["### Produtos em Ruptura"]
        lines.append("| Produto | Descrição | Segmento |")
        lines.append("|---------|-----------|----------|")
        
        for item in dimensions:
            produto = item.get('produto', '-')
            descricao = item.get('descricao', '-')[:30]
            segmento = item.get('segmento', '-')
            
            lines.append(f"| {produto} | {descricao} | {segmento} |")
        
        return "\n".join(lines)
    
    def _build_comparacao_table(self, dimensions: List[Dict]) -> str:
        """Tabela de comparação entre lojas"""
        lines = ["### Comparação por Loja"]
        lines.append("| Loja | Vendas | Produtos |")
        lines.append("|------|--------|----------|")
        
        for item in dimensions:
            une = item.get('UNE', '-')
            vendas = item.get('total_vendas', 0)
            qtd = item.get('qtd_produtos', 0)
            
            lines.append(f"| {une} | R$ {vendas:,.2f} | {int(qtd):,} |")
        
        return "\n".join(lines)
    
    def _build_generic_table(self, dimensions: List[Dict]) -> str:
        """Tabela genérica"""
        if not dimensions:
            return None
        
        # Pegar chaves do primeiro item
        keys = list(dimensions[0].keys())[:4]  # Máximo 4 colunas
        
        lines = ["### Detalhes"]
        lines.append("| " + " | ".join(k.title() for k in keys) + " |")
        lines.append("|" + "|".join(["---"] * len(keys)) + "|")
        
        for item in dimensions:
            values = [str(item.get(k, '-')) for k in keys]
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)
    
    def _build_segments_table(self, segments: List[Dict]) -> str:
        """Tabela de top segmentos por vendas"""
        lines = ["### Top Segmentos"]
        lines.append("| Segmento | Vendas |")
        lines.append("|----------|--------|")
        
        for item in segments:
            segmento = item.get('segmento', '-')
            vendas = item.get('vendas', 0)
            lines.append(f"| {segmento} | R$ {vendas:,.2f} |")
        
        return "\n".join(lines)
    
    def _build_metadata(self, metrics_result: Any, intent: Any) -> str:
        """Constrói seção de metadados"""
        lines = ["### Informações Adicionais"]
        
        # Filtros aplicados
        if metrics_result.metadata.get("filters"):
            filters = metrics_result.metadata["filters"]
            filters_str = ", ".join(f"{k}: {v}" for k, v in filters.items())
            lines.append(f"- **Filtros:** {filters_str}")
        
        # Performance
        if metrics_result.execution_time_ms:
            lines.append(f"- **Tempo de consulta:** {metrics_result.execution_time_ms:.0f}ms")
        
        # Registros
        lines.append(f"- **Registros analisados:** {metrics_result.row_count:,}")
        
        return "\n".join(lines)
    
    def to_string(self, context: StructuredContext) -> str:
        """
        Converte StructuredContext para string completa.
        
        Args:
            context: StructuredContext a ser convertido
        
        Returns:
            String Markdown completa para enviar à LLM
        """
        parts = [
            context.summary,
            "",
            context.key_metrics_md,
        ]
        
        if context.details_table_md:
            parts.extend(["", context.details_table_md])
        
        parts.extend(["", context.metadata_md])
        
        return "\n".join(parts)
