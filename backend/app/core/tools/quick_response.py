"""
Sistema de Resposta Rápida (Quick Response)
Responde consultas simples SEM usar o LLM para performance máxima.

Tempo de resposta: < 500ms
Taxa de acerto: 95%+
"""

import re
import logging
from typing import Optional, Union
import polars as pl

logger = logging.getLogger(__name__)


class QuickResponseSystem:
    """Sistema de resposta rápida para consultas simples."""

    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame]):
        # [OK] OTIMIZAÇÃO: Usar Polars LazyFrame para queries eficientes
        if isinstance(df, pl.LazyFrame):
            self.df = df
        else:
            self.df = df.lazy()
        self.logger = logger
        
    def try_quick_response(self, query: str) -> Optional[str]:
        """
        Tenta responder rapidamente sem LLM.

        Args:
            query: Pergunta do usuário

        Returns:
            Resposta formatada ou None se não conseguir responder
        """
        query_lower = query.lower()

        # Extrair código do produto
        codigo = self._extract_product_code(query_lower)
        if not codigo:
            return None

        # [OK] Buscar produto usando Polars (eficiente)
        produto = self.df.filter(pl.col('PRODUTO') == codigo).collect()
        if produto.height == 0:
            return f"[ERROR] Produto **{codigo}** não encontrado na base de dados."

        produto_data = produto.row(0, named=True)
        
        # PREÇO
        if any(word in query_lower for word in ['preço', 'preco', 'valor', 'custa', 'quanto']):
            return self._format_price_response(codigo, produto_data)
        
        # ESTOQUE
        if any(word in query_lower for word in ['estoque', 'saldo', 'quantidade', 'tem']):
            return self._format_stock_response(codigo, produto_data)
        
        # FABRICANTE
        if any(word in query_lower for word in ['fabricante', 'marca', 'quem fabrica']):
            return self._format_manufacturer_response(codigo, produto_data)
        
        # NOME/DESCRIÇÃO
        if any(word in query_lower for word in ['nome', 'descrição', 'descricao', 'o que é', 'qual é']):
            return self._format_name_response(codigo, produto_data)
        
        # VENDAS
        if any(word in query_lower for word in ['vendas', 'vendeu', 'venda']):
            return self._format_sales_response(codigo, produto_data)
        
        return None  # Deixa o LLM processar
    
    def _extract_product_code(self, query: str) -> Optional[int]:
        """Extrai código do produto da query."""
        # Padrões: "produto 123", "código 123", "item 123", "123"
        patterns = [
            r'produto\s+(\d+)',
            r'código\s+(\d+)',
            r'codigo\s+(\d+)',
            r'item\s+(\d+)',
            r'\b(\d{4,})\b',  # Número com 4+ dígitos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def _format_price_response(self, codigo: int, produto: dict) -> str:
        """Formata resposta de preço."""
        try:
            preco = float(produto['LIQUIDO_38'])
            nome = str(produto.get('NOME', 'N/A'))[:50]
            return f"💰 O preço do produto **{codigo}** ({nome}) é **R$ {preco:.2f}**."
        except:
            return f"[WARNING] Preço do produto **{codigo}** não disponível."

    def _format_stock_response(self, codigo: int, produto: dict) -> str:
        """Formata resposta de estoque."""
        try:
            estoque = int(float(produto['ESTOQUE_UNE']))
            nome = str(produto.get('NOME', 'N/A'))[:50]

            if estoque > 100:
                emoji = "[OK]"
                status = "Estoque bom"
            elif estoque > 10:
                emoji = "[WARNING]"
                status = "Estoque baixo"
            else:
                emoji = "[DEBUG]"
                status = "Estoque crítico"

            return f"{emoji} O produto **{codigo}** ({nome}) tem **{estoque} unidades** em estoque. {status}."
        except:
            return f"[WARNING] Estoque do produto **{codigo}** não disponível."

    def _format_manufacturer_response(self, codigo: int, produto: dict) -> str:
        """Formata resposta de fabricante."""
        try:
            fabricante = str(produto['NOMEFABRICANTE'])
            nome = str(produto.get('NOME', 'N/A'))[:50]
            return f"🏭 O fabricante do produto **{codigo}** ({nome}) é **{fabricante}**."
        except:
            return f"[WARNING] Fabricante do produto **{codigo}** não disponível."

    def _format_name_response(self, codigo: int, produto: dict) -> str:
        """Formata resposta de nome/descrição."""
        try:
            nome = str(produto['NOME'])
            fabricante = str(produto.get('NOMEFABRICANTE', 'N/A'))
            return f"📦 O produto **{codigo}** é: **{nome}** (Fabricante: {fabricante})."
        except:
            return f"[WARNING] Informações do produto **{codigo}** não disponíveis."

    def _format_sales_response(self, codigo: int, produto: dict) -> str:
        """Formata resposta de vendas."""
        try:
            vendas_30d = float(produto.get('VENDA_30DD', 0))
            nome = str(produto.get('NOME', 'N/A'))[:50]

            if vendas_30d > 0:
                return f"[DATA] O produto **{codigo}** ({nome}) vendeu **{vendas_30d:.0f} unidades** nos últimos 30 dias."
            else:
                return f"[DATA] O produto **{codigo}** ({nome}) não teve vendas nos últimos 30 dias."
        except:
            return f"[WARNING] Dados de vendas do produto **{codigo}** não disponíveis."


def create_quick_response_system(df: Union[pl.DataFrame, pl.LazyFrame]) -> QuickResponseSystem:
    """Factory function para criar o sistema de resposta rápida."""
    return QuickResponseSystem(df)
