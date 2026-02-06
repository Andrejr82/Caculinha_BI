# Legacy Tests Archive

⚠️ **ATENÇÃO: Testes Obsoletos**

Estes testes foram movidos da raiz do backend e **NÃO devem ser usados**.

Mantidos apenas para referência histórica.

---

## Testes Ativos

Para testes atuais e mantidos, veja:

- **`/tests/`** - Testes principais
- **`/tests/unit/`** - Testes unitários
- **`/tests/integration/`** - Testes de integração
- **`/tests/manual/`** - Testes manuais

---

## Executar Testes Ativos

```bash
# Todos os testes
pytest tests/

# Apenas unit tests
pytest tests/unit/

# Apenas integration tests
pytest tests/integration/

# Com cobertura
pytest --cov=app tests/
```

---

## Data de Arquivamento

**2026-01-27** - Movidos da raiz do backend durante limpeza de código.
