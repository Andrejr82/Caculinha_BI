# Referência de Esquema do Parquet - admmat.parquet

## INSTRUÇÕES PARA EDIÇÃO:
1. **Edite as descrições** para refletir o uso real de cada coluna
2. **Marque com ✓** as colunas que estão sendo usadas corretamente
3. **Marque com ❌** as colunas que precisam correção
4. **Adicione notas** sobre regras de negócio específicas

---

## COLUNAS DE IDENTIFICAÇÃO

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `id` | Int | ID único do registro | ✓ | Chave primária |
| `UNE` | String | Código da unidade/loja | ✓ | Usado em filtros e agrupamentos |
| `UNE_NOME` | String | Nome da unidade/loja | | |
| `PRODUTO` | String | Código do produto | ✓ | Chave de produto |
| `TIPO` | String | Tipo do produto | | |
| `NOME` | String | Nome/descrição do produto | ✓ | Usado em exibições |
| `EMBALAGEM` | String | Descrição da embalagem | | |
| `EAN` | String | Código de barras EAN | | |

---

## COLUNAS DE CLASSIFICAÇÃO

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `NOMESEGMENTO` | String | Nome do segmento | ✓ | Usado em filtros e análises |
| `NOMECATEGORIA` | String | Nome da categoria | | |
| `NOMEGRUPO` | String | Nome do grupo | | |
| `NOMESUBGRUPO` | String | Nome do subgrupo | | |
| `NOMEFABRICANTE` | String | Nome do fabricante | | |

---

## COLUNAS DE ESTOQUE

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ESTOQUE_CD` | Float | **Estoque no Centro de Distribuição** | ✓ | Usado em ruptura: ESTOQUE_CD = 0 |
| `ESTOQUE_UNE` | Float | **Estoque na Loja/Unidade** | ✓ | Estoque real da loja |
| `ESTOQUE_LV` | Float | **Linha Verde (MC - Média Considerada)** | ✓ | Parâmetro de referência, não é venda |
| `ESTOQUE_GONDOLA_LV` | Float | Estoque mínimo na gôndola | | |
| `ESTOQUE_ILHA_LV` | Float | Estoque mínimo na ilha | | |
| `ULTIMO_INVENTARIO_UNE` | Date | Data do último inventário | | |

---

## COLUNAS DE PONTO DE PEDIDO E PARÂMETROS

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `PONTO_PEDIDO_LV` | Float | Ponto de pedido (Linha Verde) | ✓ | Quando atingido, aciona reposição |
| `MEDIA_CONSIDERADA_LV` | Float | Média considerada para Linha Verde | | MC - Média Considerada |
| `MEDIA_TRAVADA` | String | Indicador de média travada | | |
| `LEADTIME_LV` | Int | Lead time de reposição | | Tempo de espera |
| `EXPOSICAO_MINIMA` | Float | Exposição mínima do produto | | |
| `EXPOSICAO_MINIMA_UNE` | Float | Exposição mínima por UNE | | |
| `EXPOSICAO_MAXIMA_UNE` | Float | Exposição máxima por UNE | | |

---

## COLUNAS DE VENDAS - MENSAL

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `MES_12` | Float | Vendas mês 12 (mais antigo) | | |
| `MES_11` | Float | Vendas mês 11 | | |
| `MES_10` | Float | Vendas mês 10 | | |
| `MES_09` | Float | Vendas mês 9 | | |
| `MES_08` | Float | Vendas mês 8 | | |
| `MES_07` | Float | Vendas mês 7 | | |
| `MES_06` | Float | Vendas mês 6 | | |
| `MES_05` | Float | Vendas mês 5 | | |
| `MES_04` | Float | Vendas mês 4 | | |
| `MES_03` | Float | Vendas mês 3 | | |
| `MES_02` | Float | Vendas mês 2 | ✓ | Usado para calcular crescimento |
| `MES_01` | Float | Vendas mês 1 (mais recente) | ✓ | Mês mais recente, usado em análises |
| `MES_PARCIAL` | Float | Vendas do mês parcial (atual) | | |

---

## COLUNAS DE VENDAS - SEMANAL

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `SEMANA_ANTERIOR_5` | Float | Vendas semana -5 | | |
| `FREQ_SEMANA_ANTERIOR_5` | Int | Frequência de vendas semana -5 | | |
| `QTDE_SEMANA_ANTERIOR_5` | Float | Quantidade vendida semana -5 | | |
| `MEDIA_SEMANA_ANTERIOR_5` | Float | Média de vendas semana -5 | | |
| `SEMANA_ANTERIOR_4` | Float | Vendas semana -4 | | |
| `FREQ_SEMANA_ANTERIOR_4` | Int | Frequência de vendas semana -4 | | |
| `QTDE_SEMANA_ANTERIOR_4` | Float | Quantidade vendida semana -4 | | |
| `MEDIA_SEMANA_ANTERIOR_4` | Float | Média de vendas semana -4 | | |
| `SEMANA_ANTERIOR_3` | Float | Vendas semana -3 | | |
| `FREQ_SEMANA_ANTERIOR_3` | Int | Frequência de vendas semana -3 | | |
| `QTDE_SEMANA_ANTERIOR_3` | Float | Quantidade vendida semana -3 | | |
| `MEDIA_SEMANA_ANTERIOR_3` | Float | Média de vendas semana -3 | | |
| `SEMANA_ANTERIOR_2` | Float | Vendas semana -2 | | |
| `FREQ_SEMANA_ANTERIOR_2` | Int | Frequência de vendas semana -2 | | |
| `QTDE_SEMANA_ANTERIOR_2` | Float | Quantidade vendida semana -2 | | |
| `MEDIA_SEMANA_ANTERIOR_2` | Float | Média de vendas semana -2 | | |
| `SEMANA_ATUAL` | Float | Vendas semana atual | | |
| `FREQ_SEMANA_ATUAL` | Int | Frequência de vendas semana atual | ✓ | Usado em filtros |
| `QTDE_SEMANA_ATUAL` | Float | Quantidade vendida semana atual | ✓ | Usado em análises recentes |
| `MEDIA_SEMANA_ATUAL` | Float | Média de vendas semana atual | | |

---

## COLUNAS DE VENDAS - PERÍODO

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `VENDA_30DD` | Float | **Vendas últimos 30 dias** | ✓ | Principal métrica de vendas |
| `FREQ_ULT_SEM` | Int | Frequência última semana | | |

---

## COLUNAS DE CLASSIFICAÇÃO ABC

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ABC_UNE_MES_04` | String | Classificação ABC mês 4 | | |
| `ABC_UNE_MES_03` | String | Classificação ABC mês 3 | | |
| `ABC_UNE_MES_02` | String | Classificação ABC mês 2 | | |
| `ABC_UNE_MES_01` | String | Classificação ABC mês 1 | | |
| `ABC_UNE_30DD` | String | Classificação ABC 30 dias | | |
| `ABC_CACULA_90DD` | String | Classificação ABC Cacula 90 dias | | |
| `ABC_UNE_30XABC_CACULA_90DD` | String | Combinação ABC UNE 30 x Cacula 90 | | |

---

## COLUNAS DE ENTRADA/RECEBIMENTO - CD

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ULTIMA_ENTRADA_DATA_CD` | Date | Data da última entrada no CD | | |
| `ULTIMA_ENTRADA_QTDE_CD` | Float | Quantidade da última entrada CD | | |
| `ULTIMA_ENTRADA_CUSTO_CD` | Float | Custo da última entrada CD | | Pode ser usado para valor estoque |

---

## COLUNAS DE ENTRADA/RECEBIMENTO - UNE

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ULTIMA_ENTRADA_DATA_UNE` | Date | Data da última entrada na loja | | |
| `ULTIMA_ENTRADA_QTDE_UNE` | Float | Quantidade da última entrada loja | | |
| `ULTIMA_VENDA_DATA_UNE` | Date | Data da última venda | | |

---

## COLUNAS DE ENDEREÇAMENTO

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ENDERECO_RESERVA` | String | Endereço de reserva | | |
| `ENDERECO_LINHA` | String | Endereço na linha | | |

---

## COLUNAS DE SOLICITAÇÃO/TRANSFERÊNCIA

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `SOLICITACAO_PENDENTE` | String | Código da solicitação pendente | | |
| `SOLICITACAO_PENDENTE_DATA` | Date | Data da solicitação pendente | | |
| `SOLICITACAO_PENDENTE_QTDE` | Float | Quantidade solicitada pendente | | |
| `SOLICITACAO_PENDENTE_SITUACAO` | String | Situação da solicitação | | |
| `ROMANEIO_SOLICITACAO` | String | Número romaneio solicitação | | |
| `ROMANEIO_ENVIO` | String | Número romaneio envio | | |

---

## COLUNAS DE PICKING

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `PICKLIST` | String | Número da picklist | | |
| `PICKLIST_SITUACAO` | String | Situação da picklist | | |
| `PICKLIST_CONFERENCIA` | String | Conferência da picklist | | |

---

## COLUNAS DE VOLUME/NOTA FISCAL

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `ULTIMO_VOLUME` | String | Número do último volume | | |
| `VOLUME_QTDE` | Float | Quantidade no volume | | |
| `NOTA` | String | Número da nota fiscal | | |
| `SERIE` | String | Série da nota fiscal | | |
| `NOTA_EMISSAO` | Date | Data de emissão da nota | | |

---

## COLUNAS DE EMBALAGEM

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `QTDE_EMB_MASTER` | Float | Quantidade na embalagem master | | |
| `QTDE_EMB_MULTIPLO` | Float | Múltiplo de embalagem | | |
| `LIQUIDO_38` | Float | Peso líquido (38?) | | Verificar unidade |

---

## COLUNAS DE CONTROLE

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `PROMOCIONAL` | String | Indicador de produto promocional | | |
| `FORALINHA` | String | Indicador de produto fora de linha | | |

---

## COLUNAS DE TIMESTAMP

| Coluna | Tipo | Descrição | Status | Notas |
|--------|------|-----------|--------|-------|
| `created_at` | Timestamp | Data/hora de criação do registro | | |
| `updated_at` | Timestamp | Data/hora da última atualização | ✓ | Usado em ordenações |

---

## REGRAS DE NEGÓCIO IMPORTANTES

### 1. **Ruptura Crítica**
```
Condição: ESTOQUE_CD = 0 AND ESTOQUE_UNE < ESTOQUE_LV AND VENDA_30DD > 0
```
- `ESTOQUE_CD = 0`: Sem estoque no centro de distribuição
- `ESTOQUE_UNE < ESTOQUE_LV`: Estoque da loja abaixo da Linha Verde (MC)
- `VENDA_30DD > 0`: Produto com vendas nos últimos 30 dias

### 2. **Linha Verde (MC - Média Considerada)**
- `ESTOQUE_LV`: É um **parâmetro de referência**, NÃO é venda de loja
- Também conhecida como **MC (Média Considerada)**
- Define o nível ideal de estoque
- Quando `ESTOQUE_UNE < ESTOQUE_LV`, há risco de ruptura

### 3. **Cálculo de Crescimento**
```python
crescimento = ((MES_01 - MES_02) / MES_02) * 100
```

### 4. **Top Produtos**
Baseado em `VENDA_30DD` (vendas últimos 30 dias)

---

## COLUNAS QUE NÃO EXISTEM (EVITAR USO)

❌ `ESTOQUE_LOJA` - Use `ESTOQUE_UNE`
❌ `LINHA_VERDE` - Use `ESTOQUE_LV`
❌ `VENDA_LOJA` - Use `VENDA_30DD` ou `MES_01`

---

## PRÓXIMOS PASSOS

1. **Edite este arquivo** com as descrições corretas de cada coluna
2. **Adicione regras de negócio** específicas na seção de regras
3. **Marque status** das colunas (✓ usadas corretamente, ❌ precisam correção)
4. **Envie de volta** para eu atualizar toda a estrutura do projeto

---

**Última atualização**: 2025-12-06
**Versão do Parquet**: admmat.parquet (100 colunas)
