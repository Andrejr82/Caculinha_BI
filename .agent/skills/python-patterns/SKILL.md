---
name: python-patterns
description: Princípios de desenvolvimento Python e tomada de decisão. Seleção de framework, padrões assíncronos, type hints, estrutura de projeto. Ensina a pensar, não a copiar.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Padrões de Python

> Princípios de desenvolvimento Python e tomada de decisão para 2025.
> **Aprenda a PENSAR, não a memorizar padrões.**

---

## ⚠️ Como Usar Esta Skill

Esta skill ensina **princípios de tomada de decisão**, não código fixo para copiar.

- PERGUNTE ao usuário a preferência de framework quando não estiver claro
- Escolha async vs sync com base no CONTEXTO
- Não use o mesmo framework por padrão todas as vezes

---

## 1. Seleção de Framework (2025)

### Árvore de Decisão

```
O que você está construindo?
│
├── API-first / Microserviços
│   └── FastAPI (async, moderno, rápido)
│
├── Full-stack web / CMS / Admin
│   └── Django (as "baterias inclusas")
│
├── Simples / Script / Aprendizado
│   └── Flask (minimalista, flexível)
│
├── Servir APIs de IA/ML
│   └── FastAPI (Pydantic, async, uvicorn)
│
└── Workers de segundo plano
    └── Celery + qualquer framework
```

### Princípios de Comparação

| Fator | FastAPI | Django | Flask |
|-------|---------|--------|-------|
| **Ideal para** | APIs, microserviços | Full-stack, CMS | Simples, aprendizado |
| **Async** | Nativo | Django 5.0+ | Via extensões |
| **Admin** | Manual | Integrado | Via extensões |
| **ORM** | Escolha o seu | Django ORM | Escolha o seu |
| **Curva de aprendizado** | Baixa | Média | Baixa |

### Perguntas de Seleção para Fazer:
1. É apenas API ou full-stack?
2. Precisa de interface administrativa?
3. A equipe é familiarizada com async?
4. Infraestrutura existente?

---

## 2. Decisão entre Async vs Sync

### Quando Usar Async

```
async def é melhor quando:
├── Operações de E/S (I/O-bound) (banco de dados, HTTP, arquivo)
├── Muitas conexões simultâneas
├── Recursos em tempo real
├── Comunicação de microserviços
└── FastAPI/Starlette/Django ASGI

def (sync) é melhor quando:
├── Operações intensivas de CPU (CPU-bound)
├── Scripts simples
├── Base de código legada
├── Equipe não familiarizada com async
└── Bibliotecas bloqueantes (sem versão async)
```

### A Regra de Ouro

```
E/S (I/O-bound) → async (esperando por algo externo)
CPU-bound → sync + multiprocessing (computando)

Não faça:
├── Misturar sync e async sem cuidado
├── Usar bibliotecas sync em código async
└── Forçar async para trabalho de CPU
```

### Seleção de Bibliotecas Async

| Necessidade | Biblioteca Async |
|-------------|------------------|
| Cliente HTTP | httpx |
| PostgreSQL | asyncpg |
| Redis | aioredis / redis-py async |
| E/S de Arquivos | aiofiles |
| ORM de Banco de Dados | SQLAlchemy 2.0 async, Tortoise |

---

## 3. Estratégia de Type Hints

### Quando Tipar

```
Sempre tipe:
├── Parâmetros de função
├── Tipos de retorno
├── Atributos de classe
├── APIs públicas

Pode pular:
├── Variáveis locais (deixe a inferência trabalhar)
├── Scripts de uso único
├── Testes (geralmente)
```

### Padrões de Tipagem Comuns

```python
# Estes são padrões, entenda-os:

# Optional → pode ser None
from typing import Optional
def find_user(id: int) -> Optional[User]: ...

# Union → um de múltiplos tipos
def process(data: str | dict) -> None: ...

# Coleções genéricas
def get_items() -> list[Item]: ...
def get_mapping() -> dict[str, int]: ...

# Callable
from typing import Callable
def apply(fn: Callable[[int], str]) -> str: ...
```

### Pydantic para Validação

```
Quando usar Pydantic:
├── Modelos de requisição/resposta de API
├── Configuração/configurações
├── Validação de dados
├── Serialização

Benefícios:
├── Validação em tempo de execução
├── JSON schema gerado automaticamente
├── Funciona nativamente com FastAPI
└── Mensagens de erro claras
```

---

## 4. Princípios de Estrutura de Projeto

### Seleção de Estrutura

```
Projeto pequeno / Script:
├── main.py
├── utils.py
└── requirements.txt

API Média:
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── schemas/
├── tests/
└── pyproject.toml

Aplicação grande:
├── src/
│   └── myapp/
│       ├── core/
│       ├── api/
│       ├── services/
│       ├── models/
│       └── ...
├── tests/
└── pyproject.toml
```

### Princípios de Estrutura FastAPI

```
Organize por recurso (feature) ou camada:

Por camada:
├── routes/ (endpoints da API)
├── services/ (lógica de negócio)
├── models/ (modelos de banco de dados)
├── schemas/ (modelos Pydantic)
└── dependencies/ (dependências compartilhadas)

Por recurso:
├── users/
│   ├── routes.py
│   ├── service.py
│   └── schemas.py
└── products/
    └── ...
```

---

## 5. Princípios de Django (2025)

### Django Async (Django 5.0+)

```
O Django suporta async em:
├── Views async
├── Middleware async
├── ORM async (limitado)
└── Deploy ASGI

Quando usar async no Django:
├── Chamadas de API externa
├── WebSocket (Channels)
├── Views de alta concorrência
└── Disparo de tarefas em segundo plano
```

### Melhores Práticas de Django

```
Design de Model:
├── Models gordos, views magras
├── Use managers para consultas comuns
├── Classes base abstratas para campos compartilhados

Views:
├── Baseadas em classe (CBV) para CRUD complexo
├── Baseadas em função (FBV) para endpoints simples
├── Use viewsets com DRF

Consultas (Queries):
├── select_related() para chaves estrangeiras (FKs)
├── prefetch_related() para relacionamentos muitos-para-muitos (M2M)
├── Evite consultas N+1
└── Use .only() para campos específicos
```

---

## 6. Princípios de FastAPI

### async def vs def no FastAPI

```
Use async def quando:
├── Estiver usando drivers de banco de dados async
├── Fizer chamadas HTTP async
├── Operações de E/S (I/O-bound)
└── Quiser lidar com concorrência

Use def quando:
├── Operações bloqueantes
├── Drivers de banco de dados sync
├── Trabalho intensivo de CPU
└── O FastAPI executa em um threadpool automaticamente
```

### Injeção de Dependência

```
Use dependências para:
├── Sessões de banco de dados
├── Usuário atual / Autorização
├── Configuração
├── Recursos compartilhados

Benefícios:
├── Testabilidade (mockar dependências)
├── Separação limpa de preocupações
├── Limpeza automática (yield)
```

### Integração Pydantic v2

```python
# FastAPI + Pydantic são fortemente integrados:

# Validação de requisição
@app.post("/users")
async def create(user: UserCreate) -> UserResponse:
    # 'user' já vem validado
    ...

# Serialização de resposta
# O tipo de retorno se torna o schema de resposta
```

---

## 7. Tarefas em Segundo Plano (Background Tasks)

### Guia de Seleção

| Solução | Ideal Para |
|---------|------------|
| **BackgroundTasks** | Tarefas simples, dentro do processo |
| **Celery** | Workflows complexos e distribuídos |
| **ARQ** | Async, baseado em Redis |
| **RQ** | Fila simples no Redis |
| **Dramatiq** | Baseado em atores, mais simples que o Celery |

### Quando Usar Cada Um

```
FastAPI BackgroundTasks:
├── Operações rápidas
├── Persistência não necessária
├── "Dispare e esqueça" (Fire-and-forget)
└── Mesmo processo

Celery/ARQ:
├── Tarefas de longa duração
├── Necessita de lógica de tentativa (retry)
├── Workers distribuídos
├── Fila persistente
└── Workflows complexos
```

---

## 8. Princípios de Tratamento de Erros

### Estratégia de Exceção

```
No FastAPI:
├── Criar classes de exceção customizadas
├── Registrar manipuladores de exceção (exception handlers)
├── Retornar formato de erro consistente
└── Logar sem expor detalhes internos

Padrão:
├── Lance exceções de domínio nos serviços
├── Capture e transforme nos handlers
└── O cliente recebe uma resposta de erro limpa
```

### Filosofia de Resposta de Erro

```
Inclua:
├── Código de erro (programático)
├── Mensagem (legível por humanos)
├── Detalhes (nível de campo quando aplicável)
└── NÃO inclua stack traces (segurança)
```

---

## 9. Princípios de Teste

### Estratégia de Teste

| Tipo | Propósito | Ferramentas |
|------|-----------|-------------|
| **Unitário** | Lógica de negócio | pytest |
| **Integração**| Endpoints de API | pytest + httpx/TestClient |
| **E2E** | Workflows completos | pytest + DB |

### Testes Async

```python
# Use pytest-asyncio para testes async

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200
```

### Estratégia de Fixtures

```
Fixtures comuns:
├── db_session → Conexão com banco de dados
├── client → Cliente de teste
├── authenticated_user → Usuário com token
└── sample_data → Configuração de dados de teste
```

---

## 10. Checklist de Decisão

Antes de implementar:

- [ ] **Perguntou ao usuário sobre a preferência de framework?**
- [ ] **Escolheu o framework para ESTE contexto?** (não apenas o padrão)
- [ ] **Decidiu entre async vs sync?**
- [ ] **Planejou a estratégia de type hints?**
- [ ] **Definiu a estrutura do projeto?**
- [ ] **Planejou o tratamento de erros?**
- [ ] **Considerou tarefas em segundo plano?**

---

## 11. Anti-Padrões a Evitar

### ❌ NÃO FAÇA:
- Usar Django por padrão para APIs simples (FastAPI pode ser melhor)
- Usar bibliotecas sync em código async
- Pular type hints em APIs públicas
- Colocar lógica de negócio em rotas/views
- Ignorar consultas N+1
- Misturar async e sync sem cuidado

### ✅ FAÇA:
- Escolher o framework com base no contexto
- Perguntar sobre requisitos async
- Usar Pydantic para validação
- Separar preocupações (rotas → serviços → repos)
- Testar caminhos críticos

---

> **Lembre-se**: Padrões Python tratam-se de tomada de decisão para o SEU contexto específico. Não copie código — pense sobre o que melhor serve à sua aplicação.
