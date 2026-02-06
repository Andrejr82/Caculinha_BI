---
name: frontend-design
description: Pensamento de design e tomada de decisão para UI web. Use ao projetar componentes, layouts, esquemas de cores, tipografia ou criar interfaces estéticas. Ensina princípios, não valores fixos.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Sistema de Design Frontend

> **Filosofia:** Cada pixel tem um propósito. Restrição é luxo. A psicologia do usuário guia as decisões.
> **Princípio Core:** PENSE, não memorize. PERGUNTE, não assuma.

---

## 🎯 Regra de Leitura Seletiva (OBRIGATÓRIO)

**Leia arquivos OBRIGATÓRIOS sempre, OPCIONAIS apenas quando necessário:**

| Arquivo | Status | Quando Ler |
|---------|--------|------------|
| [ux-psychology.md](ux-psychology.md) | 🔴 **OBRIGATÓRIO** | Sempre leia primeiro! |
| [color-system.md](color-system.md) | ⚪ Opcional | Decisões de cor/paleta |
| [typography-system.md](typography-system.md) | ⚪ Opcional | Seleção/combinação de fontes |
| [visual-effects.md](visual-effects.md) | ⚪ Opcional | Glassmorphism, sombras, gradientes |
| [animation-guide.md](animation-guide.md) | ⚪ Opcional | Animação necessária |
| [motion-graphics.md](motion-graphics.md) | ⚪ Opcional | Lottie, GSAP, 3D |
| [decision-trees.md](decision-trees.md) | ⚪ Opcional | Templates de contexto |

> 🔴 **ux-psychology.md = SEMPRE LEIA. Outros = apenas se relevante.**

---

## 🔧 Scripts de Execução

**Execute-os para auditorias (não leia, apenas rode):**

| Script | Propósito | Uso |
|--------|-----------|-----|
| `scripts/ux_audit.py` | Auditoria de Psicologia UX & Acessibilidade | `python scripts/ux_audit.py <caminho_projeto>` |

---

## ⚠️ CRÍTICO: PERGUNTE ANTES DE ASSUMIR (OBRIGATÓRIO)

> **PARE! Se o pedido do usuário for aberto, NÃO use seus padrões favoritos.**

### Quando o Pedido for Vago, PERGUNTE:

**Cor não especificada?** Pergunte:
> "Qual paleta de cores você prefere? (azul/verde/laranja/neutra/outra?)"

**Estilo não especificado?** Pergunte: 
> "Qual estilo você deseja? (minimalista/ousado/retro/futurista/orgânico?)"

**Layout não especificado?** Pergunte:
> "Você tem uma preferência de layout? (coluna única/grid/assimétrico/largura total?)"

### ⛔ TENDÊNCIAS PADRÃO A EVITAR (ANTI-PORTO SEGURO):

| Tendência Padrão de IA | Por que é Ruim | Pense Diferente |
|------------------------|-----------------|-----------------|
| **Bento Grids (Clichê Moderno)** | Usado em todo design de IA | Por que este conteúdo PRECISA de um grid? |
| **Hero Split (Esquerda/Direita)** | Previsível e Chato | Que tal Tipografia Massiva ou Narrativa Vertical? |
| **Gradientes Mesh/Aurora** | O "novo" fundo preguiçoso | Qual seria uma combinação de cores radical? |
| **Glassmorphism** | A ideia de "premium" da IA | Que tal um flat sólido de alto contraste? |
| **Ciano Profundo / Azul Fintech** | Porto seguro contra a proibição do roxo | Por que não Vermelho, Preto ou Verde Neon? |
| **"Orquestrar / Empoderar"** | Copywriting gerado por IA | Como um humano diria isso? |
| Fundo escuro + brilho neon | Super usado, "cara de IA" | O que a MARCA realmente precisa? |
| **Tudo arredondado** | Genérico/Seguro | Onde posso usar bordas brutas e afiadas? |

> 🔴 **"Cada estrutura 'segura' que você escolhe o deixa um passo mais perto de um template genérico. CORRA RISCOS."**

---

## 1. Análise de Restrições (SEMPRE PRIMEIRO)

Antes de qualquer trabalho de design, RESPONDA ESTAS QUESTÕES ou PERGUNTE AO USUÁRIO:

| Restrição | Pergunta | Por que Importa |
|-----------|----------|-----------------|
| **Cronograma** | Quanto tempo temos? | Determina a complexidade |
| **Conteúdo** | Pronto ou placeholder? | Afeta a flexibilidade do layout |
| **Marca** | Diretrizes existentes? | Pode ditar cores/fontes |
| **Tecnologia** | Qual stack? | Afeta as capacidades |
| **Público** | Quem exatamente? | Guia todas as decisões visuais |

### Público → Abordagem de Design

| Público | Pense Sobre |
|---------|-------------|
| **Gen Z** | Ousado, rápido, mobile-first, autêntico |
| **Millennials** | Limpo, minimalista, focado em valor |
| **Gen X** | Familiar, confiável, claro |
| **Boomers** | Legível, alto contraste, simples |
| **B2B** | Profissional, focado em dados, confiança |
| **Luxo** | Elegância contida, espaço em branco |

---

## 2. Princípios de Psicologia UX

### Leis Core (Internalize Estas)

| Lei | Princípio | Aplicação |
|-----|-----------|-----------|
| **Lei de Hick** | Mais escolhas = decisões mais lentas | Limite opções, use divulgação progressiva |
| **Lei de Fitts** | Maior + próximo = mais fácil de clicar | Dimensione os CTAs apropriadamente |
| **Lei de Miller** | ~7 itens na memória de trabalho | Agrupe o conteúdo em blocos |
| **Efeito Von Restorff** | Diferente = memorável | Torne os CTAs visualmente distintos |
| **Posição Serial** | Primeiro/último são mais lembrados | Info chave no início/fim |

### Níveis de Design Emocional

```
VISCERAL (instante) → Primeira impressão: cores, imagens, sensação geral
COMPORTAMENTAL (uso) → Usando: velocidade, feedback, eficiência
REFLEXIVO (memória) → Depois: "Gosto do que isso diz sobre mim"
```

### Construção de Confiança

- Indicadores de segurança em ações sensíveis
- Prova social onde relevante
- Acesso claro a contato/suporte
- Design consistente e profissional
- Políticas transparentes

---

## 3. Princípios de Layout

### Proporção Áurea (φ = 1.618)

```
Use para harmonia proporcional:
├── Conteúdo : Sidebar = cerca de 62% : 38%
├── Cada tamanho de título = anterior × 1.618 (para escala dramática)
├── Espaçamento pode seguir: sm → md → lg (cada um × 1.618)
```

### Conceito de Grid de 8 Pontos

```
Todo espaçamento e dimensionamento em múltiplos de 8:
├── Apertado: 4px (meio passo para micro)
├── Pequeno: 8px
├── Médio: 16px
├── Grande: 24px, 32px
├── XL: 48px, 64px, 80px
└── Ajuste baseado na densidade do conteúdo
```

### Princípios Chave de Dimensionamento

| Elemento | Consideração |
|----------|--------------|
| **Alvos de toque** | Tamanho mínimo confortável para toque |
| **Botões** | Altura baseada na hierarquia de importância |
| **Inputs** | Combinar altura com botões para alinhamento |
| **Cards** | Espaçamento consistente, respirável |
| **Largura de leitura** | 45-75 caracteres é o ideal |

---

## 4. Princípios de Cor

### Regra 60-30-10

```
60% → Primária/Fundo (base calma, neutra)
30% → Secundária (áreas de suporte)
10% → Destaque/Accent (CTAs, realces, atenção)
```

### Psicologia das Cores (Para Tomada de Decisão)

| Se Você Precisa de... | Considere Matizes | Evite |
|-----------------------|-------------------|-------|
| Confiança, calma | Família do Azul | Vermelhos agressivos |
| Crescimento, natureza | Família do Verde | Cinzas industriais |
| Energia, urgência | Laranja, Vermelho | Azuis passivos |
| Luxo, criatividade | Teal Profundo, Ouro, Esmeralda | Brilhantes com aspecto barato |
| Limpo, minimalista | Neutros | Cores esmagadoras |

### Processo de Seleção

1. **Qual é o setor?** (afunila as opções)
2. **Qual é a emoção?** (escolhe a primária)
3. **Modo claro ou escuro?** (define a base)
4. **PERGUNTE AO USUÁRIO** se não estiver especificado

Para teoria das cores detalhada: [color-system.md](color-system.md)

---

## 5. Princípios de Tipografia

### Seleção de Escala

| Tipo de Conteúdo | Razão de Escala | Sensação |
|------------------|-----------------|----------|
| UI Densa | 1.125-1.2 | Compacta, eficiente |
| Web Geral | 1.25 | Equilibrada (mais comum) |
| Editorial | 1.333 | Legível, espaçosa |
| Hero/Destaque | 1.5-1.618 | Impacto dramático |

### Conceito de Combinação (Pairing)

```
Contraste + Harmonia:
├── DIFERENTE o suficiente para hierarquia
├── SEMELHANTE o suficiente para coesão
└── Geralmente: display + neutra, ou serif + sans
```

### Regras de Legibilidade

- **Comprimento da linha**: 45-75 caracteres ideal
- **Altura da linha (Line height)**: 1.4-1.6 para texto do corpo
- **Contraste**: Verifique os requisitos WCAG
- **Tamanho**: 16px+ para corpo na web

Para tipografia detalhada: [typography-system.md](typography-system.md)

---

## 6. Princípios de Efeitos Visuais

### Glassmorphism (Quando Apropriado)

```
Propriedades chave:
├── Fundo semi-transparente
├── Backdrop blur (desfoque de fundo)
├── Borda sutil para definição
└── ⚠️ **AVISO:** Glassmorphism padrão azul/branco é um clichê moderno. Use de forma radical ou não use.
```

### Hierarquia de Sombras

```
Conceito de elevação:
├── Elementos mais altos = sombras maiores
├── Y-offset > X-offset (luz vindo de cima)
├── Múltiplas camadas = mais realista
└── Modo escuro: pode precisar de brilho (glow) em vez de sombra
```

### Uso de Gradientes

```
Gradientes harmoniosos:
├── Cores adjacentes no círculo (análogas)
├── OU mesmo matiz, brilhos diferentes
├── Evite pares complementares agressivos
├── 🚫 **NÃO use Gradientes Mesh/Aurora** (bolhas flutuantes)
└── VARIE radicalmente de projeto para projeto
```

Para guia completo de efeitos: [visual-effects.md](visual-effects.md)

---

## 7. Princípios de Animação

### Conceito de Timing

```
Duração baseada em:
├── Distância (mais longe = mais longo)
├── Tamanho (maior = mais lento)
├── Importância (crítico = claro)
└── Contexto (urgente = rápido, luxo = lento)
```

### Seleção de Easing

| Ação | Easing | Por que |
|------|--------|---------|
| Entrando | Ease-out | Desacelerar, assentar |
| Saindo | Ease-in | Acelerar, sair |
| Ênfase | Ease-in-out | Suave, deliberado |
| Divertido | Bounce | Divertido, energético |

### Performance

- Anime apenas transform e opacity
- Respeite a preferência de movimento reduzido (reduced-motion)
- Teste em dispositivos de baixo desempenho

Para padrões de animação: [animation-guide.md](animation-guide.md), para avançado: [motion-graphics.md](motion-graphics.md)

---

## 8. Checklist do "Fator Uau"

### Indicadores Premium

- [ ] Espaço em branco generoso (luxo = espaço para respirar)
- [ ] Profundidade e dimensão sutis
- [ ] Animações suaves e com propósito
- [ ] Atenção aos detalhes (alinhamento, consistência)
- [ ] Ritmo visual coeso
- [ ] Elementos customizados (nem tudo padrão)

### Construtores de Confiança

- [ ] Sinais de segurança onde apropriado
- [ ] Prova social / depoimentos
- [ ] Proposta de valor clara
- [ ] Imagens profissionais
- [ ] Linguagem de design consistente

### Gatilhos Emocionais

- [ ] Hero que evoca a emoção pretendida
- [ ] Elementos humanos (rostos, histórias)
- [ ] Indicadores de progresso/conquista
- [ ] Momentos de deleite (delight)

---

## 9. Anti-Padrões (O Que NÃO Fazer)

### ❌ Indicadores de Design Preguiçoso

- Fontes padrão do sistema sem consideração
- Imagens de banco que não combinam
- Espaçamento inconsistente
- Muitas cores competindo
- Paredes de texto sem hierarquia
- Contraste inacessível

### ❌ Padrões de Tendência de IA (EVITE!)

- **Mesmas cores em todo projeto**
- **Escuro + neon como padrão**
- **Tudo roxo/violeta (PROIBIÇÃO DO ROXO ✅)**
- **Bento grids para landing pages simples**
- **Gradientes Mesh & Efeitos de Brilho**
- **Mesma estrutura de layout / Clone da Vercel**
- **Não perguntar as preferências do usuário**

### ❌ Dark Patterns (Antiéticos)

- Custos ocultos
- Urgência falsa
- Ações forçadas
- UI enganosa
- "Confirmshaming" (fazer o usuário se sentir culpado ao negar)

---

## 10. Resumo do Processo de Decisão

```
Para CADA tarefa de design:

1. RESTRIÇÕES
   └── Qual o cronograma, marca, tecnologia, público?
   └── Se estiver incerto → PERGUNTE

2. CONTEÚDO
   └── Que conteúdo existe?
   └── Qual a hierarquia?

3. DIREÇÃO DE ESTILO
   └── O que é apropriado para o contexto?
   └── Se estiver incerto → PERGUNTE (não use o padrão!)

4. EXECUÇÃO
   └── Aplique os princípios acima
   └── Verifique contra os anti-padrões

5. REVISÃO
   └── "Isso serve ao usuário?"
   └── "Isso é diferente dos meus padrões?"
   └── "Eu teria orgulho disso?"
```

---

## Arquivos de Referência

Para orientações mais profundas em áreas específicas:

- [color-system.md](color-system.md) - Teoria das cores e processo de seleção
- [typography-system.md](typography-system.md) - Combinação de fontes e decisões de escala
- [visual-effects.md](visual-effects.md) - Princípios e técnicas de efeitos
- [animation-guide.md](animation-guide.md) - Princípios de motion design
- [motion-graphics.md](motion-graphics.md) - Avançado: Lottie, GSAP, SVG, 3D, Partículas
- [decision-trees.md](decision-trees.md) - Templates específicos de contexto
- [ux-psychology.md](ux-psychology.md) - Mergulho profundo na psicologia do usuário

---

> **Lembre-se:** Design é PENSAR, não copiar. Cada projeto merece uma nova consideração baseada em seu contexto único e usuários. **Evite o Porto Seguro do SaaS Moderno!**
