# ADR-001: Fallback Local no Playground

## Status
Accepted

## Contexto
O Playground precisa continuar útil mesmo sem `GEMINI_API_KEY` ou quando a LLM remota estiver indisponível.

## Decisão
Adotar fallback local determinístico para intents críticas de BI, retornando respostas úteis e rastreáveis.

## Consequências
- Positivas: continuidade operacional, menor dependência externa, UX previsível.
- Negativas: menor capacidade linguística em casos complexos.
- Mitigação: modo híbrido com LLM opcional quando disponível.
