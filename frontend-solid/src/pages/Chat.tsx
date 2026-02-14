import { createSignal, createEffect, onCleanup, onMount, For, Show } from 'solid-js';
import auth from '@/store/auth';
import { authApi } from '@/lib/api';
import { ThinkingProcess, AutoResizeTextarea, PlotlyChart, DataTable, FeedbackButtons, DownloadButton, MessageActions, ExportMenu, ShareButton, TypingIndicator } from '@/components';
import { marked } from 'marked';
import { Trash2, StopCircle, User, Bot, Sparkles, SendHorizontal, Paperclip } from 'lucide-solid';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';

// --- HELPERS (Sanitization & Markdown) ---
const sanitizeHTML = (html: string): string => {
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/on\w+='[^']*'/gi, '');
};

marked.setOptions({
  gfm: true,
  breaks: true,
});

const renderMarkdown = (text: string): string => {
  try {
    const rawHtml = marked.parse(text) as string;
    return sanitizeHTML(rawHtml);
  } catch (e) {
    console.error('Erro ao renderizar Markdown:', e);
    return sanitizeHTML(text);
  }
};

// --- INTERFACES ---
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: number;
  type?: 'text' | 'chart' | 'table' | 'final' | 'error' | 'loading_chart' | 'loading_table';
  chart_spec?: any;
  data?: any[];
  response_id?: string;
  isOptimistic?: boolean;

  // New Fields for Thinking Process
  thinkingSteps?: string[];
  isThinking?: boolean;
}

// --- MAIN COMPONENT ---
export default function Chat() {
  // State
  const [messages, setMessages] = createSignal<Message[]>([
    {
      id: '0',
      role: 'assistant',
      text: 'Olá! Sou o Caçulinha. Posso analisar vendas, estoque e tendências para você. Como posso ajudar hoje?',
      timestamp: Date.now(),
      type: 'text',
      response_id: 'initial_greeting',
      thinkingSteps: [],
      isThinking: false
    }
  ]);
  const [input, setInput] = createSignal('');
  const [isStreaming, setIsStreaming] = createSignal(false);
  const [sessionId, setSessionId] = createSignal<string>('');
  const [currentEventSource, setCurrentEventSource] = createSignal<EventSource | null>(null);
  const [editingMessageId, setEditingMessageId] = createSignal<string | null>(null);
  const [editText, setEditText] = createSignal('');

  // UI Refs
  let messagesEndRef: HTMLDivElement | undefined;
  let scrollTimeoutId: number | undefined;

  // Init
  onMount(async () => {
    let storedSession = localStorage.getItem('chat_session_id');
    if (!storedSession) {
      storedSession = crypto.randomUUID();
      localStorage.setItem('chat_session_id', storedSession);
    }
    setSessionId(storedSession);

    // Auto-scroll logic
    const scrollToBottom = () => {
      if (messagesEndRef) {
        messagesEndRef.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }

    // Observer for auto-scroll
    const observer = new MutationObserver(scrollToBottom);
    if (messagesEndRef?.parentElement) {
      observer.observe(messagesEndRef.parentElement, { childList: true, subtree: true });
    }

    // Check example query
    const exampleQuery = localStorage.getItem('example_query');
    if (exampleQuery) {
      localStorage.removeItem('example_query');
      const userMsg: Message = { id: Date.now().toString(), role: 'user', text: exampleQuery, timestamp: Date.now() };
      setMessages(prev => [...prev, userMsg]);
      await processUserMessage(exampleQuery);
    }
  });

  onCleanup(() => {
    currentEventSource()?.close();
    clearTimeout(scrollTimeoutId);
  });

  // Effects
  createEffect(() => {
    messages();
    // Scroll logic handled by onMount observer mostly, but fallback here
    if (scrollTimeoutId !== undefined) clearTimeout(scrollTimeoutId);
    scrollTimeoutId = window.setTimeout(() => {
      messagesEndRef?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
  });

  // --- ACTIONS ---

  const stopGeneration = () => {
    const es = currentEventSource();
    if (es) {
      es.close();
      setCurrentEventSource(null);
      setIsStreaming(false);
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.role === 'assistant') {
          return [...prev.slice(0, -1), {
            ...lastMsg,
            text: lastMsg.text + '\n\n_[Geração interrompida]_',
            isThinking: false
          }];
        }
        return prev;
      });
    }
  };

  const clearConversation = () => {
    if (confirm('Limpar histórico da conversa?')) {
      stopGeneration();
      setMessages([{
        id: '0', role: 'assistant', text: 'Olá! Sou o Caçulinha. Como posso ajudar?',
        timestamp: Date.now(), type: 'text', response_id: 'initial_greeting'
      }]);
      const newSession = crypto.randomUUID();
      setSessionId(newSession);
      localStorage.setItem('chat_session_id', newSession);
    }
  };

  const processUserMessage = async (userText: string) => {
    const token = auth.token();
    if (!token) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        text: '⚠️ Sessão inválida. Faça login novamente para continuar a análise.',
        type: 'error',
        timestamp: Date.now()
      }]);
      return;
    }

    // Proactive Token Refresh: Garantir que o token não expire durante o stream.
    // Fazemos uma chamada leve ao backend para disparar o interceptor de refresh se necessário.
    try {
      await authApi.getMe();
    } catch (e) {
      console.warn("⚠️ Falha ao validar/renovar token antes do stream:", e);
      // Se falhar drasticamente, o interceptor já deve ter redirecionado para login,
      // mas como precaução interrompemos aqui.
      return;
    }

    // Pegar o token possivelmente renovado do store
    const currentToken = sessionStorage.getItem('token') || token;

    setIsStreaming(true);
    const assistantId = (Date.now() + 1).toString();

    // Optimistic Message with Thinking State
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      text: '',
      timestamp: Date.now(),
      type: 'text',
      isOptimistic: true,
      thinkingSteps: [],
      isThinking: true
    }]);

    try {
      const eventSource = new EventSource(`/api/v1/chat/stream?q=${encodeURIComponent(userText)}&token=${encodeURIComponent(currentToken)}&session_id=${sessionId()}`);
      setCurrentEventSource(eventSource);

      let currentMessageId = assistantId;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.done) {
            eventSource.close();
            setCurrentEventSource(null);
            setIsStreaming(false);
            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId ? { ...msg, isOptimistic: false, isThinking: false, response_id: crypto.randomUUID() } : msg
            ));
            return;
          }

          if (data.type === 'tool_progress') {
            // Add Thinking Step
            const statusMap: Record<string, string> = {
              'Pensando': 'Planejando análise...',
              'consultar_dados_flexivel': 'Consultando banco de dados...',
              'consultar_dados_gerais': 'Acessando metadados...',
              'gerar_grafico_universal': 'Criando visualização...',
              'gerar_grafico_universal_v2': 'Gerando gráfico interativo...',
              'Processando resposta': 'Sintetizando resposta...'
            };
            const stepText = statusMap[data.tool] || `Processando solicitação...`;

            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId ? {
                ...msg,
                thinkingSteps: [...(msg.thinkingSteps || []), stepText],
                isThinking: true
              } : msg
            ));
          }
          else if (data.type === 'text') {
            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId ? { ...msg, text: msg.text + data.text, isThinking: false } : msg
            ));
          }
          else if (data.type === 'chart' && data.chart_spec) {
            // Switch to chart type or add new message if needed
            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId ? { ...msg, type: 'chart', chart_spec: data.chart_spec, text: 'Visualização gerada:', isThinking: false } : msg
            ));
          }
          else if (data.type === 'table' && data.data) {
            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId ? { ...msg, type: 'table', data: data.data, text: 'Dados tabulares:', isThinking: false } : msg
            ));
          }
          else if (data.error) {
            setMessages(prev => prev.map(msg =>
              msg.id === currentMessageId
                ? { ...msg, text: `⚠️ Não foi possível concluir a análise: ${data.error}`, type: 'error', isThinking: false }
                : msg
            ));
            eventSource.close();
            setIsStreaming(false);
          }

        } catch (err) {
          console.error('SSE Error', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error("EventSource Error", err);
        eventSource.close();
        setIsStreaming(false);
        setMessages(prev => prev.map(msg =>
          msg.id === currentMessageId
            ? { ...msg, text: msg.text + "\n\n⚠️ Conexão interrompida. Verifique o backend e tente novamente.", isThinking: false }
            : msg
        ));
      };

    } catch (err) {
      setIsStreaming(false);
    }
  };

  const handleSendMessage = () => {
    if (!input().trim() || isStreaming()) return;
    const text = input();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', text: text, timestamp: Date.now() }]);
    processUserMessage(text);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div class="flex flex-col h-[calc(100vh-3.5rem)] bg-white dark:bg-zinc-950 relative">

      {/* Header Actions (Absolute Top Right) */}
      <div class="absolute top-4 right-4 z-20 flex items-center gap-2">
        <Show when={messages().length > 1}>
          <button onClick={clearConversation} class="p-2 text-slate-400 hover:text-red-500 hover:bg-slate-100 rounded-full transition-colors" title="Nova Conversa">
            <Trash2 size={18} />
          </button>
          <ExportMenu messages={messages} sessionId={sessionId()} />
        </Show>
      </div>

      {/* Messages Area */}
      <div class="flex-1 overflow-y-auto w-full">
        <div class="max-w-3xl mx-auto px-4 py-8 pb-32">

          {/* Empty State / Logo */}
          <Show when={messages().length <= 1}>
            <div class="flex flex-col items-center justify-center min-h-[50vh] opacity-100 transition-opacity duration-500 animate-in fade-in">
              <div class="w-16 h-16 bg-white dark:bg-zinc-900 rounded-full shadow-xl flex items-center justify-center mb-6">
                <Sparkles class="text-indigo-500" size={32} />
              </div>
              <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-200 mb-2">Caçulinha</h2>
              <p class="text-slate-500 dark:text-slate-400 text-center max-w-md">
                Faça perguntas sobre vendas, estoque, rupturas ou peça análises de mercado.
              </p>
            </div>
          </Show>

          <For each={messages()}>
            {(msg) => (
              <div class={`group mb-8 w-full ${msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}`}>

                {/* Avatar for Assistant */}
                <Show when={msg.role === 'assistant'}>
                  <div class="flex-shrink-0 mr-4 mt-1">
                    <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center border border-indigo-200 dark:border-indigo-800">
                      <Bot size={18} class="text-indigo-600 dark:text-indigo-400" />
                    </div>
                  </div>
                </Show>

                <div class={`relative max-w-[85%] sm:max-w-[75%] ${msg.role === 'user' ? 'min-w-[50px]' : 'w-full'}`}>

                  {/* User Bubble */}
                  <Show when={msg.role === 'user'}>
                    <div class="bg-slate-100 dark:bg-zinc-800 px-5 py-3.5 rounded-2xl rounded-tr-sm text-slate-800 dark:text-slate-200 shadow-sm border border-slate-200/50 dark:border-zinc-700/50">
                      <div class="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                    </div>
                  </Show>

                  {/* Assistant Content */}
                  <Show when={msg.role === 'assistant'}>
                    <div class="space-y-4">

                      {/* Thinking Process */}
                      <Show when={msg.thinkingSteps && msg.thinkingSteps.length > 0}>
                        <ThinkingProcess
                          steps={msg.thinkingSteps!}
                          isThinking={msg.isThinking || false}
                          isCollapsed={!msg.isThinking} // Auto-collapse when done
                        />
                      </Show>

                      {/* Error Banner */}
                      <Show when={msg.type === 'error'}>
                        <div class="bg-red-50 text-red-700 px-4 py-3 rounded-lg border border-red-200 text-sm">
                          {msg.text}
                        </div>
                      </Show>

                      {/* Charts */}
                      <Show when={msg.type === 'chart' && msg.chart_spec}>
                        <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                          <PlotlyChart chartSpec={() => msg.chart_spec} deferLoad />
                        </div>
                      </Show>

                      {/* Tables */}
                      <Show when={msg.type === 'table' && msg.data}>
                        <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                          <DataTable data={() => msg.data || []} caption="Detalhes" />
                        </div>
                      </Show>

                      {/* Text Response */}
                      <Show when={msg.text && msg.type !== 'error'}>
                        <div
                          class="markdown-body prose dark:prose-invert prose-indigo max-w-none 
                                            bg-transparent text-slate-700 dark:text-slate-300 leading-7 text-[15px]
                                            prose-p:leading-7 prose-li:my-0.5 prose-strong:font-bold prose-headings:font-bold prose-headings:text-slate-900 dark:prose-headings:text-slate-100"
                          innerHTML={renderMarkdown(msg.text)}
                        />
                      </Show>

                      {/* Actions */}
                      <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pt-1">
                        <MessageActions messageText={msg.text} messageId={msg.id} canRegenerate={false} />
                        <Show when={msg.response_id}>
                          <FeedbackButtons messageId={msg.response_id!} onFeedback={() => { }} />
                        </Show>
                      </div>

                    </div>
                  </Show>
                </div>

              </div>
            )}
          </For>

          <Show when={isStreaming() && messages()[messages().length - 1]?.role === 'user'}>
            <div class="flex justify-start mb-8 w-full animate-pulse">
              <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-zinc-800 mr-4"></div>
              <div class="space-y-2 w-1/2">
                <div class="h-4 bg-slate-200 dark:bg-zinc-800 rounded w-full"></div>
                <div class="h-4 bg-slate-200 dark:bg-zinc-800 rounded w-2/3"></div>
              </div>
            </div>
          </Show>

          <div ref={messagesEndRef} class="h-4" />
        </div>
      </div>

      {/* Input Area (Bottom Fixed) */}
      <div class="absolute bottom-0 w-full bg-white dark:bg-zinc-950 p-4 pt-2 z-30">
        <div class="max-w-3xl mx-auto relative group">

          {/* Gradient Border/Glow effect */}
          <div class="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>

          <div class="relative flex items-end gap-2 bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm px-3 py-3 ring-0 focus-within:ring-1 focus-within:ring-indigo-500/50 focus-within:border-indigo-500/50 transition-all">

            <button class="p-2 text-slate-400 hover:text-indigo-600 rounded-full hover:bg-slate-200 dark:hover:bg-zinc-800 transition-colors pb-2.5">
              <Paperclip size={20} />
            </button>

            <AutoResizeTextarea
              value={input()}
              onInput={(e) => setInput(e.currentTarget.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming()}
              placeholder="Enviar mensagem para o Caçulinha..."
              class="flex-1 bg-transparent border-none outline-none focus:ring-0 text-slate-700 dark:text-slate-200 placeholder:text-slate-400 py-2 min-h-[44px] max-h-[200px] leading-relaxed"
            />

            <button
              onClick={isStreaming() ? stopGeneration : handleSendMessage}
              disabled={!input().trim() && !isStreaming()}
              class={`p-2 rounded-xl mb-0.5 transition-all duration-200 ${input().trim() || isStreaming()
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md'
                : 'bg-slate-200 dark:bg-zinc-800 text-slate-400 cursor-not-allowed'
                }`}
            >
              <Show when={isStreaming()} fallback={<SendHorizontal size={20} />}>
                <StopCircle size={20} class="animate-pulse" />
              </Show>
            </button>
          </div>

          <div class="text-center mt-2 pb-2">
            <p class="text-[10px] text-slate-400 font-medium">Caçulinha • AI Assistant</p>
          </div>
        </div>
      </div>

    </div>
  );
}
