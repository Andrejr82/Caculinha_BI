# Contratos de Domínio: Catálogo e Ranking Híbrido

Este documento formaliza as responsabilidades das interfaces (Ports) do domínio para o sistema de Catálogo Semântico.

## 1. Gestão de Catálogo (`product_catalog_ports.py`)

### 1.1 `IProductSourcePort`
- **Responsabilidade:** Extração de dados crus.
- **Implementação:** Deve usar DuckDB para ler o arquivo `admmat.parquet`.
- **Regra:** Somente leitura.

### 1.2 `IProductCatalogRepository`
- **Responsabilidade:** Persistência do catálogo normalizado.
- **Implementação:** Recomendado DuckDB para busca rápida e agregação.
- **Contrato:** Deve suportar versionamento explícito por `catalog_version`.

### 1.3 `ISynonymRepository` e `INormalizationPort`
- **Responsabilidade:** Limpeza e expansão de query.
- **Normalização:** Deve ser consistente entre o build (indexação) e a search (runtime).

### 1.4 `ICatalogVersionPort`
- **Responsabilidade:** Orquestração de versões.
- **Contrato:** Mudança de `active_version` deve ser atômica e afetar imediatamente as buscas.

## 2. Busca e Ranqueamento (`product_search_ports.py`)

### 2.1 `IRetrievalIndexPort`
- **Responsabilidade:** Motores de busca primários.
- **Contrato:** `search` retorna uma lista de `RetrievedItem` com scores normalizados por motor.

### 2.2 `IRankingFusionPort`
- **Responsabilidade:** Consolidar resultados.
- **Lógica:** Implementa a média ponderada entre BM25 e Vetores, aplicando Boosts de regras de negócio (Departamentos, Marcas).

### 2.3 `IRerankerPort`
- **Responsabilidade:** Polimento final.
- **Contrato:** Opcional. Se falhar ou demorar, deve retornar o ranking da fusão sem erros.

### 2.4 `IEvaluationPort`
- **Responsabilidade:** Qualidade científica.
- **Contrato:** Calcula métricas comparando o resultado do sistema com um "Golden Set" de IDs esperados.
