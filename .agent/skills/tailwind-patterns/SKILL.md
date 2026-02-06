---
name: tailwind-patterns
description: Princípios do Tailwind CSS v4. Configuração orientada a CSS, container queries, padrões modernos, arquitetura de tokens de design.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Padrões de Tailwind CSS (v4 - 2025)

> CSS moderno utilitário com configuração nativa de CSS.

---

## 1. Arquitetura do Tailwind v4

### O que mudou da v3

| v3 (Legado) | v4 (Atual) |
|-------------|------------|
| `tailwind.config.js` | Diretiva `@theme` baseada em CSS |
| Plugin PostCSS | Engine Oxide (10x mais rápido) |
| modo JIT | Nativo, sempre ativo |
| Sistema de plugins | Recursos nativos de CSS |
| Diretiva `@apply` | Ainda disponível, desencorajada |

### Conceitos Core da v4

| Conceito | Descrição |
|----------|-----------|
| **CSS-first** | Configuração no CSS, não no JavaScript |
| **Engine Oxide** | Compilador baseado em Rust, muito mais rápido |
| **Aninhamento Nativo** | Aninhamento de CSS sem PostCSS |
| **Variáveis CSS** | Todos os tokens expostos como variáveis `--*` |

---

## 2. Configuração Baseada em CSS

### Definição do Tema

```css
@theme {
  /* Cores - use nomes semânticos */
  --color-primary: oklch(0.7 0.15 250);
  --color-surface: oklch(0.98 0 0);
  --color-surface-dark: oklch(0.15 0 0);
  
  /* Escala de espaçamento */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;
  
  /* Tipografia */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

### Quando Estender vs Sobrescrever

| Ação | Uso Quando |
|------|------------|
| **Estender (Extend)** | Adicionando novos valores junto aos padrões |
| **Sobrescrever (Override)** | Substituindo a escala padrão inteiramente |
| **Tokens semânticos** | Nomenclatura específica do projeto (primary, surface) |

---

## 3. Container Queries (Nativo na v4)

### Breakpoint vs Container

| Tipo | Responde a |
|------|------------|
| **Breakpoint** (`md:`) | Largura da viewport |
| **Container** (`@container`) | Largura do elemento pai |

### Uso de Container Queries

| Padrão | Classes |
|--------|---------|
| Definir container | `@container` no pai |
| Breakpoint de container | `@sm:`, `@md:`, `@lg:` nos filhos |
| Containers nomeados | `@container/card` para especificidade |

### Quando Usar

| Cenário | Uso |
|---------|-----|
| Layouts em nível de página | Breakpoints de viewport |
| Responsividade em nível de componente | Container queries |
| Componentes reutilizáveis | Container queries (independente do contexto) |

---

## 4. Design Responsivo

### Sistema de Breakpoints

| Prefixo | Largura Mínima | Alvo |
|---------|----------------|------|
| (nenhum) | 0px | Base mobile-first |
| `sm:` | 640px | Celular grande / tablet pequeno |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Laptop |
| `xl:` | 1280px | Desktop |
| `2xl:` | 1536px | Desktop grande |

### Princípio Mobile-First

1. Escreva estilos mobile primeiro (sem prefixo)
2. Adicione substituições para telas maiores com prefixos
3. Exemplo: `w-full md:w-1/2 lg:w-1/3`

---

## 5. Modo Escuro (Dark Mode)

### Estratégias de Configuração

| Método | Comportamento | Uso Quando |
|--------|---------------|------------|
| `class` | Alternância pela classe `.dark` | Troca de tema manual |
| `media` | Segue preferência do sistema | Sem controle do usuário |
| `selector` | Seletor customizado (v4) | Tematização complexa |

### Padrão de Modo Escuro

| Elemento | Claro | Escuro |
|----------|-------|--------|
| Fundo | `bg-white` | `dark:bg-zinc-900` |
| Texto | `text-zinc-900` | `dark:text-zinc-100` |
| Bordas | `border-zinc-200` | `dark:border-zinc-700` |

---

## 6. Padrões Modernos de Layout

### Padrões Flexbox

| Padrão | Classes |
|--------|---------|
| Centralizar (ambos os eixos) | `flex items-center justify-center` |
| Empilhamento vertical | `flex flex-col gap-4` |
| Linha horizontal | `flex gap-4` |
| Espaçamento entre | `flex justify-between items-center` |
| Grid envolvente (wrap) | `flex flex-wrap gap-4` |

### Padrões Grid

| Padrão | Classes |
|--------|---------|
| Auto-ajuste responsivo | `grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))]` |
| Assimétrico (Bento) | `grid grid-cols-3 grid-rows-2` com spans |
| Layout com sidebar | `grid grid-cols-[auto_1fr]` |

> **Nota:** Prefira layouts assimétricos/Bento sobre grids simétricos de 3 colunas.

---

## 7. Sistema Moderno de Cores

### OKLCH vs RGB/HSL

| Formato | Vantagem |
|---------|----------|
| **OKLCH** | Perceptivamente uniforme, melhor para design |
| **HSL** | Matiz/saturação intuitivo |
| **RGB** | Compatibilidade legada |

### Arquitetura de Tokens de Cor

| Camada | Exemplo | Propósito |
|--------|---------|-----------|
| **Primitivo** | `--blue-500` | Valores de cor brutos |
| **Semântico** | `--color-primary` | Nomeação baseada no propósito |
| **Componente** | `--button-bg` | Específico do componente |

---

## 8. Sistema de Tipografia

### Padrão de Stack de Fontes

| Tipo | Recomendado |
|------|-------------|
| Sans | `'Inter', 'SF Pro', system-ui, sans-serif` |
| Mono | `'JetBrains Mono', 'Fira Code', monospace` |
| Display | `'Outfit', 'Poppins', sans-serif` |

### Escala de Tipos

| Classe | Tamanho | Uso |
|--------|---------|-----|
| `text-xs` | 0.75rem | Rótulos, legendas |
| `text-sm` | 0.875rem | Texto secundário |
| `text-base` | 1rem | Texto do corpo |
| `text-lg` | 1.125rem | Texto de destaque (lead) |
| `text-xl`+ | 1.25rem+ | Títulos |

---

## 9. Animação e Transições

### Animações Integradas

| Classe | Efeito |
|--------|--------|
| `animate-spin` | Rotação contínua |
| `animate-ping` | Pulso de atenção |
| `animate-pulse` | Pulso sutil de opacidade |
| `animate-bounce` | Efeito de salto |

### Padrões de Transição

| Padrão | Classes |
|--------|---------|
| Todas as propriedades | `transition-all duration-200` |
| Específico | `transition-colors duration-150` |
| Com easing | `ease-out` ou `ease-in-out` |
| Efeito de hover | `hover:scale-105 transition-transform` |

---

## 10. Extração de Componentes

### Quando Extrair

| Sinal | Ação |
|-------|------|
| Mesma combinação de classes 3+ vezes | Extrair componente |
| Variantes de estado complexas | Extrair componente |
| Elemento do sistema de design | Extrair + documentar |

### Métodos de Extração

| Método | Uso Quando |
|--------|------------|
| **Componente React/Vue** | Dinâmico, precisa de JS |
| **@apply no CSS** | Estático, sem necessidade de JS |
| **Tokens de design** | Valores reutilizáveis |

---

## 11. Anti-Padrões

| Não Faça | Faça |
|----------|------|
| Valores arbitrários em todo lugar | Use a escala do sistema de design |
| `!important` | Corrija a especificidade adequadamente |
| Estilo inline `style=` | Use utilitários |
| Listas longas de classes duplicadas | Extrair componente |
| Misturar config v3 com v4 | Migrar totalmente para CSS-first |
| Usar `@apply` excessivamente | Prefira componentes |

---

## 12. Princípios de Performance

| Princípio | Implementação |
|-----------|----------------|
| **Purge de não utilizados** | Automático na v4 |
| **Evitar dinamismo** | Sem classes em template strings |
| **Usar Oxide** | Padrão na v4, 10x mais rápido |
| **Cache de builds** | Cache em CI/CD |

---

> **Lembre-se:** O Tailwind v4 é CSS-first. Adote variáveis CSS, container queries e recursos nativos. O arquivo de configuração agora é opcional.
