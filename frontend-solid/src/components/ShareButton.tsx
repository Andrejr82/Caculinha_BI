import { createSignal, Show } from 'solid-js';
import { Share2, Copy, Check, X } from 'lucide-solid';
import auth from '@/store/auth';

interface Message {
  id: string;
  role: string;
  text: string;
  timestamp: number;
}

interface ShareButtonProps {
  messages: () => Message[];
  sessionId: string;
}

export function ShareButton(props: ShareButtonProps) {
  const [showModal, setShowModal] = createSignal(false);
  const [shareUrl, setShareUrl] = createSignal('');
  const [copied, setCopied] = createSignal(false);
  const [isSharing, setIsSharing] = createSignal(false);
  const [error, setError] = createSignal('');
  const [title, setTitle] = createSignal('');

  const shareConversation = async () => {
    const token = auth.token();
    if (!token) {
      setError('Você precisa estar autenticado para compartilhar.');
      return;
    }

    setIsSharing(true);
    setError('');

    try {
      const response = await fetch('/api/v1/shared/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: props.sessionId,
          messages: props.messages().map(m => ({
            role: m.role,
            text: m.text,
            timestamp: m.timestamp
          })),
          title: title() || 'Conversa Chat BI',
          expires_in_days: 30
        })
      });

      if (!response.ok) {
        throw new Error('Falha ao compartilhar conversa');
      }

      const data = await response.json();
      const fullUrl = `${window.location.origin}${data.share_url}`;
      setShareUrl(fullUrl);
    } catch (err) {
      console.error('Error sharing conversation:', err);
      setError('Erro ao compartilhar conversa. Tente novamente.');
    } finally {
      setIsSharing(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const openModal = () => {
    setShowModal(true);
    setShareUrl('');
    setError('');
    setTitle('');
  };

  const closeModal = () => {
    setShowModal(false);
    setShareUrl('');
    setError('');
  };

  return (
    <>
      <button
        onClick={openModal}
        class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border hover:bg-muted transition-colors"
        title="Compartilhar conversa"
      >
        <Share2 size={16} />
        <span>Compartilhar</span>
      </button>

      <Show when={showModal()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div class="bg-card border rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">Compartilhar Conversa</h3>
              <button
                onClick={closeModal}
                class="hover:bg-muted rounded p-1 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <Show when={!shareUrl()}>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium mb-2">
                    Título (opcional)
                  </label>
                  <input
                    type="text"
                    class="input w-full"
                    value={title()}
                    onInput={(e) => setTitle(e.currentTarget.value)}
                    placeholder="Dê um título para esta conversa"
                  />
                </div>

                <p class="text-sm text-muted-foreground">
                  Ao compartilhar, você criará um link público que qualquer pessoa pode acessar.
                  O link expirará em 30 dias.
                </p>

                <Show when={error()}>
                  <div class="p-3 rounded bg-red-500/10 text-red-500 text-sm">
                    {error()}
                  </div>
                </Show>

                <button
                  onClick={shareConversation}
                  disabled={isSharing()}
                  class="btn btn-primary w-full"
                >
                  {isSharing() ? 'Compartilhando...' : 'Criar Link de Compartilhamento'}
                </button>
              </div>
            </Show>

            <Show when={shareUrl()}>
              <div class="space-y-4">
                <div class="p-3 rounded bg-green-500/10 text-green-500 text-sm">
                  ✓ Conversa compartilhada com sucesso!
                </div>

                <div>
                  <label class="block text-sm font-medium mb-2">
                    Link de compartilhamento
                  </label>
                  <div class="flex gap-2">
                    <input
                      type="text"
                      class="input flex-1"
                      value={shareUrl()}
                      readonly
                    />
                    <button
                      onClick={copyToClipboard}
                      class="btn btn-primary"
                      title="Copiar link"
                    >
                      <Show when={!copied()} fallback={<Check size={16} />}>
                        <Copy size={16} />
                      </Show>
                    </button>
                  </div>
                </div>

                <p class="text-sm text-muted-foreground">
                  Este link é público e funcionará por 30 dias. Qualquer pessoa com o link poderá visualizar esta conversa.
                </p>

                <button
                  onClick={closeModal}
                  class="btn w-full"
                >
                  Fechar
                </button>
              </div>
            </Show>
          </div>
        </div>
      </Show>
    </>
  );
}
