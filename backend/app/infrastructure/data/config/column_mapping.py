"""
Mapeamento Oficial de Colunas do Parquet
Sistema: Agent_Solution_BI
Data: 2025-10-25

Este módulo contém o mapeamento entre nomes legados (código antigo) e nomes reais
das colunas do Parquet. Usado para normalizar queries e evitar erros de KeyError.

FONTE: Extraído diretamente do Parquet real (97 colunas)
"""

# ==================== MAPEAMENTO PRINCIPAL ====================
# Mapeamento: Nome Legado → Nome Real no Parquet
# ==================== MAPEAMENTO PRINCIPAL ====================
# Mapeamento: Nome Legado/Synonym → Nome Real no Parquet
COLUMN_MAP = {
    # Identificação
    "CODIGO": "PRODUTO",
    "CODIGO_PRODUTO": "PRODUTO",
    "SKU": "PRODUTO",
    
    "DESCRICAO": "NOME",
    "DESC": "NOME",
    "NOME_PRODUTO": "NOME",
    "PRODUTO_NOME": "NOME",

    # UNE
    "LOJA": "UNE",
    "CODIGO_LOJA": "UNE",
    "NOME_LOJA": "UNE_NOME",
    "NOMEUNE": "UNE_NOME",

    # Hierarquia
    "SEGMENTO": "NOMESEGMENTO",
    "CATEGORIA": "NOMECATEGORIA",
    "GRUPO": "NOMEGRUPO",
    "SUBGRUPO": "NOMESUBGRUPO",
    "FABRICANTE": "NOMEFABRICANTE",
    "MARCA": "NOMEFABRICANTE",

    # Vendas
    "VENDAS": "VENDA_30DD",
    "VENDA": "VENDA_30DD",
    "VENDA30": "VENDA_30DD",
    "VENDA_30": "VENDA_30DD",
    "VENDAS_30_DIAS": "VENDA_30DD",

    # Estoque
    "ESTOQUE": "ESTOQUE_UNE",
    "ESTOQUE_TOTAL": "ESTOQUE_UNE",
    "ESTOQUE_ATUAL": "ESTOQUE_UNE",
    "ESTOQUE_LOJA": "ESTOQUE_UNE",
    
    "ESTOQUE_LV": "ESTOQUE_LV",
    "LINHA_VERDE": "ESTOQUE_LV",
    "AREA_VENDA": "ESTOQUE_LV",
    
    "ESTOQUE_CD": "ESTOQUE_CD",
    "DEPOSITO": "ESTOQUE_CD",

    # Preços e Custos
    "PRECO": "LIQUIDO_38",
    "PRECO_VENDA": "LIQUIDO_38",
    "VALOR": "LIQUIDO_38",
    
    "CUSTO": "ULTIMA_ENTRADA_CUSTO_CD",
    
    # Classificação
    "CURVA": "ABC_UNE_30DD",
    "ABC": "ABC_UNE_30DD",
}

# ==================== MAPEAMENTO REVERSO ====================
# Nome Real (Parquet) → Informações da Coluna
COLUMN_INFO = {
    # ==================== IDENTIFICAÇÃO E HIERARQUIA ====================
    "PRODUTO": {
        "nome_legado": ["CODIGO"],
        "descricao": "Código único do produto (SKU)",
        "tipo": "int",
        "exemplo": "704559",
        "nullable": False,
    },
    "NOME": {
        "nome_legado": ["DESCRICAO"],
        "descricao": "Nome/Descrição completa do produto",
        "tipo": "str",
        "exemplo": "ALCA BOLSA 7337 DIAM.105MM PS MESCLADO 810",
        "nullable": False,
    },
    "UNE": {
        "nome_legado": ["LOJA"],
        "descricao": "Código da Unidade de Negócio (Loja)",
        "tipo": "int",
        "exemplo": "2586",
        "nullable": False,
    },
    "UNE_NOME": {
        "nome_legado": ["NOME_LOJA"],
        "descricao": "Nome da Unidade de Negócio",
        "tipo": "str",
        "exemplo": "NIG",
        "nullable": False,
    },
    "NOMESEGMENTO": {
        "nome_legado": ["SEGMENTO"],
        "descricao": "Segmento de mercado",
        "tipo": "str",
        "exemplo": "ARMARINHO E CONFECÇÃO",
        "nullable": False,
    },
    "NOMEGRUPO": {
        "nome_legado": ["GRUPO"],
        "descricao": "Grupo de produtos",
        "tipo": "str",
        "exemplo": "FERRAGEM",
        "nullable": True,
    },
    "NOMECATEGORIA": {
        "nome_legado": ["CATEGORIA"],
        "descricao": "Categoria mercadológica",
        "tipo": "str",
        "exemplo": "ACABAMENTOS CONFECÇÃO",
        "nullable": True,
    },
    "NOMESUBGRUPO": {
        "nome_legado": ["SUBGRUPO"],
        "descricao": "Subgrupo detalhado",
        "tipo": "str",
        "exemplo": "SIMPLES",
        "nullable": True,
    },
    "NOMEFABRICANTE": {
        "nome_legado": ["FABRICANTE"],
        "descricao": "Fabricante ou Marca",
        "tipo": "str",
        "exemplo": "KR AVIAMENTOS",
        "nullable": True,
    },
    
    # ==================== VENDAS E PERFORMANCE ====================
    "VENDA_30DD": {
        "nome_legado": ["VENDAS"],
        "descricao": "Vendas totais nos últimos 30 dias",
        "tipo": "float",
        "exemplo": "2.5",
        "nullable": True,
    },
    
    # ==================== VENDAS MENSAIS (HISTÓRICO) ====================
    "MES_PARCIAL": {
        "descricao": "Vendas do mês atual (parcial ou em andamento)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_01": {
        "descricao": "Vendas do mês anterior (mês -1)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_02": {
        "descricao": "Vendas de 2 meses atrás (mês -2)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_03": {
        "descricao": "Vendas de 3 meses atrás (mês -3)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_04": {
        "descricao": "Vendas de 4 meses atrás (mês -4)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_05": {
        "descricao": "Vendas de 5 meses atrás (mês -5)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_06": {
        "descricao": "Vendas de 6 meses atrás (mês -6)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_07": {
        "descricao": "Vendas de 7 meses atrás (mês -7)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_08": {
        "descricao": "Vendas de 8 meses atrás (mês -8)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_09": {
        "descricao": "Vendas de 9 meses atrás (mês -9)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_10": {
        "descricao": "Vendas de 10 meses atrás (mês -10)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_11": {
        "descricao": "Vendas de 11 meses atrás (mês -11)",
        "tipo": "float",
        "nullable": True,
    },
    "MES_12": {
        "descricao": "Vendas de 12 meses atrás (mês -12)",
        "tipo": "float",
        "nullable": True,
    },
    
    # ==================== VENDAS SEMANAIS (HISTÓRICO) ====================
    "SEMANA_ATUAL": {
        "descricao": "Vendas da semana atual",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_SEMANA_ATUAL": {
        "descricao": "Frequência de vendas na semana atual (número de dias com venda)",
        "tipo": "float",
        "nullable": True,
    },
    "QTDE_SEMANA_ATUAL": {
        "descricao": "Quantidade vendida na semana atual",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_SEMANA_ATUAL": {
        "descricao": "Média de vendas por dia na semana atual",
        "tipo": "float",
        "nullable": True,
    },
    "SEMANA_ANTERIOR_2": {
        "descricao": "Vendas da semana anterior (semana -1)",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_SEMANA_ANTERIOR_2": {
        "descricao": "Frequência de vendas na semana anterior",
        "tipo": "float",
        "nullable": True,
    },
    "QTDE_SEMANA_ANTERIOR_2": {
        "descricao": "Quantidade vendida na semana anterior",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_SEMANA_ANTERIOR_2": {
        "descricao": "Média de vendas por dia na semana anterior",
        "tipo": "float",
        "nullable": True,
    },
    "SEMANA_ANTERIOR_3": {
        "descricao": "Vendas de 2 semanas atrás (semana -2)",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_SEMANA_ANTERIOR_3": {
        "descricao": "Frequência de vendas 2 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "QTDE_SEMANA_ANTERIOR_3": {
        "descricao": "Quantidade vendida 2 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_SEMANA_ANTERIOR_3": {
        "descricao": "Média de vendas por dia 2 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "SEMANA_ANTERIOR_4": {
        "descricao": "Vendas de 3 semanas atrás (semana -3)",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_SEMANA_ANTERIOR_4": {
        "descricao": "Frequência de vendas 3 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "QTDE_SEMANA_ANTERIOR_4": {
        "descricao": "Quantidade vendida 3 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_SEMANA_ANTERIOR_4": {
        "descricao": "Média de vendas por dia 3 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "SEMANA_ANTERIOR_5": {
        "descricao": "Vendas de 4 semanas atrás (semana -4)",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_SEMANA_ANTERIOR_5": {
        "descricao": "Frequência de vendas 4 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "QTDE_SEMANA_ANTERIOR_5": {
        "descricao": "Quantidade vendida 4 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_SEMANA_ANTERIOR_5": {
        "descricao": "Média de vendas por dia 4 semanas atrás",
        "tipo": "float",
        "nullable": True,
    },
    "FREQ_ULT_SEM": {
        "descricao": "Frequência de vendas na última semana consolidada",
        "tipo": "float",
        "nullable": True,
    },
    
    # ==================== CLASSIFICAÇÕES ABC ====================
    "ABC_UNE_30DD": {
        "nome_legado": ["CURVA"],
        "descricao": "Classificação ABC da loja baseada em vendas dos últimos 30 dias",
        "tipo": "str",
        "exemplo": "A",
        "nullable": True,
    },
    "ABC_UNE_MES_01": {
        "descricao": "Classificação ABC da loja no mês anterior",
        "tipo": "str",
        "nullable": True,
    },
    "ABC_UNE_MES_02": {
        "descricao": "Classificação ABC da loja 2 meses atrás",
        "tipo": "str",
        "nullable": True,
    },
    "ABC_UNE_MES_03": {
        "descricao": "Classificação ABC da loja 3 meses atrás",
        "tipo": "str",
        "nullable": True,
    },
    "ABC_UNE_MES_04": {
        "descricao": "Classificação ABC da loja 4 meses atrás",
        "tipo": "str",
        "nullable": True,
    },
    "ABC_CACULA_90DD": {
        "descricao": "Classificação ABC global da rede Caçula (últimos 90 dias)",
        "tipo": "str",
        "nullable": True,
    },
    "ABC_UNE_30XABC_CACULA_90DD": {
        "descricao": "Comparação entre ABC da loja (30d) e ABC da rede (90d)",
        "tipo": "str",
        "nullable": True,
    },
    
    # ==================== ESTOQUE ====================
    "ESTOQUE_UNE": {
        "nome_legado": ["ESTOQUE"],
        "descricao": "Estoque total atual na loja",
        "tipo": "float",
        "exemplo": "15.0",
        "nullable": True,
    },
    "ESTOQUE_LV": {
        "nome_legado": ["LINHA_VERDE"],
        "descricao": "Estoque total na Área de Venda (Linha Verde)",
        "tipo": "float",
        "exemplo": "5.0",
        "nullable": True,
    },
    "ESTOQUE_GONDOLA_LV": {
        "descricao": "Estoque na gôndola (área de venda principal)",
        "tipo": "float",
        "nullable": True,
    },
    "ESTOQUE_ILHA_LV": {
        "descricao": "Estoque em ilha promocional ou ponta de gôndola",
        "tipo": "float",
        "nullable": True,
    },
    "ESTOQUE_CD": {
        "nome_legado": ["DEPOSITO"],
        "descricao": "Estoque no Centro de Distribuição",
        "tipo": "float",
        "exemplo": "100.0",
        "nullable": True,
    },
    "EXPOSICAO_MINIMA": {
        "descricao": "Quantidade mínima de exposição recomendada (geral)",
        "tipo": "float",
        "nullable": True,
    },
    "EXPOSICAO_MINIMA_UNE": {
        "descricao": "Quantidade mínima de exposição específica da loja",
        "tipo": "float",
        "nullable": True,
    },
    "EXPOSICAO_MAXIMA_UNE": {
        "descricao": "Quantidade máxima de exposição específica da loja",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_CONSIDERADA_LV": {
        "descricao": "Média de vendas considerada para cálculo de reposição da Linha Verde",
        "tipo": "float",
        "nullable": True,
    },
    "LEADTIME_LV": {
        "descricao": "Tempo de reposição da Linha Verde (em dias)",
        "tipo": "float",
        "nullable": True,
    },
    "PONTO_PEDIDO_LV": {
        "descricao": "Ponto de pedido calculado para reposição da Linha Verde",
        "tipo": "float",
        "nullable": True,
    },
    "MEDIA_TRAVADA": {
        "descricao": "Média de vendas travada/fixada para cálculos de reposição",
        "tipo": "float",
        "nullable": True,
    },
    "ULTIMO_INVENTARIO_UNE": {
        "descricao": "Data do último inventário realizado na loja",
        "tipo": "timestamp",
        "nullable": True,
    },
    
    # ==================== MOVIMENTAÇÃO E LOGÍSTICA ====================
    "ULTIMA_ENTRADA_DATA_CD": {
        "descricao": "Data da última entrada de mercadoria no Centro de Distribuição",
        "tipo": "timestamp",
        "nullable": True,
    },
    "ULTIMA_ENTRADA_QTDE_CD": {
        "descricao": "Quantidade da última entrada no Centro de Distribuição",
        "tipo": "float",
        "nullable": True,
    },
    "ULTIMA_ENTRADA_CUSTO_CD": {
        "descricao": "Custo unitário da última entrada no Centro de Distribuição",
        "tipo": "float",
        "nullable": True,
    },
    "ULTIMA_ENTRADA_DATA_UNE": {
        "descricao": "Data da última entrada de mercadoria na loja",
        "tipo": "timestamp",
        "nullable": True,
    },
    "ULTIMA_ENTRADA_QTDE_UNE": {
        "descricao": "Quantidade da última entrada na loja",
        "tipo": "float",
        "nullable": True,
    },
    "ULTIMA_VENDA_DATA_UNE": {
        "descricao": "Data da última venda do produto na loja",
        "tipo": "timestamp",
        "nullable": True,
    },
    "SOLICITACAO_PENDENTE": {
        "descricao": "Indica se há solicitação de transferência pendente (0=Não, 1=Sim)",
        "tipo": "int",
        "nullable": True,
    },
    "SOLICITACAO_PENDENTE_DATA": {
        "descricao": "Data da solicitação de transferência pendente",
        "tipo": "timestamp",
        "nullable": True,
    },
    "SOLICITACAO_PENDENTE_QTDE": {
        "descricao": "Quantidade solicitada na transferência pendente",
        "tipo": "float",
        "nullable": True,
    },
    "SOLICITACAO_PENDENTE_SITUACAO": {
        "descricao": "Situação da solicitação pendente (ex: Pendente, Em separação,Atendido)",
        "tipo": "str",
        "nullable": True,
    },
    "PICKLIST": {
        "descricao": "Número do picklist associado ao produto",
        "tipo": "int",
        "nullable": True,
    },
    "PICKLIST_SITUACAO": {
        "descricao": "Situação do picklist (ex: Aberto, Em separação, Conferido)",
        "tipo": "str",
        "nullable": True,
    },
    "PICKLIST_CONFERENCIA": {
        "descricao": "Data/hora da conferência do picklist",
        "tipo": "timestamp",
        "nullable": True,
    },
    "ROMANEIO_SOLICITACAO": {
        "descricao": "Número do romaneio de solicitação de transferência",
        "tipo": "int",
        "nullable": True,
    },
    "ROMANEIO_ENVIO": {
        "descricao": "Número do romaneio de envio da transferência",
        "tipo": "int",
        "nullable": True,
    },
    "ULTIMO_VOLUME": {
        "descricao": "Número do último volume expedido",
        "tipo": "int",
        "nullable": True,
    },
    "VOLUME_QTDE": {
        "descricao": "Quantidade de volumes na última expedição",
        "tipo": "int",
        "nullable": True,
    },
    "NOTA": {
        "descricao": "Número da nota fiscal de transferência",
        "tipo": "int",
        "nullable": True,
    },
    "SERIE": {
        "descricao": "Série da nota fiscal",
        "tipo": "str",
        "nullable": True,
    },
    "NOTA_EMISSAO": {
        "descricao": "Data de emissão da nota fiscal",
        "tipo": "timestamp",
        "nullable": True,
    },
    
    # ==================== PREÇOS E EMBALAGENS ====================
    "LIQUIDO_38": {
        "nome_legado": ["PRECO"],
        "descricao": "Preço de venda (Líquido 38%)",
        "tipo": "float",
        "exemplo": "12.99",
        "nullable": True,
    },
    "QTDE_EMB_MASTER": {
        "descricao": "Quantidade de unidades na embalagem master",
        "tipo": "int",
        "nullable": True,
    },
    "QTDE_EMB_MULTIPLO": {
        "descricao": "Múltiplo de embalagem para pedidos",
        "tipo": "int",
        "nullable": True,
    },
    "EMBALAGEM": {
        "descricao": "Tipo ou descrição da embalagem do produto",
        "tipo": "str",
        "nullable": True,
    },
    
    # ==================== METADADOS E CONTROLE ====================
    "id": {
        "descricao": "ID único do registro no banco de dados",
        "tipo": "int",
        "nullable": True,
    },
    "TIPO": {
        "descricao": "Tipo de produto ou classificação interna",
        "tipo": "int",
        "nullable": True,
    },
    "EAN": {
        "descricao": "Código de barras EAN do produto",
        "tipo": "str",
        "nullable": True,
    },
    "PROMOCIONAL": {
        "descricao": "Indica se o produto está em promoção (S/N)",
        "tipo": "str",
        "nullable": True,
    },
    "FORALINHA": {
        "descricao": "Indica se o produto está fora de linha (S/N)",
        "tipo": "str",
        "nullable": True,
    },
    "ENDERECO_RESERVA": {
        "descricao": "Endereço de armazenamento reserva do produto",
        "tipo": "str",
        "nullable": True,
    },
    "ENDERECO_LINHA": {
        "descricao": "Endereço de armazenamento na linha de venda",
        "tipo": "str",
        "nullable": True,
    },
    "created_at": {
        "descricao": "Data/hora de criação do registro",
        "tipo": "timestamp",
        "nullable": True,
    },
    "updated_at": {
        "descricao": "Data/hora da última atualização do registro",
        "tipo": "timestamp",
        "nullable": True,
    },
}

# ==================== COLUNAS ESSENCIAIS ====================
# Colunas mínimas necessárias para análises básicas
# ==================== COLUNAS ESSENCIAIS ====================
# Colunas mínimas necessárias para análises básicas
# IMPORTANTE: Usar nomes REAIS do Parquet (não legados)
ESSENTIAL_COLUMNS = [
    # Identificação
    'PRODUTO',           # Código do produto (SKU)
    'NOME',              # Nome/Descrição do produto
    'UNE',               # Código da loja
    'UNE_NOME',          # Nome da loja - ESSENCIAL para rankings
    
    # Hierarquia
    'NOMESEGMENTO',      # Segmento
    'NOMECATEGORIA',     # Categoria
    'NOMEGRUPO',         # Grupo
    'NOMESUBGRUPO',      # Subgrupo
    'NOMEFABRICANTE',    # Fabricante - ESSENCIAL para filtros de marca
    
    # Vendas
    'VENDA_30DD',        # Vendas últimos 30 dias
    
    # Estoque
    'ESTOQUE_UNE',       # Estoque na loja
    'ESTOQUE_LV',        # Linha Verde (Estoque Máximo)
    'ESTOQUE_CD',        # Estoque no Centro de Distribuição
    
    # Preços
    'LIQUIDO_38',        # Preço de venda
    
    # Embalagens
    'QTDE_EMB_MASTER',   # Quantidade embalagem master
    'QTDE_EMB_MULTIPLO', # Quantidade múltiplo
    
    # Classificação
    'ABC_UNE_30DD',      # Curva ABC
]

# ==================== FUNÇÕES AUXILIARES ====================

def normalize_column_name(column_name: str) -> str:
    """
    Normaliza nome de coluna (legado → real).

    Args:
        column_name: Nome da coluna (pode ser legado ou real)

    Returns:
        Nome real da coluna ou o próprio nome se não encontrado

    Examples:
        >>> normalize_column_name("PRODUTO")
        "codigo"
        >>> normalize_column_name("VENDA_30DD")
        "venda_30_d"
        >>> normalize_column_name("codigo")
        "codigo"
    """
    # Se já é um nome real, retornar
    if column_name in COLUMN_INFO:
        return column_name

    # Tentar encontrar no mapeamento
    upper_name = column_name.upper()
    return COLUMN_MAP.get(upper_name, column_name)


def get_column_info(column_name: str) -> dict:
    """
    Retorna informações sobre uma coluna.

    Args:
        column_name: Nome da coluna (real ou legado)

    Returns:
        Dicionário com informações ou None

    Example:
        >>> get_column_info("PRODUTO")
        {"nome_legado": ["PRODUTO"], "descricao": "Código único...", ...}
    """
    real_name = normalize_column_name(column_name)
    return COLUMN_INFO.get(real_name)


def validate_columns(columns: list, df_columns: list) -> dict:
    """
    Valida se colunas existem no DataFrame.

    Args:
        columns: Lista de colunas a validar
        df_columns: Lista de colunas disponíveis no DataFrame

    Returns:
        {"valid": [...], "invalid": [...], "suggestions": {...}}

    Example:
        >>> validate_columns(["PRODUTO", "VENDA_30DD"], df.columns)
        {"valid": ["codigo", "venda_30_d"], "invalid": [], "suggestions": {}}
    """
    valid = []
    invalid = []
    suggestions = {}

    for col in columns:
        normalized = normalize_column_name(col)

        if normalized in df_columns:
            valid.append(normalized)
        else:
            invalid.append(col)
            # Sugerir colunas similares
            similar = [c for c in df_columns if col.lower() in c.lower() or c.lower() in col.lower()]
            if similar:
                suggestions[col] = similar[:3]  # Top 3 sugestões

    return {
        "valid": valid,
        "invalid": invalid,
        "suggestions": suggestions
    }


def get_essential_columns() -> list:
    """
    Retorna lista de colunas essenciais.

    Returns:
        Lista com nomes reais das colunas essenciais
    """
    return ESSENTIAL_COLUMNS.copy()


def list_all_columns() -> list:
    """
    Lista todas as colunas conhecidas com suas informações.

    Returns:
        Lista de tuplas (nome_real, descricao)
    """
    return [(name, info["descricao"]) for name, info in COLUMN_INFO.items()]
