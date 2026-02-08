# Plano de Projeto: Catálogo Semântico & Ranking Híbrido

Implementação de um sistema de busca avançada e catálogo de produtos versionado, derivado da base Parquet.

## 1. Escopo e Objetivos
- **Catálogo Canônico:** Extração, normalização e taxonomia de produtos.
- **Busca Híbrida:** Combinação de BM25 (lexical) + Embeddings (semântico).
- **Ranking:** Fusão ponderada com regras de negócio e rerank opcional.
- **Governança:** Versionamento ativo e rollback de índices.

## 2. Atribuição de Agentes
- **Líder de Arquitetura:** `orchestrator`
- **Backend & Data Pipeline:** `backend-specialist`
- **Planejamento & Docs:** `project-planner`
- **Qualidade & Testes:** `debugger`

## 3. Cronograma de Fases

### Fase 1: Especificação & Planejamento (Atual)
- [x] Inspeção de dados Parquet (`admmat.parquet`)
- [x] Criação de `docs/product_catalog_spec.md`
- [x] Criação de `docs/hybrid_ranking_spec.md`
- [x] Criação deste `PLAN-catalog-ranking.md`

### Fase 2: Domínio & Contratos (Próxima)
- [ ] Implementação das entidades `ProductCanonical`, `Synonym`, `Taxonomy`.
- [ ] Definição dos Ports (Interfaces de Repositório, Indexação e Busca).

### Fase 3: Extração & Source Adapters
- [ ] Implementação do `ProductSourceParquetAdapter` usando DuckDB.

### Fase 4-6: Build, Indexação & Ranking
- [ ] Desenvolvimento do pipeline de transformação e normalização pt-BR.
- [ ] Implementação dos adaptadores de BM25 e Vetores.
- [ ] Desenvolvimento da lógica de fusão e regras de negócio.

### Fase 7-8: Integração & API
- [ ] Integração do novo ranking no pipeline do `OrchestratorAgent`.
- [ ] Exposição de endpoints de gestão de catálogo (rebuild/activate/search).

### Fase 9-10: Observabilidade & Testes
- [ ] Implementação de métricas Prometheus e logs estruturados.
- [ ] Execução da suíte completa de testes de ranking.

## 4. Riscos e Mitigações
- **Latência:** A busca vetorial + rerank pode aumentar o tempo de resposta. *Mitigação: Cache de embeddings e limite de candidatos para a fusão.*
- **Alucinação:** O catálogo derivado pode conter erros de normalização. *Mitigação: Etapa de validação no build e rollback rápido.*
- **Mudança de Schema:** Mudanças no arquivo Parquet podem quebrar o builder. *Mitigação: Detecção dinâmica de esquema no adaptador de origem.*

## 5. Critérios de Aceitação
- Pesquisa de produtos funcionando com tolerância a erros de digitação e contexto semântico.
- Capacidade de reverter o catálogo para uma versão anterior via API em < 1s.
- Cobertura de testes unitários e de integração > 80% nos novos serviços.
