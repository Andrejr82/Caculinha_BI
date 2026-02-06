import { createSignal, onMount, For, Show } from 'solid-js';
import { useParams } from '@solidjs/router';
// Removido solid-markdown devido a problemas de compatibilidade ESM
import { formatTimestamp } from '@/lib/formatters';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';

interface Message {
  role: string;
  text: string;
  timestamp: number;
}

interface SharedConversationData {
  share_id: string;
  title: string | null;
  messages: Message[];
  created_at: string;
  view_count: number;
}

export default function SharedConversation() {
  const params = useParams();
  const [conversation, setConversation] = createSignal<SharedConversationData | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal('');

  onMount(async () => {
    const shareId = params.share_id;
    if (!shareId) {
      setError('ID de compartilhamento inválido');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`/api/v1/shared/${shareId}`);

      if (!response.ok) {
        if (response.status === 404) {
          setError('Esta conversa não foi encontrada.');
        } else if (response.status === 410) {
          setError('Esta conversa expirou ou não está mais disponível.');
        } else {
          setError('Erro ao carregar conversa compartilhada.');
        }
        setLoading(false);
        return;
      }

      const data = await response.json();
      setConversation(data);
    } catch (err) {
      console.error('Error loading shared conversation:', err);
      setError('Erro ao carregar conversa compartilhada.');
    } finally {
      setLoading(false);
    }
  });

  return (
    <div class="flex flex-col h-full max-w-4xl mx-auto">
      {/* Header */}
      <div class="p-4 border-b bg-background/50 backdrop-blur">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold">
              {conversation()?.title || 'Conversa Compartilhada'}
            </h2>
            <Show when={conversation()}>
              <p class="text-sm text-muted-foreground mt-1">
                Compartilhado em {new Date(conversation()!.created_at).toLocaleDateString('pt-BR')}
                {' • '}
                {conversation()!.view_count} visualiza{conversation()!.view_count === 1 ? 'ção' : 'ções'}
              </p>
            </Show>
          </div>
          <a
            href="/"
            class="btn btn-primary"
          >
            Criar minha conversa
          </a>
        </div>
      </div>

      {/* Content */}
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <Show when={loading()}>
          <div class="flex items-center justify-center h-full">
            <div class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p class="text-muted-foreground">Carregando conversa...</p>
            </div>
          </div>
        </Show>

        <Show when={error()}>
          <div class="flex items-center justify-center h-full">
            <div class="text-center max-w-md">
              <div class="text-6xl mb-4">⚠️</div>
              <h3 class="text-xl font-semibold mb-2">Ops!</h3>
              <p class="text-muted-foreground mb-6">{error()}</p>
              <a href="/" class="btn btn-primary">
                Ir para página inicial
              </a>
            </div>
          </div>
        </Show>

        <Show when={!loading() && !error() && conversation()}>
          <div class="space-y-4">
            <div class="p-4 rounded-lg bg-muted/50 border">
              <p class="text-sm text-muted-foreground">
                ℹ️ Esta é uma visualização somente leitura de uma conversa compartilhada do Chat BI.
                Você não pode interagir ou continuar esta conversa.
              </p>
            </div>

            <For each={conversation()!.messages}>
              {(msg) => (
                <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    class={`max-w-[80%] rounded-lg p-4 text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-card border text-card-foreground'
                      }`}
                  >
                    <div class="markdown-body" style="white-space: pre-wrap;">
                      {msg.text}
                    </div>
                    <div class="text-xs text-muted-foreground mt-2 opacity-70">
                      {formatTimestamp(msg.timestamp)}
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>
        </Show>
      </div>

      {/* Footer */}
      <div class="p-4 border-t bg-background/50 backdrop-blur text-center">
        <p class="text-sm text-muted-foreground">
          Powered by <span class="font-semibold text-foreground">Chat BI</span>
          {' • '}
          <a href="/" class="text-primary hover:underline">
            Criar sua própria conversa
          </a>
        </p>
      </div>
    </div>
  );
}
