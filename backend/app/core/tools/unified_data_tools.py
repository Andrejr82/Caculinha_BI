"""
Ferramentas unificadas para acessar dados de Filial_Madureira.parquet
Este arquivo foi refatorado para usar o DataSourceManager centralizado.
"""

import logging
from typing import Dict, Any, Optional, Union
import pandas as pd
from langchain_core.tools import tool

# Importa o gerenciador de dados centralizado
from app.core.data_source_manager import get_data_manager

logger = logging.getLogger(__name__)


def _truncate_df_for_llm(df: pd.DataFrame, max_rows: int = 10) -> Dict[str, Any]:
    """Trunca o DataFrame e prepara a resposta para o LLM."""
    if df is None or df.empty:
        return {
            "data": [],
            "message": "Nenhum dado para exibir.",
            "total_records": 0
        }
    
    total_records = len(df)
    if total_records > max_rows:
        return {
            "data": df.head(max_rows).to_dict(orient="records"),
            "message": f"Mostrando as primeiras {max_rows} de {total_records} linhas.",
            "total_records": total_records
        }
    return {
        "data": df.to_dict(orient="records"),
        "total_records": total_records
    }


@tool
def listar_colunas_disponiveis() -> Dict[str, Any]:
    """
    IMPORTANTE: Use esta ferramenta PRIMEIRO quando não souber quais colunas existem!

    USE QUANDO: O usuário perguntar "quais colunas tem", "schema do banco", "estrutura dos dados"
    e a ferramenta de metadados falhar.
    
    Lista todas as colunas disponíveis na fonte de dados principal (Filial_Madureira.parquet)
    com seus tipos de dados e exemplos de valores.
    
    Esta é a ÚNICA fonte de dados do sistema. Não existe banco SQL ativo.
    
    Returns:
        Dicionário com lista de colunas, tipos e exemplos de valores.
    """
    logger.info("Listando colunas disponíveis via DataSourceManager")
    
    try:
        data_manager = get_data_manager()
        source_info = data_manager.get_source_info()

        if not source_info or source_info.get("status") == "sem_dados":
            return {
                "status": "error",
                "message": "Não foi possível carregar os dados através do DataSourceManager."
            }

        df = data_manager.get_data(limit=10) # Pega alguns dados para exemplos
        if df.empty:
             return {
                "status": "error",
                "message": "Fonte de dados vazia."
            }

        colunas_info = []
        for col, dtype in source_info.get("dtypes", {}).items():
            col_info = {
                "nome": col,
                "tipo": str(dtype),
                "exemplo": str(df[col].iloc[0]) if not df.empty and col in df.columns and len(df) > 0 else "N/A",
                "valores_nulos": int(df[col].isna().sum()) if col in df.columns else "N/A"
            }
            colunas_info.append(col_info)
            
        return {
            "status": "success",
            "total_colunas": source_info.get("shape", (0,0))[1],
            "total_registros": source_info.get("shape", (0,0))[0],
            "colunas": colunas_info,
            "arquivo": source_info.get("file"),
            "message": f"Encontradas {len(colunas_info)} colunas na fonte de dados."
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar colunas: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Erro: {str(e)}"
        }


@tool
def consultar_dados(
    coluna: Optional[str] = None,
    valor: Optional[str] = None,  # FIX: Era Union[str, int, float], causava MALFORMED_FUNCTION_CALL
    coluna_retorno: Optional[str] = None,
    limite: int = 100
) -> str:
    """
    Consulta dados na fonte de dados Filial_Madureira.parquet.
    
    Use `listar_colunas_disponiveis` para ver as colunas.
    
    Args:
        coluna: Nome da coluna para filtrar (opcional).
        valor: Valor a buscar na coluna (aceita string, int ou float).
        coluna_retorno: Coluna específica para retornar (opcional).
        limite: Limite de registros (padrão: 100).
    
    Returns:
        Uma string formatada com os dados consultados ou uma mensagem de erro/não encontrado.
    """
    logger.info(f"Consultando via DataSourceManager: coluna={coluna}, valor={valor}, coluna_retorno={coluna_retorno}, limite={limite}")
    
    try:
        data_manager = get_data_manager()
        
        # Se não houver filtro, retorna os primeiros dados
        if not coluna or valor is None:
            df_resultado = data_manager.get_data(limit=limite)
        else:
            # [OK] Converte valor para string (aceita int, float ou string)
            df_resultado = data_manager.search_data(column=coluna, value=str(valor), limit=limite)

        if df_resultado is None or df_resultado.empty:
            filtro_msg = f" com filtro {coluna}='{valor}'" if coluna and valor is not None else ""
            return f"Nenhum dado encontrado{filtro_msg}."

        # Se coluna_retorno especificada, retornar apenas essa coluna
        if coluna_retorno:
            if coluna_retorno not in df_resultado.columns:
                return f"Coluna de retorno '{coluna_retorno}' não encontrada."
            
            if df_resultado.empty:
                 return f"Nenhum valor encontrado para '{coluna_retorno}' com o filtro especificado."

            valor_retornado = df_resultado[coluna_retorno].iloc[0]
            
            if pd.isna(valor_retornado) or valor_retornado == '':
                return f"O valor para '{coluna_retorno}' no produto com {coluna}='{valor}' não foi encontrado ou está vazio."

            # Formatação humanizada para casos comuns
            coluna_upper = coluna.upper()
            coluna_retorno_upper = coluna_retorno.upper()

            # PREÇO DO PRODUTO
            if coluna_upper == 'PRODUTO' and coluna_retorno_upper == 'LIQUIDO_38':
                try:
                    preco = float(valor_retornado)
                    return f"O preço do produto {valor} é **R$ {preco:.2f}**."
                except:
                    return f"O preço do produto {valor} é R$ {valor_retornado}."

            # CUSTO DO PRODUTO
            elif coluna_upper == 'PRODUTO' and coluna_retorno_upper == 'ULTIMA_ENTRADA_CUSTO_CD':
                try:
                    custo = float(valor_retornado)
                    return f"O custo do produto {valor} é **R$ {custo:.2f}**."
                except:
                    return f"O custo do produto {valor} é R$ {valor_retornado}."

            # ESTOQUE DO PRODUTO
            elif coluna_upper == 'PRODUTO' and coluna_retorno_upper == 'ESTOQUE_UNE':
                try:
                    estoque = int(valor_retornado)
                    return f"O produto {valor} tem **{estoque} unidades** em estoque."
                except:
                    return f"O produto {valor} tem {valor_retornado} em estoque."

            # NOME DO PRODUTO
            elif coluna_upper == 'PRODUTO' and coluna_retorno_upper == 'NOME':
                return f"O produto {valor} é **{valor_retornado}**."

            # FABRICANTE DO PRODUTO
            elif coluna_upper == 'PRODUTO' and coluna_retorno_upper == 'NOMEFABRICANTE':
                return f"O fabricante do produto {valor} é **{valor_retornado}**."

            # FALLBACK (caso genérico)
            else:
                return f"O valor de {coluna_retorno} para {coluna}='{valor}' é '{valor_retornado}'."
        
        # Retornar dados completos
        response_data = _truncate_df_for_llm(df_resultado, max_rows=limite)
        return f"Consulta retornou {response_data['total_records']} registros. Primeiros resultados: {response_data['data']}"
        
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}", exc_info=True)
        return f"Erro ao consultar dados: {str(e)}."


@tool
def buscar_produto(
    codigo: Optional[str] = None,
    nome: Optional[str] = None,
    limite: int = 100
) -> Dict[str, Any]:
    """
    Busca produtos por código ou nome usando o DataSourceManager.
    
    USE QUANDO: Busca simples de cadastro. Ex: "Busque o produto X", "Existe produto com nome Y?".
    Para buscas vagas/semânticas, prefira `buscar_produtos_inteligente`.

    Args:
        codigo: Código do produto (busca em 'CODIGO').
        nome: Nome do produto (busca parcial em 'DESCRIÇÃO').
        limite: Número máximo de resultados.
    
    Returns:
        Dicionário com os produtos encontrados.
    """
    logger.info(f"Buscando produto via DataSourceManager: código={codigo}, nome={nome}")
    
    try:
        data_manager = get_data_manager()
        df_result = pd.DataFrame()
        criterio = ""
        valor_buscado = ""

        if codigo:
            df_result = data_manager.search_data(column='CODIGO', value=str(codigo).strip(), limit=limite)
            criterio = "código"
            valor_buscado = codigo
        elif nome:
            df_result = data_manager.search_data(column='DESCRIÇÃO', value=nome, limit=limite)
            criterio = "nome"
            valor_buscado = nome
        else:
            return {"status": "error", "message": "Informe código ou nome do produto."}
        
        if df_result is None or df_result.empty:
            return {
                "status": "not_found",
                "message": f"Produto não encontrado com {criterio}='{valor_buscado}'."
            }
        
        response_data = _truncate_df_for_llm(df_result, max_rows=limite)
        
        return {
            "status": "success",
            "criterio_busca": criterio,
            "valor_buscado": valor_buscado,
            "colunas": list(df_result.columns),
            **response_data
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar produto: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro: {str(e)}"}


@tool
def obter_estoque(
    codigo_produto: Optional[str] = None,
    nome_produto: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém informações de estoque de um produto usando o DataSourceManager.
    
    USE QUANDO: O usuário perguntar ESPECIFICAMENTE sobre "estoque", "saldo", "quantidade" de um item.
    
    Args:
        codigo_produto: Código do produto.
        nome_produto: Nome do produto.
    
    Returns:
        Dados de estoque do produto.
    """
    logger.info(f"Consultando estoque via DataSourceManager: código={codigo_produto}, nome={nome_produto}")
    
    try:
        data_manager = get_data_manager()
        df_produto = pd.DataFrame()
        criterio = ""

        if codigo_produto:
            df_produto = data_manager.search_data(column='CODIGO', value=str(codigo_produto).strip(), limit=1)
            criterio = f"código={codigo_produto}"
        elif nome_produto:
            df_produto = data_manager.search_data(column='DESCRIÇÃO', value=nome_produto, limit=1)
            criterio = f"nome contendo '{nome_produto}'"
        else:
            return {"status": "error", "message": "Informe código ou nome do produto."}
        
        if df_produto is None or df_produto.empty:
            return {
                "status": "not_found",
                "message": f"Produto não encontrado com {criterio}."
            }
        
        produto = df_produto.iloc[0]
        
        estoque_col = None
        estoque_valor = 0
        for col in ['QTD', 'SALDO', 'ESTOQUE']:
            if col in df_produto.columns:
                estoque_col = col
                valor = produto.get(col)
                if pd.notna(valor):
                    estoque_valor = int(valor)
                break
        
        info_produto = {
            "codigo": str(produto.get('CODIGO', 'N/A')),
            "descricao": str(produto.get('DESCRIÇÃO', 'N/A')),
            "estoque_coluna": estoque_col,
            "estoque_valor": estoque_valor,
            "fabricante": str(produto.get('FABRICANTE', 'N/A')),
            "grupo": str(produto.get('GRUPO', 'N/A'))
        }
        
        return {
            "status": "success",
            "criterio_busca": criterio,
            "produto": info_produto
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estoque: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro: {str(e)}"}


# Importação do novo tool flexível
from app.core.tools.flexible_query_tool import consultar_dados_flexivel
from app.core.tools.offline_chart_tool import gerar_grafico_offline
# [OK] FIX 2026-01-14: Importar ferramenta principal de gráficos mencionada no SYSTEM_PROMPT
from app.core.tools.universal_chart_generator import gerar_grafico_universal_v2
# [OK] FIX 2026-01-15: Ferramenta de análise multi-loja (evita loops de timeout)
from app.core.tools.une_tools import analisar_produto_todas_lojas

# Lista de ferramentas unificadas - EXPORTAÇÃO IMPORTANTE
unified_tools = [
    listar_colunas_disponiveis,
    consultar_dados,
    buscar_produto,
    obter_estoque,
    consultar_dados_flexivel,       # Ferramenta principal de consulta de dados
    analisar_produto_todas_lojas,   # [OK] FIX 2026-01-15: Análise multi-loja sem loop
    gerar_grafico_universal_v2,     # [OK] FIX: Ferramenta principal de gráficos
    gerar_grafico_offline,          # Ferramenta de backup para gráficos offline
]