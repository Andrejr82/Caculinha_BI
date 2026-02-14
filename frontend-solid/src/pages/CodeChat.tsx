import { createSignal, For, Show, onMount, createEffect, onCleanup } from 'solid-js';
import { Code, Send, Trash2, FileCode, Database, Zap, Clock, Info, BookOpen, Search, ChevronDown, ChevronRight, Loader2, StopCircle } from 'lucide-solid';
import { codeChatApi, authApi } from '../lib/api';
import auth from '@/store/auth'; // Import auth store
import { MessageActions } from '../components/MessageActions';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  code_references?: CodeReference[];
  isStreaming?: boolean;
}

interface CodeReference {
  file: string;
  score: number;
  content: string;
  lines: string;
}

interface IndexStats {
  status: string;
  reason?: string;
  total_files: number;
  total_functions: number;
  total_classes: number;
  total_lines: number;
  indexed_at: string | null;
  languages: string[];
}

export default function CodeChat() {
  const [messages, setMessages] = createSignal<Message[]>([]);
  const [input, setInput] = createSignal('');
  const [loading, setLoading] = createSignal(false);
  const [indexStats, setIndexStats] = createSignal<IndexStats | null>(null);
  const [examplesExpanded, setExamplesExpanded] = createSignal(true);

  // Streaming states
  const [currentStatus, setCurrentStatus] = createSignal<string>('');
  const [eventSource, setEventSource] = createSignal<EventSource | null>(null);

  let messagesEndRef: HTMLDivElement | undefined;

  // Examples de perguntas
  const examples = [
    {
      title: "Estrutura do Código",
      prompt: "Quais são os principais módulos do backend?"
    },
    {
      title: "Autenticação",
      prompt: "Como funciona o sistema de autenticação?"
    },
    {
      title: "API Endpoints",
      prompt: "Liste todos os endpoints da API de chat"
    },
    {
      title: "Frontend Components",
      prompt: "Quais componentes SolidJS existem no projeto?"
    }
  ];

  onMount(async () => {
    // Load index stats
    try {
      const response = await codeChatApi.getStats();
      setIndexStats(response.data);

      if (response.data.status === 'ready') {
        const welcomeMsg: Message = {
          id: '0',
          role: 'assistant',
          content: `🤖 **Olá! Sou seu Agente Fullstack de Código.**\n\nPosso responder qualquer pergunta sobre este projeto:\n\n- 📁 **${response.data.total_files.toLocaleString()}** arquivos indexados\n- 📝 **${response.data.total_functions.toLocaleString()}** funções\n- 🏗️ **${response.data.total_classes.toLocaleString()}** classes\n- 💻 **${response.data.languages.join(', ')}**\n\nFaça uma pergunta sobre o código!`,
          timestamp: new Date().toISOString()
        };
        setMessages([welcomeMsg]);
      } else {
        const reason = response.data.reason || 'index_missing';
        const reasonText =
          reason === 'gemini_api_key_missing'
            ? 'Configure `GEMINI_API_KEY` para ativar o Code Chat.'
            : 'Execute `python scripts/index_codebase.py` para gerar o índice de código.';
        setMessages([{
          id: '0',
          role: 'assistant',
          content: `⚠️ **Code Chat indisponível no momento**\n\n${reasonText}\n\nAssim que o índice estiver pronto, eu volto a responder perguntas sobre arquitetura, APIs e autenticação.`,
          timestamp: new Date().toISOString()
        }]);
      }

    } catch (error: any) {
      console.error('Erro ao carregar stats:', error);
      const errorMsg: Message = {
        id: '0',
        role: 'assistant',
        content: '⚠️ **Índice não disponível**\n\nO índice de código não foi gerado ainda.\n\nExecute: `python scripts/index_codebase.py`',
        timestamp: new Date().toISOString()
      };
      setMessages([errorMsg]);
    }
  });

  createEffect(() => {
    if (messages()) {
      setTimeout(() => messagesEndRef?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  });

  onCleanup(() => {
    if (eventSource()) {
      eventSource()?.close();
    }
  });

  const stopGeneration = () => {
    if (eventSource()) {
      eventSource()?.close();
      setEventSource(null);
      setLoading(false);
      setCurrentStatus('');

      // Add cancellation note
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last.role === 'assistant') {
          return [...prev.slice(0, -1), { ...last, content: last.content + '\n\n_[Geração interrompida]_', isStreaming: false }];
        }
        return prev;
      });
    }
  };

  const sendMessage = async (e?: Event) => {
    e?.preventDefault();
    if (!input().trim() || loading()) return;
    if (indexStats() && indexStats()!.status !== 'ready') {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: '⚠️ Code Chat ainda não está pronto.\n\nGere o índice com `python scripts/index_codebase.py` e tente novamente.',
        timestamp: new Date().toISOString()
      }]);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input(),
      timestamp: new Date().toISOString()
    };

    setMessages([...messages(), userMessage]);
    const prompt = input();
    setInput('');
    setLoading(true);
    setCurrentStatus('Iniciando...');

    // Placeholder assistant message
    const assistantId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    }]);

    // Proactive Token Refresh: Garantir que o token não expire durante o stream.
    try {
      await authApi.getMe();
    } catch (e) {
      console.warn("⚠️ Falha ao validar/renovar token antes do stream:", e);
      setLoading(false);
      setCurrentStatus('Erro na autenticação');
      return;
    }

    const token = sessionStorage.getItem('token') || auth.token();

    try {
      if (!token) throw new Error("Not authenticated");

      // Auth Hardening: Pass token in query param for SSE
      const currentToken = sessionStorage.getItem('token');
      if (!currentToken) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: '⚠️ Sessão inválida. Faça login novamente para continuar.',
          timestamp: new Date().toISOString()
        }]);
        setLoading(false);
        return;
      }
      const es = new EventSource(`/api/v1/code-chat/stream?q=${encodeURIComponent(prompt)}&token=${encodeURIComponent(currentToken)}`);
      setEventSource(es);

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'progress') {
            setCurrentStatus(data.message);
          } else if (data.type === 'references') {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, code_references: data.references } : msg
            ));
          } else if (data.type === 'token') {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, content: msg.content + data.text } : msg
            ));
          } else if (data.type === 'done') {
            setLoading(false);
            setCurrentStatus('');
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, isStreaming: false } : msg
            ));
            es.close();
            setEventSource(null);
          } else if (data.type === 'error') {
            throw new Error(data.content);
          }

        } catch (err) {
          console.error("SSE Error:", err);
          setMessages(prev => prev.map(msg =>
            msg.id === assistantId
              ? { ...msg, content: msg.content + `\n\n⚠️ Não foi possível concluir a análise de código. Detalhe: ${err}` }
              : msg
          ));
          es.close();
          setLoading(false);
        }
      };

      es.onerror = (err) => {
        console.error("SSE Connection Error:", err);
        es.close();
        setLoading(false);
        setEventSource(null);
        setMessages(prev => prev.map(msg =>
          msg.id === assistantId ? { ...msg, isStreaming: false } : msg
        ));
      };

    } catch (error: any) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ **Erro**: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setLoading(false);
    }
  };

  const clearHistory = () => {
    if (confirm('Deseja limpar o histórico?')) {
      setMessages([messages()[0]]); // Keep welcome message
    }
  };

  const loadExample = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <div class="h-full flex flex-col bg-background max-w-[1800px] mx-auto">
      {/* Context7: Executive Header with KPIs */}
      <div class="border-b bg-card/50 backdrop-blur-sm p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold flex items-center gap-2 text-foreground">
            <Code class="text-primary" />
            Code Chat <span class="text-muted font-normal text-sm border-l pl-2 ml-2">Agente Fullstack</span>
          </h2>
        </div>

        {/* Live Metrics Strip */}
        <Show when={indexStats()}>
          <div class="flex gap-4">
            <div class="flex items-center gap-3 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
              <FileCode size={16} class="text-blue-500" />
              <div>
                <div class="text-[10px] text-muted uppercase tracking-wider font-semibold">Arquivos</div>
                <div class="text-sm font-mono font-bold">{indexStats()!.total_files.toLocaleString()}</div>
              </div>
            </div>

            <div class="flex items-center gap-3 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
              <Zap size={16} class="text-purple-500" />
              <div>
                <div class="text-[10px] text-muted uppercase tracking-wider font-semibold">Funções</div>
                <div class="text-sm font-mono font-bold">{indexStats()!.total_functions.toLocaleString()}</div>
              </div>
            </div>

            <div class="flex items-center gap-3 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
              <Database size={16} class="text-green-500" />
              <div>
                <div class="text-[10px] text-muted uppercase tracking-wider font-semibold">Status</div>
                <div class="text-sm font-mono font-bold">{indexStats()!.status === 'ready' ? '✅ Pronto' : '⚠️ Indexando'}</div>
              </div>
            </div>
          </div>
        </Show>
      </div>

      <div class="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-[1fr_350px]">
        {/* Main Chat Area */}
        <div class="flex flex-col min-h-0 bg-background/50">
          {/* Messages */}
          <div class="flex-1 overflow-auto p-6 space-y-6">
            <For each={messages()}>
              {(message) => (
                <div class={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2`}>
                  <div
                    class={`max-w-[85%] rounded-2xl p-5 shadow-sm ${message.role === 'user'
                      ? 'bg-primary/10 border border-primary/20 text-foreground rounded-tr-none'
                      : 'bg-card border text-card-foreground rounded-tl-none'
                      }`}
                  >
                    <div class="flex items-center gap-2 mb-2 opacity-70 border-b border-border/10 pb-2">
                      <span class="text-xs font-bold uppercase tracking-wider">
                        {message.role === 'user' ? 'Você' : 'Agente'}
                      </span>
                      <span class="text-[10px] ml-auto">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div class="markdown-body text-sm leading-relaxed" style="background: transparent;">
                      <pre class="whitespace-pre-wrap font-sans bg-transparent border-0 p-0 m-0 text-current">{message.content}</pre>
                    </div>

                    {/* Code References */}
                    <Show when={message.code_references && message.code_references.length > 0}>
                      <div class="mt-4 pt-4 border-t border-border/10 space-y-2">
                        <div class="text-xs font-bold text-muted uppercase tracking-wider mb-2">
                          📄 Referências de Código ({message.code_references!.length})
                        </div>
                        <For each={message.code_references}>
                          {(ref) => (
                            <div class="bg-secondary/30 border rounded-lg p-3 text-xs font-mono">
                              <div class="flex items-center justify-between mb-2">
                                <span class="font-bold text-primary">{ref.file}</span>
                                <span class="text-muted">Score: {(ref.score * 100).toFixed(1)}%</span>
                              </div>
                              <pre class="text-[11px] text-muted overflow-x-auto whitespace-pre-wrap">{ref.content}</pre>
                            </div>
                          )}
                        </For>
                      </div>
                    </Show>

                    <Show when={message.role === 'assistant' && !message.isStreaming}>
                      <div class="mt-3 pt-2 border-t border-border/10">
                        <MessageActions messageText={message.content} messageId={message.id} />
                      </div>
                    </Show>
                  </div>
                </div>
              )}
            </For>

            <Show when={loading()}>
              <div class="flex justify-start">
                <div class="bg-card border rounded-2xl rounded-tl-none p-4 flex items-center gap-3">
                  {/* Thought Process Indicator */}
                  <div class="flex items-center gap-2 text-xs text-muted font-medium animate-pulse">
                    <Loader2 size={14} class="animate-spin text-primary" />
                    {currentStatus() || 'Processando...'}
                  </div>
                </div>
              </div>
            </Show>
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div class="p-4 border-t bg-background/80 backdrop-blur-md">
            <form onSubmit={sendMessage} class="flex gap-3 max-w-4xl mx-auto">
              <button
                type="button"
                onClick={clearHistory}
                class="btn btn-ghost btn-icon text-muted hover:text-destructive"
                title="Limpar Histórico"
              >
                <Trash2 size={20} />
              </button>

              <div class="flex-1 relative">
                <input
                  type="text"
                  class="input w-full pr-12 shadow-sm font-mono text-sm"
                  placeholder="Pergunte sobre o código..."
                  value={input()}
                  onInput={(e) => setInput(e.currentTarget.value)}
                  disabled={loading()}
                />
              </div>

              <Show when={loading()} fallback={
                <button
                  type="submit"
                  class="btn btn-primary shadow-md hover:shadow-lg transition-all"
                  disabled={!input().trim()}
                >
                  <Send size={20} />
                </button>
              }>
                <button
                  type="button"
                  onClick={stopGeneration}
                  class="btn btn-destructive shadow-md hover:shadow-lg transition-all"
                >
                  <StopCircle size={20} />
                </button>
              </Show>
            </form>
          </div>
        </div>

        {/* Right Sidebar - Examples & Info */}
        <div class="border-l bg-card/30 p-6 overflow-auto hidden lg:block">
          <div class="sticky top-0 space-y-8">
            {/* Examples */}
            <div class="space-y-4">
              <button
                onClick={() => setExamplesExpanded(!examplesExpanded())}
                class="w-full flex items-center justify-between text-sm font-bold uppercase tracking-wider text-muted hover:text-foreground"
              >
                <div class="flex items-center gap-2">
                  <BookOpen size={14} />
                  Exemplos
                </div>
                {examplesExpanded() ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>

              <Show when={examplesExpanded()}>
                <div class="space-y-2 animate-in slide-in-from-top-2">
                  <For each={examples}>
                    {(example) => (
                      <button
                        onClick={() => loadExample(example.prompt)}
                        class="w-full p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-secondary/50 transition-all text-left group"
                      >
                        <div class="font-semibold text-sm group-hover:text-primary transition-colors mb-1 flex items-center gap-2">
                          <Search size={12} />
                          {example.title}
                        </div>
                        <div class="text-xs text-muted line-clamp-2">{example.prompt}</div>
                      </button>
                    )}
                  </For>
                </div>
              </Show>
            </div>

            {/* Index Info */}
            <Show when={indexStats()}>
              <div class="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl space-y-2">
                <div class="flex items-center gap-2 text-blue-600 font-bold text-sm">
                  <Info size={16} />
                  Informações do Índice
                </div>
                <div class="text-xs text-muted space-y-1">
                  <div>📁 {indexStats()!.total_files.toLocaleString()} arquivos</div>
                  <div>📝 {indexStats()!.total_functions.toLocaleString()} funções</div>
                  <div>🏗️ {indexStats()!.total_classes.toLocaleString()} classes</div>
                  <div>💾 {indexStats()!.total_lines.toLocaleString()} linhas</div>
                  <Show when={indexStats()!.indexed_at}>
                    <div class="pt-2 border-t border-border/10">
                      Indexado: {new Date(indexStats()!.indexed_at!).toLocaleString()}
                    </div>
                  </Show>
                </div>
              </div>
            </Show>

            {/* Help */}
            <div class="p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-xl space-y-2">
              <div class="flex items-center gap-2 text-yellow-600 font-bold text-sm">
                <Info size={16} />
                Dicas de Uso
              </div>
              <p class="text-xs text-muted leading-relaxed">
                Faça perguntas específicas sobre o código, arquitetura, ou funcionalidades.
                O agente busca semanticamente em todo o projeto e fornece respostas contextualizadas.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
