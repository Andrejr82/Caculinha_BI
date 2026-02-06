# 📚 Índice de Documentação - BI Solution

**Última atualização**: 31 de Dezembro de 2025

Esta pasta contém toda a documentação organizada do projeto BI Solution.

---

## 📁 Estrutura de Documentação

### 🚀 `/migration/` - Migração DuckDB

Documentação completa da migração de Polars/Pandas/Dask para DuckDB (Dezembro 2025).

**Para começar, leia primeiro**:
- ✅ **`RESUMO_EXECUTIVO_MIGRACAO.md`** - Resumo executivo (não-técnico)
- 📖 **`QUICK_START_DUCKDB.md`** - Guia rápido com exemplos práticos

**Documentação técnica completa**:
- 📊 `RELATORIO_FINAL_MIGRACAO_DUCKDB.md` - Relatório técnico detalhado
- 🔍 `AUDITORIA_FERRAMENTAS_DADOS.md` - Auditoria completa (10K palavras)
- 🗺️ `PLANO_MIGRACAO_DUCKDB.md` - Plano de 6 fases
- ⏭️ `PROXIMOS_PASSOS_MIGRACAO.md` - Deploy e próximos passos
- 💡 `RESUMO_RECOMENDACOES_DUCKDB.md` - Resumo de recomendações

**Relatórios adicionais**:
- `RELATORIO_MIGRACAO_DUCKDB_2025-12-31.md`
- `RELATORIO_TESTES_DOCKER_2025-12-31.md`
- `RELATORIO_MELHORES_PRATICAS.md`

**Resultados da migração**:
- ⚡ **3.3x mais rápido** - Validado com dados reais
- 💾 **76% menos memória** - De 1.7 GB para 400 MB
- 🎯 **75% menos dependências** - 4 engines → 1
- ✅ **Zero breaking changes** - Totalmente compatível

---

### 📖 `/guides/` - Guias Operacionais

Guias práticos para operação e troubleshooting do sistema.

- `CORRECAO_HEALTHCHECK.md` - Como corrigir problemas de healthcheck Docker
- `INSTRUCOES_RAPIDAS.md` - Instruções rápidas de setup
- `TROUBLESHOOTING_WSL2.md` - Solução de problemas WSL2/Docker

---

### 🗄️ `/archive/` - Documentação Histórica

Relatórios e documentos antigos mantidos para referência histórica.

**Relatórios arquivados (Dezembro 2025)**:
- Documentação pré-migração DuckDB
- Análises de performance antigas
- Guias de negócio UNE (movidos de raiz)

---

### 🔍 `/queries/` - Consultas SQL de Exemplo

Exemplos de queries SQL utilizadas no sistema.

---

### 🔧 `/troubleshooting/` - Resolução de Problemas

Guias específicos de troubleshooting e debugging.

---

## 🎯 Acesso Rápido

### Estou começando no projeto
1. Leia `/PRD.md` (raiz do projeto)
2. Leia `/migration/RESUMO_EXECUTIVO_MIGRACAO.md`
3. Configure ambiente: `/guides/INSTRUCOES_RAPIDAS.md`

### Quero usar DuckDB
1. **Quick Start**: `/migration/QUICK_START_DUCKDB.md`
2. **Próximos passos**: `/migration/PROXIMOS_PASSOS_MIGRACAO.md`

### Tenho problemas com Docker/WSL
1. `/guides/TROUBLESHOOTING_WSL2.md`
2. `/guides/CORRECAO_HEALTHCHECK.md`

### Quero entender a migração
1. **Resumo Executivo**: `/migration/RESUMO_EXECUTIVO_MIGRACAO.md` (não-técnico)
2. **Relatório Técnico**: `/migration/RELATORIO_FINAL_MIGRACAO_DUCKDB.md`
3. **Auditoria Completa**: `/migration/AUDITORIA_FERRAMENTAS_DADOS.md`

---

## 📂 Outros Diretórios do Projeto

- `/backend/` - Código do backend (Python/FastAPI)
- `/frontend-solid/` - Código do frontend (SolidJS)
- `/scripts/` - Scripts utilitários
- `/config/` - Configurações (Docker, Prometheus, etc.)
- `/data/` - Dados e cache (não versionado)
- `/tests/` - Testes automatizados

---

## 📝 Convenções de Nomenclatura

- **`RELATORIO_*.md`** - Relatórios técnicos detalhados
- **`RESUMO_*.md`** - Resumos executivos/não-técnicos
- **`QUICK_START_*.md`** - Guias rápidos com exemplos
- **`PLANO_*.md`** - Planejamento e roadmaps
- **`TROUBLESHOOTING_*.md`** - Guias de resolução de problemas

---

**Responsável pela organização**: Claude Code (Claude Sonnet 4.5)
**Data da reorganização**: 31 de Dezembro de 2025
