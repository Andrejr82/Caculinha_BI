# Análise de Riscos — Caculinha BI Agent Platform

**Data:** 2026-02-07  
**Versão:** 1.0.0  
**Autor:** Arquiteto de Sistema

---

## Matriz de Riscos

| ID | Risco | Probabilidade | Impacto | Prioridade |
|----|-------|---------------|---------|------------|
| R01 | Agente Monolítico | Alta | Crítico | 🔴 P0 |
| R02 | Ferramentas Gigantes | Alta | Alto | 🔴 P0 |
| R03 | Ausência Multi-tenancy | Alta | Crítico | 🔴 P0 |
| R04 | Arquivos Soltos na Raiz | Média | Médio | 🟡 P1 |
| R05 | Orquestração LangGraph Incompleta | Média | Alto | 🟡 P1 |
| R06 | Testes Fragmentados | Média | Médio | 🟡 P1 |
| R07 | Auth Mista (JWT + Supabase) | Baixa | Alto | 🟡 P1 |
| R08 | Arquivos de Debug na Raiz | Baixa | Baixo | 🟢 P2 |

---

## Detalhamento por Prioridade

### 🔴 P0 — Crítico (Bloqueiam Evolução)

#### R01: Agente Monolítico (God Object)

**Descrição:**  
O arquivo `caculinha_bi_agent.py` possui **69 KB** (~2000+ linhas) centralizando toda lógica de:
- Classificação de intenção
- Seleção de ferramentas
- Execução de queries
- Geração de narrativas
- Formatação de respostas

**Impacto:**
- ❌ Impossível testar unitariamente
- ❌ Alto risco de regressão em alterações
- ❌ Difícil de escalar horizontalmente
- ❌ Onboarding de devs demorado

**Mitigação:**  
Decompor em 8 agentes especializados:
- OrchestratorAgent
- SQLAgent
- InsightAgent
- ForecastAgent
- MetadataAgent
- TenantAgent
- SecurityAgent
- MonitoringAgent

---

#### R02: Ferramentas Gigantes

**Descrição:**  
Arquivos de ferramentas com múltiplas responsabilidades:

| Arquivo | Tamanho | Problema |
|---------|---------|----------|
| `une_tools.py` | 73 KB | Análise + Visualização + Export |
| `chart_tools.py` | 63 KB | Múltiplos tipos de gráfico |

**Impacto:**
- ❌ Violação do SRP (Single Responsibility Principle)
- ❌ Dificuldade de manutenção
- ❌ Tempo de carregamento elevado

**Mitigação:**  
Separar por domínio funcional:
- `tools/analysis/`
- `tools/visualization/`
- `tools/export/`

---

#### R03: Ausência de Multi-tenancy

**Descrição:**  
Sistema opera como single-tenant:
- Dados não têm isolamento por organização
- Queries não filtram por tenant_id
- JWT não carrega tenant context

**Impacto:**
- ❌ Impossível vender como SaaS
- ❌ Risco de vazamento de dados entre clientes
- ❌ Compliance falha (LGPD, GDPR)

**Mitigação:**  
Implementar:
1. `TenantAgent` para resolução de contexto
2. Middleware de tenant resolution no JWT
3. Filtros automáticos em todas as queries

---

### 🟡 P1 — Alto (Impactam Qualidade)

#### R04: Arquivos Soltos na Raiz do Backend

**Descrição:**  
104 arquivos na raiz de `backend/`:
- Scripts de diagnóstico (30+)
- Scripts de fix (10+)
- Arquivos de log (20+)
- Scripts de teste avulsos (40+)

**Impacto:**
- ❌ Difícil navegação
- ❌ Risco de executar scripts errados
- ❌ Poluição visual

**Mitigação:**  
Mover para:
- `scripts/diagnostics/`
- `scripts/fixes/`
- `logs/`
- `tests/`

---

#### R05: Orquestração LangGraph Incompleta

**Descrição:**  
Pasta `orchestration/` contém apenas 3 arquivos. Padrão ReAct iniciado mas não finalizado.

**Impacto:**
- ❌ Perda de capacidade de auto-correção
- ❌ Fallbacks não robustos

**Mitigação:**  
Implementar `OrchestratorAgent` completo com:
- Classification Node
- Tool Selection Node
- Execution Node
- Synthesis Node
- Error Recovery Node

---

#### R06: Testes Fragmentados

**Descrição:**  
93 arquivos em `tests/` + 40+ na raiz do backend. Cobertura desconhecida.

**Impacto:**
- ❌ Dificuldade de rodar suíte completa
- ❌ Duplicação de testes
- ❌ Gaps de cobertura desconhecidos

**Mitigação:**  
1. Consolidar todos os testes em `tests/`
2. Rodar coverage report
3. Adicionar CI/CD com pytest

---

#### R07: Autenticação Mista

**Descrição:**  
Sistema usa JWT local + Supabase Auth simultaneamente. Múltiplos scripts de fix para admin.

**Impacto:**
- ❌ Complexidade desnecessária
- ❌ Bugs de edge case
- ❌ Manutenção duplicada

**Mitigação:**  
Padronizar em um único provider:
- **Recomendação:** Supabase (mais features OOTB)

---

### 🟢 P2 — Baixo (Melhorias)

#### R08: Logs e Debug na Raiz

**Descrição:**  
Arquivos de log e saída de debug espalhados:
- `*.log` (20+ arquivos)
- `*_output.txt` (15+ arquivos)

**Impacto:**
- ❌ Poluição do repositório
- ❌ Commits acidentais de dados sensíveis

**Mitigação:**  
1. Mover para `logs/`
2. Adicionar ao `.gitignore`

---

## Plano de Mitigação Prioritizado

| Fase | Ação | Risco Mitigado |
|------|------|----------------|
| **FASE 3** | Decompor agente em 8 especializados | R01 |
| **FASE 3** | Separar ferramentas por domínio | R02 |
| **FASE 6** | Implementar multi-tenancy | R03 |
| **FASE 2** | Reorganizar estrutura de pastas | R04, R08 |
| **FASE 4** | Completar orquestração | R05 |
| **FASE 5** | Consolidar e expandir testes | R06 |
| **FASE 6** | Padronizar auth | R07 |

---

## Conclusão

Os 3 riscos críticos (P0) são **bloqueadores para evolução enterprise**:
1. Agente monolítico impede manutenibilidade
2. Ferramentas gigantes violam SRP
3. Ausência de multi-tenancy impede modelo SaaS

A decomposição proposta nas próximas fases endereçará todos os riscos identificados.
