---
name: mcp-builder
description: Princípios de construção de servidor MCP (Model Context Protocol). Design de ferramentas, padrões de recursos, melhores práticas.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Construtor MCP

> Princípios para construção de servidores MCP.

---

## 1. Visão Geral do MCP

### O que é MCP?

Model Context Protocol - padrão para conectar sistemas de IA com ferramentas externas e fontes de dados.

### Conceitos Core

| Conceito | Propósito |
|----------|-----------|
| **Ferramentas (Tools)** | Funções que a IA pode chamar |
| **Recursos (Resources)** | Dados que a IA pode ler |
| **Prompts** | Templates de prompt pré-definidos |

---

## 2. Arquitetura do Servidor

### Estrutura do Projeto

```
meu-servidor-mcp/
├── src/
│   └── index.ts      # Entrada principal
├── package.json
└── tsconfig.json
```

### Tipos de Transporte

| Tipo | Uso |
|------|-----|
| **Stdio** | Local, baseado em CLI |
| **SSE** | Baseado em web, streaming |
| **WebSocket** | Tempo real, bidirecional |

---

## 3. Princípios de Design de Ferramentas

### Bom Design de Ferramenta

| Princípio | Descrição |
|-----------|-----------|
| Nome claro | Orientado a ação (get_weather, create_user) |
| Propósito único | Faz uma coisa bem feita |
| Entrada validada | Schema com tipos e descrições |
| Saída estruturada | Formato de resposta previsível |

### Design de Schema de Entrada

| Campo | Obrigatório? |
|-------|--------------|
| Type | Sim - object |
| Properties | Definir cada parâmetro |
| Required | Listar parâmetros obrigatórios |
| Description | Descrição legível para humanos |

---

## 4. Padrões de Recurso

### Tipos de Recurso

| Tipo | Uso |
|------|-----|
| Estático | Dados fixos (config, docs) |
| Dinâmico | Gerado sob demanda |
| Template | URI com parâmetros |

### Padrões de URI

| Padrão | Exemplo |
|--------|---------|
| Fixo | `docs://readme` |
| Parametrizado | `users://{userId}` |
| Coleção | `files://projeto/*` |

---

## 5. Tratamento de Erros

### Tipos de Erro

| Situação | Resposta |
|----------|----------|
| Parâmetros inválidos | Mensagem de erro de validação |
| Não encontrado | Aviso claro de "não encontrado" |
| Erro de servidor | Erro genérico, logar detalhes |

### Melhores Práticas

- Retornar erros estruturados
- Não expor detalhes internos do servidor
- Logar para depuração
- Fornecer mensagens acionáveis

---

## 6. Manipulação Multimodal

### Tipos Suportados

| Tipo | Codificação |
|------|-------------|
| Texto | Texto puro |
| Imagens | Base64 + tipo MIME |
| Arquivos | Base64 + tipo MIME |

---

## 7. Princípios de Segurança

### Validação de Entrada

- Validar todas as entradas das ferramentas
- Sanitizar dados fornecidos pelo usuário
- Limitar o acesso aos recursos

### Chaves de API

- Use variáveis de ambiente
- Não logue segredos
- Valide as permissões

---

## 8. Configuração

### Configuração do Claude Desktop

| Campo | Propósito |
|-------|-----------|
| command | Executável para rodar |
| args | Argumentos do comando |
| env | Variáveis de ambiente |

---

## 9. Testes

### Categorias de Teste

| Tipo | Foco |
|------|------|
| Unitário | Lógica da ferramenta |
| Integração | Servidor completo |
| Contrato | Validação de schema |

---

## 10. Checklist de Melhores Práticas

- [ ] Nomes de ferramentas claros e orientados a ação
- [ ] Schemas de entrada completos com descrições
- [ ] Saída JSON estruturada
- [ ] Tratamento de erros para todos os casos
- [ ] Validação de entrada
- [ ] Configuração baseada em ambiente
- [ ] Logging para depuração

---

> **Lembre-se:** As ferramentas MCP devem ser simples, focadas e bem documentadas. A IA depende das descrições para usá-las corretamente.
