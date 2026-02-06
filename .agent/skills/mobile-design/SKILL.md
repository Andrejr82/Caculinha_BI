---
name: mobile-design
description: Pensamento de design e tomada de decisão para apps iOS e Android (Mobile-first). Interação por toque, padrões de performance, convenções de plataforma. Ensina princípios, não valores fixos. Use ao construir apps React Native, Flutter ou nativos.
allowed-tools: Read, Glob, Grep, Bash
---

# Sistema de Design Mobile

> **Filosofia:** Focado no toque. Consciente com a bateria. Respeitoso com a plataforma. Capaz de funcionar offline.
> **Princípio Core:** Mobile NÃO é um desktop pequeno. PENSE nas restrições mobile, PERGUNTE a escolha da plataforma.

---

## 🔧 Scripts de Execução

**Execute estes para validação (não leia, apenas rode):**

| Script | Propósito | Uso |
|--------|-----------|-----|
| `scripts/mobile_audit.py` | Auditoria de UX Mobile & Toque | `python scripts/mobile_audit.py <caminho_projeto>` |

---

## 🔴 OBRIGATÓRIO: Leia os Arquivos de Referência Antes de Trabalhar!

**⛔ NÃO inicie o desenvolvimento até ler os arquivos relevantes:**

### Universal (Sempre Leia)

| Arquivo | Conteúdo | Status |
|------|---------|--------|
| **[mobile-design-thinking.md](mobile-design-thinking.md)** | **⚠️ ANTI-MEMORIZAÇÃO: Força o pensamento, evita padrões de IA** | **⬜ CRÍTICO PRIMEIRO** |
| **[touch-psychology.md](touch-psychology.md)** | **Lei de Fitts, gestos, haptics, zona do polegar** | **⬜ CRÍTICO** |
| **[mobile-performance.md](mobile-performance.md)** | **Performance RN/Flutter, 60fps, memória** | **⬜ CRÍTICO** |
| **[mobile-backend.md](mobile-backend.md)** | **Notificações push, sync offline, API mobile** | **⬜ CRÍTICO** |
| **[mobile-testing.md](mobile-testing.md)** | **Pirâmide de testes, E2E, específico por plataforma** | **⬜ CRÍTICO** |
| **[mobile-debugging.md](mobile-debugging.md)** | **Debug nativo vs JS, Flipper, Logcat** | **⬜ CRÍTICO** |

---

## ⚠️ CRÍTICO: PERGUNTE ANTES DE ASSUMIR (OBRIGATÓRIO)

> **PARE! Se o pedido do usuário for aberto, NÃO use seus favoritos por padrão.**

### Você DEVE perguntar se não for especificado:

| Aspecto | Pergunta | Por que |
|---------|----------|---------|
| **Plataforma** | "iOS, Android ou ambos?" | Afeta CADA decisão de design |
| **Framework** | "React Native, Flutter ou nativo?" | Determina padrões e ferramentas |
| **Navegação** | "Tab bar, drawer ou baseado em stack?" | Decisão core de UX |
| **Estado (State)** | "Qual gerenciamento de estado? (Zustand/Redux/Riverpod/BLoC?)" | Fundação da arquitetura |
| **Offline** | "Precisa funcionar offline?" | Afeta a estratégia de dados |
| **Dispositivos alvo** | "Apenas celular ou suporte a tablet?" | Complexidade do layout |

---

## ⛔ ANTI-PADRÕES MOBILE DE IA (LISTA PROIBIDA)

> 🚫 **Evite estas tendências automáticas de IA!**

#### Pecados de Performance

| ❌ NUNCA FAÇA | Por que está errado | ✅ SEMPRE FAÇA |
|---------------|----------------------|----------------|
| **ScrollView para listas longas** | Renderiza TUDO, memória explode | Use `FlatList` / `FlashList` / `ListView.builder` |
| **Função renderItem inline** | Nova função a cada render, itens re-renderizam | `useCallback` + `React.memo` |
| **Sem keyExtractor** | Chaves baseadas em índice causam bugs | ID único e estável dos dados |
| **Pular o getItemLayout** | Layout assíncrono = scroll travado | Forneça quando os itens tiverem altura fixa |
| **setState() em todo lugar** | Rebuilds desnecessários de widgets | Estado direcionado, construtores `const` |
| **Native driver: false** | Animações bloqueadas pela thread de JS | `useNativeDriver: true` sempre |
| **console.log em produção** | Bloqueia pesadamente a thread de JS | Remova antes do build de release |

#### Pecados de Toque/UX

| ❌ NUNCA FAÇA | Por que está errado | ✅ SEMPRE FAÇA |
|---------------|----------------------|----------------|
| **Alvo de toque < 44px** | Impossível tocar com precisão, frustrante | Mínimo 44pt (iOS) / 48dp (Android) |
| **Espaçamento < 8px entre alvos** | Toques acidentais nos vizinhos | Espaço mínimo de 8-12px |
| **Interação apenas por gestos** | Exclui usuários com limitações motoras | Sempre ofereça alternativa via botão |
| **Sem estado de carregamento** | Usuário pensa que o app travou | SEMPRE mostre feedback de loading |
| **Sem tratamento de erro** | Usuário preso, sem caminho de volta | Mostre erro com opção de repetir |
| **Ignorar convenções de plataforma** | Usuários confusos, memória muscular quebrada | iOS parece iOS, Android parece Android |

---

## 📱 Matriz de Decisão de Plataforma

| Elemento | iOS | Android |
|----------|-----|---------|
| **Fonte Primária** | SF Pro / SF Compact | Roboto |
| **Alvo de Toque Mín.** | 44pt × 44pt | 48dp × 48dp |
| **Navegação de Volta** | Swipe da borda esquerda | Botão/gesto de voltar do sistema |
| **Ícones da Tab Bar** | SF Symbols | Material Symbols |
| **Action Sheet** | UIActionSheet vindo de baixo | Bottom Sheet / Diálogo |
| **Progresso** | Spinner | Progresso linear (Material) |

---

## 🧠 Psicologia de UX Mobile

### Zona do Polegar (Uso com uma mão)

```
┌─────────────────────────────┐
│    DIFÍCIL DE ALCANÇAR      │ ← Navegação, menu, voltar
│       (esforço)             │
├─────────────────────────────┤
│      OK DE ALCANÇAR         │ ← Ações secundárias
│        (natural)            │
├─────────────────────────────┤
│     FÁCIL DE ALCANÇAR       │ ← CTAs PRINCIPAIS, tab bar
│ (arco natural do polegar)   │ ← Interação principal de conteúdo
└─────────────────────────────┘
```

---

## ⚡ Princípios de Performance

### Regras Críticas para React Native

```typescript
// ✅ CORRETO: renderItem memoizado + wrapper React.memo
const ListItem = React.memo(({ item }: { item: Item }) => (
  <View style={styles.item}>
    <Text>{item.title}</Text>
  </View>
));

const renderItem = useCallback(
  ({ item }: { item: Item }) => <ListItem item={item} />,
  []
);
```

### Regras Críticas para Flutter

```dart
// ✅ CORRETO: Construtores const evitam re-renderizações
class MyWidget extends StatelessWidget {
  const MyWidget({super.key}); // CONST!

  @override
  Widget build(BuildContext context) {
    return const Column( // CONST!
      children: [
        Text('Conteúdo estático'),
        MyConstantWidget(),
      ],
    );
  }
}
```

---

## 📝 CHECKPOINT (OBRIGATÓRIO Antes de qualquer trabalho Mobile)

> **Antes de escrever qualquer código mobile, você DEVE completar este checkpoint:**

```
🧠 CHECKPOINT:

Plataforma:  [ iOS / Android / Ambos ]
Framework:   [ React Native / Flutter / SwiftUI / Kotlin ]
Arquivos Lidos: [ Liste os arquivos de skill que você leu ]

3 Princípios que Aplicarei:
1. _______________
2. _______________
3. _______________

Anti-padrões que Evitarei:
1. _______________
2. _______________
```

---

> **Lembre-se:** Usuários mobile são impacientes, constantemente interrompidos e usam dedos imprecisos em telas pequenas. Projete para as PIORES condições: rede ruim, uma mão só, sol forte, bateria baixa. Se funcionar lá, funciona em qualquer lugar.
