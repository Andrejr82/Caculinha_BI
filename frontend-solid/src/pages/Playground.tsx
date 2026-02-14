import { createSignal, For, Show, onMount, createEffect } from 'solid-js';
import { Terminal, Send, Trash2, Settings, Clock, Cpu, Code, Play, X, ChevronDown, ChevronRight, Split, LayoutTemplate, ThumbsUp, ThumbsDown, Download } from 'lucide-solid';
import { playgroundApi, authApi } from '../lib/api';
import { MessageActions } from '../components/MessageActions';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';

interface Message {
   id: string;
   role: 'user' | 'assistant';
   content: string;
   timestamp: string;
   request_id?: string;
}

interface ModelInfo {
   model: string;
   temperature: number;
   max_tokens: number;
   json_mode: boolean;
   playground_mode?: string;
   playground_mode_label?: string;
   remote_llm_enabled?: boolean;
   default_temperature?: number;
   default_max_tokens?: number;
   max_temperature_limit?: number;
   max_tokens_limit?: number;
}

interface CacheStats {
   hits: number;
   misses: number;
   hit_rate: number;
   enabled: boolean;
}

interface ChatResponse {
   response: string;
   model_info: ModelInfo;
   metadata: {
      response_time: number;
      timestamp: string;
      user: string;
   };
   cache_stats: CacheStats;
}

interface PlaygroundMetrics {
   total_requests: number;
   local_requests: number;
   remote_requests: number;
   feedback_total: number;
   feedback_useful: number;
   feedback_not_useful: number;
   feedback_useful_rate: number;
}

export default function Playground() {
   // Panel A State
   const [messagesA, setMessagesA] = createSignal<Message[]>([]);
   const [modelA, setModelA] = createSignal('server-default');
   const [responseTimeA, setResponseTimeA] = createSignal(0);
   const [loadingA, setLoadingA] = createSignal(false);

   // Panel B State (Compare Mode)
   const [compareMode, setCompareMode] = createSignal(false);
   const [messagesB, setMessagesB] = createSignal<Message[]>([]);
   const [modelB, setModelB] = createSignal('server-default');
   const [responseTimeB, setResponseTimeB] = createSignal(0);
   const [loadingB, setLoadingB] = createSignal(false);

   // Shared State
   const [input, setInput] = createSignal('');
   const [systemInstruction, setSystemInstruction] = createSignal('');
   let messagesEndRefA: HTMLDivElement | undefined;
   let messagesEndRefB: HTMLDivElement | undefined;

   const [showCodeModal, setShowCodeModal] = createSignal(false);
   const [systemExpanded, setSystemExpanded] = createSignal(false);

   // Controls
   const [temperature, setTemperature] = createSignal(1.0);
   const [maxTokens, setMaxTokens] = createSignal(2048);
   const [jsonMode, setJsonMode] = createSignal(false);

   // Available models (Mock for now, could fetch from backend)
   const models = [
      { id: 'server-default', name: 'Server Default (settings.LLM_MODEL_NAME)' }
   ];

   const [modelInfo, setModelInfo] = createSignal<ModelInfo | null>(null);
   const [metrics, setMetrics] = createSignal<PlaygroundMetrics | null>(null);

   onMount(async () => {
      try {
         const response = await playgroundApi.getInfo();
         setModelInfo(response.data);
         if (response.data.model) setModelA(response.data.model);
      } catch (error) {
         console.error('Erro ao carregar info do modelo:', error);
      }
      try {
         const response = await playgroundApi.getMetrics();
         setMetrics(response.data);
      } catch {
         // metrics may require admin; keep silent for non-admin users
      }
   });

   createEffect(() => {
      if (messagesA()) setTimeout(() => messagesEndRefA?.scrollIntoView({ behavior: 'smooth' }), 100);
      if (compareMode() && messagesB()) setTimeout(() => messagesEndRefB?.scrollIntoView({ behavior: 'smooth' }), 100);
   });

   const streamRequest = async (
      _modelName: string,
      currentHistory: Message[],
      setMessages: (msgs: Message[]) => void,
      setLoading: (l: boolean) => void,
      setResponseTime: (t: number) => void
   ) => {
      setLoading(true);
      const assistantId = Date.now().toString() + Math.random().toString();

      // Placeholder for assistant
      const initialMsgs = [...currentHistory, {
         id: assistantId,
         role: 'assistant' as const,
         content: '',
         timestamp: new Date().toISOString()
      }];
      setMessages(initialMsgs);

      // Proactive Token Refresh
      try {
         await authApi.getMe();
      } catch (e) {
         console.warn("⚠️ Falha ao renovar token no playground:", e);
      }

      try {
         const response = await fetch('/api/v1/playground/stream', {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
               'Authorization': `Bearer ${sessionStorage.getItem('token')}` // Auth fix: use sessionStorage like rest of app
            },
            body: JSON.stringify({
               message: currentHistory[currentHistory.length - 1].content,
               history: currentHistory.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
               system_instruction: systemInstruction(),
               temperature: temperature(),
               max_tokens: maxTokens(),
               json_mode: jsonMode(),
               stream: true
            })
         });

         if (!response.ok) {
            const errText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errText}`);
         }

         const reader = response.body?.getReader();
         const decoder = new TextDecoder();
      let accumulatedText = "";
      let requestId: string | undefined = undefined;

         if (!reader) throw new Error("No reader");

         while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
               if (line.startsWith('data: ')) {
                  try {
                     const data = JSON.parse(line.slice(6));
                     if (data.type === 'token') {
                        accumulatedText += data.text;
                        setMessages(initialMsgs.map(m =>
                           m.id === assistantId ? { ...m, content: accumulatedText, request_id: requestId } : m
                        ));
                     } else if (data.type === 'start') {
                        requestId = data.request_id;
                     } else if (data.type === 'degraded') {
                        accumulatedText += (accumulatedText ? '\n\n' : '') + `⚠️ Modo degradado: ${data.text}`;
                        setMessages(initialMsgs.map(m =>
                           m.id === assistantId ? { ...m, content: accumulatedText || `⚠️ Modo degradado: ${data.text}`, request_id: requestId } : m
                        ));
                     } else if (data.type === 'done') {
                        setResponseTime(data.metrics.time);
                        if (data.request_id) requestId = data.request_id;
                     } else if (data.type === 'error') {
                        accumulatedText += `\n\n⚠️ Não foi possível concluir no Playground: ${data.text}`;
                        setMessages(initialMsgs.map(m =>
                           m.id === assistantId ? { ...m, content: accumulatedText, request_id: requestId } : m
                        ));
                     }
                  } catch (e) {
                     // ignore json parse error for partial chunks
                  }
               }
            }
         }

      } catch (e: any) {
         setMessages(initialMsgs.map(m =>
            m.id === assistantId ? { ...m, content: `⚠️ Falha de conexão com o Playground: ${e.message}`, request_id: requestId } : m
         ));
      } finally {
         setLoading(false);
      }
   };

   const submitFeedback = async (message: Message, useful: boolean) => {
      if (!message.request_id) return;
      try {
         await playgroundApi.submitFeedback({
            request_id: message.request_id,
            useful,
         });
      } catch (e) {
         console.warn('Falha ao enviar feedback Playground', e);
      }
   };

   const exportJson = () => {
      const payload = { panelA: messagesA(), panelB: messagesB(), exported_at: new Date().toISOString() };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `playground-export-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
   };

   const exportCsv = () => {
      const rows = [...messagesA(), ...messagesB()].map(m => ({
         id: m.id,
         role: m.role,
         timestamp: m.timestamp,
         request_id: m.request_id || '',
         content: (m.content || '').replace(/\n/g, ' ').replace(/"/g, '""')
      }));
      const header = 'id,role,timestamp,request_id,content';
      const csv = [header, ...rows.map(r => `"${r.id}","${r.role}","${r.timestamp}","${r.request_id}","${r.content}"`)].join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `playground-export-${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
   };

   const sendMessage = async (e?: Event) => {
      e?.preventDefault();
      if (!input().trim() || loadingA() || loadingB()) return;

      const userContent = input();
      setInput('');

      const userMessage: Message = {
         id: Date.now().toString(),
         role: 'user',
         content: userContent,
         timestamp: new Date().toISOString()
      };

      // Update Panel A
      const newHistoryA = [...messagesA(), userMessage];
      setMessagesA(newHistoryA);
      streamRequest(modelA(), newHistoryA, setMessagesA, setLoadingA, setResponseTimeA);

      // Update Panel B (if active)
      if (compareMode()) {
         const newHistoryB = [...messagesB(), userMessage];
         setMessagesB(newHistoryB);
         streamRequest(modelB(), newHistoryB, setMessagesB, setLoadingB, setResponseTimeB);
      }
   };

   const clearHistory = () => {
      if (confirm('Deseja limpar o histórico?')) {
         setMessagesA([]);
         setMessagesB([]);
         setResponseTimeA(0);
         setResponseTimeB(0);
      }
   };

   const loadExample = (ex: any) => {
      setSystemInstruction(ex.system);
      setInput(ex.prompt);
      setSystemExpanded(true);
   };

   const generateCodeSnippet = () => {
      // ... existing logic ...
      return "Code snippet generator to be updated for stream...";
   };

   // BI Task Cards
   const biTasks = [
      {
         title: "Ruptura por Loja",
         system: "Você é analista BI de varejo físico. Responda com Resumo, Tabela e Ação recomendada.",
         prompt: "Monte uma SQL de ruptura por loja e período para priorizar reposição."
      },
      {
         title: "Margem por Categoria",
         system: "Você é analista de performance comercial. Estruture resposta em Resumo, Tabela e Ação.",
         prompt: "Quero um template SQL para analisar margem por categoria e identificar outliers."
      },
      {
         title: "Top Produtos",
         system: "Você é analista de sortimento. Use saída objetiva para decisão de loja física.",
         prompt: "Crie uma análise dos top produtos por venda e giro para lojas físicas."
      },
      {
         title: "Transferências",
         system: "Você é analista de abastecimento. Priorize recomendações acionáveis.",
         prompt: "Preciso de uma query de transferências entre lojas com base no estoque."
      },
      {
         title: "Demanda",
         system: "Você é analista de planejamento. Entregue plano operacional curto.",
         prompt: "Sugira um roteiro para previsão de demanda semanal por loja e categoria."
      }
   ];

   const examples = [
      {
         title: "Análise Financeira",
         system: "Você é um analista financeiro sênior. Responda de forma concisa e use tabelas markdown quando apropriado.",
         prompt: "Analise o ROI de uma campanha de marketing que custou R$ 50.000 e gerou R$ 120.000 em vendas."
      },
      {
         title: "SQL Expert",
         system: "Você é um DBA especialista em SQL Server. Forneça apenas o código SQL otimizado.",
         prompt: "Escreva uma query para encontrar produtos que não venderam nos últimos 6 meses."
      },
      {
         title: "Python Data",
         system: "Você é um engenheiro de dados Python. Prefira a biblioteca Polars.",
         prompt: "Crie um script para ler um arquivo Parquet e filtrar linhas onde 'status' é 'error'."
      }
   ];

   return (
      <div class="h-full flex flex-col bg-background max-w-[100vw] overflow-hidden relative">
         {/* Header */}
         <div class="border-b bg-card/50 backdrop-blur-sm p-3 flex items-center justify-between gap-4 z-10 shrink-0">
            <div>
               <h2 class="text-lg font-bold flex items-center gap-2 text-foreground">
                  <Terminal class="text-primary" />
                  Playground
                  <span class="px-2 py-0.5 rounded-full bg-secondary text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                     {compareMode() ? 'Compare Mode' : 'Single Mode'}
                  </span>
               </h2>
            </div>

            <div class="flex items-center gap-3">
               <div class="flex items-center gap-2 bg-secondary/30 rounded-lg p-1 border border-border/50">
                  <button
                     onClick={() => setCompareMode(false)}
                     class={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${!compareMode() ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                     <LayoutTemplate size={14} class="inline mr-1.5" /> Single
                  </button>
                  <button
                     onClick={() => setCompareMode(true)}
                     class={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${compareMode() ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                     <Split size={14} class="inline mr-1.5" /> Compare
                  </button>
               </div>

               <button
                  onClick={() => setShowCodeModal(true)}
                  class="btn btn-ghost btn-icon"
                  title="Ver Código"
               >
                  <Code size={18} />
               </button>
               <button onClick={exportJson} class="btn btn-ghost btn-icon" title="Exportar JSON">
                  <Download size={18} />
               </button>
               <button onClick={exportCsv} class="btn btn-ghost btn-icon" title="Exportar CSV">
                  <FileJson size={18} />
               </button>
            </div>
         </div>

         <div class="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-[1fr_300px]">
            {/* Main Workspace */}
            <div class="flex flex-col min-h-0 bg-background/50 relative">

               {/* System Instruction */}
               <div class="border-b bg-card/20 shrink-0">
                  <button
                     onClick={() => setSystemExpanded(!systemExpanded())}
                     class="w-full flex items-center justify-between p-2 px-4 text-xs font-bold uppercase tracking-wider text-muted hover:bg-card/40"
                  >
                     <div class="flex items-center gap-2">
                        <Settings size={14} /> Persona / System Prompt
                     </div>
                     {systemExpanded() ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>

                  <Show when={systemExpanded()}>
                     <div class="p-4 pt-0 animate-in slide-in-from-top-2">
                        <textarea
                           class="input w-full min-h-[80px] font-mono text-sm bg-background/50"
                           placeholder="Ex: Você é um assistente especialista em análise de dados. Responda sempre em JSON."
                           value={systemInstruction()}
                           onInput={(e) => setSystemInstruction(e.currentTarget.value)}
                        />
                     </div>
                  </Show>
               </div>

               {/* Chat Panels Container */}
               <div class="flex-1 flex min-h-0 overflow-hidden">
                  {/* Panel A */}
                  <div class={`flex-1 flex flex-col min-w-0 border-r border-border/50 ${compareMode() ? '' : 'max-w-4xl mx-auto border-r-0'}`}>
                     {/* Panel Header */}
                     <div class="p-2 border-b bg-muted/10 flex justify-between items-center">
                        <div class="flex items-center gap-2">
                           <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                           <select
                              class="bg-transparent text-sm font-semibold text-foreground focus:outline-none cursor-pointer"
                              value={modelA()}
                              onChange={(e) => setModelA(e.currentTarget.value)}
                           >
                              <For each={models}>{m => <option value={m.id}>{m.name}</option>}</For>
                           </select>
                        </div>
                        <span class="text-xs font-mono text-muted-foreground">
                           {loadingA() ? <Clock size={12} class="animate-spin inline" /> : `${responseTimeA().toFixed(2)}s`}
                        </span>
                     </div>

                     {/* Messages A */}
                     <div class="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
                        <For each={messagesA()}>
                           {(msg) => (
                              <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                 <div class={`max-w-[90%] rounded-xl p-3 text-sm shadow-sm ${msg.role === 'user' ? 'bg-primary/10 text-foreground' : 'bg-card border'}`}>
                                    <div class="markdown-body bg-transparent" innerHTML={msg.content ? msg.content.replace(/\n/g, '<br/>') : ''} />
                                    <Show when={msg.role === 'assistant' && msg.request_id}>
                                       <div class="flex items-center gap-2 mt-2">
                                          <button class="btn btn-ghost btn-xs" onClick={() => submitFeedback(msg, true)}><ThumbsUp size={12} /></button>
                                          <button class="btn btn-ghost btn-xs" onClick={() => submitFeedback(msg, false)}><ThumbsDown size={12} /></button>
                                       </div>
                                    </Show>
                                    {/* Note: In real app use marked() here */}
                                 </div>
                              </div>
                           )}
                        </For>
                        <div ref={messagesEndRefA} />
                     </div>
                  </div>

                  {/* Panel B (Compare Mode) */}
                  <Show when={compareMode()}>
                     <div class="flex-1 flex flex-col min-w-0 bg-secondary/5">
                        {/* Panel Header */}
                        <div class="p-2 border-b bg-muted/10 flex justify-between items-center">
                           <div class="flex items-center gap-2">
                              <span class="w-2 h-2 rounded-full bg-purple-500"></span>
                              <select
                                 class="bg-transparent text-sm font-semibold text-foreground focus:outline-none cursor-pointer"
                                 value={modelB()}
                                 onChange={(e) => setModelB(e.currentTarget.value)}
                              >
                                 <For each={models}>{m => <option value={m.id}>{m.name}</option>}</For>
                              </select>
                           </div>
                           <span class="text-xs font-mono text-muted-foreground">
                              {loadingB() ? <Clock size={12} class="animate-spin inline" /> : `${responseTimeB().toFixed(2)}s`}
                           </span>
                        </div>

                        {/* Messages B */}
                        <div class="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
                           <For each={messagesB()}>
                              {(msg) => (
                                 <div class={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                 <div class={`max-w-[90%] rounded-xl p-3 text-sm shadow-sm ${msg.role === 'user' ? 'bg-primary/10 text-foreground' : 'bg-card border'}`}>
                                    <div class="markdown-body bg-transparent" innerHTML={msg.content ? msg.content.replace(/\n/g, '<br/>') : ''} />
                                    <Show when={msg.role === 'assistant' && msg.request_id}>
                                       <div class="flex items-center gap-2 mt-2">
                                          <button class="btn btn-ghost btn-xs" onClick={() => submitFeedback(msg, true)}><ThumbsUp size={12} /></button>
                                          <button class="btn btn-ghost btn-xs" onClick={() => submitFeedback(msg, false)}><ThumbsDown size={12} /></button>
                                       </div>
                                    </Show>
                                 </div>
                                 </div>
                              )}
                           </For>
                           <div ref={messagesEndRefB} />
                        </div>
                     </div>
                  </Show>
               </div>

               {/* Input Area */}
               <div class="p-4 border-t bg-background/80 backdrop-blur-md shrink-0">
                  <form onSubmit={sendMessage} class="flex gap-3 max-w-4xl mx-auto">
                     <button
                        type="button"
                        onClick={clearHistory}
                        class="btn btn-ghost btn-icon text-muted hover:text-destructive"
                        title="Limpar"
                     >
                        <Trash2 size={20} />
                     </button>

                     <div class="flex-1 relative">
                        <input
                           type="text"
                           class="input w-full pr-12 shadow-sm font-mono text-sm"
                           placeholder={compareMode() ? "Enviar para ambos os modelos..." : "Digite sua mensagem..."}
                           value={input()}
                           onInput={(e) => setInput(e.currentTarget.value)}
                           disabled={loadingA() || loadingB()}
                        />
                     </div>

                     <button
                        type="submit"
                        class="btn btn-primary shadow-md hover:shadow-lg transition-all"
                        disabled={(loadingA() || loadingB()) || !input().trim()}
                     >
                        <Show when={!loadingA() && !loadingB()} fallback={<Clock size={20} class="animate-spin" />}>
                           <Send size={20} />
                        </Show>
                     </button>
                  </form>
               </div>
            </div>

            {/* Right Sidebar - Configuration */}
            <div class="border-l bg-card/30 p-6 overflow-y-auto hidden lg:block">
               <div class="sticky top-0 space-y-8">
                  <div class="p-3 rounded-lg border bg-background/70 text-xs text-muted">
                     <strong>Modo:</strong> {modelInfo()?.playground_mode_label || 'Local only'}
                     <Show when={metrics()}>
                        <div class="mt-2 space-y-1">
                           <div>Req 7d: {metrics()!.total_requests}</div>
                           <div>Feedback útil: {metrics()!.feedback_useful_rate}%</div>
                        </div>
                     </Show>
                  </div>
                  {/* Settings Group */}
                  <div class="space-y-4">
                     <h3 class="font-bold flex items-center gap-2 text-foreground/80">
                        <Settings size={18} /> Parâmetros
                     </h3>

                     <div class="space-y-4 p-4 bg-background border rounded-xl shadow-sm">
                        {/* Temperature */}
                        <div class="space-y-3">
                           <div class="flex justify-between items-center">
                              <label class="text-sm font-medium">Temperatura</label>
                              <span class="text-xs font-mono bg-secondary px-2 py-1 rounded">{temperature().toFixed(1)}</span>
                           </div>
                           <input
                              type="range" min="0" max="2" step="0.1"
                              value={temperature()}
                              onInput={(e) => setTemperature(parseFloat(e.currentTarget.value))}
                              class="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                           />
                        </div>

                        <div class="h-px bg-border/50"></div>

                        {/* Max Tokens */}
                        <div class="space-y-3">
                           <div class="flex justify-between items-center">
                              <label class="text-sm font-medium">Max Tokens</label>
                              <span class="text-xs font-mono bg-secondary px-2 py-1 rounded">{maxTokens()}</span>
                           </div>
                           <input
                              type="range" min="100" max={modelInfo()?.max_tokens_limit || 8192} step="100"
                              value={maxTokens()}
                              onInput={(e) => setMaxTokens(parseInt(e.currentTarget.value))}
                              class="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                           />
                        </div>
                     </div>
                  </div>

                  {/* Modes Group */}
                  <div class="space-y-4">
                     <h3 class="font-bold flex items-center gap-2 text-foreground/80">
                        <Cpu size={18} /> Output
                     </h3>

                     <div class="space-y-3 p-4 bg-background border rounded-xl shadow-sm">
                        <div class="flex items-center justify-between group">
                           <div class="space-y-0.5">
                              <label class="text-sm font-medium">JSON Mode</label>
                              <p class="text-xs text-muted">Estrutura rígida</p>
                           </div>
                           <input
                              type="checkbox"
                              checked={jsonMode()}
                              onChange={(e) => setJsonMode(e.currentTarget.checked)}
                              class="toggle toggle-sm toggle-primary"
                           />
                        </div>
                     </div>
                  </div>

                  <Show when={messagesA().length === 0}>
                     <div class="space-y-2 mt-8">
                        <h3 class="font-bold text-foreground/80 text-sm">Tarefas BI</h3>
                        <For each={biTasks}>
                           {(example) => (
                              <button
                                 onClick={() => loadExample(example)}
                                 class="w-full p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-secondary/50 transition-all text-left group"
                              >
                                 <div class="font-semibold text-xs group-hover:text-primary transition-colors mb-1 flex items-center gap-2">
                                    <Play size={12} /> {example.title}
                                 </div>
                              </button>
                           )}
                        </For>
                        <h3 class="font-bold text-foreground/80 text-sm pt-3">Exemplos Técnicos</h3>
                        <For each={examples}>
                           {(example) => (
                              <button
                                 onClick={() => loadExample(example)}
                                 class="w-full p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-secondary/50 transition-all text-left group"
                              >
                                 <div class="font-semibold text-xs group-hover:text-primary transition-colors mb-1 flex items-center gap-2">
                                    <Play size={12} /> {example.title}
                                 </div>
                              </button>
                           )}
                        </For>
                     </div>
                  </Show>

               </div>
            </div>
         </div>

         {/* Code Modal */}
         <Show when={showCodeModal()}>
            <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
               <div class="bg-card w-full max-w-2xl rounded-xl shadow-2xl border animate-in zoom-in-95">
                  <div class="flex items-center justify-between p-4 border-b">
                     <h3 class="font-bold flex items-center gap-2"><Code size={20} /> Snippet de Integração</h3>
                     <button onClick={() => setShowCodeModal(false)} class="btn btn-ghost btn-icon btn-sm"><X size={18} /></button>
                  </div>
                  <div class="p-0 overflow-hidden">
                     <pre class="bg-secondary/50 p-4 text-xs font-mono overflow-x-auto text-foreground">
                        {generateCodeSnippet()}
                     </pre>
                  </div>
                  <div class="p-4 border-t flex justify-end gap-2">
                     <button onClick={() => setShowCodeModal(false)} class="btn btn-outline">Fechar</button>
                     <button class="btn btn-primary" onClick={() => {
                        navigator.clipboard.writeText(generateCodeSnippet());
                        setShowCodeModal(false);
                     }}>Copiar Código</button>
                  </div>
               </div>
            </div>
         </Show>
      </div>
   );
}
