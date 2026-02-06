import { Show } from 'solid-js';
import { Copy, RotateCw } from 'lucide-solid';

interface MessageActionsProps {
  messageText: string;
  messageId: string;
  onRegenerate?: () => void;
  canRegenerate?: boolean;
}

export function MessageActions(props: MessageActionsProps) {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(props.messageText).then(() => {
      // Show brief success feedback
      const btn = document.getElementById(`copy-${props.messageId}`);
      if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '✓ Copiado!';
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2000);
      }
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  return (
    <div class="flex items-center gap-2 mt-2 text-xs">
      <button
        id={`copy-${props.messageId}`}
        onClick={copyToClipboard}
        class="flex items-center gap-1 px-2 py-1 rounded hover:bg-muted transition-colors"
        title="Copiar mensagem"
      >
        <Copy size={14} />
        <span>Copiar</span>
      </button>

      <Show when={props.canRegenerate && props.onRegenerate}>
        <button
          onClick={props.onRegenerate}
          class="flex items-center gap-1 px-2 py-1 rounded hover:bg-muted transition-colors"
          title="Regenerar resposta"
        >
          <RotateCw size={14} />
          <span>Regenerar</span>
        </button>
      </Show>
    </div>
  );
}
