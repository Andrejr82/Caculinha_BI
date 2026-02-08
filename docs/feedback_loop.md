# Feedback Loop: Calibração e Aprendizado Ativo

O sistema de Feedback Loop permite que a percepção do usuário final (subjetiva) seja utilizada para auditar o Auditor Automático (`QualityEvaluatorAgent`).

## 1. Fluxo de Dados

1.  **Geração:** O Agente de IA gera uma resposta com scores automáticos (ex: Groundedness: 0.9).
2.  **Exposição:** O Frontend recebe o `request_id` no cabeçalho `X-Request-Id`.
3.  **Coleta:** O usuário clica em "Útil" ou "Não Útil" (e opcionalmente comenta).
4.  **Submissão:** O frontend envia `POST /api/v1/feedback` com o `request_id` e o rating.
5.  **Correlação:** No backend, o feedback é persistido no SQLite correlacionado ao `request_id`.

## 2. Uso Estratégico do Feedback

### Calibração de Prompts
Se o `QualityEvaluatorAgent` der Groundedness 1.0 para uma resposta, mas o usuário der nota 1/5 reclamando de erro nos dados, isso indica que o prompt de auditoria precisa ser mais rigoroso ou que o extrator de contexto falhou.

### Active Learning (Futuro)
Os feedbacks negativos com comentários técnicos podem ser filtrados para criar um dataset de fine-tuning para o modelo de julgamento.

## 3. Estrutura de Armazenamento (SQLite)

```sql
TABLE feedbacks {
  request_id TEXT PRIMARY KEY,
  rating INTEGER, -- 1 a 5
  comment TEXT,
  created_at DATETIME
}
```
