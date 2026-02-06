# Arquitetura de Fluxo de Dados Otimizado (SQL Push-down)

Este documento descreve como o sistema processa consultas analíticas complexas com alta performance, minimizando o tráfego de dados e a carga cognitiva do LLM.

## Fluxo de Execução

1.  **Pergunta do Usuário**
    *   *Ex:* "Gere um ranking de vendas dos segmentos da loja 3116"

2.  **Interpretação (Agente LLM)**
    *   O Agente analisa a intenção e seleciona a ferramenta `gerar_grafico_universal_v2`.
    *   *Parâmetros:* `descricao="ranking vendas segmentos une 3116"`, `filtro_une="3116"`.

3.  **Backend (Tool Execution)**
    *   A ferramenta Python recebe a chamada.
    *   **Parsing:** Detecta palavras-chave na descrição ("segmento", "venda") para definir:
        *   `Dimensão` (Group By): `NOMESEGMENTO`
        *   `Métrica` (Aggregation): `SUM(VENDA_30DD)`
    
4.  **Processamento de Dados (DuckDB Engine)**
    *   O Backend constrói uma query SQL otimizada (Push-down):
        ```sql
        SELECT NOMESEGMENTO, SUM(VENDA_30DD) 
        FROM admmat.parquet 
        WHERE UNE = 3116 
        GROUP BY NOMESEGMENTO 
        ORDER BY 2 DESC 
        LIMIT 10
        ```
    *   O DuckDB executa a query diretamente sobre o arquivo Parquet (ou cache em memória).
    *   **Resultado:** Retorna apenas as 10 linhas agregadas (ex: Armarinho: 50k, Tecidos: 30k...).
    *   *Nota:* Milhões de linhas são processadas em milissegundos sem nunca serem carregadas para a memória do Python.

5.  **Geração de Artefatos**
    *   O Backend usa o resultado agregado para gerar o objeto gráfico (Plotly JSON).
    *   Cria um resumo textual estatístico.

6.  **Resposta Final (LLM)**
    *   O LLM recebe apenas o resumo e o JSON do gráfico.
    *   Escreve a resposta natural para o usuário: "Aqui está o ranking solicitado. O segmento de Armarinho lidera com..."
