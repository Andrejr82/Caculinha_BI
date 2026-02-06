"""
Ferramentas para geração de gráficos e visualizações.
Integração com Plotly para análise visual de dados.
"""

import logging
from typing import Dict, Any
import pandas as pd
import plotly.graph_objects as go
from langchain_core.tools import tool
from app.core.data_source_manager import get_data_manager
from app.core.visualization.advanced_charts import AdvancedChartGenerator

logger = logging.getLogger(__name__)

# ============================================================================
# TOOL CONSOLIDATION STATUS (2025-12-27)
# ============================================================================
#
# [OK] ACTIVE TOOLS (Recommended - imported in caculinha_bi_agent.py):
#    1. gerar_grafico_universal_v2 (universal_chart_generator.py) - PRIMARY
#    2. gerar_ranking_produtos_mais_vendidos
#    3. gerar_dashboard_executivo
#    4. listar_graficos_disponiveis
#    5. gerar_visualizacao_customizada
#
# [WARNING]  DEPRECATED TOOLS (Not imported - use gerar_grafico_universal_v2 instead):
#    - gerar_grafico_vendas_por_categoria → Use universal_v2 with filtro_categoria
#    - gerar_grafico_estoque_por_produto → Use universal_v2 with descricao="estoque"
#    - gerar_comparacao_precos_categorias → Use universal_v2 with descricao="preços"
#    - gerar_analise_distribuicao_estoque → Use universal_v2 + histogram type
#    - gerar_grafico_pizza_categorias → Use universal_v2 with tipo_grafico="pie"
#    - gerar_dashboard_analise_completa → Use gerar_dashboard_executivo
#    - gerar_grafico_vendas_por_produto → Use universal_v2 with descricao="vendas"
#    - gerar_grafico_automatico → Use gerar_grafico_universal_v2 (no recursion)
#    - gerar_grafico_vendas_mensais_produto → Use universal_v2 with time filter
#    - gerar_grafico_vendas_por_grupo → Use universal_v2 with filtro_segmento
#    - gerar_dashboard_dinamico → Use gerar_dashboard_executivo
#
# MIGRATION GUIDE:
# Old: gerar_grafico_vendas_por_categoria(limite=10)
# New: gerar_grafico_universal_v2(descricao="vendas por categoria", limite=10)
#
# ============================================================================


def _get_theme_template() -> str:
    """Retorna o template de tema padrão."""
    return "plotly_white"


def _apply_chart_customization(
    fig: go.Figure, title: str = "", show_legend: bool = True
) -> go.Figure:
    """
    Aplica customizações padrão aos gráficos.

    Args:
        fig: Figura Plotly
        title: Título do gráfico
        show_legend: Se mostra legenda

    Returns:
        Figura com customizações aplicadas
    """
    fig.update_layout(
        template=_get_theme_template(),
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20, "color": "#1f77b4"},
        },
        hovermode="x unified",
        font=dict(size=11, family="Arial"),
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=show_legend,
        height=500,
        paper_bgcolor="rgba(240, 240, 240, 0.5)",
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
    )
    return fig


def _export_chart_to_json(fig: go.Figure) -> str:
    """
    Exporta figura como JSON para Streamlit.

    Args:
        fig: Figura Plotly

    Returns:
        JSON string da figura
    """
    return fig.to_json()


# [WARNING] DEPRECATED: Use gerar_grafico_universal_v2(descricao="vendas por categoria") instead
@tool
def gerar_grafico_vendas_por_categoria(
    limite: int = 10, ordenar_por: str = "descendente"
) -> Dict[str, Any]:
    """
    Gera gráfico de barras com o total de produtos por grupo (categoria).
    Útil para análise de categorias de produtos.

    Args:
        limite: Número máximo de categorias a mostrar
        ordenar_por: "ascendente" ou "descendente"

    Returns:
        Dicionário com gráfico Plotly e dados
    """
    logger.info(f"Gerando gráfico de produtos por grupo (limite={limite})")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        # FIXED: Use correct column name from admmat.parquet
        grupo_col = "NOMEGRUPO" if "NOMEGRUPO" in df.columns else "GRUPO"
        if df is None or df.empty or grupo_col not in df.columns:
            return {
                "status": "error",
                "message": f"Não foi possível carregar dados ou coluna de grupo não encontrada. Colunas disponíveis: {list(df.columns[:10])}",
            }

        # Preparar dados
        vendas_por_categoria = df[grupo_col].value_counts().reset_index()
        vendas_por_categoria.columns = ["grupo", "total"]

        if ordenar_por == "ascendente":
            vendas_por_categoria = vendas_por_categoria.sort_values(
                "total", ascending=True
            )
        else:
            vendas_por_categoria = vendas_por_categoria.sort_values(
                "total", ascending=False
            )

        df_chart = vendas_por_categoria.head(limite)

        # Create donut chart directly with Plotly
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df_chart["grupo"],
                    values=df_chart["total"],
                    hole=0.4,  # Donut style
                    hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
                    marker=dict(
                        colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                    )
                )
            ]
        )

        # Customizações adicionais se necessário
        fig.update_layout(title_text=f"Top {limite} Grupos por Quantidade de Produtos")

        return {
            "status": "success",
            "chart_type": "donut",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "total_grupos": len(df_chart),
                "grupos": df_chart.set_index("grupo")["total"].to_dict(),
                "total_itens": int(df_chart["total"].sum()),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de vendas: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_grafico_estoque_por_produto(
    limite: int = 15, minimo_estoque: int = 0
) -> Dict[str, Any]:
    """
    Gera gráfico de estoque disponível por produto.
    Mostra produtos com mais estoque em destaque.

    Args:
        limite: Número máximo de produtos a mostrar
        minimo_estoque: Estoque mínimo para incluir

    Returns:
        Dicionário com gráfico e dados de estoque
    """
    logger.info(f"Gerando gráfico de estoque por produto (limite={limite})")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # FIXED: Use correct column names from admmat.parquet
        estoque_col = 'ESTOQUE_UNE' if 'ESTOQUE_UNE' in df.columns else 'QTD'
        nome_col = 'NOME' if 'NOME' in df.columns else 'DESCRIÇÃO'

        if not estoque_col in df.columns or not nome_col in df.columns:
            return {
                "status": "error",
                "message": "Colunas 'QTD' e/ou 'DESCRIÇÃO' não encontradas",
            }

        # Preparar dados
        df_estoque = df[[nome_col, estoque_col]].copy()
        df_estoque[estoque_col] = pd.to_numeric(df_estoque[estoque_col], errors='coerce').fillna(0)
        df_estoque = df_estoque[df_estoque[estoque_col] >= minimo_estoque]
        df_estoque = df_estoque.sort_values(estoque_col, ascending=False).head(limite)

        # Criar gráfico
        fig = go.Figure(
            data=[
                go.Bar(
                    x=df_estoque[nome_col],
                    y=df_estoque[estoque_col],
                    marker=dict(
                        color=df_estoque[estoque_col],
                        colorscale="RdYlGn",
                        showscale=True,
                        colorbar=dict(title="Estoque"),
                    ),
                    hovertemplate="<b>%{x}</b><br>Estoque: %{y}<extra></extra>",
                    text=df_estoque[estoque_col],
                    textposition='auto',
                    texttemplate='%{text:.2s}'
                )
            ]
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            height=600,
        )

        fig = _apply_chart_customization(
            fig, title=f"Estoque Disponível por Produto (Top {limite})"
        )

        fig.update_xaxes(title_text="Produto")
        fig.update_yaxes(title_text="Quantidade em Estoque")

        return {
            "status": "success",
            "chart_type": "bar_vertical",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "total_produtos": len(df_estoque),
                "estoque_total": int(df_estoque[estoque_col].sum()),
                "estoque_medio": float(df_estoque[estoque_col].mean()),
                "estoque_maximo": int(df_estoque[estoque_col].max()),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de estoque: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_comparacao_precos_categorias() -> Dict[str, Any]:
    """
    Gera gráfico de comparação de preços médios por grupo (categoria).
    Útil para análise de precificação.

    Returns:
        Dicionário com gráfico comparativo de preços
    """
    logger.info("Gerando gráfico de comparação de preços por grupo")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # FIXED: Use correct column names from admmat.parquet  
        categoria_col = 'NOMEGRUPO' if 'NOMEGRUPO' in df.columns else 'GRUPO'
        preco_col = 'VENDA_30DD' if 'VENDA_30DD' in df.columns else 'VENDA UNIT R$'

        if not categoria_col in df.columns or not preco_col in df.columns:
            return {
                "status": "error",
                "message": f"Colunas necessárias não encontradas. Disponíveis: {list(df.columns[:10])}",
            }

        # Calcular preço médio por categoria
        df[preco_col] = pd.to_numeric(df[preco_col], errors='coerce')
        df = df.dropna(subset=[preco_col])
        
        preco_medio = (
            df.groupby(categoria_col)[preco_col]
            .agg(["mean", "min", "max", "count"])
            .reset_index()
        )
        preco_medio = preco_medio.sort_values("mean", ascending=False)

        # Criar gráfico com múltiplas séries
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=preco_medio[categoria_col],
                y=preco_medio["mean"],
                name="Preço Médio",
                marker_color="lightblue",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=preco_medio[categoria_col],
                y=preco_medio["max"],
                mode="markers+lines",
                name="Preço Máximo",
                line=dict(dash="dash", color="red"),
                marker=dict(size=8),
            )
        )

        fig = _apply_chart_customization(
            fig, title="Comparação de Preços por Grupo", show_legend=True
        )

        fig.update_xaxes(title_text="Grupo")
        fig.update_yaxes(title_text="Preço (R$)")
        fig.update_layout(xaxis_tickangle=-45, height=500)

        return {
            "status": "success",
            "chart_type": "bar_line_combo",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "grupos": len(preco_medio),
                "preco_medio_geral": float(df[preco_col].mean()),
                "preco_maximo": float(preco_medio["max"].max()),
                "preco_minimo": float(preco_medio["min"].min()),
                "grupos_data": preco_medio.to_dict("records"),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de comparação: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_analise_distribuicao_estoque() -> Dict[str, Any]:
    """
    Gera histograma e box plot da distribuição de estoque.
    Útil para análise estatística de níveis de estoque.

    Returns:
        Dicionário com gráficos de distribuição
    """
    logger.info("Gerando análise de distribuição de estoque")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # FIXED: Use correct column name from admmat.parquet
        estoque_col = 'ESTOQUE_UNE' if 'ESTOQUE_UNE' in df.columns else 'QTD'

        if not estoque_col in df.columns:
            return {"status": "error", "message": f"Coluna de estoque não encontrada. Disponíveis: {list(df.columns[:10])}"}

        # Converter para numérico
        df[estoque_col] = pd.to_numeric(df[estoque_col], errors="coerce")
        df = df.dropna(subset=[estoque_col])

        # Criar subplots
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Distribuição de Estoque", "Box Plot"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]],
        )

        # Histograma
        fig.add_trace(
            go.Histogram(
                x=df[estoque_col],
                nbinsx=30,
                name="Estoque",
                marker_color="rgba(31, 119, 180, 0.7)",
                hovertemplate="Faixa: %{x}<br>Frequência: %{y}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Box plot
        fig.add_trace(
            go.Box(
                y=df[estoque_col],
                name="Estoque",
                marker_color="rgba(31, 119, 180, 0.7)",
                boxmean="sd",
            ),
            row=1,
            col=2,
        )

        fig.update_xaxes(title_text="Nível de Estoque", row=1, col=1)
        fig.update_yaxes(title_text="Frequência", row=1, col=1)
        fig.update_yaxes(title_text="Quantidade", row=1, col=2)

        fig = _apply_chart_customization(
            fig, title="Análise de Distribuição de Estoque"
        )

        # Calcular estatísticas
        stats = {
            "media": float(df[estoque_col].mean()),
            "mediana": float(df[estoque_col].median()),
            "desvio_padrao": float(df[estoque_col].std()),
            "minimo": float(df[estoque_col].min()),
            "maximo": float(df[estoque_col].max()),
            "q1": float(df[estoque_col].quantile(0.25)),
            "q3": float(df[estoque_col].quantile(0.75)),
        }

        return {
            "status": "success",
            "chart_type": "distribution",
            "chart_data": _export_chart_to_json(fig),
            "summary": stats,
        }
    except Exception as e:
        logger.error(f"Erro ao gerar análise de distribuição: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_grafico_pizza_categorias() -> Dict[str, Any]:
    """
    Gera gráfico de pizza mostrando proporção de produtos por grupo (categoria).
    Útil para visualizar distribuição percentual.

    Returns:
        Dicionário com gráfico de pizza e proporções
    """
    logger.info("Gerando gráfico de pizza por grupo")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # FIXED: Use correct column name from admmat.parquet
        categoria_col = 'NOMEGRUPO' if 'NOMEGRUPO' in df.columns else 'GRUPO'

        if not categoria_col in df.columns:
            return {"status": "error", "message": f"Coluna de categoria não encontrada. Disponíveis: {list(df.columns[:10])}"}

        # Contar por categoria
        categorias = df[categoria_col].value_counts()

        # Criar gráfico
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=categorias.index,
                    values=categorias.values,
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>",
                )
            ]
        )

        fig = _apply_chart_customization(
            fig, title="Distribuição de Produtos por Grupo"
        )

        fig.update_layout(height=600)

        return {
            "status": "success",
            "chart_type": "pie",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "total_categorias": len(categorias),
                "total_produtos": int(categorias.sum()),
                "categorias": categorias.to_dict(),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de pizza: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_dashboard_analise_completa() -> Dict[str, Any]:
    """
    Gera dashboard completo com múltiplas visualizações em um único lugar.
    Combina 4 gráficos em um layout 2x2.

    Returns:
        Dicionário com dashboard e múltiplos gráficos
    """
    logger.info("Gerando dashboard completo")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        from plotly.subplots import make_subplots

        # FIXED: Use correct column names from admmat.parquet
        categoria_col = 'NOMEGRUPO' if 'NOMEGRUPO' in df.columns else 'GRUPO'
        estoque_col = 'ESTOQUE_UNE' if 'ESTOQUE_UNE' in df.columns else 'QTD'
        preco_col = 'VENDA_30DD' if 'VENDA_30DD' in df.columns else 'VENDA UNIT R$'
        nome_col = 'NOME' if 'NOME' in df.columns else 'DESCRIÇÃO'

        required_cols = [categoria_col, estoque_col, preco_col, nome_col]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return {"status": "error", "message": f"Colunas não encontradas: {missing}. Disponíveis: {list(df.columns[:15])}"}

        # Preparar dados
        df_conv = df.copy()
        df_conv[estoque_col] = pd.to_numeric(df_conv[estoque_col], errors="coerce")
        df_conv[preco_col] = pd.to_numeric(df_conv[preco_col], errors="coerce")

        # Criar subplots 2x2
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Produtos por Grupo",
                "Top 10 Produtos - Estoque",
                "Distribuição de Estoque",
                "Preço Médio por Grupo",
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "histogram"}, {"type": "bar"}],
            ],
        )

        # Gráfico 1: Pizza
        cat_counts = df_conv[categoria_col].value_counts()
        fig.add_trace(
            go.Pie(
                labels=cat_counts.index, values=cat_counts.values, name="Grupos"
            ),
            row=1,
            col=1,
        )

        # Gráfico 2: Top 10 Estoque
        top_estoque = df_conv.nlargest(10, estoque_col)
        fig.add_trace(
            go.Bar(
                x=top_estoque[nome_col],
                y=top_estoque[estoque_col],
                name="Estoque",
                marker_color="lightblue",
            ),
            row=1,
            col=2,
        )

        # Gráfico 3: Histograma
        fig.add_trace(
            go.Histogram(
                x=df_conv[estoque_col],
                nbinsx=20,
                name="Distribuição",
                marker_color="lightgreen",
            ),
            row=2,
            col=1,
        )

        # Gráfico 4: Preço médio
        preco_med = (
            df_conv.groupby(categoria_col)[preco_col]
            .mean()
            .sort_values(ascending=False)
        )
        fig.add_trace(
            go.Bar(
                x=preco_med.index,
                y=preco_med.values,
                name="Preço Médio",
                marker_color="lightyellow",
            ),
            row=2,
            col=2,
        )

        # Atualizar layout
        fig.update_layout(
            title_text="Dashboard de Análise - Visão Geral",
            height=900,
            showlegend=False,
            template=_get_theme_template(),
        )

        fig.update_xaxes(title_text="Produto", row=1, col=2)
        fig.update_xaxes(title_text="Estoque", row=2, col=1)
        fig.update_yaxes(title_text="Quantidade", row=1, col=2)
        fig.update_yaxes(title_text="Frequência", row=2, col=1)
        fig.update_xaxes(title_text="Grupo", row=2, col=2)
        fig.update_yaxes(title_text="Preço Médio (R$)", row=2, col=2)


        return {
            "status": "success",
            "chart_type": "dashboard",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "total_produtos": len(df_conv),
                "total_categorias": df_conv[categoria_col].nunique(),
                "estoque_total": float(df_conv[estoque_col].sum()),
                "estoque_medio": float(df_conv[estoque_col].mean()),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar dashboard: {str(e)}"}


@tool
def gerar_grafico_vendas_por_produto(
    codigo_produto: int,
) -> Dict[str, Any]:
    """
    Gera gráfico de série temporal de vendas de um produto específico.
    Este é um alias para gerar_grafico_vendas_mensais_produto.

    Args:
        codigo_produto: Código do produto (ITEM)

    Returns:
        Dicionário com gráfico de série temporal e análise
    """
    logger.info(
        f"Gerando gráfico de vendas do produto {codigo_produto} (alias)"
    )
    return gerar_grafico_vendas_mensais_produto(codigo_produto=codigo_produto)


@tool
# [WARNING] DEPRECATED: Use gerar_grafico_universal_v2() instead - NO RECURSION, better performance
def gerar_grafico_automatico(descricao: str) -> Dict[str, Any]:
    """
    Gera qualquer tipo de gráfico baseado na descrição do usuário.
    O LLM interpreta a descrição e seleciona o gráfico mais apropriado.

    Args:
        descricao: Descrição do gráfico desejado em linguagem natural

    Returns:
        Gráfico Plotly JSON correspondente ao tipo solicitado

    Exemplos de uso:
      - "gráfico de vendas por categoria"
      - "mostrar estoque disponível por produto"
      - "análise de distribuição de estoque"
      - "comparar preços entre categorias"
      - "vendas do produto 59294"
      - "dashboard completo"
    """
    logger.info(f"Gerando gráfico automático: {descricao}")

    descricao_lower = descricao.lower()

    # Detectar tipo de gráfico pela descrição
    if any(
        word in descricao_lower
        for word in [
            "vendas",
            "venda",
            "sales",
            "categoria",
            "categor",
            "top",
            "ranking",
        ]
    ):
        logger.info("Detectado: Gráfico de vendas por categoria")
        return gerar_grafico_vendas_por_categoria.invoke(
            {"limite": 10, "ordenar_por": "descendente"}
        )

    elif any(
        word in descricao_lower
        for word in [
            "estoque",
            "stock",
            "disponível",
            "quantidade",
            "quantidade",
            "inv",
            "por produto",
        ]
    ):
        logger.info("Detectado: Gráfico de estoque por produto")
        return gerar_grafico_estoque_por_produto.invoke(
            {"limite": 15, "minimo_estoque": 0}
        )

    elif any(
        word in descricao_lower
        for word in [
            "preço",
            "preco",
            "price",
            "preços",
            "comparação",
            "comparar",
            "pricing",
        ]
    ):
        logger.info("Detectado: Gráfico de comparação de preços")
        return gerar_comparacao_precos_categorias.invoke({})

    elif any(
        word in descricao_lower
        for word in [
            "distribuição",
            "distribuicao",
            "distribuição",
            "análise",
            "analise",
            "histograma",
            "box plot",
        ]
    ):
        logger.info("Detectado: Análise de distribuição")
        return gerar_analise_distribuicao_estoque.invoke({})

    elif any(
        word in descricao_lower
        for word in ["pizza", "pie", "propor", "percent", "proporção"]
    ):
        logger.info("Detectado: Gráfico de pizza")
        return gerar_grafico_pizza_categorias.invoke({})

    elif any(
        word in descricao_lower
        for word in [
            "dashboard",
            "tudo",
            "visão",
            "visao",
            "completo",
            "overview",
            "resumo",
        ]
    ):
        logger.info("Detectado: Dashboard completo")
        return gerar_dashboard_analise_completa.invoke({})

    elif any(
        word in descricao_lower
        for word in [
            "produto",
            "temporal",
            "série",
            "serie",
            "evolução",
            "evolucao",
            "sku",
            "mensal",
            "mês",
            "mes",
            "vendas produto",
        ]
    ):
        logger.info("Detectado: Gráfico de vendas por produto")
        # Extrair código do produto se presente
        import re

        match = re.search(r"\d+", descricao)
        codigo = int(match.group()) if match else 59294

        # Tentar usar a versão com dados mensais pivotados (estrutura real)
        resultado = gerar_grafico_vendas_mensais_produto.invoke(
            {"codigo_produto": codigo, "unidade_filtro": None}
        )

        # Se falhar, retornar gráfico de série temporal alternativo
        if resultado.get("status") == "error":
            logger.info("Gráfico mensal falhou, tentando série temporal")
            return gerar_grafico_vendas_por_produto.invoke(
                {"codigo_produto": codigo, "unidade": "SCR"}
            )

        return resultado

    else:
        # Por padrão, gera dashboard completo
        logger.info("Tipo não reconhecido, gerando dashboard padrão")
        return gerar_dashboard_analise_completa.invoke({})


# REMOVED 2025-12-27: Alias causava recursão e confusão com gerar_grafico_universal_v2
# OLD CODE: gerar_grafico_universal = gerar_grafico_automatico
# MIGRATION: Use gerar_grafico_universal_v2 from universal_chart_generator.py instead


@tool
def gerar_grafico_vendas_mensais_produto(
    codigo_produto: int,
) -> Dict[str, Any]:
    """
    Gera gráfico de vendas mensais para um produto específico.
    Trabalha com a estrutura de dados da Filial Madureira.

    Args:
        codigo_produto: Código do produto (ITEM)

    Returns:
        Dicionário com gráfico de vendas mensais
    """
    logger.info(f"Gerando gráfico de vendas mensais do produto {codigo_produto}")

    try:
        manager = get_data_manager()
        df_raw = manager.get_data()

        if df_raw is None or df_raw.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # A coluna de código do produto é 'PRODUTO' (conforme schema do admmat.parquet)
        codigo_col = 'PRODUTO'
        
        # Converter a coluna 'PRODUTO' para numérico para garantir a comparação
        df_raw[codigo_col] = pd.to_numeric(df_raw[codigo_col], errors='coerce')
        
        # Filtrar por código de produto
        df_produto = df_raw[df_raw[codigo_col] == codigo_produto].copy()

        if df_produto.empty:
            return {
                "status": "error",
                "message": (
                    f"Produto com código {codigo_produto} não encontrado. "
                    "Verifique o código informado."
                ),
            }

        # Extrair colunas de meses
        mes_cols = {
            'JAN': 'VENDA QTD JAN', 'FEV': 'VENDA QTD FEV', 'MAR': 'VENDA QTD MAR',
            'ABR': 'VENDA QTD ABR', 'MAI': 'VENDA QTD MAI', 'JUN': 'VENDA QTD JUN',
            'JUL': 'VENDA QTD JUL', 'AGO': 'VENDA QTD AGO', 'SET': 'VENDA QTD SET',
            'OUT': 'VENDA QTD OUT', 'NOV': 'VENDA QTD NOV', 'DEZ': 'VENDA QTD DEZ'
        }
        
        vendas_mensais = []
        mes_labels = []
        
        for mes_abrev, col_name in mes_cols.items():
            if col_name in df_produto.columns:
                valor_bruto = df_produto[col_name].iloc[0]
                valor_numerico = pd.to_numeric(valor_bruto, errors='coerce')
                valor = 0 if pd.isna(valor_numerico) else valor_numerico
                vendas_mensais.append(valor)
                mes_labels.append(mes_abrev)

        if not vendas_mensais:
            return {
                "status": "error",
                "message": "Colunas de vendas mensais não encontradas na estrutura de dados.",
            }

        # Criar gráfico
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=mes_labels,
                y=vendas_mensais,
                mode="lines+markers+text", # Adicionar 'text' ao modo
                name="Vendas",
                line=dict(color="#2563EB", width=3),
                marker=dict(
                    size=10,
                    color="#2563EB",
                    line=dict(width=2, color="white"),
                    symbol="circle",
                ),
                hovertemplate=(
                    "<b>Mês: %{x}</b><br>" "Quantidade: %{y:,.0f} unidades<extra></extra>"
                ),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.2)",
                text=vendas_mensais,
                textposition="top center"
            )
        )

        # Adicionar linha de média
        if vendas_mensais:
            media_vendas = sum(vendas_mensais) / len(vendas_mensais)
            fig.add_hline(
                y=media_vendas,
                line_dash="dash",
                line_color="red",
                annotation_text="Média",
                annotation_position="right",
            )

        fig = _apply_chart_customization(
            fig, title=(f"Vendas Mensais - Produto {codigo_produto}")
        )

        fig.update_xaxes(title_text="Mês")
        fig.update_yaxes(title_text="Quantidade (unidades)")
        fig.update_layout(height=600, hovermode="x unified")

        # Calcular estatísticas
        total_vendas = sum(vendas_mensais)
        venda_media = total_vendas / len(vendas_mensais) if vendas_mensais else 0
        venda_max = max(vendas_mensais) if vendas_mensais else 0
        venda_min = min(vendas_mensais) if vendas_mensais else 0
        venda_max_mes = mes_labels[vendas_mensais.index(venda_max)] if vendas_mensais and venda_max > 0 else "N/A"
        venda_min_mes = mes_labels[vendas_mensais.index(venda_min)] if vendas_mensais else "N/A"

        # Extrair informações adicionais do produto
        produto_info = {}
        for col in ["DESCRIÇÃO", "FABRICANTE", "GRUPO"]:
            if col in df_produto.columns:
                valor = df_produto[col].iloc[0]
                produto_info[col] = str(valor)

        return {
            "status": "success",
            "chart_type": "line_temporal_mensal",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "codigo_produto": codigo_produto,
                "total_vendas": int(total_vendas),
                "venda_media": float(venda_media),
                "venda_maxima": int(venda_max),
                "venda_minima": int(venda_min),
                "mes_maior_venda": venda_max_mes,
                "mes_menor_venda": venda_min_mes,
                "variacao": float(
                    (venda_max - venda_min) / venda_media * 100
                    if venda_media > 0
                    else 0
                ),
                "meses_analisados": len(mes_labels),
                "produto_info": produto_info,
                "dados_mensais": {
                    mes_labels[i]: int(vendas_mensais[i])
                    for i in range(len(mes_labels))
                },
            },
        }

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de vendas mensais: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_grafico_vendas_por_grupo(
    nome_grupo: str, agregacao: str = "soma"
) -> Dict[str, Any]:
    """
    Gera gráfico de vendas mensais para todos os produtos de um grupo específico.
    Útil para análise de desempenho de categorias de produtos ao longo do ano.

    Args:
        nome_grupo: Nome do grupo/categoria (ex: "ESMALTES", "CREMES", etc.)
        agregacao: Tipo de agregação - "soma" (padrão) ou "media"

    Returns:
        Dicionário com gráfico de vendas mensais do grupo
    """
    logger.info(f"Gerando gráfico de vendas do grupo: {nome_grupo}")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        # Verificar se coluna GRUPO existe
        if "GRUPO" not in df.columns:
            return {
                "status": "error",
                "message": "Coluna 'GRUPO' não encontrada no dataset"
            }

        # Filtrar produtos do grupo (case-insensitive)
        df_grupo = df[df["GRUPO"].str.upper().str.contains(nome_grupo.upper(), na=False)].copy()

        if df_grupo.empty:
            grupos_disponiveis = df["GRUPO"].unique()[:10]
            return {
                "status": "error",
                "message": (
                    f"Grupo '{nome_grupo}' não encontrado. "
                    f"Grupos disponíveis: {', '.join(map(str, grupos_disponiveis))}"
                )
            }

        # Colunas de vendas mensais
        mes_cols = {
            'JAN': 'VENDA QTD JAN', 'FEV': 'VENDA QTD FEV', 'MAR': 'VENDA QTD MAR',
            'ABR': 'VENDA QTD ABR', 'MAI': 'VENDA QTD MAI', 'JUN': 'VENDA QTD JUN',
            'JUL': 'VENDA QTD JUL', 'AGO': 'VENDA QTD AGO', 'SET': 'VENDA QTD SET',
            'OUT': 'VENDA QTD OUT', 'NOV': 'VENDA QTD NOV', 'DEZ': 'VENDA QTD DEZ'
        }

        # Converter para numérico
        for col in mes_cols.values():
            if col in df_grupo.columns:
                df_grupo[col] = pd.to_numeric(df_grupo[col], errors='coerce').fillna(0)

        # Agregar vendas mensais
        vendas_mensais = []
        mes_labels = []

        for mes_abrev, col_name in mes_cols.items():
            if col_name in df_grupo.columns:
                if agregacao == "media":
                    valor = df_grupo[col_name].mean()
                else:  # soma (padrão)
                    valor = df_grupo[col_name].sum()

                vendas_mensais.append(float(valor))
                mes_labels.append(mes_abrev)

        if not vendas_mensais:
            return {
                "status": "error",
                "message": "Colunas de vendas mensais não encontradas"
            }

        # Criar gráfico
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=mes_labels,
                y=vendas_mensais,
                mode="lines+markers+text",
                name="Vendas",
                line=dict(color="#10B981", width=3),
                marker=dict(
                    size=12,
                    color="#10B981",
                    line=dict(width=2, color="white"),
                    symbol="circle",
                ),
                hovertemplate=(
                    "<b>Mês: %{x}</b><br>"
                    "Quantidade: %{y:,.0f} unidades<extra></extra>"
                ),
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.2)",
                text=[f"{int(v):,}" for v in vendas_mensais],
                textposition="top center",
                textfont=dict(size=10)
            )
        )

        # Adicionar linha de média
        if vendas_mensais:
            media_vendas = sum(vendas_mensais) / len(vendas_mensais)
            fig.add_hline(
                y=media_vendas,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Média: {int(media_vendas):,}",
                annotation_position="right",
            )

        tipo_agregacao = "Total" if agregacao == "soma" else "Média"
        titulo = f"Vendas Mensais - Grupo: {nome_grupo.upper()} ({tipo_agregacao})"

        fig = _apply_chart_customization(fig, title=titulo)

        fig.update_xaxes(title_text="Mês")
        fig.update_yaxes(title_text="Quantidade (unidades)")
        fig.update_layout(height=600, hovermode="x unified")

        # Calcular estatísticas
        total_vendas = sum(vendas_mensais)
        venda_media = total_vendas / len(vendas_mensais) if vendas_mensais else 0
        venda_max = max(vendas_mensais) if vendas_mensais else 0
        venda_min = min(vendas_mensais) if vendas_mensais else 0
        venda_max_mes = mes_labels[vendas_mensais.index(venda_max)] if vendas_mensais and venda_max > 0 else "N/A"
        venda_min_mes = mes_labels[vendas_mensais.index(venda_min)] if vendas_mensais else "N/A"

        return {
            "status": "success",
            "chart_type": "line_temporal_grupo",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "grupo": nome_grupo.upper(),
                "total_produtos": len(df_grupo),
                "agregacao": agregacao,
                "total_vendas": int(total_vendas),
                "venda_media_mensal": float(venda_media),
                "venda_maxima": int(venda_max),
                "venda_minima": int(venda_min),
                "mes_maior_venda": venda_max_mes,
                "mes_menor_venda": venda_min_mes,
                "meses_analisados": len(mes_labels),
                "dados_mensais": {
                    mes_labels[i]: int(vendas_mensais[i])
                    for i in range(len(mes_labels))
                },
            },
        }

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de vendas por grupo: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar gráfico: {str(e)}"}


@tool
def gerar_ranking_produtos_mais_vendidos(top_n: int = 10) -> Dict[str, Any]:
    """
    Gera um gráfico de barras horizontais com o ranking dos produtos mais vendidos no ano.
    Útil para identificar os produtos mais populares.

    Args:
        top_n: O número de produtos a serem incluídos no ranking (padrão: 10).

    Returns:
        Dicionário com o gráfico de ranking e dados.
    """
    logger.info(f"Gerando ranking dos {top_n} produtos mais vendidos.")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados."}

        # FIXED: Use correct column names from admmat.parquet
        # Try VENDA_30DD first (preferred), or sum of MES_* columns
        nome_col = 'NOME' if 'NOME' in df.columns else 'DESCRIÇÃO'
        
        if 'VENDA_30DD' in df.columns:
            df['VENDAS_TOTAIS'] = pd.to_numeric(df['VENDA_30DD'], errors='coerce').fillna(0)
        else:
            # Fallback to MES_* columns
            mes_cols = [col for col in df.columns if col.startswith('MES_')]
            if not mes_cols:
                return {"status": "error", "message": "Nenhuma coluna de vendas encontrada."}
            for col in mes_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df['VENDAS_TOTAIS'] = df[mes_cols].sum(axis=1)

        # Preparar dados para o gráfico
        ranking_df = df.sort_values('VENDAS_TOTAIS', ascending=False).head(top_n)
        ranking_df = ranking_df.sort_values('VENDAS_TOTAIS', ascending=True)

        # Criar gráfico
        fig = go.Figure(go.Bar(
            x=ranking_df['VENDAS_TOTAIS'],
            y=ranking_df[nome_col],
            orientation='h',
            marker=dict(color='#2563EB'),
            text=ranking_df['VENDAS_TOTAIS'],
            textposition='auto',
            texttemplate='%{text:.2s}'
        ))

        fig = _apply_chart_customization(
            fig, title=f"Top {top_n} Produtos Mais Vendidos"
        )
        fig.update_layout(
            yaxis=dict(tickmode='linear'),
            xaxis_title="Total de Vendas (Unidades)",
            yaxis_title="Produto"
        )

        return {
            "status": "success",
            "chart_type": "bar_horizontal",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "top_n": top_n,
                "produtos": ranking_df[[nome_col, 'VENDAS_TOTAIS']].to_dict('records')
            }
        }

    except Exception as e:
        logger.error(f"Erro ao gerar ranking de produtos: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar ranking: {str(e)}"}


@tool
def listar_graficos_disponiveis() -> Dict[str, Any]:
    """
    Lista os gráficos e dashboards RECOMENDADOS disponíveis no sistema (2025).
    Use esta ferramenta quando o usuário perguntar "quais gráficos você pode gerar?",
    "que tipos de visualizações existem?", ou similares.

    Returns:
        Dicionário com lista de gráficos recomendados e suas descrições
    """
    logger.info("Listando gráficos recomendados (active tools only)")

    graficos_info = {
        "total_tipos": 4,
        "ferramentas_recomendadas": {
            "Ferramenta Universal (Principal)": [
                {
                    "nome": "gerar_grafico_universal_v2",
                    "descricao": "FERRAMENTA PRINCIPAL - Gera qualquer tipo de gráfico com filtros dinâmicos (UNE, segmento, categoria)",
                    "capacidades": [
                        "Auto-detecção de dimensão e métrica",
                        "Suporta: bar, pie, line, scatter, histogram",
                        "Filtros: filtro_une, filtro_segmento, filtro_categoria",
                        "Performance otimizada (sem recursão)"
                    ],
                    "exemplos": [
                        "gerar_grafico_universal_v2(descricao='vendas por categoria', limite=10)",
                        "gerar_grafico_universal_v2(descricao='estoque por produto', filtro_une=1685)",
                        "gerar_grafico_universal_v2(descricao='preços por segmento', tipo_grafico='bar')"
                    ]
                }
            ],
            "Rankings e Análises": [
                {
                    "nome": "gerar_ranking_produtos_mais_vendidos",
                    "descricao": "Ranking dos produtos mais vendidos com métricas detalhadas",
                    "exemplo": "gerar_ranking_produtos_mais_vendidos(top_n=10)"
                }
            ],
            "Dashboards Executivos": [
                {
                    "nome": "gerar_dashboard_executivo",
                    "descricao": "Dashboard executivo multi-métrica otimizado para tomada de decisão",
                    "exemplo": "gerar_dashboard_executivo()"
                }
            ],
            "Visualizações Customizadas": [
                {
                    "nome": "gerar_visualizacao_customizada",
                    "descricao": "Cria visualizações personalizadas com dados fornecidos pelo usuário",
                    "exemplo": "gerar_visualizacao_customizada(titulo='Meu Gráfico', tipo_grafico='bar', dados=...)"
                }
            ]
        },
        "recomendacao_uso": {
            "casos_gerais": "Use gerar_grafico_universal_v2 para 90% dos casos",
            "rankings": "Use gerar_ranking_produtos_mais_vendidos para top N produtos",
            "visao_geral": "Use gerar_dashboard_executivo para visão executiva completa",
            "casos_especiais": "Use gerar_visualizacao_customizada para dados customizados"
        },
        "migracao": "Ferramentas legadas foram consolidadas. Use gerar_grafico_universal_v2 para casos anteriormente cobertos por 10+ tools específicas."
    }

    return {
        "status": "success",
        "graficos_disponiveis": graficos_info,
        "message": f"Total de {graficos_info['total_tipos']} ferramentas recomendadas (consolidadas em 2025)"
    }


@tool
def gerar_dashboard_executivo() -> Dict[str, Any]:
    """
    Gera dashboard executivo completo com os principais indicadores de negócio.
    Layout 2x3 otimizado para análise gerencial e tomada de decisão.

    Inclui:
    - Vendas por categoria (Top 10)
    - Ranking produtos mais vendidos
    - Análise de estoque
    - Comparação de preços
    - Distribuição de produtos
    - Métricas principais

    Returns:
        Dicionário com dashboard executivo completo
    """
    logger.info("Gerando dashboard executivo")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Não foi possível carregar dados"}

        from plotly.subplots import make_subplots

        # Preparar dados
        df_conv = df.copy()

        # Converter colunas para numérico
        for col in ['QTD', 'VENDA UNIT R$', 'VENDA R$', 'LUCRO R$']:
            if col in df_conv.columns:
                df_conv[col] = pd.to_numeric(df_conv[col], errors='coerce').fillna(0)

        # Calcular vendas totais se não existir
        mes_cols = [col for col in df_conv.columns if 'VENDA QTD' in col]
        if mes_cols:
            df_conv['VENDAS_TOTAIS'] = df_conv[mes_cols].sum(axis=1)

        # Criar subplots 2x3
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                "Top 10 Grupos (Quantidade)",
                "Top 10 Produtos Mais Vendidos",
                "Análise de Lucro por Grupo",
                "Distribuição de Estoque",
                "Preço Médio por Grupo",
                "Status de Vendas Mensais"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                [{"type": "histogram"}, {"type": "bar"}, {"type": "scatter"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # 1. Top 10 Grupos
        if 'GRUPO' in df_conv.columns:
            grupos = df_conv['GRUPO'].value_counts().head(10)
            fig.add_trace(
                go.Bar(
                    x=grupos.index,
                    y=grupos.values,
                    name="Produtos",
                    marker_color="#2563EB"
                ),
                row=1, col=1
            )

        # 2. Top 10 Produtos Mais Vendidos
        if 'VENDAS_TOTAIS' in df_conv.columns and 'DESCRIÇÃO' in df_conv.columns:
            top_vendas = df_conv.nlargest(10, 'VENDAS_TOTAIS')
            fig.add_trace(
                go.Bar(
                    x=top_vendas['VENDAS_TOTAIS'],
                    y=top_vendas['DESCRIÇÃO'],
                    orientation='h',
                    name="Vendas",
                    marker_color="#10B981"
                ),
                row=1, col=2
            )

        # 3. Lucro por Grupo
        if 'GRUPO' in df_conv.columns and 'LUCRO R$' in df_conv.columns:
            lucro_grupo = df_conv.groupby('GRUPO')['LUCRO R$'].sum().sort_values(ascending=False).head(10)
            fig.add_trace(
                go.Bar(
                    x=lucro_grupo.index,
                    y=lucro_grupo.values,
                    name="Lucro",
                    marker_color="#F59E0B"
                ),
                row=1, col=3
            )

        # 4. Distribuição de Estoque
        if 'QTD' in df_conv.columns:
            fig.add_trace(
                go.Histogram(
                    x=df_conv['QTD'],
                    nbinsx=30,
                    name="Estoque",
                    marker_color="#8B5CF6"
                ),
                row=2, col=1
            )

        # 5. Preço Médio por Grupo
        if 'GRUPO' in df_conv.columns and 'VENDA UNIT R$' in df_conv.columns:
            preco_grupo = df_conv.groupby('GRUPO')['VENDA UNIT R$'].mean().sort_values(ascending=False).head(10)
            fig.add_trace(
                go.Bar(
                    x=preco_grupo.index,
                    y=preco_grupo.values,
                    name="Preço Médio",
                    marker_color="#EC4899"
                ),
                row=2, col=2
            )

        # 6. Vendas Mensais Totais
        if mes_cols:
            vendas_mensais = df_conv[mes_cols].sum()
            meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            fig.add_trace(
                go.Scatter(
                    x=meses,
                    y=vendas_mensais.values,
                    mode='lines+markers',
                    name="Vendas Mensais",
                    line=dict(color="#14B8A6", width=3),
                    marker=dict(size=8),
                    fill='tozeroy'
                ),
                row=2, col=3
            )

        # Atualizar layout
        fig.update_layout(
            title_text="Dashboard Executivo - Visão Geral do Negócio",
            height=900,
            showlegend=False,
            template=_get_theme_template(),
            margin=dict(l=60, r=60, t=100, b=60)
        )

        # Ajustar eixos
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        fig.update_xaxes(tickangle=-45, row=1, col=3)
        fig.update_xaxes(tickangle=-45, row=2, col=2)

        # Calcular métricas
        metricas = {
            "total_produtos": len(df_conv),
            "total_grupos": df_conv['GRUPO'].nunique() if 'GRUPO' in df_conv.columns else 0,
            "lucro_total": float(df_conv['LUCRO R$'].sum()) if 'LUCRO R$' in df_conv.columns else 0,
            "vendas_totais": float(df_conv['VENDAS_TOTAIS'].sum()) if 'VENDAS_TOTAIS' in df_conv.columns else 0,
            "estoque_total": float(df_conv['QTD'].sum()) if 'QTD' in df_conv.columns else 0,
            "valor_estoque": float((df_conv['QTD'] * df_conv['VENDA UNIT R$']).sum()) if all(c in df_conv.columns for c in ['QTD', 'VENDA UNIT R$']) else 0
        }

        return {
            "status": "success",
            "chart_type": "dashboard_executivo",
            "chart_data": _export_chart_to_json(fig),
            "summary": metricas
        }

    except Exception as e:
        logger.error(f"Erro ao gerar dashboard executivo: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro ao gerar dashboard: {str(e)}"}


@tool
def gerar_dashboard_dinamico(graficos: list) -> Dict[str, Any]:
    """
    Gera um dashboard dinâmico com uma seleção de gráficos.

    Args:
        graficos: Uma lista dos nomes das ferramentas de gráfico a serem incluídas.
                  Exemplos de nomes de ferramentas válidas:
                  - 'gerar_grafico_vendas_por_categoria'
                  - 'gerar_grafico_estoque_por_produto'
                  - 'gerar_comparacao_precos_categorias'
                  - 'gerar_analise_distribuicao_estoque'
                  - 'gerar_grafico_pizza_categorias'
                  - 'gerar_ranking_produtos_mais_vendidos'

    Returns:
        Dicionário com o dashboard e múltiplos gráficos.
    """
    logger.info(f"Gerando dashboard dinâmico com os seguintes gráficos: {graficos}")

    if not graficos:
        return {"status": "error", "message": "Nenhum gráfico especificado para o dashboard."}

    from plotly.subplots import make_subplots
    import math
    import json

    num_graficos = len(graficos)
    if num_graficos > 4:
        return {"status": "error", "message": "O dashboard dinâmico suporta no máximo 4 gráficos."}
    
    rows = math.ceil(num_graficos / 2)
    cols = 2 if num_graficos > 1 else 1
    
    # Mapeamento de nomes de ferramentas para funções
    tool_map = {
        'gerar_grafico_vendas_por_categoria': gerar_grafico_vendas_por_categoria,
        'gerar_grafico_estoque_por_produto': gerar_grafico_estoque_por_produto,
        'gerar_comparacao_precos_categorias': gerar_comparacao_precos_categorias,
        'gerar_analise_distribuicao_estoque': gerar_analise_distribuicao_estoque,
        'gerar_grafico_pizza_categorias': gerar_grafico_pizza_categorias,
        'gerar_ranking_produtos_mais_vendidos': gerar_ranking_produtos_mais_vendidos,
    }

    figuras = []
    titulos = []
    for nome_ferramenta in graficos:
        if nome_ferramenta in tool_map:
            try:
                resultado = tool_map[nome_ferramenta].invoke({})
                if resultado.get("status") == "success":
                    chart_data = json.loads(resultado["chart_data"])
                    figura_individual = go.Figure(chart_data)
                    figuras.append(figura_individual)
                    titulos.append(figura_individual.layout.title.text)
                else:
                    logger.warning(f"A ferramenta '{nome_ferramenta}' falhou: {resultado.get('message')}")
            except Exception as e:
                logger.error(f"Erro ao executar a ferramenta '{nome_ferramenta}': {e}", exc_info=True)
    
    if not figuras:
        return {"status": "error", "message": "Nenhum dos gráficos solicitados pôde ser gerado."}

    # Recalcular layout com base nos gráficos gerados com sucesso
    num_graficos = len(figuras)
    rows = math.ceil(num_graficos / 2)
    cols = 2 if num_graficos > 1 else 1

    fig = make_subplots(
        rows=rows, 
        cols=cols, 
        subplot_titles=titulos,
        vertical_spacing=0.15, # Aumentar espaçamento vertical
        horizontal_spacing=0.1 # Aumentar espaçamento horizontal
    )

    for i, figura_individual in enumerate(figuras):
        row = i // cols + 1
        col = i % cols + 1
        for trace in figura_individual.data:
            fig.add_trace(trace, row=row, col=col)

    fig.update_layout(
        title_text="Dashboard Dinâmico",
        height=450 * rows, # Ajustar altura
        showlegend=False,
        template=_get_theme_template(),
        margin=dict(l=40, r=40, t=120, b=40), # Adicionar margens
    )
    # Ajustar tamanho da fonte dos subtítulos
    fig.update_annotations(font_size=14)

    return {
        "status": "success",
        "chart_type": "dashboard",
        "chart_data": _export_chart_to_json(fig),
        "summary": {
            "total_graficos": len(figuras),
            "graficos_incluidos": titulos,
        },
    }


@tool
def gerar_visualizacao_customizada(
    eixo_x: str,
    eixo_y: str,
    tipo_grafico: str,
    titulo: str,
    coluna_cor: str = None,
    agregacao: str = None
) -> Dict[str, Any]:
    """
    Cria uma visualização totalmente personalizada a partir dos dados.
    Use esta ferramenta quando NENHUMA outra ferramenta específica atender ao pedido do usuário.
    Permite cruzar quaisquer duas variáveis numéricas ou categóricas.

    Args:
        eixo_x: Nome da coluna para o eixo X (ex: 'DESCRIÇÃO', 'ESTOQUE', 'VENDA UNIT R$')
        eixo_y: Nome da coluna para o eixo Y (ex: 'QTD', 'VENDA R$', 'LUCRO R$')
        tipo_grafico: 'bar', 'line', 'scatter' (dispersão), 'histogram', 'box'
        titulo: Título do gráfico
        coluna_cor: (Opcional) Nome da coluna para agrupar por cores (ex: 'GRUPO')
        agregacao: (Opcional) 'soma', 'media', 'contagem' (se precisar agrupar dados)

    Returns:
        Gráfico Plotly customizado
    """
    logger.info(f"Gerando visualização customizada: {tipo_grafico} | {eixo_x} vs {eixo_y}")

    try:
        manager = get_data_manager()
        df = manager.get_data()

        if df is None or df.empty:
            return {"status": "error", "message": "Dados não disponíveis"}

        # Validação básica de colunas
        cols_existentes = df.columns
        if eixo_x not in cols_existentes:
            # Tentar match aproximado case-insensitive
            match_x = next((c for c in cols_existentes if c.upper() == eixo_x.upper()), None)
            if match_x: eixo_x = match_x
            else: return {"status": "error", "message": f"Coluna X '{eixo_x}' não encontrada"}

        if eixo_y not in cols_existentes:
            match_y = next((c for c in cols_existentes if c.upper() == eixo_y.upper()), None)
            if match_y: eixo_y = match_y
            else: return {"status": "error", "message": f"Coluna Y '{eixo_y}' não encontrada"}

        df_chart = df.copy()

        # Converter numéricos
        for col in [eixo_y, eixo_x]:
            # Se parece numérico, converter
            if df_chart[col].dtype == object:
                try:
                    df_chart[col] = pd.to_numeric(df_chart[col])
                except:
                    pass # Manter como texto se falhar

        # Agregação se solicitada
        if agregacao:
            grp_cols = [eixo_x]
            if coluna_cor and coluna_cor in df_chart.columns:
                grp_cols.append(coluna_cor)
            
            agg_func = 'sum' if agregacao == 'soma' else 'mean' if agregacao == 'media' else 'count'
            
            df_chart = df_chart.groupby(grp_cols)[eixo_y].agg(agg_func).reset_index()

        # Limitar dados para não travar o frontend se for scatter de muitos pontos
        if len(df_chart) > 2000:
            df_chart = df_chart.sample(2000)

        # Construir Gráfico
        fig = go.Figure()

        if tipo_grafico == 'scatter':
            fig.add_trace(go.Scatter(
                x=df_chart[eixo_x],
                y=df_chart[eixo_y],
                mode='markers',
                marker=dict(
                    color=df_chart[coluna_cor] if coluna_cor and coluna_cor in df_chart.columns else '#2563EB',
                    size=8,
                    opacity=0.7
                ),
                text=df_chart['DESCRIÇÃO'] if 'DESCRIÇÃO' in df_chart.columns else None
            ))
        
        elif tipo_grafico == 'bar':
            fig.add_trace(go.Bar(
                x=df_chart[eixo_x],
                y=df_chart[eixo_y],
                marker_color='#2563EB'
            ))

        elif tipo_grafico == 'line':
            df_chart = df_chart.sort_values(eixo_x)
            fig.add_trace(go.Scatter(
                x=df_chart[eixo_x],
                y=df_chart[eixo_y],
                mode='lines+markers'
            ))

        elif tipo_grafico == 'box':
            fig.add_trace(go.Box(
                y=df_chart[eixo_y],
                x=df_chart[eixo_x] if eixo_x else None,
                boxpoints='outliers'
            ))

        elif tipo_grafico == 'histogram':
            fig.add_trace(go.Histogram(
                x=df_chart[eixo_x]
            ))

        fig = _apply_chart_customization(fig, title=titulo)
        fig.update_xaxes(title_text=eixo_x)
        fig.update_yaxes(title_text=eixo_y)

        return {
            "status": "success",
            "chart_type": f"custom_{tipo_grafico}",
            "chart_data": _export_chart_to_json(fig),
            "summary": {
                "tipo": tipo_grafico,
                "pontos": len(df_chart),
                "eixos": f"{eixo_x} vs {eixo_y}"
            }
        }

    except Exception as e:
        logger.error(f"Erro em visualização customizada: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# Lista de todas as ferramentas de gráficos disponíveis
chart_tools = [
    # Ferramentas de análise e consulta
    listar_graficos_disponiveis,  # NOVO: Lista todos os gráficos disponíveis

    # Customização flexível (SOTA 2025)
    gerar_visualizacao_customizada,

    # Gráficos individuais
    gerar_grafico_vendas_por_categoria,
    gerar_grafico_estoque_por_produto,
    gerar_comparacao_precos_categorias,
    gerar_analise_distribuicao_estoque,
    gerar_grafico_pizza_categorias,
    gerar_grafico_vendas_por_produto,
    gerar_grafico_vendas_mensais_produto,
    gerar_grafico_vendas_por_grupo,  # Gráfico de vendas por grupo/categoria
    gerar_ranking_produtos_mais_vendidos,

    # Dashboards completos
    gerar_dashboard_analise_completa,
    gerar_dashboard_executivo,  # NOVO: Dashboard executivo 2x3
    gerar_dashboard_dinamico,

    # Gráficos inteligentes
    gerar_grafico_automatico,
]
