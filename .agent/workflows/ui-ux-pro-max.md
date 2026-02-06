---
description: Planejar e implementar UI
---

---
description: Inteligência de design movida por IA com mais de 50 estilos, mais de 95 paletas de cores e geração automatizada de sistemas de design.
---

# ui-ux-pro-max

Guia abrangente de design para aplicações web e mobile. Contém mais de 50 estilos, 97 paletas de cores, 57 combinações de fontes, 99 diretrizes de UX e 25 tipos de gráficos em 9 stacks tecnológicas. Banco de dados pesquisável com recomendações baseadas em prioridade.

## Pré-requisitos

Verifique se o Python está instalado:

```bash
python3 --version || python --version
```

Se o Python não estiver instalado, instale-o com base no SO do usuário:

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3
```

**Windows:**
```powershell
winget install Python.Python.3.12
```

---

## Como Usar Este Workflow

Quando o usuário solicitar trabalho de UI/UX (projetar, construir, criar, implementar, revisar, consertar, melhorar), siga este fluxo:

### Passo 1: Analisar Requisitos do Usuário

Extraia informações chave do pedido do usuário:
- **Tipo de produto**: SaaS, e-commerce, portfólio, dashboard, landing page, etc.
- **Palavras-chave de estilo**: minimalista, divertido (playful), profissional, elegante, modo escuro, etc.
- **Setor (Industry)**: saúde, fintech, games, educação, etc.
- **Stack**: React, Vue, Next.js, ou o padrão `html-tailwind`

### Passo 2: Gerar Sistema de Design (OBRIGATÓRIO)

**Sempre comece com `--design-system`** para obter recomendações abrangentes com justificativas:

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "<tipo_do_produto> <setor> <palavras_chave>" --design-system [-p "Nome do Projeto"]
```

Este comando:
1. Pesquisa em 5 domínios em paralelo (produto, estilo, cor, landing, tipografia)
2. Aplica regras de raciocínio de `ui-reasoning.csv` para selecionar as melhores correspondências
3. Retorna o sistema de design completo: padrão, estilo, cores, tipografia, efeitos
4. Inclui anti-padrões para evitar

**Exemplo:**
```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Passo 2b: Persistir o Sistema de Design (Padrão Master + Overrides)

Para salvar o sistema de design para recuperação hierárquica entre sessões, adicione `--persist`:

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Nome do Projeto"
```

Isso cria:
- `design-system/MASTER.md` — Fonte de Verdade Global com todas as regras de design
- `design-system/pages/` — Pasta para substituições (overrides) específicas de páginas

**Com substituição específica de página (override):**
```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Nome do Projeto" --page "dashboard"
```

Isso também cria:
- `design-system/pages/dashboard.md` — Desvios específicos da página em relação ao Master

**Como funciona a recuperação hierárquica:**
1. Ao construir uma página específica (ex: "Checkout"), primeiro verifique `design-system/pages/checkout.md`
2. Se o arquivo da página existir, suas regras **substituem** o arquivo Master
3. Se não, use exclusivamente o `design-system/MASTER.md`

### Passo 3: Complementar com Pesquisas Detalhadas (conforme necessário)

Após obter o sistema de design, use pesquisas de domínio para obter detalhes adicionais:

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "<palavra_chave>" --domain <dominio> [-n <resultados_max>]
```

**Quando usar pesquisas detalhadas:**

| Necessidade | Domínio | Exemplo |
|-------------|---------|---------|
| Mais opções de estilo | `style` | `--domain style "glassmorphism dark"` |
| Recomendações de gráficos | `chart` | `--domain chart "real-time dashboard"` |
| Melhores práticas de UX | `ux` | `--domain ux "animation accessibility"` |
| Fontes alternativas | `typography` | `--domain typography "elegant luxury"` |
| Estrutura de landing | `landing` | `--domain landing "hero social-proof"` |

### Passo 4: Diretrizes da Stack (Padrão: html-tailwind)

Obtenha as melhores práticas específicas de implementação. Se o usuário não especificar uma stack, **use `html-tailwind` por padrão**.

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "<palavra_chave>" --stack html-tailwind
```

Stacks disponíveis: `html-tailwind`, `react`, `nextjs`, `vue`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`

---

## Referência de Pesquisa

### Domínios Disponíveis

| Domínio | Use Para | Exemplos de Palavras-chave |
|---------|----------|----------------------------|
| `product` | Recomendações de tipo de produto | SaaS, e-commerce, portfólio, healthcare, beauty, service |
| `style` | Estilos de UI, cores, efeitos | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | Combinações de fontes, Google Fonts | elegante, divertido, profissional, moderno |
| `color` | Paletas de cores por tipo de produto | saas, ecommerce, healthcare, beauty, fintech, service |
| `landing` | Estrutura de página, estratégias de CTA | hero, hero-centric, testimonial, pricing, social-proof |
| `chart` | Tipos de gráficos, recomendações de bibliotecas | tendência, comparação, linha do tempo, funil, pizza |
| `ux` | Melhores práticas, anti-padrões | animação, acessibilidade, z-index, carregamento |
| `react` | Performance React/Next.js | waterfall, bundle, suspense, memo, rerender, cache |
| `web` | Diretrizes de interface web | aria, foco, teclado, semântico, virtualização |
| `prompt` | Prompts de IA, palavras-chave de CSS | (nome do estilo) |

### Stacks Disponíveis

| Stack | Foco |
|-------|------|
| `html-tailwind` | Utilitários Tailwind, responsividade, a11y (PADRÃO) |
| `react` | Estado, hooks, performance, padrões |
| `nextjs` | SSR, roteamento, imagens, rotas de API |
| `vue` | Composition API, Pinia, Vue Router |
| `svelte` | Runes, stores, SvelteKit |
| `swiftui` | Views, Estado, Navegação, Animação |
| `react-native` | Componentes, Navegação, Listas |
| `flutter` | Widgets, Estado, Layout, Temas |
| `shadcn` | COMPONENTES shadcn/ui, temas, formulários, padrões |
| `jetpack-compose` | Composables, Modifiers, State Hoisting, Recomposição |

---

## Exemplo de Workflow

**Pedido do usuário:** "Fazer uma landing page para um serviço de cuidados com a pele profissional"

### Passo 1: Analisar Requisitos
- Tipo de produto: Serviço de Beleza/Spa
- Palavras-chave de estilo: elegante, profissional, suave
- Setor: Beleza/Bem-estar
- Stack: html-tailwind (padrão)

### Passo 2: Gerar Sistema de Design (OBRIGATÓRIO)

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "beauty spa wellness service elegant" --design-system -p "Serenity Spa"
```

**Saída:** Sistema de design completo com padrão, estilo, cores, tipografia, efeitos e anti-padrões.

### Passo 3: Complementar com Pesquisas Detalhadas (conforme necessário)

```bash
# Obter diretrizes de UX para animação e acessibilidade
python3 .shared/ui-ux-pro-max/scripts/search.py "animation accessibility" --domain ux

# Obter opções alternativas de tipografia se necessário
python3 .shared/ui-ux-pro-max/scripts/search.py "elegant luxury serif" --domain typography
```

### Passo 4: Diretrizes da Stack

```bash
python3 .shared/ui-ux-pro-max/scripts/search.py "layout responsive form" --stack html-tailwind
```

**Então:** Sintetize o sistema de design + pesquisas detalhadas e implemente o design.

---

## Formatos de Saída

A flag `--design-system` suporta dois formatos de saída:

```bash
# Caixa ASCII (padrão) - melhor para exibição no terminal
python3 .shared/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system

# Markdown - melhor para documentação
python3 .shared/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system -f markdown
```

---

## Dicas para Melhores Resultados

1. **Seja específico com as palavras-chave** - "dashboard SaaS de saúde" > "app"
2. **Pesquise várias vezes** - Diferentes palavras-chave revelam diferentes insights
3. **Combine domínios** - Estilo + Tipografia + Cor = Sistema de design completo
4. **Sempre verifique UX** - Pesquise "animação", "z-index", "acessibilidade" para problemas comuns
5. **Use a flag de stack** - Obtenha melhores práticas específicas de implementação
6. **Itere** - Se a primeira pesquisa não corresponder, tente palavras-chave diferentes

---

## Regras Comuns para UI Profissional

Estes são problemas frequentemente ignorados que fazem a UI parecer amadora:

### Ícones e Elementos Visuais

| Regra | Faça | Não Faça |
|-------|------|----------|
| **Sem ícones emoji** | Use ícones SVG (Heroicons, Lucide, Simple Icons) | Use emojis como 🎨 🚀 ⚙️ como ícones de UI |
| **Estados de hover estáveis** | Use transições de cor/opacidade no hover | Use transformações de escala que deslocam o layout |
| **Logos de marcas corretos** | Pesquise o SVG oficial no Simple Icons | Adivinhe ou use caminhos de logo incorretos |
| **Tamanho de ícone consistente** | Use viewBox fixo (24x24) com w-6 h-6 | Misture tamanhos de ícones diferentes aleatoriamente |

### Interação e Cursor

| Regra | Faça | Não Faça |
|-------|------|----------|
| **Cursor pointer** | Adicione `cursor-pointer` em todos os cards clicáveis/interativos | Deixe o cursor padrão em elementos interativos |
| **Feedback de hover** | Forneça feedback visual (cor, sombra, borda) | Nenhuma indicação de que o elemento é interativo |
| **Transições suaves** | Use `transition-colors duration-200` | Mudanças de estado instantâneas ou muito lentas (>500ms) |

### Contraste Modo Claro/Escuro

| Regra | Faça | Não Faça |
|-------|------|----------|
| **Card 'glass' no modo claro** | Use `bg-white/80` ou opacidade maior | Use `bg-white/10` (muito transparente) |
| **Contraste de texto claro** | Use `#0F172A` (slate-900) para texto | Use `#94A3B8` (slate-400) para o corpo do texto |
| **Texto discreto claro** | Use no mínimo `#475569` (slate-600) | Use gray-400 ou mais claro |
| **Visibilidade da borda** | Use `border-gray-200` no modo claro | Use `border-white/10` (invisível) |

### Layout e Espaçamento

| Regra | Faça | Não Faça |
|-------|------|----------|
| **Navbar flutuante** | Adicione espaçamento `top-4 left-4 right-4` | Cole a navbar em `top-0 left-0 right-0` |
| **Padding do conteúdo** | Considere a altura da navbar fixa | Deixe o conteúdo se esconder atrás de elementos fixos |
| **Max-width consistente** | Use o mesmo `max-w-6xl` ou `max-w-7xl` | Misture diferentes larguras de contêiner |

---

## Checklist Pré-Entrega

Antes de entregar o código da UI, verifique estes itens:

### Qualidade Visual
- [ ] Nenhum emoji usado como ícone (use SVG)
- [ ] Todos os ícones de um conjunto consistente (Heroicons/Lucide)
- [ ] Logos de marcas estão corretos (verificados no Simple Icons)
- [ ] Estados de hover não causam deslocamento de layout
- [ ] Use cores de tema diretamente (bg-primary) em vez de wrapper var()

### Interação
- [ ] Todos os elementos clicáveis têm `cursor-pointer`
- [ ] Estados de hover fornecem feedback visual claro
- [ ] Transições são suaves (150-300ms)
- [ ] Estados de foco visíveis para navegação por teclado

### Modo Claro/Escuro
- [ ] O texto no modo claro tem contraste suficiente (mínimo 4.5:1)
- [ ] Elementos 'glass'/transparentes visíveis no modo claro
- [ ] Bordas visíveis em ambos os modos
- [ ] Teste ambos os modos antes da entrega

### Layout
- [ ] Elementos flutuantes têm espaçamento adequado das bordas
- [ ] Nenhum conteúdo escondido atrás de navbars fixas
- [ ] Responsivo em 375px, 768px, 1024px, 1440px
- [ ] Sem rolagem horizontal no mobile

### Acessibilidade
- [ ] Todas as imagens têm texto alt
- [ ] Inputs de formulário têm labels
- [ ] A cor não é o único indicador
- [ ] `prefers-reduced-motion` respeitado