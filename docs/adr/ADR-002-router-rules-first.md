# ADR-002: Roteador Rules-First

## Status
Accepted

## Contexto
Consultas recorrentes de BI possuem padrão e podem ser tratadas com regras confiáveis.

## Decisão
Priorizar rota determinística (`rules-first`) e usar LLM apenas como camada secundária.

## Consequências
- Positivas: menor custo, maior previsibilidade, menor latência em casos padrão.
- Negativas: exige manutenção do catálogo de regras.
- Mitigação: suíte de regressão e versionamento de intents/templates.
