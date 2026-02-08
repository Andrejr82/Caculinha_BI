# Especificação Técnica: Catálogo Semântico de Produtos

Este documento define a estrutura e o processo de derivação do Catálogo Canônico de Produtos a partir da base Parquet operacional.

## 1. Definição do Catálogo Canônico (Source-of-Truth Derivado)

O catálogo será extraído do arquivo `admmat.parquet` e persistido em uma estrutura otimizada para busca (DuckDB).

### 1.1 Esquema de Dados (Entidade Canonical)

| Campo | Origem Parquet | Tipo | Descrição |
|-------|----------------|------|-----------|
| `product_id` | `PRODUTO` | BIGINT | ID único do produto |
| `name_raw` | `NOME` | VARCHAR | Nome original na base |
| `name_canonical` | (derivado) | VARCHAR | Nome normalizado e limpo |
| `brand` | `MARCA` | VARCHAR | Marca do produto |
| `dept` | `NOMESEGMENTO` | VARCHAR | Departamento/Segmento |
| `category` | `NOMEGRUPOMAT` | VARCHAR | Categoria/Grupo |
| `subcategory` | `NOMESUBGRUPOMAT` | VARCHAR | Subcategoria/Subgrupo |
| `searchable_text` | (composto) | TEXT | Texto concatenado para indexação (Nome + Marca + Categ) |
| `attributes_json` | `NOMEFAMILIAMAT`, `EAN` | JSON | Metadados adicionais |
| `updated_at` | `updated_at` | TIMESTAMP | Data da última extração |

## 2. Processo de Normalização (pt-BR)

Para garantir alta qualidade na busca, aplicaremos:
- **Case Folding:** Tudo para lowercase.
- **Remoção de Acentos:** Conversão de "AÇÚCAR" para "acucar".
- **Tokenização Pragmática:** Divisão por espaços e caracteres especiais.
- **Limpeza de Unidades:** Normalizar "KG", "KILO", "GRAMAS", "G" para padrões canônicos.
- **Remoção de Stopwords:** Filtrar termos irrelevantes (de, para, com).

## 3. Taxonomia e Sinônimos

### 3.1 Hierarquia
A taxonomia seguirá a estrutura:
`NOMESEGMENTO (Dept) -> NOMEGRUPOMAT (Category) -> NOMESUBGRUPOMAT (Subcategory)`

O sistema permitirá overrides manuais via tabela de configuração `taxonomy_overrides`.

### 3.2 Dicionário de Sinônimos
- **Mapeamento:** `termo_usuario ↔ termo_canonico`.
- **Exemplos:** `"refri" ↔ "refrigerante"`, `"agua sanit" ↔ "agua sanitaria"`.
- **Seed Inicial:** Gerado automaticamente a partir de variações encontradas na base.

## 4. Estratégia de Versionamento

- Cada execução do `CatalogBuilder` gera um `build_id` (timestamp).
- O catálogo é persistido com esse ID.
- Existe um ponteiro `active_version` que indica qual catálogo as APIs de busca devem usar.
- **Rollback:** É possível apontar `active_version` para um `build_id` anterior instantaneamente.

## 5. Governança e Performance

- A base Parquet original é tratada como **Read-Only**.
- O catálogo derivado é atualizado via processo de `rebuild` (full ou incremental).
- Cardinalidade: Monitoramento de n# de produtos únicos para evitar explosão de memória.
