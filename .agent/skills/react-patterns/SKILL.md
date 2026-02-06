---
name: react-patterns
description: Padrões e princípios modernos do React. Hooks, composição, performance, melhores práticas de TypeScript.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Padrões de React

> Princípios para construir aplicações React prontas para produção.

---

## 1. Princípios de Design de Componentes

### Tipos de Componentes

| Tipo | Uso | Estado |
|------|-----|--------|
| **Server** | Busca de dados, estático | Nenhum |
| **Client** | Interatividade | useState, effects |
| **Presentational** | Exibição de UI | Apenas props |
| **Container** | Lógica/estado | Estado pesado |

### Regras de Design

- Uma responsabilidade por componente
- Props para baixo, eventos para cima
- Composição sobre herança
- Prefira componentes pequenos e focados

---

## 2. Padrões de Hook

### Quando Extrair Hooks

| Padrão | Extrair Quando |
|--------|----------------|
| **useLocalStorage** | Mesma lógica de armazenamento necessária |
| **useDebounce** | Múltiplos valores com debounce |
| **useFetch** | Padrões de busca repetidos |
| **useForm** | Estado de formulário complexo |

### Regras de Hook

- Hooks apenas no nível superior
- Mesma ordem em cada renderização
- Hooks customizados começam com "use"
- Limpar efeitos no unmount (desmontagem)

---

## 3. Seleção de Gerenciamento de Estado

| Complexidade | Solução |
|--------------|---------|
| Simples | useState, useReducer |
| Local compartilhado | Context |
| Estado do servidor | React Query, SWR |
| Global complexo | Zustand, Redux Toolkit |

### Posicionamento de Estado

| Escopo | Onde |
|--------|------|
| Componente único | useState |
| Pai-filho | Elevar o estado (Lift state up) |
| Subárvore | Context |
| App inteiro | Global store |

---

## 4. Padrões do React 19

### Novos Hooks

| Hook | Propósito |
|------|-----------|
| **useActionState** | Estado de envio de formulário |
| **useOptimistic** | Atualizações de UI otimistas |
| **use** | Ler recursos durante a renderização |

### Benefícios do Compilador

- Memoização automática
- Menos uso manual de useMemo/useCallback
- Foco em componentes puros

---

## 5. Padrões de Composição

### Componentes Compostos (Compound Components)

- Pai fornece o contexto
- Filhos consomem o contexto
- Composição flexível baseada em slots
- Exemplo: Tabs, Accordion, Dropdown

### Render Props vs Hooks

| Caso de Uso | Prefira |
|-------------|---------|
| Lógica reutilizável | Hook customizado |
| Flexibilidade de render | Render props |
| Transversal (Cross-cutting) | Higher-order component |

---

## 6. Princípios de Performance

### Quando Otimizar

| Sinal | Ação |
|-------|------|
| Renders lentos | Perfil (Profile) primeiro |
| Listas grandes | Virtualização |
| Cálculo caro | useMemo |
| Callbacks estáveis | useCallback |

### Ordem de Otimização

1. Verifique se está realmente lento
2. Perfil com DevTools
3. Identifique o gargalo
4. Aplique a correção direcionada

---

## 7. Tratamento de Erros

### Uso de Error Boundary

| Escopo | Posicionamento |
|--------|----------------|
| App inteiro | Nível raiz |
| Recurso (Feature) | Nível de rota/recurso |
| Componente | Em volta de componente de risco |

### Recuperação de Erro

- Mostrar UI de fallback
- Logar o erro
- Oferecer opção de tentar novamente
- Preservar dados do usuário

---

## 8. Padrões de TypeScript

### Tipagem de Props

| Padrão | Uso |
|--------|-----|
| Interface | Props de componente |
| Type | Uniões, complexos |
| Generic | Componentes reutilizáveis |

### Tipos Comuns

| Necessidade | Tipo |
|-------------|------|
| Filhos (Children) | ReactNode |
| Manipulador de evento | MouseEventHandler |
| Ref | RefObject<Element> |

---

## 9. Princípios de Teste

| Nível | Foco |
|-------|------|
| Unitário | Funções puras, hooks |
| Integração | Comportamento do componente |
| E2E | Fluxos do usuário |

### Prioridades de Teste

- Comportamento visível ao usuário
- Casos de borda
- Estados de erro
- Acessibilidade

---

## 10. Anti-Padrões

| ❌ Não faça | ✅ Faça |
|-------------|---------|
| Prop drilling profundo | Use context |
| Componentes gigantes | Divida em menores |
| useEffect para tudo | Server components |
| Otimização prematura | Perfil primeiro |
| Index como key | ID único estável |

---

> **Lembre-se:** React trata-se de composição. Construa pequeno, combine com cuidado.
