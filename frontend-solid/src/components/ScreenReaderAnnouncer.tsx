import { createSignal, Show, onCleanup } from 'solid-js';

type AnnouncementPriority = 'polite' | 'assertive';

interface Announcement {
  id: string;
  message: string;
  priority: AnnouncementPriority;
}

// Global announcement state
const [announcements, setAnnouncements] = createSignal<Announcement[]>([]);

/**
 * Screen Reader Announcer Manager
 * Implementa WCAG 2.1 - Live Regions para anúncios dinâmicos
 */
export const announcer = {
  /**
   * Anuncia uma mensagem para screen readers
   * @param message - Mensagem a ser anunciada
   * @param priority - 'polite' (padrão, aguarda) ou 'assertive' (interrompe)
   */
  announce: (message: string, priority: AnnouncementPriority = 'polite') => {
    const id = `announcement-${Date.now()}-${Math.random()}`;
    const announcement: Announcement = { id, message, priority };

    setAnnouncements(prev => [...prev, announcement]);

    // Remove após 5 segundos (tempo suficiente para ser lido)
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(a => a.id !== id));
    }, 5000);
  },

  /**
   * Atalho para anúncios polidos (padrão)
   */
  polite: (message: string) => {
    announcer.announce(message, 'polite');
  },

  /**
   * Atalho para anúncios assertivos (urgente)
   */
  assertive: (message: string) => {
    announcer.announce(message, 'assertive');
  },

  /**
   * Limpa todas as mensagens
   */
  clear: () => {
    setAnnouncements([]);
  },
};

/**
 * Componente de Screen Reader Announcer
 * Deve ser renderizado uma vez no root da aplicação
 */
export function ScreenReaderAnnouncer() {
  return (
    <>
      {/* Região para anúncios polidos (não interrompe) */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        class="sr-only"
      >
        <Show when={announcements().find(a => a.priority === 'polite')}>
          {(announcement) => announcement().message}
        </Show>
      </div>

      {/* Região para anúncios assertivos (interrompe) */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        class="sr-only"
      >
        <Show when={announcements().find(a => a.priority === 'assertive')}>
          {(announcement) => announcement().message}
        </Show>
      </div>
    </>
  );
}

/**
 * Hook para anunciar mudanças de loading/sucesso/erro
 * Útil para feedback de operações assíncronas
 */
export function useLoadingAnnouncer() {
  return {
    loading: (message: string = 'Carregando...') => {
      announcer.polite(message);
    },
    success: (message: string) => {
      announcer.polite(message);
    },
    error: (message: string) => {
      announcer.assertive(message);
    },
  };
}
