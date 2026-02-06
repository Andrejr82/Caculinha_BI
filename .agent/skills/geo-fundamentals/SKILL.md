---
name: geo-fundamentals
description: Otimização de Mecanismo Generativo para motores de busca de IA (ChatGPT, Claude, Perplexity).
allowed-tools: Read, Glob, Grep
---

# Fundamentos de GEO

> Otimização para motores de busca alimentados por IA.

---

## 1. O que é GEO?

**GEO** = Otimização de Mecanismo Generativo (Generative Engine Optimization)

| Objetivo | Plataforma |
|----------|------------|
| Ser citado em respostas de IA | ChatGPT, Claude, Perplexity, Gemini |

### SEO vs GEO

| Aspecto | SEO | GEO |
|---------|-----|-----|
| Objetivo | Ranking #1 | Citações da IA |
| Plataforma | Google | Motores de IA |
| Métricas | Rankings, CTR | Taxa de citação |
| Foco | Palavras-chave | Entidades, dados |

---

## 2. O Cenário dos Motores de IA

| Motor | Estilo de Citação | Oportunidade |
|-------|-------------------|--------------|
| **Perplexity** | Numerado [1][2] | Maior taxa de citação |
| **ChatGPT** | Inline/notas de rodapé | GPTs Customizados |
| **Claude** | Contextual | Conteúdo de formato longo |
| **Gemini** | Seção de fontes | Cruzamento com SEO |

---

## 3. Fatores de Recuperação Rerieval (RAG)

Como os motores de IA selecionam o conteúdo para citar:

| Fator | Peso |
|-------|------|
| Relevância semântica | ~40% |
| Correspondência de palavra-chave | ~20% |
| Sinais de autoridade | ~15% |
| Recência (Freshness) | ~10% |
| Diversidade de fontes | ~15% |

---

## 4. Conteúdo que é Citado

| Elemento | Por que Funciona |
|----------|-----------------|
| **Estatísticas originais** | Dados únicos e citáveis |
| **Citações de especialistas** | Transferência de autoridade |
| **Definições claras** | Fácil de extrair |
| **Guias passo a passo** | Valor acionável |
| **Tabelas de comparação** | Informação estruturada |
| **Seções de FAQ** | Respostas diretas |

---

## 5. Checklist de Conteúdo GEO

### Elementos de Conteúdo

- [ ] Títulos baseados em perguntas
- [ ] Resumo/TL;DR no topo
- [ ] Dados originais com fontes
- [ ] Citações de especialistas (nome, cargo)
- [ ] Seção de FAQ (3-5 perguntas e respostas)
- [ ] Definições claras
- [ ] Timestamp de "Última atualização"
- [ ] Autor com credenciais

### Elementos Técnicos

- [ ] Schema Article com datas
- [ ] Schema Person para o autor
- [ ] Schema FAQPage
- [ ] Carregamento rápido (< 2.5s)
- [ ] Estrutura HTML limpa

---

## 6. Construção de Entidade

| Ação | Propósito |
|------|-----------|
| Google Knowledge Panel | Reconhecimento de entidade |
| Wikipedia (se notável) | Fonte de autoridade |
| Informação consistente na web | Consolidação de entidade |
| Menções da indústria | Sinais de autoridade |

---

## 7. Acesso de Crawlers de IA

### Principais User-Agents de IA

| Crawler | Motor |
|---------|-------|
| GPTBot | ChatGPT/OpenAI |
| Claude-Web | Claude |
| PerplexityBot | Perplexity |
| Googlebot | Gemini (compartilhado) |

### Decisão de Acesso

| Estratégia | Quando |
|------------|--------|
| Permitir todos | Deseja citações da IA |
| Bloquear GPTBot | Não deseja treinamento da OpenAI |
| Seletivo | Permitir alguns, bloquear outros |

---

## 8. Medição

| Métrica | Como rastrear |
|---------|---------------|
| Citações de IA | Monitoramento manual |
| Menções "Segundo [Marca]"| Busca na IA |
| Citações de concorrentes | Comparar market share |
| Tráfego referido pela IA | Parâmetros UTM |

---

## 9. Anti-Padrões

| ❌ NÃO FAÇA | ✅ FAÇA |
|-------------|---------|
| Publicar sem datas | Adicionar timestamps |
| Atribuições vagas | Nomear as fontes |
| Pular info do autor | Mostrar credenciais |
| Conteúdo raso | Cobertura abrangente |

---

> **Lembre-se:** A IA cita conteúdo que é claro, autoritativo e fácil de extrair. Seja a melhor resposta.

---

## Script

| Script | Propósito | Comando |
|--------|-----------|---------|
| `scripts/geo_checker.py` | Auditoria GEO (Prontidão para citação de IA) | `python scripts/geo_checker.py <caminho_projeto>` |
