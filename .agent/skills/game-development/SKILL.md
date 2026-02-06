---
name: game-development
description: Orquestrador de desenvolvimento de jogos. Encaminha para skills específicas de plataforma com base nas necessidades do projeto.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Desenvolvimento de Jogos

> **Skill orquestradora** que fornece princípios core e direciona para sub-skills especializadas.

---

## Quando Usar Esta Skill

Você está trabalhando em um projeto de desenvolvimento de jogos. Esta skill ensina os PRINCÍPIOS do desenvolvimento de jogos e o direciona para a sub-skill correta baseada no contexto.

---

## Roteamento de Sub-Skills

### Seleção de Plataforma

| Se o jogo visa... | Use a Sub-Skill |
|-------------------|-----------------|
| Navegadores web (HTML5, WebGL) | `game-development/web-games` |
| Mobile (iOS, Android) | `game-development/mobile-games` |
| PC (Steam, Desktop) | `game-development/pc-games` |
| Headsets de VR/AR | `game-development/vr-ar` |

### Seleção de Dimensão

| Se o jogo é... | Use a Sub-Skill |
|----------------|-----------------|
| 2D (sprites, tilemaps) | `game-development/2d-games` |
| 3D (meshes, shaders) | `game-development/3d-games` |

### Áreas de Especialidade

| Se você precisa de... | Use a Sub-Skill |
|-----------------------|-----------------|
| GDD, balanceamento, psicologia do jogador | `game-development/game-design` |
| Multiplayer, rede | `game-development/multiplayer` |
| Estilo visual, pipeline de assets, animação | `game-development/game-art` |
| Design de som, música, áudio adaptativo | `game-development/game-audio` |

---

## Princípios Core (Todas as Plataformas)

### 1. O Game Loop (Loop do Jogo)

Todo jogo, independente da plataforma, segue este padrão:

```
INPUT  → Ler ações do jogador
UPDATE → Processar lógica do jogo (fixed timestep)
RENDER → Desenhar o frame (interpolado)
```

**Regra do Timestep Fixo:**
- Física/lógica: Taxa fixa (ex: 50Hz)
- Renderização: O mais rápido possível
- Interpolar entre estados para visuais suaves

---

### 2. Matriz de Seleção de Padrões

| Padrão | Use Quando | Exemplo |
|--------|------------|---------|
| **State Machine** | 3-5 estados discretos | Jogador: Idle→Walk→Jump |
| **Object Pooling** | Criação/destruição frequente | Balas, partículas |
| **Observer/Events** | Comunicação entre sistemas | Atualizações de Vida→UI |
| **ECS** | Milhares de entidades similares | Unidades de RTS, partículas |
| **Command** | Desfazer, replay, rede | Gravação de input |
| **Behavior Tree** | Decisões complexas de IA | IA de Inimigo |

**Regra de Decisão:** Comece com State Machine. Adicione ECS apenas quando a performance exigir.

---

### 3. Abstração de Input

Abstraia os inputs em AÇÕES, não em teclas brutas:

```
"pular"  → Espaço, Gamepad A, Toque na tela
"mover"  → WASD, Stick esquerdo, Joystick virtual
```

**Por que:** Permite controles remapeáveis e multiplataforma.

---

### 4. Orçamento de Performance (60 FPS = 16.67ms)

| Sistema | Orçamento |
|---------|-----------|
| Input | 1ms |
| Física | 3ms |
| IA | 2ms |
| Lógica do Jogo | 4ms |
| Renderização | 5ms |
| Buffer | 1.67ms |

**Prioridade de Otimização:**
1. Algoritmo (O(n²) → O(n log n))
2. Batching (reduzir draw calls)
3. Pooling (evitar picos de GC)
4. LOD (detalhe por distância)
5. Culling (pular o que é invisível)

---

### 5. Seleção de IA por Complexidade

| Tipo de IA | Complexidade | Use Quando |
|------------|--------------|------------|
| **FSM** | Simples | 3-5 estados, comportamento previsível |
| **Behavior Tree** | Média | Modular, amigável para designers |
| **GOAP** | Alta | Emergente, baseado em planejamento |
| **Utility AI** | Alta | Decisões baseadas em pontuação (scoring) |

---

### 6. Estratégia de Colisão

| Tipo | Melhor Para |
|------|-------------|
| **AABB** | Retângulos, verificações rápidas |
| **Circle** | Objetos redondos, barato |
| **Spatial Hash** | Muitos objetos de tamanho similar |
| **Quadtree** | Mundos grandes, tamanhos variados |

---

## Anti-Padrões (Universais)

| NÃO FAÇA | FAÇA |
|----------|------|
| Atualizar tudo a cada frame | Use eventos, flags de sujeira (dirty) |
| Criar objetos em loops críticos (hot loops) | Object pooling |
| Não usar cache | Cache de referências |
| Otimizar sem profiling | Fazer profiling primeiro |
| Misturar input com lógica | Abstrair camada de input |

---

## Exemplos de Roteamento

### Exemplo 1: "Quero fazer um jogo de plataforma 2D para navegador"
→ Comece com `game-development/web-games` para seleção de framework
→ Depois `game-development/2d-games` para padrões de sprite/tilemap
→ Referencie `game-development/game-design` para design de níveis

### Exemplo 2: "Jogo de puzzle mobile para iOS e Android"
→ Comece com `game-development/mobile-games` para input de toque e lojas
→ Use `game-development/game-design` para balanceamento do puzzle

### Exemplo 3: "Shooter em VR multiplayer"
→ `game-development/vr-ar` para conforto e imersão
→ `game-development/3d-games` para renderização
→ `game-development/multiplayer` para rede

---

> **Lembre-se:** Grandes jogos vêm da iteração, não da perfeição. Prototipe rápido, depois refine.
