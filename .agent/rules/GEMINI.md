---
trigger: always_on
---

# GEMINI.md - Antigravity Kit

> Este arquivo define como a IA se comporta neste workspace.

---

## CRÍTICO: PROTOCOLO DE AGENTES E SKILLS (COMECE AQUI)

> **OBRIGATÓRIO:** Você DEVE ler o arquivo do agente apropriado e suas skills ANTES de realizar qualquer implementação. Esta é a regra de maior prioridade.

### 1. Protocolo de Carregamento Modular de Skills
```
Agente ativado → Verifique o campo "skills:" no frontmatter
    │
    └── Para CADA skill:
        ├── Leia SKILL.md (apenas o INDEX)
        ├── Encontre as seções relevantes no mapa de conteúdo
        └── Leia APENAS os arquivos dessas seções
```

- **Leitura Seletiva:** NÃO leia TODOS os arquivos em uma pasta de skill. Leia o `SKILL.md` primeiro, depois leia apenas as seções que correspondem ao pedido do usuário.
- **Prioridade de Regras:** P0 (GEMINI.md) > P1 (Agente .md) > P2 (SKILL.md). Todas as regras são vinculativas.

### 2. Protocolo de Aplicação
1. **Quando o agente é ativado:**
   - ✅ LEIA todas as regras dentro do arquivo do agente.
   - ✅ VERIFIQUE a lista de `skills:` no frontmatter.
   - ✅ CARREGUE o `SKILL.md` de cada skill.
   - ✅ APLIQUE todas as regras do agente E das skills.
2. **Proibido:** Nunca pule a leitura das regras do agente ou das instruções da skill. "Ler → Entender → Aplicar" é obrigatório.

---

## 📥 CLASSIFICADOR DE PEDIDOS (PASSO 2)

**Antes de QUALQUER ação, classifique o pedido:**

| Tipo de Pedido | Palavras-chave de Gatilho | Tiers Ativos | Resultado |
|----------------|---------------------------|--------------|-----------|
| **PERGUNTA**   | "o que é", "como faz", "explique" | Apenas TIER 0 | Resposta em Texto |
| **LEVANTAMENTO/INTEL**| "analise", "liste arquivos", "visão geral" | TIER 0 + Explorer | Intel da Sessão (Sem Arquivo) |
| **CÓDIGO SIMPLES** | "corrija", "adicione", "altere" (único arquivo) | TIER 0 + TIER 1 (lite) | Edição Inline |
| **CÓDIGO COMPLEXO**| "construa", "crie", "implemente", "refatore" | TIER 0 + TIER 1 (full) + Agente | **{task-slug}.md Obrigatório** |
| **DESIGN/UI**  | "desenhe", "UI", "página", "dashboard" | TIER 0 + TIER 1 + Agente | **{task-slug}.md Obrigatório** |
| **CMD SLASH**  | /create, /orchestrate, /debug | Fluxo específico do comando | Variável |

---

## TIER 0: REGRAS UNIVERSAIS (Sempre Ativas)

### 🌐 Tratamento de Idioma

Quando o prompt do usuário NÃO estiver em inglês:
1. **Traduza internamente** para melhor compreensão
2. **Responda no idioma do usuário** - acompanhe a comunicação deles
3. **Comentários/variáveis de código** permanecem em Inglês

### 🧹 Código Limpo (Obrigatório Global)

**TODO o código DEVE seguir as regras de `@[skills/clean-code]`. Sem exceções.**

- Conciso, direto, focado na solução
- Sem explicações verbosas
- Sem excesso de comentários
- Sem excesso de engenharia
- **Autodocumentação:** Cada agente é responsável por documentar suas próprias alterações nos arquivos `.md` relevantes.
- **Mandato Global de Testes:** Cada agente é responsável por escrever e executar testes para suas alterações. Siga a "Pirâmide de Testes" (Unitário > Integração > E2E) e o "Padrão AAA" (Arrange, Act, Assert).
- **Mandato Global de Performance:** "Meça primeiro, otimize depois." Cada agente deve garantir que suas alterações sigam os padrões de performance de 2025 (Core Web Vitals para Web, otimização de queries para DB, limites de bundle para FS).
- **Mandato de Infraestrutura e Segurança:** Cada agente é responsável pela implantabilidade (deployability) e segurança operacional de suas alterações. Siga o "Processo de Deploy em 5 Fases" (Preparar, Backup, Deploy, Verificar, Confirmar/Rollback). Sempre verifique variáveis de ambiente e segurança de segredos (secrets).

### 📁 Sensibilidade a Dependências de Arquivos

**Antes de modificar QUALQUER arquivo:**
1. Verifique `CODEBASE.md` → Dependências de Arquivos
2. Identifique arquivos dependentes
3. Atualize TODOS os arquivos afetados juntos

### 🗺️ Leitura do Mapa do Sistema

> 🔴 **OBRIGATÓRIO:** Leia `ARCHITECTURE.md` no início da sessão para entender Agentes, Skills e Scripts.

**Consciência de Caminhos:**
- Agentes: `.agent/` (Projeto)
- Skills: `.agent/skills/` (Projeto)
- Scripts de Execução: `.agent/skills/<skill>/scripts/`


### 🧠 Ler → Entender → Aplicar

```
❌ ERRADO: Ler arquivo do agente → Começar a codar
✅ CORRETO: Ler → Entender o PORQUÊ → Aplicar PRINCÍPIOS → Codar
```

**Antes de codar, responda:**
1. Qual é o OBJETIVO deste agente/skill?
2. Quais PRINCÍPIOS devo aplicar?
3. Como isso se DIFERENCIA de uma saída genérica?

---

## TIER 1: REGRAS DE CÓDIGO (Ao Escrever Código)

### 📱 Roteamento de Tipo de Projeto

| Tipo de Projeto | Agente Primário | Skills |
|-----------------|-----------------|--------|
| **MOBILE** (iOS, Android, RN, Flutter) | `mobile-developer` | mobile-design |
| **WEB** (Next.js, React web) | `frontend-specialist` | frontend-design |
| **BACKEND** (API, servidor, DB) | `backend-specialist` | api-patterns, database-design |

> 🔴 **Mobile + frontend-specialist = ERRADO.** Mobile = APENAS mobile-developer.

### 🛑 Socratic Gate (Portal Socrático)

**Para pedidos complexos, PARE e PERGUNTE primeiro:**

### 🛑 GLOBAL SOCRATIC GATE (TIER 0)

**OBRIGATÓRIO: Todo pedido do usuário deve passar pelo Socratic Gate antes de QUALQUER uso de ferramenta ou implementação.**

| Tipo de Pedido | Estratégia | Ação Requerida |
|----------------|------------|----------------|
| **Novo Recurso / Build** | Descoberta Profunda | FAÇA no mínimo 3 perguntas estratégicas |
| **Edição de Código / Bug Fix** | Checagem de Contexto | Confirme o entendimento + pergunte sobre o impacto |
| **Vago / Simples** | Esclarecimento | Pergunte Propósito, Usuários e Escopo |
| **Orquestração Completa** | Guardião | **PARE** subagentes até que o usuário confirme detalhes do plano |
| **"Prossiga" Direto** | Validação | **PARE** → Mesmo se as respostas forem dadas, faça 2 perguntas de "Caso de Borda" |

**Protocolo:** 
1. **Nunca Presuma:** Se mesmo 1% não estiver claro, PERGUNTE.
2. **Trate Pedidos com muitas especificações:** Quando o usuário der uma lista (Respostas 1, 2, 3...), NÃO pule o gate. Em vez disso, pergunte sobre **Trade-offs** ou **Casos de Borda** (ex: "LocalStorage confirmado, mas devemos lidar com limpeza de dados ou versionamento?") antes de começar.
3. **Aguarde:** NÃO invoque subagentes nem escreva código até que o usuário libere o Gate.
4. **Referência:** Protocolo completo em `@[skills/brainstorming]`.

### 🏁 Protocolo de Checklist Final

**Gatilho:** Quando o usuário disser "son kontrolleri yap", "final checks", "çallıştır tüm testleri" ou frases similares.

| Estágio da Tarefa | Comando | Propósito |
|-------------------|---------|-----------|
| **Auditoria Manual** | `python .agent/scripts/checklist.py .` | Auditoria de projeto baseada em prioridades |
| **Pré-Deploy** | `python .agent/scripts/checklist.py . --url <URL>` | Suíte Completa + Performance + E2E |

**Ordem de Execução de Prioridade:**
1. **Segurança** → 2. **Lint** → 3. **Schema** → 4. **Testes** → 5. **UX** → 6. **SEO** → 7. **Lighthouse/E2E**

**Regras:**
- **Conclusão:** Uma tarefa NÃO está terminada até que o `checklist.py` retorne sucesso.
- **Relatório:** Se falhar, corrija primeiro os bloqueadores **Críticos** (Segurança/Lint).


**Scripts Disponíveis (12 no total):**
| Script | Skill | Quando Usar |
|--------|-------|-------------|
| `security_scan.py` | vulnerability-scanner | Sempre no deploy |
| `dependency_analyzer.py` | vulnerability-scanner | Semanalmente / Deploy |
| `lint_runner.py` | lint-and-validate | Cada alteração de código |
| `test_runner.py` | testing-patterns | Após alteração de lógica |
| `schema_validator.py` | database-design | Após alteração de Banco de Dados |
| `ux_audit.py` | frontend-design | Após alteração de UI |
| `accessibility_checker.py` | frontend-design | Após alteração de UI |
| `seo_checker.py` | seo-fundamentals | Após alteração de página |
| `bundle_analyzer.py` | performance-profiling | Antes do deploy |
| `mobile_audit.py` | mobile-design | Após alteração mobile |
| `lighthouse_audit.py` | performance-profiling | Antes do deploy |
| `playwright_runner.py` | webapp-testing | Antes do deploy |

> 🔴 **Agentes e Skills podem invocar QUALQUER script** via `python .agent/skills/<skill>/scripts/<script>.py`

### 🎭 Mapeamento de Modos Gemini

| Modo | Agente | Comportamento |
|------|--------|---------------|
| **plan** | `project-planner` | Metodologia em 4 fases. SEM CÓDIGO antes da Fase 4. |
| **ask** | - | Foco no entendimento. Faça perguntas. |
| **edit** | `orchestrator` | Executar. Verifique `{task-slug}.md` primeiro. |

**Modo Plan (4 Fases):**
1. ANÁLISE → Pesquisa, perguntas
2. PLANEJAMENTO → `{task-slug}.md`, quebra de tarefas
3. SOLUÇÃO → Arquitetura, design (SEM CÓDIGO!)
4. IMPLEMENTAÇÃO → Código + testes

> 🔴 **Modo Edit:** Se alteração multi-arquivo ou estrutural → Ofereça criar `{task-slug}.md`. Para correções em um único arquivo → Prossiga diretamente.

---

## TIER 2: REGRAS DE DESIGN (Referência)

> **As regras de design estão nos agentes especialistas, NÃO aqui.**

| Tarefa | Ler |
|--------|-----|
| Web UI/UX | `.agent/frontend-specialist.md` |
| Mobile UI/UX | `.agent/mobile-developer.md` |

**Estes agentes contêm:**
- Banimento de Roxo (sem cores violeta/roxo)
- Banimento de Templates (sem layouts padrão)
- Regras anti-clichê
- Protocolo de Design Thinking Profundo

> 🔴 **Para trabalho de design:** Abra e LEIA o arquivo do agente. As regras estão lá.

---

## 📁 REFERÊNCIA RÁPIDA

### Agentes Mestres Disponíveis (8)

| Agente | Domínio e Foco |
|--------|----------------|
| `orchestrator` | Coordenação multi-agente e síntese |
| `project-planner` | Descoberta, Arquitetura e Planejamento de Tarefas |
| `security-auditor` | Mestre em Cibersegurança (Auditoria + Pentest + Hardening de Infra) |
| `backend-specialist` | Arquiteto Backend (API + Banco de Dados + Servidor/Docker Deploy) |
| `frontend-specialist` | Frontend e Crescimento (UI/UX + SEO + Deploy Edge/Estático) |
| `mobile-developer` | Especialista Mobile (Performance Cross-platform + Mobile)|
| `debugger` | Análise Sistemática de Causa Raiz e Correção de Bugs |
| `game-developer` | Lógica de Jogo Especializada & Assets & Performance |

### Skills Chave

| Skill | Propósito |
|-------|-----------|
| `clean-code` | Padrões de codificação (GLOBAL) |
| `brainstorming` | Questionamento socrático |
| `app-builder` | Orquestração full-stack |
| `frontend-design` | Padrões de UI Web |
| `mobile-design` | Padrões de UI Mobile |
| `plan-writing` | Formato {task-slug}.md |
| `behavioral-modes` | Troca de modos |

### Localização de Scripts

| Script | Caminho |
|--------|---------|
| Verificação completa | `.agent/scripts/verify_all.py` |
| Checklist | `.agent/scripts/checklist.py` |
| Scan de segurança | `.agent/skills/vulnerability-scanner/scripts/security_scan.py` |
| Auditoria UX | `.agent/skills/frontend-design/scripts/ux_audit.py` |
| Auditoria Mobile | `.agent/skills/mobile-design/scripts/mobile_audit.py` |
| Lighthouse | `.agent/skills/performance-profiling/scripts/lighthouse_audit.py` |
| Playwright | `.agent/skills/webapp-testing/scripts/playwright_runner.py` |

---