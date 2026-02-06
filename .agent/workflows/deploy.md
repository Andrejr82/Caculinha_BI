---
description: Comando de deploy para releases de produção. Checagens pré-voo e execução de deploy.
---

# /deploy - Deploy em Produção

$ARGUMENTS

---

## Propósito

Este comando lida com o deploy em produção com checagens pré-voo (pre-flight checks), execução de deploy e verificação.

---

## Sub-comandos

```
/deploy            - Assistente de deploy interativo
/deploy check      - Executar apenas checagens pré-deploy
/deploy preview    - Deploy para preview/staging
/deploy production - Deploy para produção
/deploy rollback   - Rollback para versão anterior
```

---

## Checklist Pré-Deploy

Antes de qualquer deploy:

```markdown
## 🚀 Checklist Pré-Deploy

### Qualidade de Código
- [ ] Sem erros de TypeScript (`npx tsc --noEmit`)
- [ ] ESLint passando (`npx eslint .`)
- [ ] Todos os testes passando (`npm test`)

### Segurança
- [ ] Sem segredos (secrets) no código
- [ ] Variáveis de ambiente documentadas
- [ ] Dependências auditadas (`npm audit`)

### Performance
- [ ] Tamanho do bundle aceitável
- [ ] Sem instruções console.log
- [ ] Imagens otimizadas

### Documentação
- [ ] README atualizado
- [ ] CHANGELOG atualizado
- [ ] Docs de API atualizados

### Pronto para o deploy? (y/n)
```

---

## Fluxo de Deploy

```
┌─────────────────┐
│  /deploy        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Checagens      │
│  Pré-voo        │
└────────┬────────┘
         │
    Passou? ──Não──► Corrigir problemas
         │
        Sim
         │
         ▼
┌─────────────────┐
│  Build da       │
│  Aplicação      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy para    │
│  A Plataforma   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Health check   │
│  & verificação  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ✅ Concluído   │
└─────────────────┘
```

---

## Formato de Saída

### Deploy com Sucesso

```markdown
## 🚀 Deploy Concluído

### Resumo
- **Versão:** v1.2.3
- **Ambiente:** produção
- **Duração:** 47 segundos
- **Plataforma:** Vercel

### URLs
- 🌐 Produção: https://app.exemplo.com.br
- 📊 Dashboard: https://vercel.com/project

### O que mudou
- Adicionado recurso de perfil de usuário
- Corrigido bug de login
- Dependências atualizadas

### Health Check (Verificação de Saúde)
✅ API respondendo (200 OK)
✅ Banco de dados conectado
✅ Todos os serviços saudáveis
```

### Falha no Deploy

```markdown
## ❌ Falha no Deploy

### Erro
Build falhou no passo: compilação TypeScript

### Detalhes
```
error TS2345: Argument of type 'string' is not assignable...
```

### Resolução
1. Corrija o erro de TypeScript em `src/services/user.ts:45`
2. Rode `npm run build` localmente para verificar
3. Tente `/deploy` novamente

### Rollback Disponível
A versão anterior (v1.2.2) ainda está ativa.
Rode `/deploy rollback` se necessário.
```

---

## Suporte de Plataformas

| Plataforma | Comando | Notas |
|------------|---------|-------|
| Vercel | `vercel --prod` | Auto-detectado para Next.js |
| Railway | `railway up` | Precisa da CLI do Railway |
| Fly.io | `fly deploy` | Precisa do flyctl |
| Docker | `docker compose up -d` | Para auto-hospedagem |

---

## Exemplos

```
/deploy
/deploy check
/deploy preview
/deploy production --skip-tests
/deploy rollback
```
