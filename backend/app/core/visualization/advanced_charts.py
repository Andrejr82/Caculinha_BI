"""
Módulo de Gráficos Avançados para Business Intelligence
Versão simplificada para Agent Solution BI
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


class AdvancedChartGenerator:
    """Gerador de gráficos avançados para análises de negócio."""

    def __init__(self):
        """Inicializa o gerador de gráficos."""
        self.color_palette = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "warning": "#d62728",
            "info": "#9467bd",
        }

    def create_product_ranking_chart(
        self, df: pd.DataFrame, limit: int = 10, chart_type: str = "horizontal_bar"
    ) -> go.Figure:
        """
        Cria gráfico de ranking de produtos.

        Args:
            df: DataFrame com dados de produtos
            limit: Número de produtos no ranking
            chart_type: Tipo do gráfico

        Returns:
            Figura Plotly
        """
        try:
            # Assumir que df tem colunas relevantes
            if df.empty:
                logger.warning("DataFrame vazio para criar gráfico")
                return go.Figure()

            fig = px.bar(
                df.head(limit),
                title=f"Top {limit} Produtos",
                color_discrete_sequence=[self.color_palette["primary"]],
            )

            fig.update_layout(
                template="plotly_white",
                showlegend=True,
                height=500,
            )

            return fig

        except Exception as e:
            logger.error(f"Erro ao criar gráfico: {e}")
            return go.Figure()

    def create_time_series_chart(self, df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de série temporal."""
        try:
            fig = px.line(
                df,
                title="Evolução Temporal",
                markers=True,
                color_discrete_sequence=[self.color_palette["secondary"]],
            )

            fig.update_layout(
                template="plotly_white",
                showlegend=True,
                height=500,
            )

            return fig

        except Exception as e:
            logger.error(f"Erro ao criar gráfico temporal: {e}")
            return go.Figure()

    def create_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de pizza."""
        try:
            fig = px.pie(
                df,
                title="Distribuição",
                hole=0.3,
            )

            fig.update_layout(
                template="plotly_white",
                showlegend=True,
                height=500,
            )

            return fig

        except Exception as e:
            logger.error(f"Erro ao criar gráfico de pizza: {e}")
            return go.Figure()
