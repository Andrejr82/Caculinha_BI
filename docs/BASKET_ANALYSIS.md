# Basket Analysis

## O que a feature faz

A feature adiciona market basket analysis com servico proprio no backend, endpoint dedicado e integracao no chat para perguntas sobre:

- cesta de compras
- produtos comprados juntos
- afinidade entre produtos
- cross-sell
- basket analysis

## Modos de analise

- `real_transactional`: transaction key forte e validada, com cobertura e multi-item suficientes.
- `subset_transactional_supported`: subset controlado com chave parcial/hipotetica; os insights permanecem inferencias analiticas.
- `unsupported`: modo padrao quando a base nao comprova granularidade transacional suficiente.

## Regra conservadora atual

- A base principal `backend/data/parquet/admmat.parquet` segue tratada como snapshot analitico.
- A coluna `NOTA` pode existir como candidato, mas nao e promovida automaticamente para basket real.
- Se a validacao nao atingir os thresholds minimos, a resposta retorna `unsupported`.

## Endpoint

`POST /api/v1/analytics/basket-analysis`

Alias:

`POST /api/v2/analytics/basket-analysis`

## Request

```json
{
  "start_date": null,
  "end_date": null,
  "une": null,
  "segment": null,
  "category": null,
  "target_product": null,
  "min_support": 0.01,
  "min_confidence": 0.2,
  "min_lift": 1.0,
  "max_rules": 20
}
```

## Response

```json
{
  "status": "success",
  "analysis_mode": "real_transactional",
  "data_source": "backend/data/parquet/admmat.parquet",
  "transactions_analyzed": 120,
  "unique_items": 3,
  "parameters": {},
  "top_itemsets": [
    {
      "items": ["caderno", "caneta"],
      "support": 1.0,
      "size": 2
    }
  ],
  "top_rules": [
    {
      "antecedent": ["caderno"],
      "consequent": ["caneta"],
      "support": 1.0,
      "confidence": 1.0,
      "lift": 1.0
    }
  ],
  "business_summary": [],
  "limitations": [],
  "diagnostics": {}
}
```

## Como validar

### Testes automatizados

```bash
python -m pytest backend/tests/unit/test_basket_analysis_service.py backend/tests/unit/test_chat_service_dataset_basket.py backend/tests/integration/test_basket_analysis_endpoint.py -q
python -m pytest backend/tests/test_chatbi_tool_routing_integration.py backend/tests/unit/test_basket_tools.py -q
```

### Validacao manual do endpoint

1. Suba o backend.
2. Envie um `POST` autenticado para `/api/v1/analytics/basket-analysis`.
3. Verifique:
   - `status`
   - `analysis_mode`
   - `limitations`
   - `diagnostics.detected_columns`

### Validacao manual no chat

Perguntas exemplo:

- `quais produtos comprados juntos na cesta de compras?`
- `quais oportunidades de cross-sell existem no segmento papelaria?`
- `qual a afinidade entre produtos na UNE 135?`

Resultado esperado:

- sem anexo: usa o novo pipeline analitico sobre a base local
- com anexo/payload manual: continua usando o pipeline deterministico de basket ja existente

## Interpretacao das metricas

- `support`: frequencia do itemset no conjunto de transacoes analisado
- `confidence`: probabilidade condicional da consequencia dado o antecedente
- `lift`: ganho relativo da regra vs ocorrencia independente

## Limitacoes atuais

- a base principal nao e promovida automaticamente para basket real
- `NOTA` e tratada como hipotese controlada
- `unsupported` e a resposta correta quando a validacao nao comprova suporte real
