# Utilitários Migrados

Utilitários compartilhados migrados do frontend React para SolidJS.

## Arquivos

### `cn.ts`
Função para combinar classes CSS com suporte a Tailwind. Usa `clsx` e `tailwind-merge`.

```typescript
import { cn } from './cn';

// Exemplo de uso
const className = cn('base-class', condition && 'conditional-class', 'another-class');
```

### `a11y.ts`
Funções utilitárias para acessibilidade:

- `generateAriaId(prefix)` - Gera IDs únicos para elementos ARIA
- `announceToScreenReader(message, priority)` - Anuncia mensagens para screen readers
- `isVisibleToScreenReader(element)` - Verifica visibilidade para screen readers
- `trapFocus(container)` - Gerencia foco em modais/dialogs

```typescript
import { trapFocus, announceToScreenReader } from './a11y';

// Exemplo: trap focus em modal
const cleanup = trapFocus(modalElement);
// Chamar cleanup() quando fechar o modal

// Exemplo: anunciar mensagem
announceToScreenReader('Dados salvos com sucesso!', 'polite');
```

## Compatibilidade

Todos os utilitários são compatíveis com SolidJS e não dependem de APIs específicas do React.
