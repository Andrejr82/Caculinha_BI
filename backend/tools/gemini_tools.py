"""
Gemini Tools Configuration - Configuração de Function Calling para Gemini
FIX 2026-02-04: Configuração centralizada de ferramentas disponíveis para a LLM

Funcionalidades:
- Define as 6 ferramentas disponíveis para o agente BI
- Formato compatível com Gemini Function Calling API
- Descrições detalhadas para guiar a LLM
"""

from typing import List, Dict, Any


GEMINI_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_dados_flexivel",
            "description": """
Executa consulta flexível nos dados das Lojas Caçula (DuckDB + Parquet).

Use esta função para:
- Análises de vendas por categoria, produto, loja ou período
- Consultas de estoque (quantidade, cobertura, disponibilidade)
- Cálculos de KPIs (faturamento, giro, mix de produtos)
- Agregações e rankings

COLUNAS DISPONÍVEIS:
- CODIGO: Código do produto (SKU)
- NOME: Descrição do produto
- UNE: Código da loja
- NOMESEGMENTO: Segmento (Papelaria, Tecidos, etc)
- NOMEGRUPO: Grupo de produtos
- VENDA_30DD: Vendas últimos 30 dias
- ESTOQUE: Quantidade em estoque atual
- LIQUIDO_38: Preço de venda
- ULTIMA_ENTRADA_CUSTO_CD: Custo do produto

EXEMPLOS:
- Top categorias: agregacao="SUM", coluna_agregacao="VENDA_30DD", agrupar_por='["NOMESEGMENTO"]'
- Filtrar estoque: filtros="ESTOQUE > 0 AND NOMESEGMENTO = 'Papelaria'"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "filtros": {
                        "type": "string",
                        "description": "Filtros SQL (WHERE). Ex: \"NOMESEGMENTO = 'Papelaria' AND ESTOQUE > 0\""
                    },
                    "colunas": {
                        "type": "string",
                        "description": "Colunas para SELECT (JSON array). Ex: '[\"CODIGO\", \"NOME\", \"ESTOQUE\"]'"
                    },
                    "agregacao": {
                        "type": "string",
                        "description": "Função de agregação: SUM, COUNT, AVG, MIN, MAX"
                    },
                    "coluna_agregacao": {
                        "type": "string",
                        "description": "Coluna para aplicar agregação. Ex: 'VENDA_30DD'"
                    },
                    "agrupar_por": {
                        "type": "string",
                        "description": "Colunas para GROUP BY (JSON array). Ex: '[\"NOMESEGMENTO\"]'"
                    },
                    "ordenar_por": {
                        "type": "string",
                        "description": "Coluna para ORDER BY. Ex: 'valor' ou 'ESTOQUE'"
                    },
                    "ordem_desc": {
                        "anyOf": [
                            {"type": "boolean"},
                            {"type": "string"}
                        ],
                        "description": "Se True, ordena decrescente (DESC). Aceita boolean ou string ('true'/'false'). Padrão: True"
                    },
                    "limite": {
                        "type": "string",
                        "description": "Limite de resultados. Padrão: '100'. Máximo: '500'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gerar_grafico_universal_v2",
            "description": """
Gera gráficos e visualizações para apresentar dados de forma visual.

TIPOS DE GRÁFICO:
- barras: Comparação de categorias (vendas por segmento)
- linhas: Tendência temporal (vendas por mês)
- pizza: Distribuição percentual (market share)
- pareto: Análise ABC/80-20 (principais produtos)
- scatter: Correlação entre variáveis

Use quando o usuário pedir:
- "Mostre um gráfico de..."
- "Visualize..."
- "Compare visualmente..."
- "Plote..."
- "Ranking visual..."
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo_grafico": {
                        "type": "string",
                        "enum": ["barras", "linhas", "pizza", "pareto", "scatter"],
                        "description": "Tipo de gráfico a gerar"
                    },
                    "titulo": {
                        "type": "string",
                        "description": "Título do gráfico. Ex: 'Vendas por Segmento'"
                    },
                    "eixo_x": {
                        "type": "string",
                        "description": "Coluna para eixo X. Ex: 'NOMESEGMENTO'"
                    },
                    "eixo_y": {
                        "type": "string",
                        "description": "Coluna para eixo Y (valores). Ex: 'VENDA_30DD'"
                    },
                    "descricao": {
                        "type": "string",
                        "description": "Descrição textual do gráfico desejado"
                    }
                },
                "required": ["tipo_grafico"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "encontrar_rupturas_criticas",
            "description": """
Identifica produtos em ruptura ou risco iminente de ruptura.

CLASSIFICAÇÃO DE RISCO:
- CRÍTICO (< 3 dias cobertura): Ação imediata necessária
- ALERTA (3-7 dias): Planejar transferência
- SAUDÁVEL (7-30 dias): Estoque adequado
- EXCESSIVO (> 30 dias): Capital imobilizado

Retorna:
- Lista de SKUs em risco
- Cobertura em dias
- Estoque atual vs CD
- Sugestão de transferência

Use quando o usuário perguntar:
- "Produtos em ruptura?"
- "Risco de falta?"
- "Quais SKUs estão críticos?"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "segmento": {
                        "type": "string",
                        "description": "Filtrar por segmento. Ex: 'Papelaria'"
                    },
                    "une": {
                        "type": "string",
                        "description": "Filtrar por loja (código UNE)"
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Máximo de resultados. Padrão: 20"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_abastecimento_une",
            "description": """
Calcula métricas de abastecimento para uma UNE (loja) específica.

Retorna:
- Total de SKUs na loja
- SKUs em ruptura
- SKUs com estoque saudável
- SKUs com excesso
- Sugestões de transferência do CD

Use quando o usuário perguntar:
- "Como está o abastecimento da loja X?"
- "Status de estoque da UNE 1685?"
- "Precisa transferir para qual loja?"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "une": {
                        "type": "string",
                        "description": "Código da UNE (loja). Ex: '1685'"
                    }
                },
                "required": ["une"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_dicionario_dados",
            "description": """
Retorna informações sobre o schema de dados disponível.

Use para:
- Descobrir quais colunas existem
- Entender tipos de dados
- Verificar valores possíveis
- Mapear nomes de colunas

Retorna:
- Lista de colunas disponíveis
- Descrição de cada coluna
- Tipo de dado
- Exemplos de valores
            """,
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analisar_produto_todas_lojas",
            "description": """
Analisa um produto específico em TODAS as lojas.

Retorna para cada loja:
- Estoque atual
- Vendas últimos 30 dias
- Dias de cobertura
- Status (Crítico/Alerta/Saudável/Excessivo)
- Recomendação de transferência

Use quando o usuário perguntar:
- "Como está o produto X em todas as lojas?"
- "Analise o SKU 369947"
- "Estoque do produto X por loja"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo_produto": {
                        "type": "string",
                        "description": "Código do produto (SKU). Ex: '369947'"
                    }
                },
                "required": ["codigo_produto"]
            }
        }
    }
]


def get_tools_for_gemini() -> List[Dict[str, Any]]:
    """Retorna configuração de tools no formato Gemini"""
    return GEMINI_TOOLS


def get_tool_names() -> List[str]:
    """Retorna lista de nomes das ferramentas disponíveis"""
    return [tool["function"]["name"] for tool in GEMINI_TOOLS]


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Retorna configuração de uma ferramenta específica"""
    for tool in GEMINI_TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None


# Exportar para uso direto
__all__ = [
    "GEMINI_TOOLS",
    "get_tools_for_gemini",
    "get_tool_names",
    "get_tool_by_name"
]
