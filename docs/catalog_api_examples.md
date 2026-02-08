# Documentação da API de Catálogo Semântico 🌐

Esta API gerencia o ciclo de vida do catálogo de produtos canônicos (1.1M+ itens), incluindo reconstrução, versionamento e busca híbrida.

## Endpoints Disponíveis

### 1. Status do Catálogo
Retorna a versão ativa e o estado atual do motor de busca.

- **GET** `/api/v1/catalog/status`
- **Response:**
```json
{
  "active_version": "cat-f082428d",
  "status": "ready"
}
```

### 2. Busca Híbrida Profunda
Realiza uma busca combinada (BM25 + Vetorial) no catálogo.

- **POST** `/api/v1/catalog/search`
- **Request Body:**
```json
{
  "query": "alca bolsa madeira",
  "limit": 5
}
```
- **Response:**
```json
{
  "query": "alca bolsa madeira",
  "results": [
    {
      "product_id": 704566,
      "name": "alca bolsa 7710 diam 98mm pp madeira 380",
      "brand": "CAÇULA",
      "category": "ARTESANATO",
      "score": 0.0333,
      "rationale": "Fusion Match (BM25: 4.09, Vector: 0.81)"
    }
  ]
}
```

### 3. Rebuild Total (Manutenção)
Dispara o pipeline de extração do Parquet, normalização e indexação. Este processo corre em background.

- **POST** `/api/v1/catalog/rebuild`
- **Request Body:**
```json
{
  "description": "Atualização semanal de preços e nomes"
}
```

## Integração com IA
O `CaculinhaBIAgent` utiliza automaticamente estas capacidades através da ferramenta `pesquisar_produto_catalogo_profundo`.

### Exemplo de Uso no Chat:
- **Usuário:** "Quais bolsas de madeira temos no catálogo?"
- **Agente:** "Utilizando a busca profunda, encontrei os seguintes itens: [ID: 704566] Alça Bolsa PP Madeira... [ID: 704565] Alça Bolsa PP Imbuia..."
