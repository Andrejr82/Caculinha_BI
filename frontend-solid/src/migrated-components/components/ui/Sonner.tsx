import { createSignal, For, type JSX } from "solid-js";
import { Portal } from "solid-js/web";
import { cn } from "../../utils/cn";

type ToastType = "default" | "success" | "error" | "warning";

interface Toast {
  id: string;
  message: string;
  type?: ToastType;
  duration?: number;
}

const [toasts, setToasts] = createSignal<Toast[]>([]);

/**
 * Toast notification system (Sonner alternative)
 * Migrated from React to SolidJS (native implementation)
 */
export function toast(message: string, options?: { type?: ToastType; duration?: number }) {
  const id = Math.random().toString(36).substr(2, 9);
  const newToast: Toast = {
    id,
    message,
    type: options?.type || "default",
    duration: options?.duration || 3000,
  };

  setToasts((prev) => [...prev, newToast]);

  setTimeout(() => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, newToast.duration);
}

/**
 * Toaster component - renders toast notifications
 */
export function Toaster() {
  const getToastClasses = (type: ToastType) => {
    const base = "rounded-lg border p-4 shadow-lg";
    switch (type) {
      case "success": return `${base} bg-green-50 border-green-200 text-green-900`;
      case "error": return `${base} bg-red-50 border-red-200 text-red-900`;
      case "warning": return `${base} bg-yellow-50 border-yellow-200 text-yellow-900`;
      default: return `${base} bg-background border-border`;
    }
  };

  return (
    <Portal>
      <div
        data-slot="toaster"
        class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md"
      >
        <For each={toasts()}>
          {(t) => (
            <div
              data-slot="toast"
              class={cn(
                getToastClasses(t.type || "default"),
                "animate-in slide-in-from-right"
              )}
            >
              {t.message}
            </div>
          )}
        </For>
      </div>
    </Portal>
  );
}
