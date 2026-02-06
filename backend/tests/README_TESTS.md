# Testes de Integridade de Dados Reais (Metrics-First)

Este documento descreve como executar os testes de integridade que verificam se o Agente está respeitando o "Truth Contract" (Contrato da Verdade) e utilizando dados reais do `admmat.parquet`.

## 🎯 Objetivo
Garantir que:
1.  O Agente recupere os números exatos do banco de dados (DuckDB).
2.  A narrativa gerada contenha esses números (sem alucinações).
3.  O contexto não vaze entre sessões (Entity Carry-Over).

## 🛠️ Ferramenta de Verificação
O script `backend/tests/verify_real_data_integrity.py` é a ferramenta principal.

### Como Executar
```bash
python backend/tests/verify_real_data_integrity.py
```

### O que ele testa?
1.  **Vendas Globais:** Pergunta o total de vendas e compara com `SELECT sum(VENDA_30DD)`.
2.  **Vendas por Loja:** Escolhe uma loja aleatória (ex: 2586), pergunta o total dela e valida.
3.  **Ranking de Segmentos:** Pergunta qual segmento mais vende e verifica se o Agente identifica o campeão.

### Interpretação dos Resultados
- **✅ PASS:** O número/nome encontrado na narrativa corresponde ao banco de dados (com tolerância de arredondamento).
- **❌ FAIL:** O Agente alucinou um número, errou a entidade ou não respondeu a pergunta.
- **⚠️ WARNING:** O número está próximo mas fora da tolerância, ou houve um problema de formatação.

## 🐛 Bugs Identificados e Corrigidos (Janeiro 2026)
- **Context Leakage:** Identificado que o `QueryInterpreter` mantinha estado entre requisições se a sessão não fosse explicitamente renovada. O teste agora força uma nova sessão para cada caso.
- **Intent Classification:** Identificado que perguntas de "Ranking" podem cair em "Vendas Gerais" e não trazer os dados de segmentos necessários. Isso é um gap funcional a ser melhorado no `MetricsCalculator`.

## 🏗️ Estrutura do Teste
```python
class TruthContractVerifier:
    def verify_case(self, ...):
        # 1. Busca a Verdade (SQL direto no Parquet)
        truth = duckdb.query(sql)
        
        # 2. Pergunta ao Agente (Simulação completa do ChatServiceV3)
        response = agent.ask(question)
        
        # 3. Compara (Regex + Fuzzy Matching)
        assert truth in response
```

## 🔄 Testes de Integração (Backend)
Testam os componentes `MetricsCalculator` e `ContextBuilder` isoladamente usando dados reais (Parquet) mas sem chamar a LLM (economia de tokens).

### Como Executar
```bash
cd backend
python -m pytest tests/integration/test_chat_metrics_integration.py -v
```

## 🖥️ Testes End-to-End (Frontend)
Utilizam **Playwright** para simular um usuário real no navegador. Requer que o Backend e Frontend estejam rodando localmente.

### Pré-requisitos
- Backend rodando em `http://localhost:8000`
- Frontend rodando em `http://localhost:3000`
- Instalar dependências: `pip install playwright pytest-playwright && playwright install`

### Como Executar
```bash
cd backend
pytest tests/e2e/test_chat_flow.py
```
