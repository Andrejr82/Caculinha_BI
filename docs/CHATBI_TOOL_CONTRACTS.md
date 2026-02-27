# ChatBI Tool Contracts

## 1. Objetivo
Definir contrato operacional de ferramentas para reduzir drift entre prompt, roteamento e execução real.

## 2. Fonte de verdade
- Registro e execução de tools: `backend/app/core/agents/caculinha_bi_agent.py`
- Roteamento: `backend/app/core/utils/query_router.py`
- Ferramentas: `backend/app/core/tools/`

## 3. Contratos principais

### `gerar_grafico_universal_v2`
- Uso: pedidos de gráfico, ranking visual, comparação por loja/segmento.
- Parâmetros-chave:
  - `descricao` (obrigatório)
  - `tipo_grafico` (`bar|line|pie|auto`)
  - `quebra_por` (`LOJA|SEGMENTO|CATEGORIA|PRODUTO|...`)
  - `filtro_segmento`, `filtro_une`, `limite`
- Sucesso:
  - `status=success`
  - `chart_data` (JSON plotly)
  - `summary` (top_3, total, mensagem)
- Erro:
  - `status=error`
  - `error_code=NO_DATA` (quando aplicável)
  - `diagnostics` (recorte/RLS)

### `consultar_dados_flexivel`
- Uso: consulta tabular/agregações ad-hoc.
- Parâmetros-chave:
  - `filtros` (dict/json-string)
  - `colunas`
  - `agregacao`, `coluna_agregacao`, `agrupar_por`
  - `ordenar_por`, `ordem_desc`, `limite`
- Sucesso:
  - `total_resultados`
  - `resultados`
  - `mensagem`
- Erro:
  - `error` + payload vazio.

### `pesquisar_precos_concorrentes`
- Uso: benchmark de concorrentes específicos.
- Entrada típica:
  - `descricao_produto`, `segmento`, `estado`, `cidade`, `concorrentes`, `limite`
- Saída:
  - itens consolidados, fontes, escopo, métricas comparativas.

### `pesquisar_mercado_web`
- Uso: pesquisa aberta de mercado (sem concorrente específico).
- Entrada típica:
  - `termo_pesquisa`, `limite`
- Saída:
  - itens, fontes consultadas, resumo de mercado.

### `encontrar_rupturas_criticas`
- Uso: análise de ruptura.
- Entrada típica:
  - `segmento`, `une`, `limite`
- Saída:
  - total crítico, itens críticos, prioridades.

### `calcular_abastecimento_une`

- Uso: diagnóstico de abastecimento por loja.
- Entrada:
  - `une_id`
- Saída:
  - status de cobertura, itens críticos/excesso, recomendações.

### `analisar_produto_todas_lojas`
- Uso: visão de produto em toda rede.
- Entrada:
  - `produto_codigo`
- Saída:
  - distribuição por loja, cobertura e sinais operacionais.

### `consultar_dicionario_dados`
- Uso: descoberta de schema/colunas para ferramentas.

### `analisar_historico_vendas`
- Uso: histórico de vendas para recorte temporal e contexto analítico.

## 4. Regras de compatibilidade
- Argumentos podem chegar como `str` ou tipo nativo; normalização ocorre no agente.
- `limite` deve ser coerido com segurança para evitar falhas de schema/provider.

## 5. Erros padronizados
- `NO_DATA`: sem dados no recorte.
- `NO_DATA` + `diagnostics.likely_rls_block=true`: provável bloqueio de acesso por segmento.

## 6. Checklist para nova tool
1. Declarar assinatura estável.
2. Definir retorno de sucesso/erro explícito.
3. Adicionar regra de roteamento.
4. Adicionar teste unitário + integração mínima.
5. Atualizar este documento.

