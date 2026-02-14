"""
Ferramenta Universal de Geração de Gráficos - Context7 2025
Solução definitiva para gráficos com filtros dinâmicos e performance otimizada.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import plotly.graph_objects as go
from langchain_core.tools import tool
from backend.app.core.data_source_manager import get_data_manager

logger = logging.getLogger(__name__)


def _export_chart_to_json(fig: go.Figure) -> str:
    """Exporta figura como JSON para frontend."""
    return fig.to_json()


@tool
def gerar_grafico_universal_v2(
    descricao: str,
    filtro_une: Optional[str] = None,
    filtro_segmento: Optional[str] = None,
    filtro_categoria: Optional[str] = None,
    filtro_produto: Optional[str] = None,
    tipo_grafico: str = "auto",
    quebra_por: Optional[str] = None,  # NEW: Controle explícito de agrupamento
    limite: Optional[Union[int, str]] = None
) -> Dict[str, Any]:
    """
    Gera gráficos interativos, rankings visuais, comparações e dashboards estatísticos.
    
    USE QUANDO: O usuário pedir "gráfico", "plotar", "visualizar", "ranking", "top N", 
    "comparar lojas", "tendência visual", "pizza", "barras", "evolução".
    
    Args:
        descricao: Descrição do que deve ser visualizado (ex: "vendas por segmento")
        filtro_une: Código da loja/UNE (ex: "1685" ou "1685, 2365").
        filtro_segmento: Nome do segmento
        filtro_categoria: Nome da categoria
        filtro_produto: Código do produto (SKU)
        tipo_grafico: "bar", "pie", "line", "auto"
        quebra_por: Campo para agrupar/eixo X. Opções: "LOJA", "SEGMENTO", "CATEGORIA", "PRODUTO", "TEMPO", "FABRICANTE".
        limite: Número máximo de itens (ex: 10).

    Returns:
        Gráfico Plotly JSON com dados filtrados
    """
    # ... (parser de filtros existente) ...
    # 1. Parse de Filtros Numéricos (Lista ou Único)
    lista_unes = []
    if filtro_une is not None:
        try:
            if isinstance(filtro_une, str) and "," in filtro_une:
                lista_unes = [int(u.strip()) for u in filtro_une.split(",") if u.strip().isdigit()]
            elif isinstance(filtro_une, list):
                lista_unes = [int(u) for u in filtro_une]
            else:
                lista_unes = [int(filtro_une)]
        except (ValueError, TypeError):
            logger.warning(f"Erro ao parsear filtro_une: {filtro_une}")

    lista_produtos = []
    if filtro_produto is not None:
        try:
            if isinstance(filtro_produto, str) and "," in filtro_produto:
                lista_produtos = [int(p.strip()) for p in filtro_produto.split(",") if p.strip().isdigit()]
            elif isinstance(filtro_produto, list):
                lista_produtos = [int(p) for p in filtro_produto]
            else:
                lista_produtos = [int(filtro_produto)]
        except (ValueError, TypeError):
            logger.warning(f"Erro ao parsear filtro_produto: {filtro_produto}")

    try:
        if limite is not None:
            limite = int(limite)
        else:
            limite = 100
    except:
        limite = 100
        
    logger.info(f"[UNIVERSAL CHART] Gerando: {descricao} | UNEs={lista_unes} | Segmento={filtro_segmento} | Quebra={quebra_por}")

    # -------------------------------------------------------------------------
    # 0. Detectar intenção de visualização (DIMENSÕES E MÉTRICAS)
    # -------------------------------------------------------------------------
    descricao_lower = descricao.lower()
    
    # Lógica de Comparação
    is_comparison = len(lista_unes) > 1 and ("compar" in descricao_lower or "entre" in descricao_lower or "vs" in descricao_lower)
    # Detectar "por loja" / "todas as lojas"
    # FIX: Usar quebra_por explícito se fornecido
    is_by_store = False
    if quebra_por and any(x in quebra_por.upper() for x in ["LOJA", "UNE", "STORE"]):
        is_by_store = True
    else:
        is_by_store = any(kw in descricao_lower for kw in ["por loja", "por une", "todas as lojas", "cada loja", "em todas", "todas lojas"])

    # -------------------------------------------------------------------------
    # DEFENSIVE OVERRIDE 2026-01-28: Prevent Truncation
    # Se o usuário pediu "todas as lojas" e o limite for baixo (<50), FORÇAR 200.
    # -------------------------------------------------------------------------
    if is_by_store and ("todas" in descricao_lower or "all" in descricao_lower):
        if limite < 50:
            logger.warning(f"[OVERRIDE] Limite de {limite} muito baixo para 'Todas as Lojas'. Forçando 200.")
            limite = 200

    # Default metrics
    group_col = "NOMESEGMENTO" 
    titulo_dimensao = "Segmento"
    metric_col = "SUM(VENDA_30DD)"
    titulo_metrica = "Vendas (30 dias)"

    # Definição de Colunas de Agrupamento (Dimensão)
    # FIX: Priorizar quebra_por explícito
    if quebra_por:
        qp = quebra_por.upper()
        if "LOJA" in qp or "UNE" in qp:
            group_col = "UNE"
            titulo_dimensao = "Loja (UNE)"
        elif "SEGMENTO" in qp:
            group_col = "NOMESEGMENTO"
            titulo_dimensao = "Segmento"
        elif "CATEGORIA" in qp:
            group_col = "NOMECATEGORIA"
            titulo_dimensao = "Categoria"
        elif "PRODUTO" in qp:
            group_col = "NOME"
            titulo_dimensao = "Produto"
        elif "GRUPO" in qp:
            group_col = "NOMEGRUPO"
            titulo_dimensao = "Grupo"
        elif "FABRICANTE" in qp:
            group_col = "NOMEFABRICANTE"
            titulo_dimensao = "Fabricante"
    
    # Fallback para lógica implícita se quebra_por não for definido
    elif is_comparison or is_by_store:
        group_col = "UNE"
        titulo_dimensao = "Loja (UNE)"
    elif "segmento" in descricao_lower:
        group_col = "NOMESEGMENTO"
        titulo_dimensao = "Segmento"
    elif "categoria" in descricao_lower:
        group_col = "NOMECATEGORIA"
        titulo_dimensao = "Categoria"
    elif "grupo" in descricao_lower:
        group_col = "NOMEGRUPO"
        titulo_dimensao = "Grupo"
    elif "fabricante" in descricao_lower:
        group_col = "NOMEFABRICANTE"
        titulo_dimensao = "Fabricante"
    elif "produto" in descricao_lower and not lista_produtos:
        group_col = "NOME"
        titulo_dimensao = "Produto"
    elif lista_produtos:
        if not is_by_store and not is_comparison:
             group_col = "NOME"
             titulo_dimensao = "Produto"
        else:
             group_col = "UNE"
             titulo_dimensao = "Loja (UNE)"

    # Definição de Métricas
    if any(kw in descricao_lower for kw in ["venda", "faturamento", "receita", "valor"]):
        metric_col = "SUM(VENDA_30DD)" # Usando coluna agregada
        titulo_metrica = "Vendas (R$)"
    elif any(kw in descricao_lower for kw in ["estoque", "quantidade", "volume"]):
        metric_col = "SUM(ESTOQUE_ATUAL)"
        titulo_metrica = "Estoque (un)"
    elif any(kw in descricao_lower for kw in ["ruptura", "falta"]):
        # Ruptura é complexa, count where estoque <= 0
        metric_col = "COUNT(*)"
        titulo_metrica = "Itens em Ruptura"
        # Nota: Ruptura exige filtro WHERE ESTOQUE <= 0, tratado na query abaixo

    df = None
    
    # -------------------------------------------------------------------------
    # OTIMIZAÇÃO DUCKDB (Push-down Predicates)
    # Tenta filtrar via SQL antes de carregar para Pandas
    # -------------------------------------------------------------------------
    try:
        from backend.app.core.parquet_cache import cache
        from backend.app.core.context import get_current_user_segments # RLS
        
        # 1. Garantir que a tabela está carregada em memória (Zero-Copy)
        table_name = cache._adapter.get_memory_table("admmat.parquet")
        
        # 2. Construir Query SQL
        # Ajuste para Ruptura
        where_clause = "1=1"
        if "ruptura" in descricao_lower:
             where_clause += " AND ESTOQUE_ATUAL <= 0"
        
        # FIX 2026-01-28: Aumentar limite padrão para cobrir todas as lojas (aprox 50)
        # O limite 15 anterior estava cortando resultados de "todas as lojas"
        limit_clause = f"LIMIT {limite}" if limite else "LIMIT 200"
        
        sql_query = f"""
            SELECT 
                {group_col} as dimensao,
                {metric_col} as metrica
            FROM {table_name} 
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY metrica DESC
            {limit_clause}
        """
        
        # --- RLS INJECTION (SEGURANÇA) ---
        allowed_segments = get_current_user_segments()
        if allowed_segments and "*" not in allowed_segments:
            safe_segments = [s.replace("'", "''") for s in allowed_segments]
            segments_sql = ",".join([f"'{s}'" for s in safe_segments])
            where_clause += f" AND NOMESEGMENTO IN ({segments_sql})"
            logger.info(f"[RLS] Aplicando filtro SQL: NOMESEGMENTO IN ({segments_sql})")
        # ---------------------------------
        
        if lista_unes:
            unes_str = ",".join(map(str, lista_unes))
            where_clause += f" AND UNE IN ({unes_str})"
            
        if filtro_segmento:
            # Code Archaeologist: FIX SQL INJECTION - Use LIKE with parameter
            # Workaround: Sanitize input rigorously
            seg_clean = filtro_segmento.replace("'", "''").replace("%", "").replace("_", "")
            if seg_clean.replace(" ", "").isalnum() or all(c.isalnum() or c.isspace() for c in seg_clean):
                where_clause += f" AND NOMESEGMENTO ILIKE '%{seg_clean}%'"
            else:
                logger.warning(f"Filtro de segmento rejeitado por conter caracteres suspeitos: {filtro_segmento}")
            
        if filtro_categoria:
            # Code Archaeologist: FIX SQL INJECTION - Sanitize input
            cat_clean = filtro_categoria.replace("'", "''").replace("%", "").replace("_", "")
            if cat_clean.replace(" ", "").isalnum() or all(c.isalnum() or c.isspace() for c in cat_clean):
                where_clause += f" AND NOMECATEGORIA ILIKE '%{cat_clean}%'"
            else:
                logger.warning(f"Filtro de categoria rejeitado: {filtro_categoria}")
            
        if lista_produtos:
            prods_str = ",".join(map(str, lista_produtos))
            # Cast para garantir comparação correta com ints
            where_clause += f" AND CAST(PRODUTO AS BIGINT) IN ({prods_str})"
            
        sql_query = f"""
            SELECT 
                {group_col} as dimensao,
                {metric_col} as metrica
            FROM {table_name} 
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY metrica DESC
            {limit_clause}
        """

        logger.info(f"[DUCKDB OPTIMIZATION] Executando SQL: {sql_query}")
        
        # 3. Executar via Adapter
        result = cache._adapter.query(sql_query)
        
        if hasattr(result, 'df'):
            df = result.df()
        elif hasattr(result, 'to_pandas'):
            df = result.to_pandas()
        else:
            df = pd.DataFrame(result)
            
        logger.info(f"[DUCKDB OPTIMIZATION] Sucesso! {len(df)} registros recuperados via SQL.")
        
    except Exception as sql_err:
        logger.warning(f"[DUCKDB OPTIMIZATION] Falhou, usando fallback Pandas lento: {sql_err}")
        df = None

    # -------------------------------------------------------------------------
    # FALLBACK PANDAS (Lógica Original)
    # -------------------------------------------------------------------------
    if df is None:
        # 1. Obter dados (Full Scan lento)
        manager = get_data_manager()
        df = manager.get_data()
        
        # Conversão robusta para Pandas
        if hasattr(df, 'to_pandas'):
            df = df.to_pandas()
        elif hasattr(df, 'df'):
            df = df.df()
        elif not isinstance(df, pd.DataFrame):
            try:
                df = pd.DataFrame(df)
            except Exception:
                pass 

        if df is None or df.empty:
            return {"status": "error", "message": "Dados não disponíveis"}

        # 2. Aplicar filtros (Lento em Pandas)
        df_filtered = df

        if lista_unes:
            if 'UNE' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['UNE'].isin(lista_unes)]
                logger.info(f"Filtrado UNEs {lista_unes}: {len(df_filtered)} registros")

        if filtro_segmento:
            if 'NOMESEGMENTO' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['NOMESEGMENTO'].str.contains(filtro_segmento, case=False, na=False)]

        if filtro_categoria:
            if 'NOMECATEGORIA' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['NOMECATEGORIA'].str.contains(filtro_categoria, case=False, na=False)]

        if lista_produtos:
            if 'PRODUTO' in df_filtered.columns:
                df_filtered['PRODUTO'] = pd.to_numeric(df_filtered['PRODUTO'], errors='coerce')
                df_filtered = df_filtered[df_filtered['PRODUTO'].isin(lista_produtos)]
    else:
        # Se veio do SQL, já está filtrado
        df_filtered = df

    if df_filtered.empty:
        return {
            "status": "error",
            "message": f"Nenhum dado encontrado para os filtros aplicados."
        }

    # 3. Dados finais prontos para agregação
    logger.info(f"Dados finais para gráfico: {len(df_filtered)} linhas")


    # Definição de Métricas
    if "estoque" in descricao_lower:
        metric_col = "ESTOQUE_UNE"
        titulo_metrica = "Estoque"
        agg_func = "SUM"
    elif "preco" in descricao_lower:
        metric_col = "PRECO_VENDA"
        titulo_metrica = "Preço Médio"
        agg_func = "AVG"
    elif "custo" in descricao_lower:
        metric_col = "PRECO_CUSTO" # Ajuste conforme nome real da coluna se necessário
        titulo_metrica = "Custo Médio"
        agg_func = "AVG"
    else:
        # Default vendas
        metric_col = "VENDA_30DD"
        titulo_metrica = "Vendas"
        agg_func = "SUM"

    df_agg = None

    # -------------------------------------------------------------------------
    # OTIMIZAÇÃO DUCKDB (Aggregation Push-down)
    # Executa o GROUP BY direto no motor SQL
    # -------------------------------------------------------------------------
    try:
        from backend.app.core.parquet_cache import cache
        from backend.app.core.context import get_current_user_segments # RLS
        
        table_name = cache._adapter.get_memory_table("admmat.parquet")
        
        # Monta a query de agregação
        # Ex: SELECT NOMESEGMENTO as dimensao, SUM(VENDA_30DD) as valor FROM ...
        
        select_clause = f"SELECT {group_col} as dimensao, {agg_func}(CAST({metric_col} AS DOUBLE)) as valor"
        where_clause = " FROM " + table_name + " WHERE 1=1"
        
        # --- RLS INJECTION (SEGURANÇA) ---
        allowed_segments = get_current_user_segments()
        if allowed_segments and "*" not in allowed_segments:
            safe_segments = [s.replace("'", "''") for s in allowed_segments]
            segments_sql = ",".join([f"'{s}'" for s in safe_segments])
            where_clause += f" AND NOMESEGMENTO IN ({segments_sql})"
        # ---------------------------------
        
        if lista_unes:
            unes_str = ",".join(map(str, lista_unes))
            where_clause += f" AND UNE IN ({unes_str})"
            
        if filtro_segmento:
            seg_clean = filtro_segmento.replace("'", "''")
            where_clause += f" AND NOMESEGMENTO ILIKE '%{seg_clean}%'"
            
        if filtro_categoria:
            cat_clean = filtro_categoria.replace("'", "''")
            where_clause += f" AND NOMECATEGORIA ILIKE '%{cat_clean}%'"
            
        if lista_produtos:
            prods_str = ",".join(map(str, lista_produtos))
            where_clause += f" AND CAST(PRODUTO AS BIGINT) IN ({prods_str})"
            
        # Group By e Order By
        group_by_clause = f" GROUP BY {group_col}"
        
        if group_col == "UNE":
             # Ordenar por número da loja se for comparação
             order_by_clause = " ORDER BY 1 ASC" 
        else:
             # Ordenar por valor descrescente (Ranking)
             order_by_clause = " ORDER BY 2 DESC"
             
        full_sql = select_clause + where_clause + group_by_clause + order_by_clause + f" LIMIT {limite}"
            
        logger.info(f"[DUCKDB AGGREGATION] Executando SQL: {full_sql}")
        
        # Executar
        result = cache._adapter.query(full_sql)
        
        if hasattr(result, 'df'):
            df_agg = result.df()
        elif hasattr(result, 'to_pandas'):
            df_agg = result.to_pandas()
        else:
            df_agg = pd.DataFrame(result, columns=["dimensao", "valor"])
            
        logger.info(f"[DUCKDB AGGREGATION] Sucesso! {len(df_agg)} linhas agregadas.")
        
    except Exception as sql_err:
        logger.warning(f"[DUCKDB AGGREGATION] Falhou: {sql_err}. Tentando fallback Pandas...")
        df_agg = None

    # -------------------------------------------------------------------------
    # FALLBACK PANDAS (Código legado para segurança)
    # -------------------------------------------------------------------------
    if df_agg is None:
        # 1. Obter dados (Full Scan lento)
        manager = get_data_manager()
        df = manager.get_data()
        
        # Conversão robusta para Pandas
        if hasattr(df, 'to_pandas'):
            df = df.to_pandas()
        elif hasattr(df, 'df'):
            df = df.df()
        elif not isinstance(df, pd.DataFrame):
            try:
                df = pd.DataFrame(df)
            except Exception:
                pass 

        if df is None or df.empty:
            return {"status": "error", "message": "Dados não disponíveis"}

        # 2. Aplicar filtros
        df_filtered = df

        if lista_unes:
            if 'UNE' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['UNE'].isin(lista_unes)]

        if filtro_segmento:
            if 'NOMESEGMENTO' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['NOMESEGMENTO'].str.contains(filtro_segmento, case=False, na=False)]

        if filtro_categoria:
            if 'NOMECATEGORIA' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['NOMECATEGORIA'].str.contains(filtro_categoria, case=False, na=False)]

        if lista_produtos:
            if 'PRODUTO' in df_filtered.columns:
                df_filtered['PRODUTO'] = pd.to_numeric(df_filtered['PRODUTO'], errors='coerce')
                df_filtered = df_filtered[df_filtered['PRODUTO'].isin(lista_produtos)]

        # 3. Agregar em Pandas
        if group_col not in df_filtered.columns:
            return {"status": "error", "message": f"Coluna {group_col} não encontrada"}

        if metric_col:
            df_filtered = df_filtered.copy()
            df_filtered.loc[:, metric_col] = pd.to_numeric(df_filtered[metric_col], errors='coerce').fillna(0)
            
            if agg_func == "SUM":
                df_agg = df_filtered.groupby(group_col)[metric_col].sum().reset_index()
            elif agg_func == "AVG":
                df_agg = df_filtered.groupby(group_col)[metric_col].mean().reset_index()
            else:
                df_agg = df_filtered.groupby(group_col)[metric_col].count().reset_index()
        else:
            df_agg = df_filtered[group_col].value_counts().reset_index()
        
        df_agg.columns = ["dimensao", "valor"]
        
        if group_col == "UNE":
                df_agg["dimensao"] = pd.to_numeric(df_agg["dimensao"], errors='coerce')
                df_agg = df_agg.sort_values("dimensao")
        else:
                df_agg = df_agg.sort_values("valor", ascending=False).head(limite)

    # -------------------------------------------------------------------------
    # GERAÇÃO DO GRÁFICO (Comum para ambos os caminhos)
    # -------------------------------------------------------------------------
    
    if df_agg is None or df_agg.empty:
        return {"status": "error", "message": "Sem dados agregados"}

    # Garantir tipos
    df_agg["dimensao"] = df_agg["dimensao"].astype(str)
    
    # 5. Gerar gráfico
    if tipo_grafico == "auto":
        tipo_grafico = "bar"

    fig = go.Figure()

    if tipo_grafico == "pie":
        fig.add_trace(go.Pie(labels=df_agg["dimensao"], values=df_agg["valor"], hole=0.3))
    elif tipo_grafico in ("line", "linhas"):
        fig.add_trace(go.Scatter(
            x=df_agg["dimensao"],
            y=df_agg["valor"],
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=7),
            text=df_agg["valor"].apply(lambda x: f"{x:,.0f}"),
        ))
    elif tipo_grafico == "pareto":
        pareto_df = df_agg.copy()
        total = float(pareto_df["valor"].sum() or 0)
        pareto_df["acumulado_pct"] = (pareto_df["valor"].cumsum() / total * 100) if total > 0 else 0
        fig.add_trace(go.Bar(
            x=pareto_df["dimensao"],
            y=pareto_df["valor"],
            marker_color="#1f77b4",
            name="Valor"
        ))
        fig.add_trace(go.Scatter(
            x=pareto_df["dimensao"],
            y=pareto_df["acumulado_pct"],
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
            yaxis="y2",
            name="% Acumulado"
        ))
        fig.update_layout(
            yaxis2=dict(
                title="% Acumulado",
                overlaying="y",
                side="right",
                range=[0, 110],
                showgrid=False,
            )
        )
    else:
        fig.add_trace(go.Bar(
            x=df_agg["dimensao"], 
            y=df_agg["valor"],
            marker_color='#1f77b4',
            text=df_agg["valor"].apply(lambda x: f"{x:,.0f}"),
            textposition='auto'
        ))

    titulo = f"{titulo_metrica} por {titulo_dimensao}"
    if filtro_segmento: titulo += f" ({filtro_segmento})"

    fig.update_layout(
        title=titulo,
        template="plotly_white",
        height=600,  # Aumentado de 500 para 600
        margin=dict(l=60, r=40, t=80, b=120),  # Margens maiores para labels
        xaxis_title=titulo_dimensao,
        yaxis_title=titulo_metrica,
        xaxis_tickangle=-45  # Rotacionar labels do eixo X para melhor leitura
    )

    # 6. Resumo analítico para melhorar resposta textual do LLM.
    total_valor = float(df_agg["valor"].sum() or 0)
    top_n = df_agg.nlargest(min(3, len(df_agg)), "valor")[["dimensao", "valor"]]
    bottom_n = df_agg.nsmallest(min(3, len(df_agg)), "valor")[["dimensao", "valor"]]

    def _to_pairs(frame: pd.DataFrame) -> List[Dict[str, Any]]:
        return [{"dimensao": str(r["dimensao"]), "valor": float(r["valor"])} for _, r in frame.iterrows()]

    summary_msg = (
        f"Análise concluída: {len(df_agg)} itens. "
        f"Total de {titulo_metrica.lower()}: {total_valor:,.2f}. "
        f"Maior destaque: {top_n.iloc[0]['dimensao']} ({float(top_n.iloc[0]['valor']):,.2f})."
        if len(df_agg) > 0
        else "Análise concluída sem dados agregados."
    )

    return {
        "status": "success",
        "chart_type": tipo_grafico,
        "chart_data": _export_chart_to_json(fig),
        "summary": {
            "dimensao": titulo_dimensao,
            "metrica": titulo_metrica,
            "total_itens": len(df_agg),
            "total_valor": total_valor,
            "top_3": _to_pairs(top_n),
            "bottom_3": _to_pairs(bottom_n),
            "mensagem": summary_msg,
        }
    }
