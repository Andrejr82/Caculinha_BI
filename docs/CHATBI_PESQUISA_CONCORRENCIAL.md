# ChatBI - Pesquisa Concorrencial (RJ/MG/ES)

## Objetivo
Adicionar no ChatBI atual a capacidade de pesquisar referências de preço externas para apoiar Compras.

## Como funciona
- Ferramenta: `pesquisar_precos_concorrentes`
- Roteamento automático por intenção no próprio agente quando a pergunta mencionar:
  - concorrente, cotação, pesquisa de preço, comparar preço
  - nomes como Americanas, Amigão, TID'S, Bellart, Tubarão, Kalunga, Casa&Video
- Escopo geográfico controlado por configuração: `RJ,MG,ES`.

## Método de consulta externa (fallback)
1. `playwright` (navegador real para páginas dinâmicas com JavaScript)
2. `crawler` (parser estruturado HTML com BeautifulSoup + fallback regex)
3. `websearch` (busca pública por concorrente com extração de preço por página, sem API)
2. `mercadolivre` (API pública)
3. `serpapi` (Google Shopping, quando `SERPAPI_API_KEY` estiver configurada)
4. `bellart` (conector direto por domínio)
5. `manual` (arquivo local `backend/data/reference/competitive_prices.json`)

Ordem configurável em `COMPETITIVE_PROVIDER_PRIORITY`.

## Variáveis de ambiente
No `backend/.env`:

- `COMPETITIVE_INTEL_ENABLED=true`
- `COMPETITIVE_PROVIDER_PRIORITY=playwright,crawler,websearch,social,mercadolivre,serpapi,bellart,manual`
- `COMPETITIVE_ALLOWED_STATES=RJ,MG,ES`
- `COMPETITIVE_HTTP_TIMEOUT_SEC=10`
- `COMPETITIVE_TOTAL_TIMEOUT_SEC=25`
- `COMPETITIVE_MAX_RESULTS=20`
- `COMPETITIVE_MANUAL_FILE=data/reference/competitive_prices.json`
- `COMPETITIVE_DOMAIN_WHITELIST=bellartdecor.com.br,kalunga.com.br,americanas.com.br,casaevideo.com.br,lebiscuit.com.br,mercadolivre.com.br,amazon.com.br,shopee.com.br`
- `SERPAPI_API_KEY=`
- `SERPAPI_ENGINE=google_shopping`

## Quality Gate (obrigatório)
- Validação de evidência por item:
  - produto e preço válidos obrigatórios
  - para fonte externa: URL e domínio permitido (whitelist) obrigatórios
  - para base manual: URL opcional
- Itens inválidos são descartados automaticamente antes da resposta.

## Upload de CSV (Compras)
- Endpoint: `POST /api/v1/competitive/import-csv` (admin)
- Template: `GET /api/v1/competitive/csv-template`
- Finalidade: subir cotações internas para uso imediato no ChatBI.

## Resposta padrão ao usuário
A saída é formatada em 4 blocos:
1. Resumo executivo
2. Tabela operacional
3. Ação recomendada
4. Recorte e evidência

## Observações
- Sem chave de API externa e sem base manual preenchida, o sistema retorna mensagem orientativa (sem inventar dado).
- Mesmo sem API e sem CSV, os providers `playwright/crawler/websearch/social` tentam consulta pública por concorrente.
- A resposta retorna `fontes_consultadas` com URL/domínio/fonte/concorrente para trilha de evidência.
- A implementação está no ChatBI existente, sem criar nova rota de produto.
