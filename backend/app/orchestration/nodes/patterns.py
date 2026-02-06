import re
from typing import List, Tuple, Dict, Any

"""
Definição de padrões Regex para o Agente Híbrido.
Formato: (Regex Pattern, Nome da Tool, Função para extrair argumentos)
"""



def empty_args(match: re.Match) -> Dict[str, Any]:
    return {}

def extract_price_query(match: re.Match) -> Dict[str, Any]:
    # Extrai código ou nome para consulta de preço
    term = match.group(1).strip()
    return {
        "filtros": {"PRODUTO": term} if term.isdigit() else {"NOME": term},
        "colunas": ["PRODUTO", "NOME", "PRECO_VENDA", "ESTOQUE_UNE"],
        "limite": 5
    }

def extract_stock_une_query(match: re.Match) -> Dict[str, Any]:
    # Extrai produto e UNE. Ex: produto 123 na une 456
    produto = match.group(1).strip()
    une = match.group(2).strip()
    return {
        "filtros": {
            ("PRODUTO" if produto.isdigit() else "NOME"): produto,
            "UNE": int(une)
        },
        "colunas": ["PRODUTO", "NOME", "UNE", "ESTOQUE_UNE", "VENDA_30DD"],
        "limite": 5
    }


def extract_chart_query(match: re.Match) -> Dict[str, Any]:
    # Regex groups: 1=metric/filter, 2=dimension
    # Ex: "vendas do produto 123" (g1) "em todas as lojas" (g2)
    part1 = match.group(1).strip()
    dimensao = match.group(2).strip()
    
    # 1. Extrair filtros da parte 1
    # Tenta achar "produto <id>" ou "produto <nome>"
    filtros = {}
    
    # Busca por ID de produto
    prod_id_match = re.search(r"produto\s+(\d+)", part1, re.IGNORECASE)
    if prod_id_match:
        filtros["PRODUTO"] = int(prod_id_match.group(1))
        # Remove do termo métrica para não atrapalhar
        metrica = part1.replace(prod_id_match.group(0), "").strip()
    else:
        # Busca por Nome de produto (mais arriscado, simplificado)
        prod_name_match = re.search(r"produto\s+([a-zA-Z\s]+)", part1, re.IGNORECASE)
        if prod_name_match:
             filtros["NOME"] = prod_name_match.group(1).strip()
             metrica = part1.replace(prod_name_match.group(0), "").strip()
        else:
             metrica = part1

    # Limpeza final da métrica (remove "do ", "da ", "de ")
    metrica = re.sub(r"^(do|da|de)\s+", "", metrica).strip()
    if not metrica: metrica = "VENDA" # Default
    
    # 2. Heurística de tipo
    tipo = "line" if "evolução" in match.string.lower() or "tempo" in dimensao.lower() else "bar"
    
    return {
        "tipo_grafico": tipo,
        "metrica": metrica,
        "dimensao": dimensao,
        "filtros": filtros,
        "limite": 10
    }

# Lista de Tuplas: (Pattern, Tool Name, Argument Extractor Function)
HEURISTIC_PATTERNS: List[Tuple[str, str, Any]] = [
    # 0. GRÁFICOS (Prioridade Alta)
    # Suporta:
    # "gráfico de vendas por grupo" (original)
    # "gráfico de vendas do produto 123 em todas as lojas" (novo)
    # "gere gráfico de rankig de venddas segmentos na une 2365" (messy)
    # Regex flexível: Captura tudo entre "gráfico" e o separador "por/em/nas"
    (
        r"(?:gráfico|plotar|ver|analisar).*?\s+(.+?)\s+(?:por|em|nas)\s+(.+)",
        "gerar_grafico_offline",
        extract_chart_query
    ),

    # 1. Preço do Produto (Código ou Nome)
    # Ex: "qual é o preço do produto 369947?"
    (
        r"preço.*produto\s+(.+)", 
        "consultar_dados_flexivel", 
        extract_price_query
    ),

    # 2. Estoque por UNE (Código/Nome + UNE)
    # Ex: "qual é o estoque do produto 59294 na une 2365?"
    (
        r"estoque.*produto\s+(.+)\s+na\s+une\s+(\d+)", 
        "consultar_dados_flexivel", 
        extract_stock_une_query
    ),
    
    # 3. Listar Colunas (Manter existente)
    (
        r".*(colunas|campos|metadados|estrutura|tabelas).*", 
        "consultar_dicionario_dados", # Atualizado para ferramenta correta
        empty_args
    ),
]
