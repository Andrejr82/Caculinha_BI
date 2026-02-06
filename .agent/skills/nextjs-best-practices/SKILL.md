---
name: nextjs-best-practices
description: Princípios do Next.js App Router. Server Components, busca de dados, padrões de roteamento.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Melhores Práticas de Next.js

> Princípios para desenvolvimento com Next.js App Router.

---

## 1. Server vs Client Components

### Árvore de Decisão

```
Precisa de...?
│
├── useState, useEffect, manipuladores de evento
│   └── Componente Client ('use client')
│
├── Busca direta de dados, sem interatividade
│   └── Componente Server (padrão)
│
└── Ambos? 
    └── Dividir: Pai Server + Filho Client
```

### Por Padrão

| Tipo | Uso |
|------|-----|
| **Server** | Busca de dados, layout, conteúdo estático |
| **Client** | Formulários, botões, UI interativa |

---

## 2. Padrões de Busca de Dados (Data Fetching)

### Estratégia de Fetch

| Padrão | Uso |
|--------|-----|
| **Padrão (Default)** | Estático (cache no build) |
| **Revalidate** | ISR (atualização baseada em tempo) |
| **No-store** | Dinâmico (a cada requisição) |

### Fluxo de Dados

| Fonte | Padrão |
|-------|--------|
| Banco de Dados | Busca no Componente Server |
| API | fetch com cache |
| Entrada do usuário | Estado Client + server action |

---

## 3. Princípios de Roteamento

### Convenções de Arquivo

| Arquivo | Propósito |
|---------|-----------|
| `page.tsx` | UI da Rota |
| `layout.tsx` | Layout compartilhado |
| `loading.tsx` | Estado de carregamento |
| `error.tsx` | Error boundary |
| `not-found.tsx` | Página 404 |

### Organização de Rotas

| Padrão | Uso |
|--------|-----|
| Grupos de rotas `(nome)` | Organizar sem afetar a URL |
| Rotas paralelas `@slot` | Múltiplas páginas no mesmo nível |
| Interceptação `(.)` | Overlays de modal |

---

## 4. Rotas de API

### Manipuladores de Rota (Route Handlers)

| Método | Uso |
|--------|-----|
| GET | Ler dados |
| POST | Criar dados |
| PUT/PATCH | Atualizar dados |
| DELETE | Remover dados |

### Melhores Práticas

- Validar entrada com Zod
- Retornar status codes apropriados
- Tratar erros graciosamente
- Usar Edge runtime quando possível

---

## 5. Princípios de Performance

### Otimização de Imagem

- Usar componente next/image
- Definir prioridade para o que está "acima da dobra" (above-fold)
- Fornecer placeholder de desfoque (blur)
- Usar tamanhos responsivos

### Otimização de Bundle

- Imports dinâmicos para componentes pesados
- Divisão de código baseada em rota (automática)
- Analisar com bundle analyzer

---

## 6. Metadados

### Estático vs Dinâmico

| Tipo | Uso |
|------|-----|
| Export estático | Metadados fixos |
| generateMetadata | Dinâmico por rota |

### Tags Essenciais

- título (50-60 caracteres)
- descrição (150-160 caracteres)
- Imagens Open Graph
- URL Canônica

---

## 7. Estratégia de Cache

### Camadas de Cache

| Camada | Controle |
|--------|----------|
| Request | opções do fetch |
| Data | revalidate/tags |
| Rota inteira | config da rota |

### Revalidação

| Método | Uso |
|--------|-----|
| Baseada em tempo | `revalidate: 60` |
| Sob demanda | `revalidatePath/Tag` |
| Sem cache | `no-store` |

---

## 8. Server Actions

### Casos de Uso

- Envios de formulário
- Mutações de dados
- Gatilhos de revalidação

### Melhores Práticas

- Marcar com 'use server'
- Validar todas as entradas
- Retornar respostas tipadas
- Tratar erros

---

## 9. Anti-Padrões

| ❌ Não faça | ✅ Faça |
|-------------|---------|
| 'use client' em todo lugar | Server por padrão |
| Busca no componente client | Busca no server |
| Pular estados de carregamento | Use loading.tsx |
| Ignorar error boundaries | Use error.tsx |
| Bundles client grandes | Imports dinâmicos |

---

## 10. Estrutura de Projeto

```
app/
├── (marketing)/     # Grupo de rota
│   └── page.tsx
├── (dashboard)/
│   ├── layout.tsx   # Layout do dashboard
│   └── page.tsx
├── api/
│   └── [recurso]/
│       └── route.ts
└── components/
    └── ui/
```

---

> **Lembre-se:** Componentes Server são o padrão por um motivo. Comece por eles, adicione client apenas quando necessário.
