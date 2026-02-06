---
name: systematic-debugging
description: Metodologia de depuração sistemática em 4 fases com análise de causa raiz e verificação baseada em evidências. Use ao depurar problemas complexos.
allowed-tools: Read, Glob, Grep
---

# Depuração Sistemática

> Fonte: obra/superpowers

## Visão Geral
Esta skill fornece uma abordagem estruturada para depuração que evita palpites aleatórios e garante que os problemas sejam devidamente compreendidos antes de serem resolvidos.

## Processo de Depuração em 4 Fases

### Fase 1: Reproduzir
Antes de corrigir, reproduza o problema de forma confiável.

```markdown
## Passos de Reprodução
1. [Passo exato para reproduzir]
2. [Próximo passo]
3. [Resultado esperado vs resultado real]

## Taxa de Reprodução
- [ ] Sempre (100%)
- [ ] Frequentemente (50-90%)
- [ ] Às vezes (10-50%)
- [ ] Raro (<10%)
```

### Fase 2: Isolar
Estreite a busca pela fonte do problema.

```markdown
## Perguntas de Isolamento
- Quando isso começou a acontecer?
- O que mudou recentemente?
- Isso acontece em todos os ambientes?
- Podemos reproduzir com o mínimo de código?
- Qual é a menor mudança que dispara o erro?
```

### Fase 3: Compreender
Encontre a causa raiz, não apenas os sintomas.

```markdown
## Análise de Causa Raiz
### Os 5 Porquês
1. Por que: [Primeira observação]
2. Por que: [Razão mais profunda]
3. Por que: [Ainda mais profunda]
4. Por que: [Chegando perto]
5. Por que: [Causa raiz]
```

### Fase 4: Corrigir e Verificar
Corrija e certifique-se de que está realmente resolvido.

```markdown
## Verificação da Correção
- [ ] O bug não se reproduz mais
- [ ] Funcionalidades relacionadas ainda funcionam
- [ ] Nenhum novo problema foi introduzido
- [ ] Teste adicionado para evitar regressão
```

## Checklist de Depuração

```markdown
## Antes de Iniciar
- [ ] Consigo reproduzir consistentemente
- [ ] Tenho um caso de reprodução mínima
- [ ] Entendo o comportamento esperado

## Durante a Investigação
- [ ] Verificar mudanças recentes (git log)
- [ ] Verificar logs em busca de erros
- [ ] Adicionar logs se necessário
- [ ] Usar debugger/breakpoints

## Após a Correção
- [ ] Causa raiz documentada
- [ ] Correção verificada
- [ ] Teste de regressão adicionado
- [ ] Códigos similares verificados
```

## Comandos Comuns de Depuração

```bash
# Mudanças recentes
git log --oneline -20
git diff HEAD~5

# Buscar por um padrão
grep -r "padraoDoErro" --include="*.ts"

# Verificar logs
pm2 logs nome-do-app --err --lines 100
```

## Anti-Padrões

❌ **Mudanças aleatórias** - "Talvez se eu mudar isso..."
❌ **Ignorar evidências** - "Isso não pode ser a causa"
❌ **Pressupor** - "Deve ser X" sem provas
❌ **Não reproduzir primeiro** - Corrigir às cegas
❌ **Parar nos sintomas** - Não encontrar a causa raiz

---

> **Lembre-se:** A depuração sistemática trata de coletar evidências. Se você não consegue explicar o PORQUÊ da correção funcionar, você não terminou.
