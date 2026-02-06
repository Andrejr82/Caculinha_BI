# 🧪 Testes Manuais do Chat BI

## ⚠️ IMPORTANTE

Os testes automatizados falharam porque o endpoint `/chat` requer autenticação completa.

**Solução:** Testes manuais via interface web (mais confiável).

---

## 📋 CHECKLIST DE TESTES MANUAIS

### Pré-requisitos

1. ✅ Backend rodando (`python backend/main.py`)
2. ✅ Frontend rodando (`npm run dev` em `frontend-solid/`)
3. ✅ Fazer login no sistema
4. ✅ Abrir Chat BI

---

## 🧪 TESTE 1: Limites de Dados (35 UNEs) - CRÍTICO

**Query:**
```
gere um relatorio de vendas do produto 369947 em todas as lojas
```

**Verificar:**
- [ ] Gráfico mostra **35 UNEs** (não 10)
- [ ] Todas as lojas aparecem
- [ ] Dados completos sem truncamento
- [ ] Sem erro de limite

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 2: Contexto Expandido (30 mensagens)

**Sequência de Queries:**
```
1. "Qual o estoque do produto 369947?"
2. "E as vendas dos últimos 30 dias?"
3. "Quais lojas vendem mais?"
4. "Mostre um gráfico"
5. "Compare com o produto 123456"
6. "Qual a diferença percentual?"
7. "E o estoque atual?"
8. "Mostre tendência"
9. "Analise os últimos 60 dias"
10. "Quais são as rupturas?"
... (continuar até 15+ mensagens)
```

**Verificar:**
- [ ] Agente lembra contexto de mensagens anteriores
- [ ] Não perde referência ao produto
- [ ] Respostas coerentes até 30 mensagens
- [ ] Sem "esquecimento" de contexto

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 3: Respostas Completas (2000 chars)

**Query:**
```
Faça uma análise detalhada das vendas do produto 369947 incluindo:
- Vendas por loja
- Estoque atual
- Tendências dos últimos 90 dias
- Recomendações de compra
- Análise de ruptura
```

**Verificar:**
- [ ] Resposta completa (até 2000 chars)
- [ ] Todas as seções incluídas
- [ ] Sem truncamento em "..." após 500 chars
- [ ] Análise detalhada

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 4: Gráficos Expandidos (100 itens)

**Query:**
```
Mostre um gráfico de vendas dos top 50 produtos
```

**Verificar:**
- [ ] Gráfico com 50 produtos (não 10)
- [ ] Todos os dados visíveis
- [ ] Sem erro de limite
- [ ] Gráfico renderizado corretamente

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 5: Busca Expandida (100 resultados)

**Query:**
```
Liste todos os produtos do segmento "Varejo"
```

**Verificar:**
- [ ] Até 100 produtos retornados (não 10)
- [ ] Lista completa
- [ ] Sem truncamento
- [ ] Dados corretos

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 6: Schema Dinâmico

**Query:**
```
Quais colunas estão disponíveis no banco de dados?
```

**Verificar:**
- [ ] Lista de colunas essenciais
- [ ] Sem erro `AttributeError`
- [ ] Resposta correta
- [ ] Método `get_essential_columns()` funcionando

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 7: Funcionalidades Existentes (Regressão)

**Queries:**
```
1. "Qual o estoque da loja 1685?"
2. "Mostre vendas do produto 369947"
3. "Gere um gráfico de vendas por loja"
4. "Analise o segmento Varejo"
```

**Verificar:**
- [ ] Todas as funcionalidades anteriores funcionam
- [ ] Sem erros novos
- [ ] Performance mantida
- [ ] Sem regressões

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 8: Limites Máximos

**Query:**
```
Mostre dados de 1000 produtos
```

**Verificar:**
- [ ] Limite máximo de 500 respeitado
- [ ] Mensagem clara sobre limite
- [ ] Sem crash
- [ ] Resposta adequada

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## 🧪 TESTE 9: Tratamento de Erros

**Query:**
```
Mostre dados do produto 999999999
```

**Verificar:**
- [ ] Mensagem clara de "produto não encontrado"
- [ ] Sem crash
- [ ] Sugestão de produtos similares (opcional)
- [ ] Resposta amigável

**Resultado:**
- Status: ⏳ PENDENTE
- Observações: _______________

---

## ✅ CRITÉRIOS DE APROVAÇÃO

**Para aprovar commit:**
- ✅ 9/9 testes passaram
- ✅ Nenhuma regressão detectada
- ✅ Performance aceitável
- ✅ Sem erros no console

**Se falhar:**
- ❌ Documentar problema específico
- ❌ Corrigir
- ❌ Re-testar
- ❌ **NÃO fazer commit até 100% OK**

---

## 📊 RESUMO

**Testes Passados:** ___/9  
**Testes Falhados:** ___/9  
**Status Geral:** ⏳ PENDENTE

**Aprovado para Commit?** ⬜ SIM  ⬜ NÃO

**Observações Gerais:**
_______________________________________
_______________________________________
_______________________________________

---

## 🚀 PRÓXIMOS PASSOS

1. ⏳ Executar todos os 9 testes manualmente
2. ⏳ Documentar resultados neste arquivo
3. ⏳ Se todos passarem → Aprovar commit
4. ⏳ Se algum falhar → Debugar e corrigir
