# Product Requirements Document (PRD)
# Agent Solution BI - Lojas Caçula

**Versão:** 2.1
**Data:** 28 de Dezembro de 2025
**Status:** Em Produção (Fase de Modernização e Manutenção)
**Proprietário do Produto:** Gerência de BI & Engenharia de IA

---

## 1. Visão do Produto

### 1.1 Resumo Executivo

O **Agent Solution BI** é uma plataforma de Business Intelligence conversacional que combina Inteligência Artificial Generativa (Google Gemini 3.0 Flash) com processamento de dados de alta performance (Polars + DuckDB) para transformar mais de 1 milhão de registros de vendas e estoque da rede Lojas Caçula em insights acionáveis através de linguagem natural.

A solução elimina a necessidade de expertise técnica em SQL ou BI tradicional, permitindo que gestores de categoria, gerentes de loja e a diretoria executiva obtenham análises complexas através de perguntas simples como "Quais produtos de Tecidos estão em ruptura na UNE 1?".

### 1.2 Problema a Resolver

**Desafios Atuais:**
- **Latência Decisória:** Gestores aguardam horas/dias para receber relatórios de BI, perdendo janelas de oportunidade.
- **Complexidade Técnica:** Análises avançadas exigem conhecimento de SQL/Excel avançado, limitando autonomia operacional.
- **Ruptura de Gôndola:** Falta de visibilidade em tempo real sobre produtos com estoque em CD mas ausentes nas lojas (perda de vendas estimada em 15-20%).
- **Gestão de Mix Ineficiente:** Dificuldade em identificar os produtos "Classe A" que sustentam 80% do faturamento (Princípio de Pareto).
- **Imobilização de Capital:** Excesso de estoque de itens de baixo giro sem visibilidade clara.

### 1.3 Proposta de Valor

**Para Gestores de Categoria:**
- Análises de desempenho de segmento/categoria em segundos via chat.
- Alertas proativos de ruptura com sugestões de ação.
- Visão clara da Curva ABC para priorização de compras.

**Para Gerentes de Loja (UNE):**
- Monitoramento de estoque e vendas da sua unidade.
- Sugestões inteligentes de transferência CD → Loja.
- Indicadores de saúde operacional (cobertura, giro).

**Para Diretoria:**
- Dashboard estratégico consolidado com KPIs de todas as UNEs.
- Análise de tendências de crescimento MoM/YoY.
- Visão holística da eficiência de capital de giro.

---

## 2. Objetivos do Negócio

### 2.1 Objetivos Primários

| ID | Objetivo | Métrica de Sucesso | Prazo |
|----|----------|-------------------|-------|
| OBJ-01 | Reduzir Taxa de Ruptura de Gôndola | Queda de 15% a 20% em rupturas críticas | 3 meses |
| OBJ-02 | Aumentar Eficiência Operacional | 80% das análises realizadas em < 5 segundos | Imediato |
| OBJ-03 | Democratizar Acesso a Dados | 90% dos gestores acessando BI sem suporte técnico | 6 meses |
| OBJ-04 | Otimizar Capital de Giro | Redução de 10% em estoque imobilizado (Classe C) | 6 meses |

### 2.2 KPIs de Produto

- **Adoção:** 80% dos gestores usando o sistema semanalmente.
- **Satisfação:** Net Promoter Score (NPS) > 8.0.
- **Performance:** 95% das consultas completadas em < 3 segundos.
- **Confiabilidade:** 99.5% de disponibilidade (uptime).
- **Precisão:** Taxa de sucesso de respostas da IA > 95% (validação via feedback).

---

## 3. Usuários-Alvo e Personas

### Persona 1: Gestor de Categoria
**Nome:** Maria Silva
**Cargo:** Gerente de Categoria - Tecidos
**Necessidades:**
- Análise rápida de performance de produtos do seu segmento.
- Identificação de tendências de crescimento/queda.
- Visão de estoque e cobertura por produto.

**Dores:**
- Dependência de equipe de BI para relatórios customizados.
- Dificuldade em cruzar dados de vendas, estoque e margem.

**Jornada no Sistema:**
1. Login com credenciais segmentadas (acesso apenas a dados de Tecidos).
2. Pergunta no chat: "Quais produtos de Tecidos cresceram mais de 10% no último mês?".
3. Recebe gráfico interativo e tabela com dados.
4. Exporta relatório para apresentação à diretoria.

---

### Persona 2: Gerente de Loja (UNE)
**Nome:** João Santos
**Cargo:** Gerente - Loja Caçula UNE 1
**Necessidades:**
- Monitoramento diário de estoque da sua unidade.
- Alertas de produtos próximos à ruptura.
- Sugestões de transferência para evitar perda de vendas.

**Dores:**
- Ruptura de produtos com demanda mas sem estoque na loja (enquanto há disponibilidade no CD).
- Processos manuais para solicitar transferências.

**Jornada no Sistema:**
1. Acessa Dashboard de Rupturas.
2. Visualiza lista priorizada de produtos em risco.
3. Clica em "Sugestões de Transferência".
4. Valida e aprova transferência automática de 50 unidades do CD para sua loja.

---

### Persona 3: Diretor Executivo
**Nome:** Carlos Mendes
**Cargo:** Diretor de Operações
**Necessidades:**
- Visão consolidada de performance de toda a rede.
- Identificação de UNEs ou categorias com problemas.
- Análise de Pareto para foco estratégico.

**Dores:**
- Excesso de relatórios fragmentados.
- Dificuldade em identificar prioridades rapidamente.

**Jornada no Sistema:**
1. Acessa Dashboard Executivo.
2. Visualiza KPIs: Valor Total de Estoque, Taxa de Ruptura Média, Mix de Produtos.
3. Pergunta no chat: "Quais UNEs tiveram queda de mais de 5% nas vendas no último mês?".
4. Recebe análise detalhada com gráficos de tendência.
5. Exporta dados para reunião de diretoria.

---

## 4. Requisitos Funcionais

### 4.1 Autenticação e Autorização

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-01 | Login via usuário/senha com JWT | P0 | ✅ Implementado |
| RF-02 | Controle de acesso baseado em segmento | P0 | ✅ Implementado |
| RF-03 | Integração com Supabase Auth (opcional) | P2 | ✅ Implementado |
| RF-04 | Expiração de token em 60 minutos | P1 | ✅ Implementado |
| RF-05 | Refresh token para renovação automática | P1 | ✅ Implementado |

**Detalhamento:**
- Gestores têm acesso apenas aos dados dos segmentos permitidos (ex: "ARMARINHO E CONFECÇÃO").
- Diretoria possui `allowed_segments: []` (acesso global).
- Mascaramento automático de PII (CPF, email, telefone) em todas as respostas.

---

### 4.2 Chat BI Conversacional

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-06 | Interface de chat com histórico de sessão | P0 | ✅ Implementado |
| RF-07 | Processamento de linguagem natural via Gemini | P0 | ✅ Implementado |
| RF-08 | Streaming de respostas (SSE) | P0 | ✅ Implementado |
| RF-09 | Geração automática de gráficos Plotly | P0 | ✅ Implementado |
| RF-10 | Suporte a tabelas markdown em respostas | P1 | ✅ Implementado |
| RF-11 | Cache semântico de respostas (6h TTL) | P1 | ✅ Implementado |
| RF-12 | Sistema de feedback (positivo/negativo) | P1 | ✅ Implementado |
| RF-13 | Exportação de gráficos (PNG/SVG) | P2 | ✅ Implementado |
| RF-14 | Edição de mensagens enviadas | P2 | ✅ Implementado |

**Capacidades do Chat:**
- **Consultas Analíticas:** "Top 10 produtos por vendas no último mês na UNE 2".
- **Comparações:** "Compare vendas de Tecidos vs Papelaria nos últimos 3 meses".
- **Rupturas:** "Quais produtos estão em ruptura mas têm estoque no CD?".
- **Transferências:** "Sugira transferências para a UNE 5 baseadas em vendas".
- **Pareto:** "Mostre a curva ABC de produtos por receita".

---

### 4.3 Dashboard Estratégico

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-15 | KPIs em tempo real (Valor Estoque, Ruptura, Mix) | P0 | ✅ Implementado |
| RF-16 | Filtros por segmento/categoria/UNE | P1 | ✅ Implementado |
| RF-17 | Gráfico de tendência de vendas (30 dias) | P1 | ✅ Implementado |
| RF-18 | Análise de Pareto (80/20) por receita | P0 | ✅ Implementado |
| RF-19 | Dashboards interativos com drill-down | P1 | ✅ Implementado |

---

### 4.4 Gestão de Rupturas

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-20 | Lista de rupturas críticas com priorização | P0 | ✅ Implementado |
| RF-21 | Drill-down por UNE/Segmento/Categoria | P1 | ✅ Implementado |
| RF-22 | Identificação de produtos com estoque em CD | P0 | ✅ Implementado |
| RF-23 | Cálculo de perda de receita estimada | P1 | ✅ Implementado |

---

### 4.5 Sugestões de Transferência

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-24 | Algoritmo de sugestão CD → Loja | P0 | ✅ Implementado |
| RF-25 | Seleção inteligente de UNE (1→1, 1→N, N→N) | P1 | ✅ Implementado |
| RF-26 | Validação de regras de negócio (MC, ICMS) | P1 | ✅ Implementado |
| RF-27 | Histórico de transferências solicitadas | P2 | ✅ Implementado |

---

### 4.6 AI Insights Proativos

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-28 | Análise automática de crescimento MoM | P1 | ✅ Implementado |
| RF-29 | Identificação de produtos com excesso de estoque | P1 | ✅ Implementado |
| RF-30 | Painel de Insights gerado por IA | P1 | ✅ Implementado |

---

### 4.7 Sistema de Aprendizado (RAG)

| ID | Requisito | Prioridade | Status |
|----|-----------|-----------|--------|
| RF-31 | Busca semântica de queries similares (FAISS) | P1 | ✅ Implementado |
| RF-32 | Coleta de exemplos de sucesso para RAG | P1 | ✅ Implementado |
| RF-33 | Auto-correção de código (Self-Healing) | P1 | ✅ Implementado |
| RF-34 | Indexação de base de código para Code Chat | P2 | ✅ Implementado |

---

## 5. Requisitos Não-Funcionais

### 5.1 Performance e Limpeza

| ID | Requisito | Métrica | Status |
|----|-----------|---------|--------|
| RNF-01 | Consultas analíticas < 3 segundos (p95) | 95% < 3s | ✅ Implementado |
| RNF-02 | Geração de gráficos < 5 segundos | 95% < 5s | ✅ Implementado |
| RNF-03 | Arquitetura limpa (sem arquivos obsoletos) | < 100 arquivos raiz | ✅ Atualizado (28/12) |
| RNF-04 | Cache semântico otimizado | hit rate > 40% | ✅ Implementado |

---

## 7. Stack Tecnológica

### 7.1 Frontend
- **Framework:** SolidJS 1.8+ (Performance nativa)
- **Visualização:** Plotly.js 2.x
- **Estilização:** TailwindCSS 3.x
- **Build Tool:** Vite 5.x

### 7.2 Backend
- **Framework:** FastAPI 0.104+
- **Motor de Dados:** Polars + DuckDB (Processamento Colunar)
- **IA:** Google Gemini 3.0 Flash
- **RAG:** FAISS + Sentence-Transformers

---

## 8. Roadmap de Produto

### Fase 1: MVP (Q4 2024) ✅
- Core do Agente BI e Dashboards.

### Fase 2: Otimização & Modernização (Q1 2025) ✅
- **Implementado em 28/12/2025:** Limpeza completa de arquivos obsoletos, consolidação de documentação técnica e melhoria no sistema de backups/restore.

### Fase 3: Integração & Automação (Q2-Q3 2025) 🟡
- 🟡 Alertas automáticos (email/push).
- 🟡 Integração direta com ERP para execução de pedidos.

---

## 17. Histórico de Versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2024-11-15 | [Nome] | Versão inicial do PRD |
| 2.0 | 2025-12-21 | [Nome] | Atualização DuckDB e RAG |
| 2.1 | 2025-12-28 | Gemini Agent | Atualização pós-limpeza de arquitetura e validação de features de exportação e seleção UNE. |

---

**Lojas Caçula © 2025 - Transformando dados em decisões estratégicas.**