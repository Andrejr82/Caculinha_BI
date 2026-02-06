# Regras de Negócio UNE (Unidade de Negócio)

Este documento detalha as regras de negócio implementadas no sistema Agent Solution BI, especificamente focadas nas operações de UNE (Unidade de Negócio), Abastecimento e Transferências.

---

## 1. Glossário

- **UNE (Unidade de Negócio)**: Representa uma loja física ou ponto de estoque. Identificada por `une_id`.
- **Linha Verde (LV)**: Nível ideal de estoque para um determinado produto em uma UNE. É a meta de estoque.
- **Média Considerada LV**: Preço médio de venda ou custo utilizado como referência para cálculos de margem (MC).
- **Margem de Contribuição (MC)**: Lucro obtido por unidade vendida, descontados os custos variáveis.
- **Ruptura**: Situação em que o estoque de um produto chega a zero ou nível crítico, impedindo vendas.

---

## 2. Cálculos e Métricas

### 2.1 Margem de Contribuição (MC) por Produto
A MC é calculada preferencialmente usando a `media_considerada_lv` como base de preço.

**Fórmula:**
```python
Se media_considerada_lv existe:
    MC = media_considerada_lv * 0.25  (Margem estimada de 25%)
Senão, se vendas_diarias existe:
    MC = vendas_diarias * 0.20        (Margem estimada de 20% sobre volume)
```

### 2.2 Preço Final
O preço final de venda sugerido considera o preço base e impostos/margens adicionais.

**Fórmula:**
```python
Preço Final = Preço Base (media_considerada_lv) * 1.10 (Margem) * 1.05 (Imposto)
```

### 2.3 Necessidade de Abastecimento
Determina quanto estoque falta para atingir a meta (Linha Verde).

**Fórmula:**
```python
Necessidade = Max(0, Linha Verde - Estoque Atual)
```

### 2.4 Dias para Ruptura (Cobertura)
Estima em quantos dias o estoque atual acabará, dado o ritmo de vendas atual.

**Fórmula:**
```python
Dias Cobertura = Estoque Atual / Vendas Diárias
```

---

## 3. Classificação de Criticidade

O sistema classifica a urgência de reabastecimento em três níveis, baseando-se no estoque atual em relação à Linha Verde (LV) e na cobertura de dias.

| Nível     | Critério de Estoque       | Critério de Cobertura | Ação Recomendada         |
| :-------- | :------------------------ | :-------------------- | :----------------------- |
| **URGENTE** | `< 50% da LV`             | `< 3 dias`            | Transferência imediata   |
| **ALTA**    | `< 100% da LV`            | `< 7 dias`            | Planejar reabastecimento |
| **NORMAL**  | `>= 100% da LV`           | `>= 7 dias`           | Monitorar                |

---

## 4. Regras de Transferência entre UNEs

### 4.1 Validação de Transferência
Antes de permitir uma transferência de produto da `UNE Origem` para `UNE Destino`, o sistema verifica:

1.  **Disponibilidade na Origem**:
    - `Estoque Origem >= Quantidade Solicitada`
    - *Bloqueio*: Impede a transferência se não houver saldo suficiente.

2.  **Capacidade no Destino (Alerta de Excesso)**:
    - Verifica se o destino ficará sobrecarregado.
    - `Estoque Futuro Destino = Estoque Atual Destino + Quantidade Solicitada + Transferências Pendentes`
    - *Alerta*: Se `Estoque Futuro Destino > 1.2 * Linha Verde Destino` (20% acima da meta), o sistema emite um alerta de "Excesso de Estoque", mas permite a operação (soft warning).

### 4.2 Sugestão Automática de Transferência
O sistema proativamente sugere transferências para resolver rupturas críticas.

**Algoritmo:**
1.  Identificar produtos com **Ruptura Crítica** (URGENTE/ALTA).
2.  Para cada produto em ruptura (Destino):
    - Buscar outras UNEs que possuam o mesmo produto (Origem Potencial).
    - Filtrar UNEs onde:
        - `UNE Origem != UNE Destino`
        - `Estoque Origem > Necessidade do Destino` (garante que a origem tem sobras).
3.  Validar a transferência usando as regras de 4.1.
4.  Gerar sugestão se validado com sucesso.
5.  Priorizar sugestões por criticidade (URGENTE primeiro).

---

## 5. Implementação Técnica

As regras acima estão implementadas em `backend/app/core/tools/une_tools.py` e são expostas através de ferramentas para os agentes de IA (`validar_transferencia_produto`, `sugerir_transferencias_automaticas`, etc.).
