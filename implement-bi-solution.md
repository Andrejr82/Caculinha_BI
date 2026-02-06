---
description: Implementar BI Solution
---

# 🚀 MEGA PROMPT PARA ANTIGRAVITY IDE - BI SOLUTION LOJAS CAÇULA
**Otimizado para Claude Opus 4.5 (Thinking) com Continuidade Multi-LLM**

---

## 📋 METADADOS DO PROMPT

```yaml
Projeto: BI Solution - Agent Comercial Lojas Caçula
Objetivo: Implementar correções críticas + melhorias de prompt engineering
LLM Primário: Claude Opus 4.5 (Thinking)
LLMs Fallback: Claude Sonnet 4, Gemini 2.0 Pro, GPT-4o
Repositório: https://github.com/Andrejr82/BI_Solution
Framework: Antigravity Kit (20 Agents + 36 Skills + 11 Workflows)
Tempo Estimado: 4-8 horas de execução
Complexidade: Alta (refatoração arquitetural + novos módulos)
```

---

## 🎯 CONTEXTO ESTRATÉGICO

Você é um **Senior AI Engineer** trabalhando no sistema **BI Solution** para a rede varejista **Lojas Caçula** (40 anos, 15 lojas, varejo multisegmento: Papelaria, Tecidos, Utilidades, Brinquedos).

### Problema Atual
O sistema usa **Google Gemini 3.0 Flash** mas tem:
- ❌ 6 bugs críticos de código
- ❌ Engenharia de prompts inadequada (LLM não sabe quem é, o que fazer, nem como fazer)
- ❌ Taxa de sucesso: ~30% (meta: 90%+)
- ❌ Ferramentas ausentes ou mal configuradas

### Sua Missão
Implementar **TODAS as correções e melhorias** do plano de implementação anexo, seguindo **EXATAMENTE** as especificações técnicas fornecidas.

---

## 📦 ESTRUTURA DO REPOSITÓRIO

```
BI_Solution/
├── backend/
│   ├── app/
│   │   └── core/
│   │       ├── agents/
│   │       │   └── caculinha_bi_agent.py  # ⚠️ BUG: is_graph_request não definida
│   │       ├── tools/
│   │       │   └── flexible_query_tool.py # ⚠️ BUG: linha duplicada
│   │       └── llm_factory.py             # ⚠️ BUG: fallback incorreto
│   ├── prompts/                           # 📁 CRIAR NOVOS ARQUIVOS AQUI
│   ├── utils/                             # 📁 CRIAR NOVOS ARQUIVOS AQUI
│   └── tools/                             # 📁 CRIAR gemini_tools.py
├── data/parquet/                          # DuckDB + arquivos Parquet
├── frontend-solid/                        # Interface SolidJS
└── docs/                                  # Documentação

NOVOS ARQUIVOS A CRIAR:
✅ backend/prompts/system_prompt_cacula.txt
✅ backend/prompts/few_shot_examples.json
✅ backend/utils/sql_validator.py
✅ backend/utils/query_executor.py
✅ backend/tools/gemini_tools.py
```

---

## 🔧 PARTE 1: CORREÇÕES CRÍTICAS DE BUGS

### BUG A.1 - Variável `is_graph_request` Não Definida

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`  
**Linhas:** 984-1003  
**Erro:** `NameError: name 'is_graph_request' is not defined`

**SOLUÇÃO RECOMENDADA (Opção 1):**

Adicione ANTES da linha 984:

```python
# Detectar se é solicitação de gráfico
graph_keywords = ["gráfico", "grafico", "chart", "visualização", "visualizacao", "plote", "plot", "ranking", "top"]
is_graph_request = any(keyword in user_query.lower() for keyword in graph_keywords)
```

**ALTERNATIVA (Opção 2 - Simplificada):**

Remova COMPLETAMENTE as linhas 984-1003 (o ReAct loop moderno não precisa de fallback manual).

**AÇÃO:** Escolha Opção 1 para manter compatibilidade.

---

### BUG A.2 - Ferramentas Essenciais Removidas

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`  
**Linhas:** 137-150

**PROBLEMA:**
```python
# ❌ ATUAL (incompleto)
core_tools = [
    consultar_dados_flexivel,
    gerar_grafico_universal_v2,
    calcular_abastecimento_une,
    encontrar_rupturas_criticas,
]
```

**SOLUÇÃO:**
```python
# ✅ CORRETO (restaurar ferramentas)
core_tools = [
    consultar_dados_flexivel,
    gerar_grafico_universal_v2,
    calcular_abastecimento_une,
    encontrar_rupturas_criticas,
    consultar_dicionario_dados,        # RESTAURAR
    analisar_produto_todas_lojas,      # RESTAURAR
]
```

**AÇÃO:** Adicione as 2 ferramentas faltantes.

---

### BUG A.3 - Sintaxe Duplicada

**Arquivo:** `backend/app/core/tools/flexible_query_tool.py`  
**Linha:** 161

**PROBLEMA:**
```python
limite = 500
limite = 500  # ← LINHA DUPLICADA (remover)
```

**SOLUÇÃO:** Delete a segunda linha.

---

### BUG A.4 - LLM Factory Fallback Incorreto

**Arquivo:** `backend/app/core/llm_factory.py`  
**Linha:** 50

**PROBLEMA:**
```python
# ❌ ATUAL (hardcoded)
self.primary = primary or "groq"
```

**SOLUÇÃO:**
```python
# ✅ CORRETO (usar configuração)
self.primary = primary or settings.LLM_PROVIDER or "google"
```

**AÇÃO:** Substituir linha 50.

---

## 📝 PARTE 2: NOVOS ARQUIVOS - SYSTEM PROMPT

### ARQUIVO B.1 - System Prompt Especializado

**Caminho:** `backend/prompts/system_prompt_cacula.txt`

**CONTEÚDO COMPLETO:**

```markdown
# IDENTIDADE
Você é o **Assistente BI das Lojas Caçula**, uma rede varejista brasileira com 40 anos de tradição.

## CONTEXTO DO NEGÓCIO

### Sobre a Empresa
- **Nome:** Lojas Caçula
- **Website:** www.lojascacula.com.br
- **Segmento:** Varejo multisegmento
- **Categorias Principais:**
  * Papelaria (Cadernos, Canetas, Material Escolar)
  * Tecidos (Tecidos por Metro, Aviamentos)
  * Utilidades Domésticas
  * Brinquedos
  * Eletrônicos
  * Artigos para Festas

### Estrutura Operacional
- **Centro de Distribuição (CD):** Armazém central
- **Lojas Físicas:** 15 unidades distribuídas
- **Modelo:** CD abastece lojas via transferências

### Objetivos Estratégicos
1. **Evitar Rupturas:** Garantir produto disponível na gôndola
2. **Otimizar Estoque:** Reduzir capital imobilizado
3. **Maximizar Giro:** Foco nos 20% de SKUs que geram 80% da receita (Pareto)
4. **Gestão Inteligente:** Sugestões proativas de transferência CD→Loja

---

## DADOS DISPONÍVEIS

### Database: DuckDB (Parquet)
Localização: `data/parquet/`

### TABELA PRINCIPAL: admmat.parquet
**Colunas Prioritárias:**
- CODIGO: Código do produto (SKU)
- NOME: Descrição do produto
- UNE: Código da loja
- NOMESEGMENTO: Categoria principal
- VENDA_30DD: Vendas últimos 30 dias
- ESTOQUE: Quantidade em estoque
- LIQUIDO_38: Preço de venda
- ULTIMA_ENTRADA_CUSTO_CD: Custo do produto

---

## REGRAS DE NEGÓCIO

### 1. Classificação de Estoque por Cobertura
- **🔴 CRÍTICO (< 3 dias):** Ruptura iminente - AÇÃO IMEDIATA
- **🟡 ALERTA (3-7 dias):** Risco moderado - Planejar transferência
- **🟢 SAUDÁVEL (7-30 dias):** Estoque adequado
- **⚪ EXCESSIVO (> 30 dias):** Capital imobilizado - Considerar promoção

### 2. Análise Pareto (Curva ABC)
- **Classe A:** Top 20% SKUs que geram 80% da receita → PRIORIDADE MÁXIMA
- **Classe B:** 30% SKUs que geram 15% da receita → Monitorar
- **Classe C:** 50% SKUs que geram 5% da receita → Considerar descontinuar

---

## FERRAMENTAS DISPONÍVEIS (USE APENAS ESTAS)

1. **consultar_dados_flexivel** - Queries SQL genéricas no DuckDB
2. **gerar_grafico_universal_v2** - Criar visualizações
3. **calcular_abastecimento_une** - Cálculo de abastecimento por UNE
4. **encontrar_rupturas_criticas** - Identificar produtos em ruptura
5. **consultar_dicionario_dados** - Descobrir colunas disponíveis
6. **analisar_produto_todas_lojas** - Análise multi-loja

> ⚠️ **NUNCA mencione ferramentas que não estão nesta lista!**

---

## ESTILO DE RESPOSTA

### Diretrizes
1. **Tom Profissional e Acionável:**
   - ✅ "Identifiquei 47 SKUs em ruptura. Recomendo transferência imediata."
   - ❌ "Existem alguns produtos que podem estar com estoque baixo."

2. **Sempre Cite Números Concretos:**
   - ✅ "Categoria Papelaria: R$ 1.2M de faturamento (234 SKUs)"
   - ❌ "Papelaria está vendendo bem."

3. **Use Terminologia do Varejo:**
   - SKU, Giro, Ruptura, Mix, Cobertura, CD, Classe ABC

4. **Priorize Ações sobre Análises:**
   - Estrutura: Situação → Números → Recomendação

### Cores da Marca
- 🟢 **Verde (#166534):** Situação saudável
- 🔴 **Vermelho (#991B1B):** Alerta urgente
- 🟡 **Dourado (#C9A961):** Oportunidade
- 🟤 **Marrom (#8B7355):** Contexto

---

## VALIDAÇÕES E RESTRIÇÕES

### Queries SQL
1. **NUNCA usar:** DELETE, DROP, TRUNCATE, ALTER, UPDATE, CREATE
2. **SEMPRE adicionar LIMIT:** Se não especificado, usar LIMIT 500
3. **TIMEOUT:** Queries > 30s são canceladas
4. **Joins:** Máximo 3 JOINs por query

### Período Padrão
- Se não especificado: Últimos 30 dias
- Formato de data: DD/MM/YYYY para apresentação
- Moeda: R$ (Real Brasileiro)
```

---

## 📊 PARTE 3: FEW-SHOT EXAMPLES

### ARQUIVO C.1 - Exemplos de Interações

**Caminho:** `backend/prompts/few_shot_examples.json`

**CONTEÚDO (Primeiro exemplo completo, demais resumidos):**

```json
{
  "examples": [
    {
      "category": "vendas_analise",
      "user": "Quais categorias venderam mais no último mês?",
      "assistant_reasoning": "Usuário quer ranking de categorias por faturamento. Vou consultar vendas dos últimos 30 dias agrupando por NOMESEGMENTO.",
      "tool_calls": [
        {
          "tool": "consultar_dados_flexivel",
          "parameters": {
            "agregacao": "SUM",
            "coluna_agregacao": "VENDA_30DD",
            "agrupar_por": "[\"NOMESEGMENTO\"]",
            "ordenar_por": "valor",
            "limite": "10"
          }
        }
      ],
      "assistant_response": "📊 **TOP 5 CATEGORIAS (Últimos 30 dias)**\n\n| Categoria | Faturamento | Mix SKUs |\n|-----------|-------------|----------|\n| Papelaria | R$ 1.247.890 | 234 |\n| Tecidos | R$ 892.450 | 156 |\n\n🟡 **INSIGHT:** Papelaria representa 58% do faturamento."
    },
    {
      "category": "ruptura_identificacao",
      "user": "Temos produtos em risco de ruptura?",
      "assistant_reasoning": "Identificar SKUs com cobertura crítica.",
      "tool_calls": [{"tool": "encontrar_rupturas_criticas"}],
      "assistant_response": "🔴 **ALERTA: 47 SKUs em Ruptura Iminente**\n\n**CRÍTICOS (< 3 dias):**\n1. SKU 12345 - Caderno 200 Fls: 2.1 dias\n   💡 Transferir 280un HOJE"
    },
    {
      "category": "grafico",
      "user": "Mostre um gráfico das vendas por segmento",
      "assistant_reasoning": "Usuário quer visualização. Usar gerar_grafico_universal_v2.",
      "tool_calls": [
        {
          "tool": "gerar_grafico_universal_v2",
          "parameters": {
            "tipo_grafico": "barras",
            "titulo": "Vendas por Segmento",
            "eixo_x": "NOMESEGMENTO",
            "eixo_y": "VENDA_30DD"
          }
        }
      ],
      "assistant_response": "📈 Gerei o gráfico de vendas por segmento."
    }
  ]
}
```

---

## 🛡️ PARTE 4: SQL VALIDATOR

### ARQUIVO D.1 - Validador de Segurança

**Caminho:** `backend/utils/sql_validator.py`

**INSTRUÇÕES:**
1. Copiar TODO o código do plano de implementação (linhas 274-407)
2. O validador DEVE:
   - Bloquear operações perigosas (DELETE, DROP, etc)
   - Limitar JOINs (máx 3)
   - Adicionar LIMIT automático se ausente
   - Validar sintaxe SQL com `sqlparse`

**CÓDIGO COMPLETO:** [Ver plano de implementação, linhas 274-407]

---

## ⚡ PARTE 5: QUERY EXECUTOR

### ARQUIVO E.1 - Executor com Timeout

**Caminho:** `backend/utils/query_executor.py`

**INSTRUÇÕES:**
1. Copiar TODO o código do plano de implementação (linhas 417-485)
2. O executor DEVE:
   - Conectar DuckDB em modo read-only
   - Validar SQL antes de executar
   - Timeout de 30 segundos
   - Retornar dict com data, rows_count, execution_time

**CÓDIGO COMPLETO:** [Ver plano de implementação, linhas 417-485]

---

## 🔧 PARTE 6: GEMINI TOOLS

### ARQUIVO F.1 - Configuração de Function Calling

**Caminho:** `backend/tools/gemini_tools.py`

**INSTRUÇÕES:**
1. Copiar TODO o código do plano de implementação (linhas 495-580)
2. Definir APENAS as 6 ferramentas listadas:
   - consultar_dados_flexivel
   - gerar_grafico_universal_v2
   - encontrar_rupturas_criticas
   - calcular_abastecimento_une
   - consultar_dicionario_dados
   - analisar_produto_todas_lojas

**CÓDIGO COMPLETO:** [Ver plano de implementação, linhas 495-580]

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

Execute NESTA ORDEM exata:

### ✅ FASE 1: Correções de Bugs (30 min)

```bash
# 1. Corrigir is_graph_request
- [ ] Editar backend/app/core/agents/caculinha_bi_agent.py
- [ ] Adicionar definição da variável ANTES da linha 984
- [ ] Testar que não há mais NameError

# 2. Restaurar ferramentas
- [ ] Editar backend/app/core/agents/caculinha_bi_agent.py (linha 137)
- [ ] Adicionar consultar_dicionario_dados
- [ ] Adicionar analisar_produto_todas_lojas

# 3. Remover duplicata
- [ ] Editar backend/app/core/tools/flexible_query_tool.py
- [ ] Deletar linha 161 duplicada

# 4. Corrigir LLM Factory
- [ ] Editar backend/app/core/llm_factory.py (linha 50)
- [ ] Substituir "groq" por settings.LLM_PROVIDER
```

### ✅ FASE 2: Novos Arquivos (2-3 horas)

```bash
# 5. System Prompt
- [ ] Criar backend/prompts/system_prompt_cacula.txt
- [ ] Copiar conteúdo COMPLETO da Parte 2
- [ ] Validar formatação Markdown

# 6. Few-Shot Examples
- [ ] Criar backend/prompts/few_shot_examples.json
- [ ] Copiar JSON com 3 exemplos mínimos
- [ ] Validar sintaxe JSON (usar jsonlint)

# 7. SQL Validator
- [ ] Criar backend/utils/sql_validator.py
- [ ] Copiar código completo (linhas 274-407)
- [ ] Adicionar import sqlparse ao requirements.txt

# 8. Query Executor
- [ ] Criar backend/utils/query_executor.py
- [ ] Copiar código completo (linhas 417-485)
- [ ] Importar sql_validator

# 9. Gemini Tools
- [ ] Criar backend/tools/gemini_tools.py
- [ ] Copiar código completo (linhas 495-580)
- [ ] Listar APENAS 6 ferramentas permitidas
```

### ✅ FASE 3: Integração (1 hora)

```bash
# 10. Atualizar Master Prompt
- [ ] Editar backend/app/core/agents/master_prompt.py
- [ ] Carregar system_prompt_cacula.txt
- [ ] Adicionar few_shot_examples.json ao contexto

# 11. Integrar Validator nas Tools
- [ ] Editar backend/app/core/tools/flexible_query_tool.py
- [ ] Importar sql_validator
- [ ] Validar SQL antes de executar

# 12. Testes de Integração
- [ ] Testar query simples: "Quais categorias vendem mais?"
- [ ] Testar ruptura: "Produtos em risco?"
- [ ] Testar gráfico: "Gráfico de vendas por segmento"
```

---

## 🎯 CRITÉRIOS DE SUCESSO

Após implementação, o sistema DEVE:

1. ✅ **Zero erros de código** (NameError, SyntaxError, etc)
2. ✅ **Taxa de sucesso > 80%** em queries do setor comercial
3. ✅ **Respostas acionáveis** (não apenas análises genéricas)
4. ✅ **Validação SQL** funcionando (bloqueia DELETE, adiciona LIMIT)
5. ✅ **Few-shot examples** sendo aplicados corretamente
6. ✅ **Terminologia correta** (SKU, Ruptura, Cobertura, etc)

---

## 🔄 CONTINUIDADE MULTI-LLM

### Se Claude Opus 4.5 Atingir Limite

**CHECKPOINT MARKERS** (adicione no código):

```python
# === CHECKPOINT 1: BUGS CORRIGIDOS ===
# Data: [AUTO-GENERATED]
# Status: ✅ Fase 1 completa
# Próximo: Criar system_prompt_cacula.txt

# === CHECKPOINT 2: SYSTEM PROMPT CRIADO ===
# Status: ✅ Fase 2 parcial
# Próximo: Criar few_shot_examples.json

# === CHECKPOINT 3: TODOS ARQUIVOS CRIADOS ===
# Status: ✅ Fase 2 completa
# Próximo: Integração (Fase 3)

# === CHECKPOINT 4: IMPLEMENTAÇÃO COMPLETA ===
# Status: ✅ Sistema pronto para testes
```

### Resumo para Próximo LLM

Se você (Claude Opus) precisar parar, forneça este resumo para continuidade:

```markdown
# RESUMO DE PROGRESSO - BI SOLUTION

## Concluído
- [x] Fase 1: Bugs corrigidos (4/4)
- [x] Fase 2: Arquivos criados (5/5)
- [ ] Fase 3: Integração pendente

## Arquivos Modificados
1. backend/app/core/agents/caculinha_bi_agent.py
   - Linha 984: Adicionada definição is_graph_request
   - Linha 137: Restauradas 2 ferramentas

2. backend/app/core/tools/flexible_query_tool.py
   - Linha 161: Removida duplicata

3. backend/app/core/llm_factory.py
   - Linha 50: Corrigido fallback

## Arquivos Novos Criados
1. ✅ backend/prompts/system_prompt_cacula.txt
2. ✅ backend/prompts/few_shot_examples.json
3. ✅ backend/utils/sql_validator.py
4. ✅ backend/utils/query_executor.py
5. ✅ backend/tools/gemini_tools.py

## Próximos Passos (Para Próximo LLM)
1. Integrar system_prompt em master_prompt.py
2. Adicionar sql_validator em flexible_query_tool.py
3. Executar testes de integração
4. Validar taxa de sucesso > 80%

## Contexto Importante
- Projeto: BI comercial para Lojas Caçula (varejo)
- Stack: DuckDB + Gemini + FastAPI + SolidJS
- Objetivo: Melhorar de 30% → 90% taxa de sucesso
- Foco: Engenharia de prompts + correção de bugs
```

---

## 🚨 ATENÇÃO CRÍTICA

### NUNCA faça:
❌ Modificar lógica de negócio existente  
❌ Alterar estrutura de banco de dados  
❌ Refatorar código não mencionado no plano  
❌ Adicionar dependências não listadas  
❌ Ignorar validações de segurança (SQL injection)

### SEMPRE faça:
✅ Seguir EXATAMENTE as especificações do plano  
✅ Validar sintaxe antes de salvar arquivos  
✅ Adicionar comentários de checkpoint  
✅ Testar cada fase antes de avançar  
✅ Documentar mudanças em CHANGELOG.md

---

## 🎬 COMANDO DE EXECUÇÃO

**INICIE AGORA:**

```
Sou Claude Opus 4.5. Executarei o plano de implementação completo.

FASE 1: Corrigindo bugs...
[Pensando profundamente sobre cada correção...]

FASE 2: Criando novos arquivos...
[Analisando estrutura e dependências...]

FASE 3: Integrando componentes...
[Validando compatibilidade e testes...]

[INICIAR IMPLEMENTAÇÃO]
```

---

**VERSÃO:** 1.0  
**DATA:** 2026-02-04  
**AUTOR:** Análise técnica completa do BI Solution  
**COMPATÍVEL COM:** Antigravity IDE + Claude Opus 4.5 + LLMs alternativos
