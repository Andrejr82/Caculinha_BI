---
name: nodejs-best-practices
description: Princípios de desenvolvimento Node.js e tomada de decisão. Seleção de framework, padrões assíncronos, segurança e arquitetura. Ensina a pensar, não a copiar.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Melhores Práticas de Node.js

> Princípios e tomada de decisão para o desenvolvimento Node.js em 2025.
> **Aprenda a PENSAR, não a memorizar padrões de código.**

---

## ⚠️ Como Usar Esta Skill

Esta skill ensina **princípios de tomada de decisão**, não código fixo para copiar.

- PERGUNTE ao usuário as preferências quando não estiver claro
- Escolha o framework/padrão com base no CONTEXTO
- Não use a mesma solução por padrão todas as vezes

---

## 1. Seleção de Framework (2025)

### Árvore de Decisão

```
O que você está construindo?
│
├── Edge/Serverless (Cloudflare, Vercel)
│   └── Hono (zero-dependência, cold starts ultra-rápidos)
│
├── API de Alta Performance
│   └── Fastify (2-3x mais rápido que o Express)
│
├── Familiaridade corporativa/equipe
│   └── NestJS (estruturado, DI, decoradores)
│
├── Legado/Estável/Ecossistema máximo
│   └── Express (maduro, maior quantidade de middlewares)
│
└── Full-stack com frontend
    └── Next.js API Routes ou tRPC
```

### Princípios de Comparação

| Fator | Hono | Fastify | Express |
|-------|------|---------|---------|
| **Ideal para** | Edge, serverless | Performance | Legado, aprendizado |
| **Cold start** | Mais rápido | Rápido | Moderado |
| **Ecossistema** | Em crescimento | Bom | O maior |
| **TypeScript** | Nativo | Excelente | Bom |
| **Curva de aprendizado** | Baixa | Média | Baixa |

### Perguntas de Seleção para Fazer:
1. Qual é o alvo de deploy?
2. O tempo de cold start é crítico?
3. A equipe já tem experiência prévia?
4. Existe código legado para manter?

---

## 2. Considerações de Runtime (2025)

### TypeScript Nativo

```
Node.js 22+: --experimental-strip-types
├── Execute arquivos .ts diretamente
├── Sem necessidade de etapa de build para projetos simples
└── Considere para: scripts, APIs simples
```

### Decisão do Sistema de Módulos

```
ESM (import/export)
├── Padrão moderno
├── Melhor tree-shaking
├── Carregamento de módulos assíncrono
└── Use para: novos projetos

CommonJS (require)
├── Compatibilidade legada
├── Maior suporte de pacotes npm
└── Use para: bases de código existentes, alguns casos de borda
```

### Seleção de Runtime

| Runtime | Melhor Para |
|---------|-------------|
| **Node.js** | Uso geral, maior ecossistema |
| **Bun** | Performance, bundler integrado |
| **Deno** | Foco em segurança, TypeScript integrado |

---

## 3. Princípios de Arquitetura

### Conceito de Estrutura em Camadas

```
Fluxo da Requisição:
│
├── Camada de Controller/Rota
│   ├── Lida com especificidades HTTP
│   ├── Validação de entrada na borda
│   └── Chama a camada de serviço
│
├── Camada de Serviço
│   ├── Lógica de negócio
│   ├── Independente de framework
│   └── Chama a camada de repositório
│
└── Camada de Repositório
    ├── Apenas acesso a dados
    ├── Consultas ao banco de dados
    └── Interações com ORM
```

### Por que Isso Importa:
- **Testabilidade**: Mockar camadas independentemente
- **Flexibilidade**: Trocar o banco de dados sem tocar na lógica de negócio
- **Clareza**: Cada camada tem uma responsabilidade única

### Quando Simplificar:
- Scripts pequenos → Único arquivo está OK
- Protótipos → Menos estrutura é aceitável
- Sempre pergunte: "Isso vai crescer?"

---

## 4. Princípios de Tratamento de Erros

### Tratamento de Erros Centralizado

```
Padrão:
├── Criar classes de erro customizadas
├── Lançar (throw) de qualquer camada
├── Capturar no nível superior (middleware)
└── Formatar resposta consistente
```

### Filosofia de Resposta de Erro

```
O Cliente recebe:
├── Status HTTP apropriado
├── Código de erro para tratamento programático
├── Mensagem amigável ao usuário
└── SEM detalhes internos (segurança!)

Os Logs recebem:
├── Stack trace completo
├── Contexto da requisição
├── ID do usuário (se aplicável)
└── Timestamp (data/hora)
```

### Seleção de Código de Status (Status Code)

| Situação | Status | Quando |
|----------|--------|--------|
| Entrada ruim | 400 | Cliente enviou dados inválidos |
| Sem auth | 401 | Credenciais ausentes ou inválidas |
| Sem permissão | 403 | Auth válida, mas não permitido |
| Não encontrado | 404 | Recurso não existe |
| Conflito | 409 | Duplicidade ou conflito de estado |
| Validação | 422 | Schema válido, mas regras de negócio falham |
| Erro do servidor| 500 | Nossa culpa, logar tudo |

---

## 5. Princípios de Padrões Assíncronos

### Quando Usar Cada Um

| Padrão | Usar Quando |
|--------|-------------|
| `async/await` | Operações assíncronas sequenciais |
| `Promise.all` | Operações independentes em paralelo |
| `Promise.allSettled` | Paralelo onde algumas podem falhar |
| `Promise.race` | Timeout ou a primeira resposta vence |

### Consciência do Event Loop

```
I/O-bound (async ajuda):
├── Consultas ao banco de dados
├── Requisições HTTP
├── Sistema de arquivos
└── Operações de rede

CPU-bound (async não ajuda):
├── Operações de criptografia
├── Processamento de imagens
├── Cálculos complexos
└── → Use worker threads ou delegue a tarefa (offload)
```

### Evitando Bloquear o Event Loop

- Nunca use métodos síncronos em produção (fs.readFileSync, etc.)
- Delegue trabalho intensivo de CPU
- Use streaming para grandes volumes de dados

---

## 6. Princípios de Validação

### Validar nas Bordas

```
Onde validar:
├── Ponto de entrada da API (body/params da requisição)
├── Antes de operações no banco de dados
├── Dados externos (respostas de API, uploads de arquivos)
└── Variáveis de ambiente (na inicialização)
```

### Seleção de Biblioteca de Validação

| Biblioteca | Melhor Para |
|------------|-------------|
| **Zod** | Foco em TypeScript, inferência |
| **Valibot** | Bundle menor (tree-shakeable) |
| **ArkType** | Crítico para performance |
| **Yup** | Uso existente com React Form |

### Filosofia de Validação

- Falhe rápido: Valide cedo
- Seja específico: Mensagens de erro claras
- Não confie: Nem mesmo em dados "internos"

---

## 7. Princípios de Segurança

### Checklist de Segurança (Não é Código)

- [ ] **Validação de entrada**: Todas as entradas validadas
- [ ] **Consultas parametrizadas**: Sem concatenação de strings para SQL
- [ ] **Hashing de senha**: bcrypt ou argon2
- [ ] **Verificação de JWT**: Sempre verifique assinatura e expiração
- [ ] **Rate limiting**: Proteja-se contra abusos
- [ ] **Headers de segurança**: Helmet.js ou equivalente
- [ ] **HTTPS**: Em todos os lugares em produção
- [ ] **CORS**: Configurado corretamente
- [ ] **Segredos (Secrets)**: Apenas variáveis de ambiente
- [ ] **Dependências**: Auditadas regularmente

### Mentalidade de Segurança

```
Não confie em nada:
├── Query params → validar
├── Request body → validar
├── Headers → verificar
├── Cookies → validar
├── Uploads de arquivos → escanear
└── APIs externas → validar resposta
```

---

## 8. Princípios de Teste

### Seleção de Estratégia de Teste

| Tipo | Propósito | Ferramentas |
|------|-----------|-------------|
| **Unitário** | Lógica de negócio | node:test, Vitest |
| **Integração**| Endpoints de API | Supertest |
| **E2E** | Fluxos completos | Playwright |

### O que Testar (Prioridades)

1. **Caminhos críticos**: Auth, pagamentos, core do negócio
2. **Casos de borda**: Entradas vazias, limites
3. **Tratamento de erros**: O que acontece quando as coisas falham?
4. **Não vale a pena testar**: Código do framework, getters triviais

### Test Runner Integrado (Node.js 22+)

```
node --test src/**/*.test.ts
├── Sem dependência externa
├── Bom relatório de cobertura
└── Modo watch disponível
```

---

## 10. Anti-Padrões a Evitar

### ❌ NÃO FAÇA:
- Usar Express para novos projetos edge (use Hono)
- Usar métodos síncronos em código de produção
- Colocar lógica de negócio em controllers
- Pular validação de entrada
- Hardcodar segredos (secrets)
- Confiar em dados externos sem validação
- Bloquear o event loop com trabalho de CPU

### ✅ FAÇA:
- Escolher o framework com base no contexto
- Perguntar ao usuário as preferências quando não estiver claro
- Usar arquitetura em camadas para projetos que crescem
- Validar todas as entradas
- Usar variáveis de ambiente para segredos
- Fazer perfil (profile) antes de otimizar

---

## 11. Checklist de Decisão

Antes de implementar:

- [ ] **Perguntou ao usuário sobre a preferência de stack?**
- [ ] **Escolheu o framework para ESTE contexto?** (não apenas o padrão)
- [ ] **Considerou o alvo de deploy?**
- [ ] **Planejou a estratégia de tratamento de erros?**
- [ ] **Identificou os pontos de validação?**
- [ ] **Considerou os requisitos de segurança?**

---

> **Lembre-se**: As melhores práticas de Node.js tratam-se de tomada de decisão, não de memorizar padrões. Cada projeto merece uma análise fresca baseada em seus requisitos.
