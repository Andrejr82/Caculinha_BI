import { createSignal, Show } from 'solid-js';
import { AlertTriangle, Trash2, X } from 'lucide-solid';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { announcer } from './ScreenReaderAnnouncer';

export interface ConfirmDialogOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
}

// Global confirm dialog state
const [isOpen, setIsOpen] = createSignal(false);
const [dialogOptions, setDialogOptions] = createSignal<ConfirmDialogOptions | null>(null);
const [isProcessing, setIsProcessing] = createSignal(false);

// Confirm Dialog Manager API
export const confirmDialog = {
  show: (options: ConfirmDialogOptions) => {
    setDialogOptions(options);
    setIsOpen(true);
  },

  danger: (title: string, message: string, onConfirm: () => void | Promise<void>) => {
    confirmDialog.show({
      title,
      message,
      variant: 'danger',
      confirmLabel: 'Excluir',
      onConfirm
    });
  },

  warning: (title: string, message: string, onConfirm: () => void | Promise<void>) => {
    confirmDialog.show({
      title,
      message,
      variant: 'warning',
      confirmLabel: 'Continuar',
      onConfirm
    });
  },

  close: () => {
    setIsOpen(false);
    setIsProcessing(false);
    setTimeout(() => setDialogOptions(null), 200);
  }
};

// Confirm Dialog Component
export function ConfirmDialogContainer() {
  let dialogRef: HTMLDivElement | undefined;

  // ✅ ACESSIBILIDADE: Focus trap para prender foco no modal
  useFocusTrap(isOpen, () => dialogRef);

  const handleConfirm = async () => {
    const options = dialogOptions();
    if (!options) return;

    setIsProcessing(true);

    try {
      await options.onConfirm();
      confirmDialog.close();
      // ✅ ACESSIBILIDADE: Anunciar sucesso
      announcer.polite('Ação confirmada');
    } catch (error) {
      console.error('Confirm action error:', error);
      setIsProcessing(false);
      // ✅ ACESSIBILIDADE: Anunciar erro
      announcer.assertive('Erro ao processar ação');
    }
  };

  const handleCancel = () => {
    const options = dialogOptions();
    if (options?.onCancel) {
      options.onCancel();
    }
    confirmDialog.close();
  };

  const getIcon = () => {
    const variant = dialogOptions()?.variant || 'info';
    const iconProps = { size: 48 };

    switch (variant) {
      case 'danger':
        return <Trash2 {...iconProps} class="text-red-500" />;
      case 'warning':
        return <AlertTriangle {...iconProps} class="text-yellow-500" />;
      default:
        return <AlertTriangle {...iconProps} class="text-blue-500" />;
    }
  };

  const getButtonClasses = () => {
    const variant = dialogOptions()?.variant || 'info';

    switch (variant) {
      case 'danger':
        return 'bg-red-600 hover:bg-red-700 text-white';
      case 'warning':
        return 'bg-yellow-600 hover:bg-yellow-700 text-white';
      default:
        return 'bg-blue-600 hover:bg-blue-700 text-white';
    }
  };

  return (
    <Show when={isOpen() && dialogOptions()}>
      {/* Backdrop */}
      <div
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[10000] flex items-center justify-center p-4 animate-in fade-in duration-200"
        onClick={handleCancel}
      >
        {/* Dialog */}
        <div
          ref={dialogRef}
          class="bg-background border rounded-lg shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200"
          onClick={(e) => e.stopPropagation()}
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="dialog-title"
          aria-describedby="dialog-description"
        >
          {/* Header */}
          <div class="p-6 pb-4">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 mt-1">
                {getIcon()}
              </div>
              <div class="flex-1">
                <h2 id="dialog-title" class="text-xl font-bold text-foreground mb-2">
                  {dialogOptions()!.title}
                </h2>
                <p id="dialog-description" class="text-sm text-muted-foreground">
                  {dialogOptions()!.message}
                </p>
              </div>
              <button
                onClick={handleCancel}
                class="flex-shrink-0 p-1 hover:bg-muted rounded transition-colors"
                aria-label="Fechar"
                disabled={isProcessing()}
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Actions */}
          <div class="p-6 pt-0 flex gap-3 justify-end">
            <button
              onClick={handleCancel}
              class="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
              disabled={isProcessing()}
            >
              {dialogOptions()!.cancelLabel || 'Cancelar'}
            </button>
            <button
              onClick={handleConfirm}
              class={`px-4 py-2 rounded-lg transition-colors disabled:opacity-50 ${getButtonClasses()}`}
              disabled={isProcessing()}
            >
              <Show when={isProcessing()} fallback={dialogOptions()!.confirmLabel || 'Confirmar'}>
                <span class="flex items-center gap-2">
                  <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processando...
                </span>
              </Show>
            </button>
          </div>
        </div>
      </div>
    </Show>
  );
}
