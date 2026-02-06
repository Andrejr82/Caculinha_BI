import { onMount, onCleanup } from 'solid-js';

/**
 * Hook para prender o foco dentro de um elemento (modal, dialog, etc.)
 * Implementa WCAG 2.1 - Focus Trap para acessibilidade
 *
 * @param isActive - Se o trap está ativo
 * @param containerRef - Ref do container que deve prender o foco
 */
export function useFocusTrap(isActive: () => boolean, containerRef: () => HTMLElement | undefined) {
  let previouslyFocusedElement: HTMLElement | null = null;

  const getFocusableElements = (container: HTMLElement): HTMLElement[] => {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (!isActive()) return;

    const container = containerRef();
    if (!container) return;

    // ESC para fechar (será tratado pelo componente)
    if (e.key === 'Escape') {
      return;
    }

    // TAB navigation
    if (e.key === 'Tab') {
      const focusableElements = getFocusableElements(container);

      if (focusableElements.length === 0) {
        e.preventDefault();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // SHIFT + TAB (backward)
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      }
      // TAB (forward)
      else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  };

  onMount(() => {
    // Salvar elemento focado anteriormente
    if (isActive()) {
      previouslyFocusedElement = document.activeElement as HTMLElement;

      // Focar no primeiro elemento focável do container
      const container = containerRef();
      if (container) {
        const focusableElements = getFocusableElements(container);
        if (focusableElements.length > 0) {
          setTimeout(() => focusableElements[0].focus(), 100);
        }
      }
    }

    // Adicionar listener de teclado
    document.addEventListener('keydown', handleKeyDown);

    onCleanup(() => {
      document.removeEventListener('keydown', handleKeyDown);

      // Restaurar foco ao elemento anterior
      if (previouslyFocusedElement && !isActive()) {
        setTimeout(() => previouslyFocusedElement?.focus(), 0);
      }
    });
  });
}
