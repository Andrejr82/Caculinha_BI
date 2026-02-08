# Especificação Técnica: Response Quality Gate

Este documento define os padrões de qualidade e governança para as respostas geradas pela plataforma Caculinha BI Enterprise.

## 1. Definições de Qualidade no Varejo

No contexto do Caculinha BI, uma resposta de alta qualidade deve ser **acionável**, **verídica** e **contextualizada**.

### Pilares de Avaliação:
*   **Qualidade Linguística (quality_score):** Clareza, tom profissional, ausência de erros gramaticais e aderência ao padrão Context7.
*   **Utilidade Prática (utility_score):** A resposta ajuda na tomada de decisão? Contém números, tendências ou sugestões de ação?
*   **Groundedness / RAG (groundedness_score):** A resposta é baseada estritamente nos dados retornados pelas ferramentas? Evita alucinações sobre colunas ou valores inexistentes?

## 2. Matriz de Scores e Thresholds

Cada resposta recebe três notas de **0.0 a 1.0**.

| Score | Descrição |
|-------|-----------|
| **quality_score** | Coerência e formato da narrativa. |
| **utility_score** | Valor agregado para o gestor de UNE/CD. |
| **groundedness_score** | Fidelidade aos dados do Parquet/RAG. |

### Configuração de Thresholds:

| Status | Condição | Ação |
|--------|----------|------|
| **OK** | Todos os scores >= 0.8 | Liberação total da resposta. |
| **WARNING** | Qualquer score entre 0.5 e 0.79 | Libera com alerta de "baixa confiança" no metadata. |
| **BLOCK** | Qualquer score < 0.5 | Substitui por resposta segura (Safe Response). |

## 3. Estratégias de Fallback e Memória

A integração com a camada de memória depende da classificação final:

| Classificação | Persistência em Memória | Entrega ao Usuário |
|---------------|-------------------------|-------------------|
| **OK**        | Sim                     | Resposta Original |
| **WARNING**   | Sim (com tag warning)   | Resposta Original + Metadata de Alerta |
| **BLOCK**     | Não                     | Resposta Cautelosa (Safe Response) |

---

## 6. Persona do Avaliador (Judge Persona)

O `QualityEvaluatorAgent` opera sob a persona de um **Auditor de Dados de Varejo Senior**.
Seu objetivo não é apenas verificar se o texto é bonito, mas se os números citados batem com os fatos fornecidos pelo RAG.

**Diretrizes de Auditoria:**
- **Zero Tolerância para Inventar Colunas:** Se o RAG retornar "PRECO" e a IA falar "Margem de Contribuição", o `groundedness_score` deve cair.
- **Foco em Decisão:** Uma resposta que termina com "Como posso ajudar mais?" é menos útil que uma que termina com "Recomendo verificar o estoque da Loja 1685 devido à ruptura detectada".

## 7. Esquema de Saída (JSON Schema)

O avaliador deve retornar obrigatoriamente um JSON estruturado para processamento programático:

```json
{
  "scores": {
    "quality": 0.95,
    "utility": 0.80,
    "groundedness": 1.0
  },
  "reasoning": {
    "quality": "Texto bem estruturado seguindo Context7.",
    "utility": "Sugeriu conferência de estoque, mas faltou citar o valor exato da quebra.",
    "groundedness": "Todos os valores citados (estoque=10) constam no documento RAG."
  },
  "final_decision": "OK"
}
```

---

## 🏁 Checklist de Aceite (Quality Gate)

- [ ] Persona de Auditor Senior aplicada ao prompt do Avaliador.
- [ ] O Agente Avaliador gera JSON estruturado com scores e justificativas.
- [ ] Respostas com dados inventados recebem `groundedness_score` < 0.3.
- [ ] O Bloqueio interrompe a gravação na memória (Memory Shield).
- [ ] Os scores e reasoning aparecem nos logs JSON detalhados.
- [ ] O endpoint de feedback persiste as notas e o `request_id` correlacionado.
