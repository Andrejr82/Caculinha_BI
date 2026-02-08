# Documentação: Catalog Builder & Transformação

O `CatalogBuilderService` é responsável por transformar os dados brutos do Parquet em um Catálogo Canônico otimizado para busca semântica.

## 1. Pipeline de Transformação
O processo segue um fluxo vetorizado via Pandas para garantir performance em larga escala (1M+ registros).

1.  **Extração:** O `ProductSourceParquetAdapter` lê as colunas do arquivo original.
2.  **Normalização (PTBRNormalizer):**
    - Conversão para lowercase.
    - Remoção de acentos (NFD normalization).
    - Remoção de caracteres especiais.
    - Limpeza de espaços extras.
3.  **Enriquecimento Semântico:**
    - Geração do campo `searchable_text`: Concatenação de `nome_canonical` + `marca` + `categoria`.
    - Atribuição de `catalog_version` para controle de rollback.
4.  **Persistência (DuckDBCatalogRepository):**
    - Inserção em lote (bulk insert) no banco de dados DuckDB local.

## 2. Performance e Escalabilidade
| Métrica | Resultado (1.1M registros) |
|---------|----------------------------|
| Tempo de Extração | ~15 segundos |
| Tempo de Transformação | ~10 segundos |
| Tempo de Persistência | ~60 segundos |
| **Total Build Time** | **< 2 minutos** |

## 3. Versionamento
Cada rebuild gera um novo `catalog_version` (ex: `cat-939081b9`). O sistema mantém a versão anterior intacta, permitindo rollback instantâneo se a nova versão apresentar problemas de qualidade.

## 4. Como Executar
```bash
$env:PYTHONPATH="."; python scripts/run_full_rebuild.py
```
O script cuidará de todo o processo e ativará a nova versão automaticamente.
