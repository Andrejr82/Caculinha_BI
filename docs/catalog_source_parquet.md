# Documentação: Fonte de Dados Parquet (`ProductSourceParquetAdapter`)

O sistema utiliza o arquivo `admmat.parquet` como fonte primária para a construção do Catálogo Canônico.

## 1. Localização e Arquitetura
- **Path:** `backend/data/parquet/admmat.parquet` (configurável no `.env`).
- **Motor:** DuckDB (In-process SQL engine).
- **Interface:** `IProductSourcePort`.

## 2. Esquema de Extração e Mapeamento

O adaptador realiza um mapeamento dinâmico para garantir que o sistema não quebre caso colunas secundárias desapareçam.

| Campo Destino | Coluna Parquet Original | Fallback (se ausente) |
|---------------|-------------------------|-----------------------|
| `product_id` | `PRODUTO` | (Obrigatório) |
| `name_raw` | `NOME` | (Obrigatório) |
| `brand` | `MARCA` | `''` |
| `dept` | `NOMESEGMENTO` | `''` |
| `category` | `NOMEGRUPOMAT` | `''` |
| `subcategory` | `NOMESUBGRUPOMAT` | `''` |
| `family` | `NOMEFAMILIAMAT` | `''` |
| `updated_at` | `updated_at` | `''` |

## 3. Performance
- **Full Load:** A extração de 1.1M+ de registros leva aproximadamente 3-5 segundos via DuckDB.
- **Incremental:** Filtra por `updated_at` para atualizações rápidas do catálogo.

## 4. Uso
```python
adapter = ProductSourceParquetAdapter(path)
data = await adapter.load_full_catalog()
```
