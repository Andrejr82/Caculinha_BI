---
name: clean-code
description: Padrões de código pragmáticos - conciso, direto, sem excesso de engenharia, sem comentários desnecessários
allowed-tools: Read, Write, Edit
version: 2.0
priority: CRITICAL
---

# Clean Code - Padrões de Código de IA Pragmáticos

> **HABILIDADE CRÍTICA** - Seja **conciso, direto e focado na solução**.

---

## Princípios Core

| Princípio | Regra |
|-----------|-------|
| **SRP** | Responsabilidade Única - cada função/classe faz UMA coisa |
| **DRY** | Don't Repeat Yourself - extraia duplicatas, reutilize |
| **KISS** | Keep It Simple - solução mais simples que funcione |
| **YAGNI** | You Aren't Gonna Need It - não construa features não utilizadas |
| **Boy Scout** | Deixe o código mais limpo do que o encontrou |

---

## Regras de Nomenclatura

| Elemento | Convenção |
|----------|-----------|
| **Variáveis** | Revele a intenção: `contagemUsuarios` não `n` |
| **Funções** | Verbo + substantivo: `obterUsuarioPorId()` não `usuario()` |
| **Booleanos** | Forma de pergunta: `estaAtivo`, `temPermissao`, `podeEditar` |
| **Constantes** | SCREAMING_SNAKE: `CONTAGEM_MAXIMA_RETRY` |

> **Regra:** Se você precisa de um comentário para explicar um nome, renomeie-o.

---

## Regras de Função

| Regra | Descrição |
|-------|-----------|
| **Pequena** | Máx 20 linhas, idealmente 5-10 |
| **Uma Coisa** | Faz uma coisa e faz bem feita |
| **Um Nível** | Um nível de abstração por função |
| **Poucos Args** | Máx 3 argumentos, prefira 0-2 |
| **Sem Efeitos Colaterais** | Não mude as entradas de forma inesperada |

---

## Estrutura do Código

| Padrão | Aplicação |
|--------|-----------|
| **Cláusulas de Guarda** | Retornos antecipados para casos de borda |
| **Plano > Aninhado** | Evite aninhamento profundo (máx 2 níveis) |
| **Composição** | Funções pequenas compostas juntas |
| **Colocação** | Mantenha código relacionado próximo |

---

## Estilo de Codificação de IA

| Situação | Ação |
|-----------|------|
| Usuário pede feature | Escreva diretamente |
| Usuário relata bug | Corrija, não explique |
| Requisito não está claro | Pergunte, não assuma |

---

## Anti-Padrões (NÃO FAÇA)

| ❌ Padrão | ✅ Correção |
|-----------|-------------|
| Comentar cada linha | Delete comentários óbvios |
| Helper para uma linha | Use o código inline |
| Factory para 2 objetos | Instanciação direta |
| utils.ts com 1 função | Coloque o código onde é usado |
| "Primeiro vamos importar..." | Apenas escreva o código |
| Aninhamento profundo | Cláusulas de guarda |
| Números mágicos | Constantes nomeadas |
| Funções "Deus" | Divida por responsabilidade |

---

## 🔴 Antes de Editar QUALQUER Arquivo (PENSE PRIMEIRO!)

**Antes de mudar um arquivo, pergunte-se:**

| Pergunta | Por que |
|----------|---------|
| **O que importa este arquivo?** | Eles podem quebrar |
| **O que este arquivo importa?** | Mudanças de interface |
| **Que testes cobrem isso?** | Testes podem falhar |
| **É um componente compartilhado?** | Múltiplos lugares afetados |

**Checagem Rápida:**
```
Arquivo para editar: UserService.ts
└── Quem importa isso? → UserController.ts, AuthController.ts
└── Eles também precisam de mudanças? → Cheque as assinaturas das funções
```

> 🔴 **Regra:** Edite o arquivo + todos os arquivos dependentes na MESMA tarefa.
> 🔴 **Nunca deixe imports quebrados ou atualizações faltando.**

---

## Resumo

| Faça | Não Faça |
|------|----------|
| Escreva código diretamente | Escreva tutoriais |
| Deixe o código se autodocumentar | Adicione comentários óbvios |
| Corrija bugs imediatamente | Explique a correção primeiro |
| Use inline para coisas pequenas | Crie arquivos desnecessários |
| Nomeie as coisas claramente | Use abreviações |
| Mantenha funções pequenas | Escreva funções de 100+ linhas |

> **Lembre-se: O usuário quer código funcionando, não uma aula de programação.**

---

## 🔴 Auto-Checagem Antes de Concluir (OBRIGATÓRIO)

**Antes de dizer "tarefa concluída", verifique:**

| Checagem | Pergunta |
|----------|----------|
| ✅ **Objetivo atingido?** | Eu fiz exatamente o que o usuário pediu? |
| ✅ **Arquivos editados?** | Eu modifiquei todos os arquivos necessários? |
| ✅ **Código funciona?** | Eu testei/verifiquei a mudança? |
| ✅ **Sem erros?** | Lint e TypeScript passam? |
| ✅ **Nada esquecido?** | Algum caso de borda esquecido? |

> 🔴 **Regra:** Se QUALQUER checagem falhar, corrija antes de concluir.

---

## Scripts de Verificação (OBRIGATÓRIO)

> 🔴 **CRÍTICO:** Cada agente executa APENAS os scripts de sua própria skill após concluir o trabalho.

### Mapeamento Agente → Script

| Agente | Script | Comando |
|--------|--------|---------|
| **frontend-specialist** | Auditoria UX | `python .agent/skills/frontend-design/scripts/ux_audit.py .` |
| **frontend-specialist** | Checagem A11y | `python .agent/skills/frontend-design/scripts/accessibility_checker.py .` |
| **backend-specialist** | Validador de API | `python .agent/skills/api-patterns/scripts/api_validator.py .` |
| **mobile-developer** | Auditoria Mobile | `python .agent/skills/mobile-design/scripts/mobile_audit.py .` |
| **database-architect** | Validar Schema | `python .agent/skills/database-design/scripts/schema_validator.py .` |
| **security-auditor** | Scan de Segurança | `python .agent/skills/vulnerability-scanner/scripts/security_scan.py .` |
| **seo-specialist** | Checagem SEO | `python .agent/skills/seo-fundamentals/scripts/seo_checker.py .` |
| **seo-specialist** | Checagem GEO | `python .agent/skills/geo-fundamentals/scripts/geo_checker.py .` |
| **performance-optimizer** | Lighthouse | `python .agent/skills/performance-profiling/scripts/lighthouse_audit.py <url>` |
| **test-engineer** | Executor de Testes | `python .agent/skills/testing-patterns/scripts/test_runner.py .` |
| **test-engineer** | Playwright | `python .agent/skills/webapp-testing/scripts/playwright_runner.py <url>` |
| **Qualquer agente** | Checagem de Lint | `python .agent/skills/lint-and-validate/scripts/lint_runner.py .` |
| **Qualquer agente** | Cobertura de Tipos | `python .agent/skills/lint-and-validate/scripts/type_coverage.py .` |
| **Qualquer agente** | Checagem i18n | `python .agent/skills/i18n-localization/scripts/i18n_checker.py .` |

---

### 🔴 Tratamento de Saída de Script (LER → SUMARIZAR → PERGUNTAR)

**Ao rodar um script de validação, você DEVE:**

1. **Rodar o script** e capturar TODA a saída
2. **Analisar a saída** - identificar erros, avisos e sucessos
3. **Sumarizar para o usuário** neste formato:

```markdown
## Resultados do Script: [nome_do_script.py]

### ❌ Erros Encontrados (X itens)
- [Arquivo:Linha] Descrição do erro 1
- [Arquivo:Linha] Descrição do erro 2

### ⚠️ Avisos (Y itens)
- [Arquivo:Linha] Descrição do aviso

### ✅ Passou (Z itens)
- Checagem 1 passou
- Checagem 2 passou

**Devo corrigir os X erros?**
```

4. **Esperar a confirmação do usuário** antes de corrigir
5. **Após corrigir** → Rodar o script novamente para confirmar

> 🔴 **VIOLAÇÃO:** Rodar o script e ignorar a saída = tarefa FALHA.
> 🔴 **VIOLAÇÃO:** Auto-corrigir sem perguntar = Não permitido.
> 🔴 **Regra:** Sempre LEIA a saída → SUMARIZE → PERGUNTE → depois corrija.
