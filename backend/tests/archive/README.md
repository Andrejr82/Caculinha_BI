# Testes Arquivados (Arquitetura V2)

## ⚠️ ATENÇÃO: NÃO EXECUTAR ESSES TESTES

Este diretório contém testes da arquitetura antiga (V2) baseada em:
- LangGraph
- ChatServiceV2
- Tool selection via LLM

## Status

**Arquitetura V2:** ❌ DEPRECIADA (removida em 2026-01-16)
**Arquitetura V3:** ✅ ATIVA (Metrics-First)

## Motivo do Arquivamento

Esses testes foram mantidos apenas para **referência histórica** e **comparação**.

A arquitetura V2 foi completamente substituída pela V3 (Metrics-First) que:
- ✅ Elimina loops infinitos
- ✅ Reduz latência em 60-70%
- ✅ Reduz consumo de tokens em 75-80%
- ✅ Elimina 90% das alucinações
- ✅ Respostas consistentes e determinísticas

## Testes Ativos

Para executar os testes da arquitetura V3, use:

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Todos os testes ativos
pytest tests/ --ignore=tests/archive/
```

## Conteúdo

Este diretório contém 45 arquivos de teste incluindo:
- `test_gemini_full.py` - Testes do ChatServiceV2
- `test_local_graph.py` - Testes do LangGraph
- `test_supabase_auth.py` - Testes de autenticação
- E outros testes legados

## Quando Remover

Esses arquivos podem ser removidos permanentemente após:
- ✅ 6 meses de V3 em produção
- ✅ Zero necessidade de referência
- ✅ Aprovação da equipe

---

**Data de Arquivamento:** 2026-01-16
**Arquitetura Atual:** V3 (Metrics-First)
