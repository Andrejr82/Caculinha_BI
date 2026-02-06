import { createSignal, For, Show, onCleanup } from 'solid-js';
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-solid';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// Global toast store
const [toasts, setToasts] = createSignal<Toast[]>([]);

// Toast Manager API
export const toastManager = {
  show: (toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const newToast: Toast = { id, ...toast };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove after duration
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        toastManager.remove(id);
      }, duration);
    }

    return id;
  },

  success: (message: string, duration?: number) => {
    return toastManager.show({ type: 'success', message, duration });
  },

  error: (message: string, duration?: number) => {
    return toastManager.show({ type: 'error', message, duration });
  },

  info: (message: string, duration?: number) => {
    return toastManager.show({ type: 'info', message, duration });
  },

  warning: (message: string, duration?: number) => {
    return toastManager.show({ type: 'warning', message, duration });
  },

  remove: (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  },

  clear: () => {
    setToasts([]);
  }
};

// Toast Item Component
function ToastItem(props: { toast: Toast }) {
  const getIcon = () => {
    switch (props.toast.type) {
      case 'success':
        return <CheckCircle size={20} />;
      case 'error':
        return <XCircle size={20} />;
      case 'warning':
        return <AlertTriangle size={20} />;
      case 'info':
        return <Info size={20} />;
    }
  };

  const getColorClasses = () => {
    switch (props.toast.type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-400 border-green-200 dark:border-green-800';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 border-red-200 dark:border-red-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400 border-blue-200 dark:border-blue-800';
    }
  };

  return (
    <div
      class={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] max-w-md animate-in slide-in-from-right duration-300 ${getColorClasses()}`}
      role="alert"
      aria-live="polite"
    >
      <div class="flex-shrink-0">
        {getIcon()}
      </div>
      <div class="flex-1 text-sm font-medium">
        {props.toast.message}
      </div>
      <button
        onClick={() => toastManager.remove(props.toast.id)}
        class="flex-shrink-0 p-1 hover:bg-black/10 dark:hover:bg-white/10 rounded transition-colors"
        aria-label="Fechar notificação"
      >
        <X size={16} />
      </button>
    </div>
  );
}

// Toast Container Component
export function ToastContainer() {
  return (
    <div
      class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none"
      aria-label="Notificações"
    >
      <For each={toasts()}>
        {(toast) => (
          <div class="pointer-events-auto">
            <ToastItem toast={toast} />
          </div>
        )}
      </For>
    </div>
  );
}
