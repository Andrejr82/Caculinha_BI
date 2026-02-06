# 📘 Guia de Uso Avançado - Agent Solution BI com Gemini 2.5 Pro

## 🎯 Objetivo

Este guia demonstra como aproveitar ao máximo as capacidades STEM do Gemini 2.5 Pro através de queries complexas e análises avançadas.

---

## 🧮 Análises Estatísticas Avançadas

### 1. Análise de Tendências com Regressão

**Objetivo:** Identificar se as vendas estão crescendo, decrescendo ou estáveis.

**Query Simples:**
```
Analise a tendência de vendas do produto 369947
```

**Query Avançada:**
```
Analise a tendência de vendas do produto 369947 nos últimos 90 dias 
usando regressão polinomial e me diga se devo aumentar o estoque
```

**O que o Gemini 2.5 Pro faz:**
1. Invoca `analise_regressao_vendas` com tipo "polinomial"
2. Calcula R² para avaliar qualidade do modelo
3. Identifica tendência (crescente/decrescente/estável)
4. Fornece previsão para 30 dias com intervalo de confiança
5. **Raciocina** sobre implicações para gestão de estoque

**Resposta Esperada:**
> "Analisei as vendas do produto 369947 usando regressão polinomial. A tendência é **crescente** com coeficiente angular de 0.5 vendas/dia. O modelo tem excelente qualidade (R² = 0.85), indicando alta confiabilidade. A previsão para os próximos 30 dias é de 1500 unidades (intervalo de confiança: 1400-1600).
>
> **Recomendação:** Sim, você deve aumentar o estoque gradualmente. Com tendência crescente confirmada e alta confiabilidade do modelo, sugiro aumentar o EOQ em 20% para evitar rupturas."

---

### 2. Detecção de Anomalias

**Objetivo:** Identificar picos ou quedas anormais nas vendas.

**Query Simples:**
```
Detecte vendas anormais do produto 369947
```

**Query Avançada:**
```
Detecte vendas anormais do produto 369947 nos últimos 90 dias com 
sensibilidade alta e explique possíveis causas
```

**O que o Gemini 2.5 Pro faz:**
1. Invoca `detectar_anomalias_vendas` com sensibilidade 3.0 (alta)
2. Calcula Z-scores para cada dia
3. Identifica outliers (picos e quedas)
4. **Raciocina** sobre possíveis causas

**Resposta Esperada:**
> "Detectei 3 anomalias nas vendas do produto 369947:
>
> 1. **15/01/2026** - Pico de vendas (250 unidades, Z-score: 3.2)
>    - 3.2 desvios padrão acima da média (100 unidades)
>    - **Possível causa:** Promoção, evento especial ou demanda sazonal
>
> 2. **20/01/2026** - Queda abrupta (30 unidades, Z-score: -2.8)
>    - **Possível causa:** Ruptura de estoque ou problema de fornecimento
>
> 3. **25/01/2026** - Pico moderado (180 unidades, Z-score: 2.5)
>
> **Recomendação:** Investigue o pico de 15/01. Se foi uma promoção bem-sucedida, considere replicar. Para a queda de 20/01, verifique se houve ruptura de estoque."

---

### 3. Análise de Correlação (Produtos Complementares)

**Objetivo:** Identificar produtos que vendem juntos.

**Query Simples:**
```
Quais produtos vendem junto com o produto 369947?
```

**Query Avançada:**
```
Analise a correlação de vendas entre os produtos 369947, 123456 e 789012 
e sugira estratégias de venda cruzada
```

**O que o Gemini 2.5 Pro faz:**
1. Invoca `analise_correlacao_produtos` com os 3 produtos
2. Calcula matriz de correlação
3. Identifica pares altamente correlacionados
4. Classifica como complementares ou substitutos
5. **Raciocina** sobre estratégias de venda

**Resposta Esperada:**
> "Analisei a correlação entre os 3 produtos:
>
> **Produtos Complementares:**
> - 369947 ↔ 123456: Correlação 0.85 (muito alta)
>   - Quando 369947 vende bem, 123456 também vende
>   - **Estratégia:** Criar bundle promocional (ex: "Compre 369947 + 123456 com 15% desconto")
>
> **Produtos Substitutos:**
> - 369947 ↔ 789012: Correlação -0.3 (negativa fraca)
>   - Quando 369947 vende, 789012 vende menos
>   - **Estratégia:** Posicionar como alternativas (ex: "Se 369947 está em falta, oferecemos 789012")
>
> **Ações Recomendadas:**
> 1. Criar display conjunto para 369947 e 123456
> 2. Treinar equipe para sugerir 123456 quando cliente comprar 369947
> 3. Monitorar estoque de ambos para evitar ruptura simultânea"

---

## 📦 Otimização de Estoque Avançada

### 4. EOQ com Múltiplas Restrições

**Objetivo:** Calcular quantidade ideal de compra considerando limitações reais.

**Query Simples:**
```
Calcule o EOQ para produto 369947
```

**Query Avançada:**
```
Calcule o EOQ para produto 369947 considerando:
- Orçamento disponível: R$ 5000
- Espaço no depósito: 500 unidades
- Lead time do fornecedor: 15 dias
- Queremos 95% de nível de serviço
```

**O que o Gemini 2.5 Pro faz:**
1. Invoca `calcular_eoq` com todos os parâmetros avançados
2. Calcula EOQ teórico (fórmula clássica)
3. Aplica restrições de orçamento e espaço
4. Calcula safety stock usando Z-score (95% = 1.65σ)
5. Determina ponto de reposição
6. **Raciocina** sobre trade-offs

**Resposta Esperada:**
> "Calculei o EOQ para o produto 369947 considerando suas restrições:
>
> **Resultados:**
> - EOQ teórico: 849 unidades
> - EOQ ajustado: **500 unidades** (limitado por espaço)
> - Safety stock: 50 unidades (nível de serviço 95%)
> - Ponto de reposição: 150 unidades
> - Custo total anual: R$ 2.500
>
> **Análise de Restrições:**
> - ✅ Orçamento (R$ 5000): Não limitante (500 unidades × R$ 8 = R$ 4000)
> - ❌ **Espaço (500 unidades): LIMITANTE** - Reduziu EOQ de 849 para 500
>
> **Trade-offs:**
> - Ao reduzir de 849 para 500, você terá:
>   - ➕ Mais pedidos por ano (24 vs 14)
>   - ➖ Custo total 15% maior (mais pedidos = mais custos fixos)
>   - ➕ Menor capital imobilizado
>
> **Recomendação:** Se possível, negocie mais espaço no depósito. Aumentar para 850 unidades reduziria custos em R$ 375/ano."

---

## 🔗 Queries Multi-Step (Raciocínio Complexo)

### 5. Análise Completa de Produto

**Query Avançada:**
```
Para o produto 369947:
1. Analise a tendência de vendas
2. Detecte anomalias
3. Se a tendência for crescente, calcule EOQ otimizado
4. Identifique produtos complementares
5. Sugira um plano de ação completo
```

**O que o Gemini 2.5 Pro faz:**
1. Executa 4 ferramentas sequencialmente
2. Combina resultados de forma coerente
3. **Raciocina** sobre implicações integradas
4. Cria plano de ação estratégico

**Resposta Esperada:**
> "Realizei uma análise completa do produto 369947:
>
> **1. Tendência de Vendas:**
> - Tendência: **Crescente** (0.5 vendas/dia)
> - Qualidade: Excelente (R² = 0.85)
> - Previsão 30 dias: 1500 unidades
>
> **2. Anomalias Detectadas:**
> - 1 pico em 15/01 (promoção bem-sucedida)
> - Sem quedas críticas
>
> **3. EOQ Otimizado:**
> - Como a tendência é crescente, recomendo EOQ de 849 unidades
> - Safety stock: 50 unidades (lead time 15 dias)
> - Ponto de reposição: 150 unidades
>
> **4. Produtos Complementares:**
> - Produto 123456 (correlação 0.85)
> - Oportunidade de venda cruzada
>
> **5. PLANO DE AÇÃO COMPLETO:**
>
> **Curto Prazo (Próximos 7 dias):**
> - [ ] Fazer pedido de 849 unidades (EOQ otimizado)
> - [ ] Criar bundle promocional com produto 123456
> - [ ] Investigar sucesso da promoção de 15/01 para replicar
>
> **Médio Prazo (Próximos 30 dias):**
> - [ ] Monitorar estoque diariamente (tendência crescente)
> - [ ] Treinar equipe para venda cruzada com 123456
> - [ ] Reavaliar EOQ se tendência acelerar
>
> **Longo Prazo (Próximos 90 dias):**
> - [ ] Negociar lead time menor com fornecedor (reduz safety stock)
> - [ ] Expandir espaço de armazenamento se possível
> - [ ] Analisar sazonalidade para ajustes futuros
>
> **Métricas de Sucesso:**
> - Taxa de ruptura < 5%
> - Giro de estoque > 12x/ano
> - Margem de contribuição > 25%"

---

## 🎯 Queries por Cenário de Negócio

### Cenário 1: Planejamento de Compras

**Query:**
```
Preciso planejar compras para o próximo mês. Analise os produtos 
369947, 123456 e 789012 e me diga quanto comprar de cada, 
considerando tendências e orçamento total de R$ 15000
```

---

### Cenário 2: Investigação de Queda de Vendas

**Query:**
```
As vendas do produto 369947 caíram 30% este mês. Detecte anomalias, 
analise a tendência e sugira possíveis causas e ações corretivas
```

---

### Cenário 3: Otimização de Mix de Produtos

**Query:**
```
Analise a correlação entre todos os produtos da categoria "Eletrônicos" 
e sugira quais produtos devo promover juntos para maximizar vendas
```

---

### Cenário 4: Previsão de Demanda Sazonal

**Query:**
```
Estamos entrando na volta às aulas. Analise a tendência de vendas 
dos produtos escolares nos últimos 2 anos e preveja a demanda para 
os próximos 60 dias
```

---

## 💡 Dicas para Queries Eficazes

### ✅ Boas Práticas

1. **Seja Específico:**
   - ❌ "Analise vendas"
   - ✅ "Analise a tendência de vendas do produto 369947 nos últimos 90 dias"

2. **Forneça Contexto:**
   - ❌ "Calcule EOQ"
   - ✅ "Calcule EOQ para produto 369947 considerando orçamento de R$ 5000"

3. **Peça Raciocínio:**
   - ❌ "Detecte anomalias"
   - ✅ "Detecte anomalias e explique possíveis causas"

4. **Combine Análises:**
   - ✅ "Analise tendência, detecte anomalias e sugira ações"

### ⚠️ Limitações

1. **Dados Históricos:** Análises requerem mínimo 30 dias de histórico
2. **Correlação ≠ Causalidade:** Alta correlação não implica causa-efeito
3. **Modelos Estatísticos:** R² < 0.6 indica baixa confiabilidade
4. **Anomalias:** Sensibilidade muito alta pode gerar falsos positivos

---

## 📚 Glossário de Termos Estatísticos

| Termo | Significado | Interpretação |
|-------|-------------|---------------|
| **R²** | Coeficiente de determinação | 0.85 = 85% da variação é explicada pelo modelo |
| **Z-score** | Desvios padrão da média | 2.5 = 2.5 desvios acima/abaixo da média |
| **Correlação** | Relação entre variáveis | 0.85 = forte relação positiva |
| **Safety Stock** | Estoque de segurança | Buffer para cobrir variações de demanda |
| **EOQ** | Economic Order Quantity | Quantidade ideal que minimiza custos |
| **Intervalo de Confiança** | Margem de erro | 95% = 95% de chance do valor real estar no intervalo |

---

## 🎓 Próximos Passos

1. **Pratique com Dados Reais:** Teste queries no Chat BI
2. **Combine Ferramentas:** Use múltiplas análises em uma query
3. **Interprete Resultados:** Foque no raciocínio, não apenas nos números
4. **Itere:** Refine queries baseado nas respostas do Gemini 2.5 Pro

---

**Desenvolvido por:** Agent BI Team  
**Versão:** 1.0.0  
**Data:** 2026-01-24
