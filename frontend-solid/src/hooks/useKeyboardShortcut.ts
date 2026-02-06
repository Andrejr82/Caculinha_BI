import { onMount, onCleanup } from 'solid-js';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  callback: (e: KeyboardEvent) => void;
  description?: string;
}

/**
 * Hook para registrar atalhos de teclado globais
 * Implementa WCAG 2.1 - Keyboard Accessible
 *
 * @param shortcuts - Array de atalhos a serem registrados
 * @param enabled - Se os atalhos estão habilitados (padrão: true)
 */
export function useKeyboardShortcut(shortcuts: KeyboardShortcut[], enabled: () => boolean = () => true) {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (!enabled()) return;

    // Ignorar se estiver digitando em input/textarea
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      // Exceto se for Escape (sempre funciona)
      if (e.key !== 'Escape') {
        return;
      }
    }

    for (const shortcut of shortcuts) {
      const keyMatches = e.key.toLowerCase() === shortcut.key.toLowerCase();
      const ctrlMatches = shortcut.ctrl ? e.ctrlKey || e.metaKey : !e.ctrlKey && !e.metaKey;
      const shiftMatches = shortcut.shift ? e.shiftKey : !e.shiftKey;
      const altMatches = shortcut.alt ? e.altKey : !e.altKey;

      if (keyMatches && ctrlMatches && shiftMatches && altMatches) {
        e.preventDefault();
        shortcut.callback(e);
        break;
      }
    }
  };

  onMount(() => {
    document.addEventListener('keydown', handleKeyDown);

    onCleanup(() => {
      document.removeEventListener('keydown', handleKeyDown);
    });
  });
}

// Atalhos predefinidos comuns
export const commonShortcuts = {
  search: (callback: () => void): KeyboardShortcut => ({
    key: 'k',
    ctrl: true,
    description: 'Abrir busca',
    callback: () => callback(),
  }),

  escape: (callback: () => void): KeyboardShortcut => ({
    key: 'Escape',
    description: 'Fechar/Cancelar',
    callback: () => callback(),
  }),

  help: (callback: () => void): KeyboardShortcut => ({
    key: '?',
    shift: true,
    description: 'Abrir ajuda',
    callback: () => callback(),
  }),

  save: (callback: () => void): KeyboardShortcut => ({
    key: 's',
    ctrl: true,
    description: 'Salvar',
    callback: () => callback(),
  }),

  refresh: (callback: () => void): KeyboardShortcut => ({
    key: 'r',
    ctrl: true,
    description: 'Recarregar',
    callback: () => callback(),
  }),
};
