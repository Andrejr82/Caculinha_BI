---
name: performance-profiling
description: Princípios de análise de performance (profiling). Técnicas de medição, análise e otimização.
allowed-tools: Read, Glob, Grep, Bash
---

# Perfil de Performance (Profiling)

> Medir, analisar, otimizar - nessa ordem.

---

## 🔧 Scripts de Execução

**Execute-os para profiling automatizado:**

| Script | Propósito | Uso |
|--------|-----------|-----|
| `scripts/lighthouse_audit.py` | Auditoria de performance Lighthouse | `python scripts/lighthouse_audit.py https://exemplo.com` |

---

## 1. Core Web Vitals

### Alvos

| Métrica | Bom | Ruim | Mede |
|---------|-----|------|------|
| **LCP** | < 2.5s | > 4.0s | Carregamento |
| **INP** | < 200ms | > 500ms | Interatividade |
| **CLS** | < 0.1 | > 0.25 | Estabilidade visual |

### Quando Medir

| Estágio | Ferramenta |
|---------|------------|
| Desenvolvimento | Lighthouse local |
| CI/CD | Lighthouse CI |
| Produção | RUM (Real User Monitoring) |

---

## 2. Fluxo de Profiling

### O Processo de 4 Passos

```
1. LINHA DE BASE (BASELINE) → Medir o estado atual
2. IDENTIFICAR → Encontrar o gargalo
3. CORRIGIR → Realizar mudança direcionada
4. VALIDAR → Confirmar a melhoria
```

### Seleção de Ferramenta de Profiling

| Problema | Ferramenta |
|----------|------------|
| Carregamento da página | Lighthouse |
| Tamanho do bundle | Bundle analyzer |
| Runtime | DevTools Performance |
| Memória | DevTools Memory |
| Rede | DevTools Network |

---

## 3. Análise de Bundle

### O que procurar

| Problema | Indicador |
|----------|-----------|
| Dependências grandes | Topo do bundle |
| Código duplicado | Múltiplos chunks |
| Código não utilizado | Baixa cobertura |
| Divisões (splits) ausentes | Chunk único e grande |

### Ações de Otimização

| Descoberta | Ação |
|------------|------|
| Biblioteca grande | Importar módulos específicos |
| Dependências duplicadas | Deduplicar, atualizar versões |
| Rota no bundle principal | Code splitting (divisão de código) |
| Exports não utilizados | Tree shaking |

---

## 4. Profiling de Runtime

### Análise da aba Performance

| Padrão | Significado |
|--------|-------------|
| Tarefas longas (>50ms) | Bloqueio de UI |
| Muitas tarefas pequenas | Possível oportunidade de lote (batching) |
| Layout/paint | Gargalo de renderização |
| Script | Execução de JavaScript |

### Análise da aba Memória

| Padrão | Significado |
|--------|-------------|
| Heap crescente | Possível vazamento (leak) |
| Retenção grande | Verificar referências |
| DOM órfão (detached) | Não foi limpo corretamente |

---

## 5. Gargalos Comuns

### Por Sintoma

| Sintoma | Causa Provável |
|---------|----------------|
| Carregamento inicial lento | JS grande, bloqueio de renderização |
| Interações lentas | Manipuladores de evento pesados |
| "Jank" durante o scroll | Thrashing de layout |
| Memória crescente | Vazamentos, referências retidas |

---

## 6. Prioridades de "Ganhos Rápidos" (Quick Wins)

| Prioridade | Ação | Impacto |
|------------|------|---------|
| 1 | Habilitar compressão | Alto |
| 2 | Lazy loading de imagens | Alto |
| 3 | Code splitting de rotas | Alto |
| 4 | Cache de ativos estáticos | Médio |
| 5 | Otimizar imagens | Médio |

---

## 7. Anti-Padrões

| ❌ NÃO FAÇA | ✅ FAÇA |
|-------------|---------|
| Palpitar sobre problemas | Fazer profiling primeiro |
| Micro-otimizar | Corrigir o maior problema |
| Otimizar precocemente | Otimizar quando necessário |
| Ignorar usuários reais | Usar dados de RUM |

---

> **Lembre-se:** O código mais rápido é aquele que não é executado. Remova antes de otimizar.
