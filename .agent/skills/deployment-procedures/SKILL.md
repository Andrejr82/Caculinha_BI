---
name: deployment-procedures
description: Princípios de deploy em produção e tomada de decisão. Workflows de deploy seguro, estratégias de rollback e verificação. Ensina a pensar, não scripts.
allowed-tools: Read, Glob, Grep, Bash
---

# Procedimentos de Deploy

> Princípios de deploy e tomada de decisão para releases seguras em produção.
> **Aprenda a PENSAR, não a memorizar scripts.**

---

## ⚠️ Como Usar Esta Skill

Esta skill ensina **princípios de deploy**, não scripts bash para copiar.

- Cada deploy é único
- Entenda o PORQUÊ de cada passo
- Adapte os procedimentos à sua plataforma

---

## 1. Seleção de Plataforma

### Árvore de Decisão

```
O que você está implantando?
│
├── Site estático / JAMstack
│   └── Vercel, Netlify, Cloudflare Pages
│
├── Web app simples
│   ├── Gerenciado → Railway, Render, Fly.io
│   └── Controle → VPS + PM2/Docker
│
├── Microserviços
│   └── Orquestração de containers
│
└── Serverless
    └── Edge functions, Lambda
```

### Cada Plataforma Tem Procedimentos Diferentes

| Plataforma | Método de Deploy |
|------------|------------------|
| **Vercel/Netlify** | Git push, auto-deploy |
| **Railway/Render** | Git push ou CLI |
| **VPS + PM2** | SSH + passos manuais |
| **Docker** | Push de imagem + orquestração |
| **Kubernetes** | kubectl apply |

---

## 2. Princípios Pré-Deploy

### As 4 Categorias de Verificação

| Categoria | O que verificar |
|-----------|-----------------|
| **Qualidade do Código** | Testes passando, lint limpo, revisado |
| **Build** | Build de produção funciona, sem avisos |
| **Ambiente** | Vars de ambiente configuradas, segredos atuais |
| **Segurança** | Backup feito, plano de rollback pronto |

### Checklist Pré-Deploy

- [ ] Todos os testes passando
- [ ] Código revisado e aprovado
- [ ] Build de produção com sucesso
- [ ] Variáveis de ambiente verificadas
- [ ] Migrações de banco de dados prontas (se houver)
- [ ] Plano de rollback documentado
- [ ] Equipe notificada
- [ ] Monitoramento pronto

---

## 3. Princípios do Workflow de Deploy

### O Processo de 5 Fases

```
1. PREPARAR
   └── Verificar código, build, vars de ambiente

2. BACKUP
   └── Salvar o estado atual antes de mudar

3. IMPLANTAR (DEPLOY)
   └── Executar com o monitoramento aberto

4. VERIFICAR
   └── Check de saúde (health check), logs, fluxos chave

5. CONFIRMAR ou REVERTER (ROLLBACK)
   └── Tudo bem? Confirme. Problemas? Rollback.
```

### Princípios das Fases

| Fase | Princípio |
|------|-----------|
| **Preparar** | Nunca faça deploy de código não testado |
| **Backup** | Não é possível fazer rollback sem backup |
| **Implantar** | Assista acontecer, não vá embora |
| **Verificar** | Confie, mas verifique |
| **Confirmar** | Tenha o gatilho de rollback pronto |

---

## 4. Verificação Pós-Deploy

### O que Verificar

| Verificação | Por que |
|-------------|---------|
| **Endpoint de Saúde (Health)** | O serviço está rodando |
| **Logs de erro** | Sem novos erros |
| **Fluxos chave do usuário** | Recursos críticos funcionam |
| **Performance** | Tempos de resposta aceitáveis |

### Janela de Verificação

- **Primeiros 5 minutos**: Monitoramento ativo
- **15 minutos**: Confirmar que está estável
- **1 hora**: Verificação final
- **Dia seguinte**: Revisar métricas

---

## 5. Princípios de Rollback (Reversão)

### Quando Fazer Rollback

| Sintoma | Ação |
|---------|------|
| Serviço fora do ar | Rollback imediato |
| Erros críticos | Rollback |
| Performance >50% degradada | Considerar rollback |
| Problemas menores | Corrigir pra frente (fix forward) se for rápido |

### Estratégia de Rollback por Plataforma

| Plataforma | Método de Rollback |
|------------|-------------------|
| **Vercel/Netlify** | Redisparo do commit anterior |
| **Railway/Render** | Rollback no dashboard |
| **VPS + PM2** | Restaurar backup, reiniciar |
| **Docker** | Tag de imagem anterior |
| **K8s** | kubectl rollout undo |

### Princípios de Rollback

1. **Velocidade sobre perfeição**: Reverter primeiro, depurar depois
2. **Não acumule erros**: Um rollback, não múltiplas mudanças
3. **Comunique**: Avise a equipe o que aconteceu
4. **Post-mortem**: Entenda o porquê após estar estável

---

## 6. Deploy com Zero Downtime (Sem Interrupção)

### Estratégias

| Estratégia | Como Funciona |
|------------|---------------|
| **Rolling** | Substitui instâncias uma por uma |
| **Blue-Green** | Alterna o tráfego entre ambientes |
| **Canary** | Mudança gradual de tráfego |

### Princípios de Seleção

| Cenário | Estratégia |
|---------|------------|
| Release padrão | Rolling |
| Mudança de alto risco | Blue-green (rollback fácil) |
| Precisa de validação | Canary (testar com tráfego real) |

---

## 7. Procedimentos de Emergência

### Prioridade com Serviço Fora do Ar

1. **Avaliar**: Qual é o sintoma?
2. **Correção rápida**: Reiniciar se não estiver claro
3. **Rollback**: Se reiniciar não ajudar
4. **Investigar**: Após estar estável

### Ordem de Investigação

| Verificação | Problemas Comuns |
|-------------|------------------|
| **Logs** | Erros, exceções |
| **Recursos** | Disco cheio, memória |
| **Rede** | DNS, firewall |
| **Dependências** | Banco de dados, APIs |

---

## 8. Anti-Padrões

| ❌ NÃO FAÇA | ✅ FAÇA |
|-------------|---------|
| Deploy na sexta-feira | Deploy no início da semana |
| Apressar o deploy | Siga o processo |
| Pular o staging | Sempre teste primeiro |
| Deploy sem backup | Backup antes do deploy |
| Ir embora após o deploy | Monitore por 15+ min |
| Múltiplas mudanças de uma vez | Uma mudança por vez |

---

## 9. Checklist de Decisão

Antes de fazer o deploy:

- [ ] **Procedimento apropriado para a plataforma?**
- [ ] **Estratégia de backup pronta?**
- [ ] **Plano de rollback documentado?**
- [ ] **Monitoramento configurado?**
- [ ] **Equipe notificada?**
- [ ] **Tempo para monitorar depois?**

---

## 10. Melhores Práticas

1. **Deploys pequenos e frequentes** em vez de grandes releases
2. **Feature flags** para mudanças arriscadas
3. **Automatize** passos repetitivos
4. **Documente** cada deployment
5. **Revise** o que deu errado após problemas
6. **Teste o rollback** antes de precisar dele

---

> **Lembre-se:** Cada deploy é um risco. Minimize o risco através da preparação, não da velocidade.
