# 🧪 Plano de Testes: Chat BI

## 🎯 Objetivo
Validar que todas as correções de limitações funcionam corretamente no Chat BI antes do commit.

---

## 📋 TESTES CRÍTICOS

### 1. Teste de Limites de Dados ✅

**Objetivo:** Verificar que o produto 369947 mostra TODAS as 35 UNEs

**Comando:**
```
gere um relatorio de vendas do produto 369947 em todas as lojas
```

**Resultado Esperado:**
- ✅ Gráfico com 35 UNEs (não 10)
- ✅ Todas as lojas aparecem
- ✅ Dados completos sem truncamento

**Status:** ⏳ PENDENTE

---

### 2. Teste de Contexto Expandido ✅

**Objetivo:** Verificar que o agente mantém contexto por 30 mensagens

**Comandos:**
```
1. "Qual o estoque do produto 369947?"
2. "E as vendas dos últimos 30 dias?"
3. "Quais lojas vendem mais?"
4. "Mostre um gráfico"
5. "E o produto 123456?" (continuar até 15+ mensagens)
```

**Resultado Esperado:**
- ✅ Agente lembra contexto de mensagens anteriores
- ✅ Não perde referência ao produto
- ✅ Respostas coerentes até 30 mensagens

**Status:** ⏳ PENDENTE

---

### 3. Teste de Respostas Completas ✅

**Objetivo:** Verificar que respostas não são truncadas em 500 chars

**Comando:**
```
Faça uma análise detalhada das vendas do produto 369947 incluindo:
- Vendas por loja
- Estoque atual
- Tendências
- Recomendações
```

**Resultado Esperado:**
- ✅ Resposta completa (até 2000 chars)
- ✅ Todas as seções incluídas
- ✅ Sem truncamento prematuro

**Status:** ⏳ PENDENTE

---

### 4. Teste de Gráficos Expandidos ✅

**Objetivo:** Verificar que gráficos mostram até 100 itens

**Comando:**
```
Mostre um gráfico de vendas dos top 50 produtos
```

**Resultado Esperado:**
- ✅ Gráfico com 50 produtos (não 10)
- ✅ Todos os dados visíveis
- ✅ Sem erro de limite

**Status:** ⏳ PENDENTE

---

### 5. Teste de Busca Expandida ✅

**Objetivo:** Verificar que busca retorna até 100 resultados

**Comando:**
```
Busque todos os produtos do segmento "Varejo"
```

**Resultado Esperado:**
- ✅ Até 100 produtos retornados (não 10)
- ✅ Lista completa
- ✅ Sem truncamento

**Status:** ⏳ PENDENTE

---

### 6. Teste de Schema Dinâmico ✅

**Objetivo:** Verificar que `get_essential_columns()` funciona

**Comando:**
```
Quais colunas estão disponíveis no banco de dados?
```

**Resultado Esperado:**
- ✅ Lista de colunas essenciais
- ✅ Sem erro `AttributeError`
- ✅ Resposta correta

**Status:** ⏳ PENDENTE

---

## 🔧 TESTES DE REGRESSÃO

### 7. Teste de Funcionalidades Existentes

**Comandos:**
```
1. "Qual o estoque da loja 1685?"
2. "Mostre vendas do produto 369947"
3. "Gere um gráfico de vendas por loja"
4. "Analise o segmento Varejo"
```

**Resultado Esperado:**
- ✅ Todas as funcionalidades anteriores funcionam
- ✅ Sem erros novos
- ✅ Performance mantida

**Status:** ⏳ PENDENTE

---

## 🚨 TESTES DE ERRO

### 8. Teste de Limites Máximos

**Comando:**
```
Busque dados com limite de 1000 itens
```

**Resultado Esperado:**
- ✅ Limite máximo de 500 respeitado
- ✅ Mensagem clara sobre limite
- ✅ Sem crash

**Status:** ⏳ PENDENTE

---

### 9. Teste de Produto Inexistente

**Comando:**
```
Mostre dados do produto 999999999
```

**Resultado Esperado:**
- ✅ Mensagem clara de "produto não encontrado"
- ✅ Sem crash
- ✅ Sugestão de produtos similares

**Status:** ⏳ PENDENTE

---

## 📊 CHECKLIST DE VALIDAÇÃO

- [ ] Backend reiniciado com novas correções
- [ ] Frontend conectado ao backend
- [ ] Teste 1: Limites de dados (35 UNEs)
- [ ] Teste 2: Contexto expandido (30 msgs)
- [ ] Teste 3: Respostas completas (2000 chars)
- [ ] Teste 4: Gráficos expandidos (100 itens)
- [ ] Teste 5: Busca expandida (100 resultados)
- [ ] Teste 6: Schema dinâmico
- [ ] Teste 7: Funcionalidades existentes
- [ ] Teste 8: Limites máximos
- [ ] Teste 9: Tratamento de erros

---

## ✅ CRITÉRIOS DE APROVAÇÃO

**Para aprovar commit:**
- ✅ 9/9 testes passaram
- ✅ Nenhuma regressão detectada
- ✅ Performance aceitável
- ✅ Sem erros no console

**Se falhar:**
- ❌ Identificar problema
- ❌ Corrigir
- ❌ Re-testar
- ❌ Não fazer commit até 100% OK

---

## 🎯 COMO EXECUTAR

### Passo 1: Reiniciar Backend

```bash
cd backend
python main.py
```

**Aguardar:** "Application startup complete"

### Passo 2: Abrir Chat BI

```
http://localhost:3000
```

### Passo 3: Executar Testes

Seguir comandos acima um por um e marcar resultados.

### Passo 4: Documentar Resultados

Anotar qualquer problema encontrado neste arquivo.

---

## 📝 NOTAS

- Testes devem ser executados em ordem
- Documentar qualquer comportamento inesperado
- Se encontrar bug, parar e reportar
- Não fazer commit até TODOS os testes passarem

---

## 🚀 PRÓXIMOS PASSOS

1. ⏳ Executar testes no Chat BI
2. ⏳ Documentar resultados
3. ⏳ Corrigir problemas (se houver)
4. ⏳ Re-testar
5. ⏳ Aprovar commit quando 100% OK
