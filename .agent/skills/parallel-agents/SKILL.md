---
name: parallel-agents
description: Padrões de orquestração multi-agente. Use quando múltiplas tarefas independentes podem ser executadas com diferentes conhecimentos de domínio ou quando uma análise abrangente exige múltiplas perspectivas.
allowed-tools: Read, Glob, Grep
---

# Agentes Paralelos Nativos

> Orquestração através da ferramenta de Agente integrada do Antigravity.

---

## Visão Geral

Esta skill permite coordenar múltiplos agentes especializados através do sistema nativo de agentes. Ao contrário de scripts externos, esta abordagem mantém toda a orquestração sob o controle do Antigravity.

---

## Quando Usar Orquestração

✅ **Bom para:**
- Tarefas complexas que exigem múltiplos domínios de especialização
- Análise de código sob as perspectivas de segurança, performance e qualidade
- Revisões abrangentes (arquitetura + segurança + testes)
- Implementação de recursos que precisam de trabalho em backend + frontend + banco de dados

❌ **Não indicado para:**
- Tarefas simples de domínio único
- Correções rápidas ou pequenas mudanças
- Tarefas onde um único agente é suficiente

---

## Invocação de Agente Nativo

### Agente Único
```
Use o agente security-auditor para revisar a autenticação
```

### Cadeia Sequencial
```
Primeiro, use o explorer-agent para descobrir a estrutura do projeto.
Depois, use o backend-specialist para revisar os endpoints da API.
Finalmente, use o test-engineer para identificar lacunas nos testes.
```

### Com Passagem de Contexto
```
Use o frontend-specialist para analisar os componentes React.
Com base nessas descobertas, peça ao test-engineer para gerar testes de componente.
```

### Retomar Trabalho Anterior
```
Retome o agente [agentId] e continue com requisitos adicionais.
```

---

## Padrões de Orquestração

### Padrão 1: Análise Abrangente
```
Agentes: explorer-agent → [agentes de domínio] → síntese

1. explorer-agent: Mapear estrutura da base de código
2. security-auditor: Postura de segurança
3. backend-specialist: Qualidade da API
4. frontend-specialist: Padrões de UI/UX
5. test-engineer: Cobertura de testes
6. Sintetizar todas as descobertas
```

### Padrão 2: Revisão de Funcionalidade (Feature)
```
Agentes: agentes de domínio afetados → test-engineer

1. Identificar domínios afetados (backend? frontend? ambos?)
2. Invocar agentes de domínio relevantes
3. test-engineer verifica as mudanças
4. Sintetizar recomendações
```

### Padrão 3: Auditoria de Segurança
```
Agentes: security-auditor → penetration-tester → síntese

1. security-auditor: Revisão de configuração e código
2. penetration-tester: Testes ativos de vulnerabilidade
3. Sintetizar com remediação priorizada
```

---

## Agentes Disponíveis

| Agente | Especialidade | Frases de Gatilho |
|--------|---------------|-------------------|
| `orchestrator` | Coordenação | "abrangente", "multi-perspectiva" |
| `security-auditor` | Segurança | "segurança", "auth", "vulnerabilidades" |
| `penetration-tester` | Testes de Segurança | "pentest", "red team", "exploit" |
| `backend-specialist` | Backend | "API", "servidor", "Node.js", "Express" |
| `frontend-specialist` | Frontend | "React", "UI", "componentes", "Next.js" |
| `test-engineer` | Testes | "testes", "cobertura", "TDD" |
| `devops-engineer` | DevOps | "deploy", "CI/CD", "infraestrutura" |
| `database-architect` | Banco de Dados | "schema", "Prisma", "migrações" |
| `mobile-developer` | Mobile | "React Native", "Flutter", "mobile" |
| `api-designer` | Design de API | "REST", "GraphQL", "OpenAPI" |
| `debugger` | Depuração | "bug", "erro", "não funciona" |
| `explorer-agent` | Descoberta | "explorar", "mapear", "estrutura" |
| `documentation-writer` | Documentação | "escrever docs", "criar README" |
| `performance-optimizer`| Performance | "lento", "otimizar", "profiling" |
| `project-planner` | Planejamento | "planejar", "roadmap", "marcos" |
| `seo-specialist` | SEO | "SEO", "meta tags", "ranking de busca" |
| `game-developer` | Jogos | "jogo", "Unity", "Godot", "Phaser" |

---

## Protocolo de Síntese

Após a conclusão de todos os agentes, sintetize:

```markdown
## Síntese de Orquestração

### Resumo da Tarefa
[O que foi realizado]

### Contribuições dos Agentes
| Agente | Descoberta |
|--------|------------|
| security-auditor | Encontrou X |
| backend-specialist | Identificou Y |

### Recomendações Consolidadas
1. **Crítico**: [Problema do Agente A]
2. **Importante**: [Problema do Agente B]
3. **Desejável**: [Melhoria do Agente C]

### Itens de Ação
- [ ] Corrigir problema crítico de segurança
- [ ] Refatorar endpoint de API
- [ ] Adicionar testes ausentes
```

---

## Melhores Práticas

1. **Agentes disponíveis** - 17 agentes especializados podem ser orquestrados
2. **Ordem lógica** - Descoberta → Análise → Implementação → Testes
3. **Compartilhar contexto** - Passe as descobertas relevantes para os agentes subsequentes
4. **Síntese única** - Um relatório unificado, não saídas separadas
5. **Verificar mudanças** - Sempre inclua o `test-engineer` para modificações de código

---

## Benefícios Chave

- ✅ **Sessão única** - Todos os agentes compartilham o mesmo contexto
- ✅ **Controlado por IA** - O Antigravity orquestra de forma autônoma
- ✅ **Integração nativa** - Funciona com agentes integrados de Exploração e Plano
- ✅ **Suporte a retomada** - Pode continuar o trabalho de agentes anteriores
- ✅ **Passagem de contexto** - As descobertas fluem entre os agentes
