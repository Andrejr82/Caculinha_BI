---
name: server-management
description: Princípios de gerenciamento de servidor e tomada de decisão. Gerenciamento de processos, estratégia de monitoramento e decisões de escalonamento. Ensina a pensar, não comandos.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Gerenciamento de Servidor

> Princípios de gerenciamento de servidor para operações em produção.
> **Aprenda a PENSAR, não a memorizar comandos.**

---

## 1. Princípios de Gerenciamento de Processos

### Seleção de Ferramenta

| Cenário | Ferramenta |
|---------|------------|
| **App Node.js** | PM2 (clustering, reload) |
| **Qualquer app** | systemd (nativo do Linux) |
| **Containers** | Docker/Podman |
| **Orchestração** | Kubernetes, Docker Swarm |

### Objetivos do Gerenciamento de Processos

| Objetivo | O que significa |
|----------|-----------------|
| **Reiniciar em crash** | Recuperação automática |
| **Reload sem downtime** | Sem interrupção de serviço |
| **Clustering** | Usar todos os núcleos da CPU |
| **Persistência** | Sobreviver a reboot do servidor |

---

## 2. Princípios de Monitoramento

### O que Monitorar

| Categoria | Métricas Chave |
|-----------|----------------|
| **Disponibilidade** | Uptime, health checks |
| **Performance** | Tempo de resposta, throughput |
| **Erros** | Taxa de erro, tipos |
| **Recursos** | CPU, memória, disco |

### Estratégia de Severidade de Alerta

| Nível | Resposta |
|-------|----------|
| **Crítico** | Ação imediata |
| **Aviso (Warning)** | Investigar em breve |
| **Informação (Info)** | Revisar diariamente |

### Seleção de Ferramenta de Monitoramento

| Necessidade | Opções |
|-------------|---------|
| Simples/Grátis | Métricas do PM2, htop |
| Observabilidade total | Grafana, Datadog |
| Rastreamento de erros | Sentry |
| Uptime | UptimeRobot, Pingdom |

---

## 3. Princípios de Gerenciamento de Logs

### Estratégia de Log

| Tipo de Log | Propósito |
|-------------|-----------|
| **Logs de aplicação** | Depuração, auditoria |
| **Logs de acesso** | Análise de tráfego |
| **Logs de erro** | Detecção de problemas |

### Princípios de Log

1. **Rotacionar logs** para evitar que o disco encha
2. **Log estruturado** (JSON) para parsing facilitado
3. **Níveis apropriados** (error/warn/info/debug)
4. **Sem dados sensíveis** nos logs

---

## 4. Decisões de Escalonamento (Scaling)

### Quando Escalonar

| Sintoma | Solução |
|---------|---------|
| CPU alta | Adicionar instâncias (horizontal) |
| Memória alta | Aumentar RAM ou corrigir vazamento |
| Resposta lenta | Perfil (profile) primeiro, depois escala |
| Picos de tráfego | Auto-scaling |

### Estratégia de Escalonamento

| Tipo | Quando Usar |
|------|-------------|
| **Vertical** | Correção rápida, instância única |
| **Horizontal** | Sustentável, distribuído |
| **Automático** | Tráfego variável |

---

## 5. Princípios de Health Check (Check de Saúde)

### O que constitui "Saudável"

| Verificação | Significado |
|-------------|-------------|
| **HTTP 200** | Serviço respondendo |
| **Banco de dados conectado** | Dados acessíveis |
| **Dependências OK** | Serviços externos alcancáveis |
| **Recursos OK** | CPU/memória não esgotados |

### Implementação de Health Check

- Simples: Apenas retornar 200
- Profundo: Verificar todas as dependências
- Escolha com base nas necessidades do balanceador de carga

---

## 6. Princípios de Segurança

| Área | Princípio |
|------|-----------|
| **Acesso** | Apenas chaves SSH, sem senhas |
| **Firewall** | Apenas portas necessárias abertas |
| **Atualizações** | Patches de segurança regulares |
| **Segredos (Secrets)** | Variáveis de ambiente, não arquivos |
| **Auditoria** | Logar acessos e mudanças |

---

## 7. Prioridade de Diagnóstico (Troubleshooting)

Quando algo está errado:

1. **Verificar se está rodando** (status do processo)
2. **Verificar logs** (mensagens de erro)
3. **Verificar recursos** (disco, memória, CPU)
4. **Verificar rede** (portas, DNS)
5. **Verificar dependências** (banco de dados, APIs)

---

## 8. Anti-Padrões

| ❌ NÃO FAÇA | ✅ FAÇA |
|-------------|---------|
| Rodar como root | Usar usuário não-root |
| Ignorar os logs | Configurar rotação de logs |
| Pular monitoramento | Monitorar desde o primeiro dia |
| Reinicializações manuais | Configurar auto-restart |
| Sem backups | Agenda regular de backups |

---

## 10. Conclusão

> **Lembre-se:** Um servidor bem gerenciado é entediante. Esse é o objetivo.
