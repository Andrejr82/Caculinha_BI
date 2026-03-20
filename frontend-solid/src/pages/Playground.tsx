import { createEffect, createSignal, For, Show, onMount } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Clock,
  Code,
  Cpu,
  Download,
  FileJson,
  LayoutTemplate,
  Play,
  Send,
  Settings,
  Split,
  Terminal,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  X,
} from 'lucide-solid';

import { authApi, playgroundApi } from '../lib/api';
import { announcer } from '../components/ScreenReaderAnnouncer';
import { toastManager } from '../components/Toast';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';
import './playground-surfaces.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  request_id?: string;
  feedback_status?: 'useful' | 'not_useful';
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

interface PlaygroundMetrics {
  total_requests: number;
  local_requests: number;
  remote_requests: number;
  feedback_total: number;
  feedback_useful: number;
  feedback_not_useful: number;
  feedback_useful_rate: number;
}

const PLAYGROUND_LAB_STORAGE_KEY = 'playground_lab_state_v1';
const MAX_PERSISTED_LAB_MESSAGES = 12;

function loadPersistedLabState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(PLAYGROUND_LAB_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return parsed as {
      compareMode?: boolean;
      input?: string;
      systemInstruction?: string;
      temperature?: number;
      maxTokens?: number;
      jsonMode?: boolean;
      modelA?: string;
      modelB?: string;
      messagesA?: Message[];
      messagesB?: Message[];
    };
  } catch {
    return null;
  }
}

function escapeHtml(content: string): string {
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatTime(timestamp?: string): string {
  if (!timestamp) return '--:--';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '--:--';
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function PlaygroundMetricCard(props: { label: string; value: string; note: string }) {
  return (
    <div class="playground-kpi">
      <div class="playground-kpi-label">{props.label}</div>
      <div class="playground-kpi-value">{props.value}</div>
      <div class="playground-kpi-note">{props.note}</div>
    </div>
  );
}

function PlaygroundMessageBubble(props: {
  message: Message;
  onApprove?: () => void;
  onReject?: () => void;
}) {
  const isAssistant = () => props.message.role === 'assistant';
  const feedbackStatusLabel = () =>
    props.message.feedback_status === 'useful' ? 'Útil registrado' : 'Não útil registrado';

  return (
    <div
      class={`playground-message ${
        isAssistant() ? 'playground-message--assistant' : 'playground-message--user'
      }`}
    >
      <div class="playground-message-label">
        <span>{isAssistant() ? 'Playground' : 'Você'}</span>
        <span class="playground-message-time">{formatTime(props.message.timestamp)}</span>
      </div>

      <div
        class="markdown-body playground-markdown bg-transparent"
        innerHTML={
          props.message.content ? escapeHtml(props.message.content).replace(/\n/g, '<br/>') : ''
        }
      />

      <Show when={isAssistant() && props.message.request_id}>
        <div class="playground-feedback">
          <span class="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Feedback
          </span>
          <button
            class="btn btn-ghost btn-xs"
            onClick={() => props.onApprove?.()}
            aria-pressed={props.message.feedback_status === 'useful'}
            disabled={!!props.message.feedback_status}
          >
            <ThumbsUp size={12} />
          </button>
          <button
            class="btn btn-ghost btn-xs"
            onClick={() => props.onReject?.()}
            aria-pressed={props.message.feedback_status === 'not_useful'}
            disabled={!!props.message.feedback_status}
          >
            <ThumbsDown size={12} />
          </button>
          <Show when={props.message.feedback_status}>
            <span class="playground-status-pill is-success">{feedbackStatusLabel()}</span>
          </Show>
          <span class="ml-auto text-[11px] font-mono text-muted-foreground">
            {props.message.request_id}
          </span>
        </div>
      </Show>
    </div>
  );
}

export default function Playground() {
  const navigate = useNavigate();

  const [messagesA, setMessagesA] = createSignal<Message[]>([]);
  const [modelA, setModelA] = createSignal('server-default');
  const [responseTimeA, setResponseTimeA] = createSignal(0);
  const [loadingA, setLoadingA] = createSignal(false);

  const [compareMode, setCompareMode] = createSignal(false);
  const [messagesB, setMessagesB] = createSignal<Message[]>([]);
  const [modelB, setModelB] = createSignal('server-default');
  const [responseTimeB, setResponseTimeB] = createSignal(0);
  const [loadingB, setLoadingB] = createSignal(false);

  const [input, setInput] = createSignal('');
  const [systemInstruction, setSystemInstruction] = createSignal('');
  const [showCodeModal, setShowCodeModal] = createSignal(false);
  const [systemExpanded, setSystemExpanded] = createSignal(false);

  const [temperature, setTemperature] = createSignal(1.0);
  const [maxTokens, setMaxTokens] = createSignal(2048);
  const [jsonMode, setJsonMode] = createSignal(false);

  const [modelInfo, setModelInfo] = createSignal<ModelInfo | null>(null);
  const [metrics, setMetrics] = createSignal<PlaygroundMetrics | null>(null);
  const [accessBlockedMessage, setAccessBlockedMessage] = createSignal<string | null>(null);
  const [stateHydrated, setStateHydrated] = createSignal(false);

  let messagesEndRefA: HTMLDivElement | undefined;
  let messagesEndRefB: HTMLDivElement | undefined;

  const models = [{ id: 'server-default', name: 'Server Default (settings.LLM_MODEL_NAME)' }];

  const biTasks = [
    {
      title: 'Ruptura por Loja',
      system:
        'Você é analista BI de varejo físico. Responda com Resumo executivo, Tabela operacional e Próximas ações.',
      prompt: 'Monte uma SQL de ruptura por loja e período para priorizar reposição.',
      copy: 'Fluxo rápido para priorização de reposição e recorte por período.',
    },
    {
      title: 'Margem por Categoria',
      system:
        'Você é analista de performance comercial. Estruture resposta em Resumo executivo, Tabela operacional e Próximas ações.',
      prompt: 'Quero um template SQL para analisar margem por categoria e identificar outliers.',
      copy: 'Útil para achar outliers e categorias que drenam margem.',
    },
    {
      title: 'Top Produtos',
      system: 'Você é analista de sortimento. Use saída objetiva para decisão de loja física.',
      prompt: 'Crie uma análise dos top produtos por venda e giro para lojas físicas.',
      copy: 'Combina giro com ranking operacional para tomada de decisão.',
    },
    {
      title: 'Transferências',
      system: 'Você é analista de abastecimento. Priorize recomendações acionáveis.',
      prompt: 'Preciso de uma query de transferências entre lojas com base no estoque.',
      copy: 'Ajuda a montar um plano tático entre UNEs.',
    },
    {
      title: 'Demanda',
      system: 'Você é analista de planejamento. Entregue plano operacional curto.',
      prompt: 'Sugira um roteiro para previsão de demanda semanal por loja e categoria.',
      copy: 'Bom ponto de partida para demanda e sazonalidade.',
    },
  ];

  const examples = [
    {
      title: 'Análise Financeira',
      system:
        'Você é um analista financeiro sênior. Responda de forma concisa e use tabelas markdown quando apropriado.',
      prompt:
        'Analise o ROI de uma campanha de marketing que custou R$ 50.000 e gerou R$ 120.000 em vendas.',
      copy: 'Experimenta uma resposta curta com framing executivo.',
    },
    {
      title: 'SQL Expert',
      system: 'Você é um DBA especialista em SQL Server. Forneça apenas o código SQL otimizado.',
      prompt: 'Escreva uma query para encontrar produtos que não venderam nos últimos 6 meses.',
      copy: 'Força o Playground para geração focada em SQL puro.',
    },
    {
      title: 'Python Data',
      system: 'Você é um engenheiro de dados Python. Prefira a biblioteca Polars.',
      prompt: "Crie um script para ler um arquivo Parquet e filtrar linhas onde 'status' é 'error'.",
      copy: 'Bom para validar persona técnica e estilo de biblioteca.',
    },
  ];

  onMount(async () => {
    const persistedState = loadPersistedLabState();
    if (persistedState) {
      if (typeof persistedState.compareMode === 'boolean') setCompareMode(persistedState.compareMode);
      if (typeof persistedState.input === 'string') setInput(persistedState.input);
      if (typeof persistedState.systemInstruction === 'string') {
        setSystemInstruction(persistedState.systemInstruction);
        setSystemExpanded(!!persistedState.systemInstruction.trim());
      }
      if (typeof persistedState.temperature === 'number') setTemperature(persistedState.temperature);
      if (typeof persistedState.maxTokens === 'number') setMaxTokens(persistedState.maxTokens);
      if (typeof persistedState.jsonMode === 'boolean') setJsonMode(persistedState.jsonMode);
      if (typeof persistedState.modelA === 'string') setModelA(persistedState.modelA);
      if (typeof persistedState.modelB === 'string') setModelB(persistedState.modelB);
      if (Array.isArray(persistedState.messagesA)) {
        setMessagesA(persistedState.messagesA.filter((message) => message && typeof message.content === 'string').slice(-MAX_PERSISTED_LAB_MESSAGES));
      }
      if (Array.isArray(persistedState.messagesB)) {
        setMessagesB(persistedState.messagesB.filter((message) => message && typeof message.content === 'string').slice(-MAX_PERSISTED_LAB_MESSAGES));
      }
    }
    setStateHydrated(true);

    try {
      const response = await playgroundApi.getInfo();
      setModelInfo(response.data);
      if (response.data.model && !(persistedState?.modelA && persistedState.modelA !== 'server-default')) {
        setModelA(response.data.model);
      }
      if (response.data?.playground_access_enabled === false) {
        navigate('/dashboard', { replace: true });
        return;
      }
      setAccessBlockedMessage(null);
    } catch (error) {
      const detail = (error as any)?.response?.data?.detail;
      if ((error as any)?.response?.status === 403) {
        navigate('/dashboard', { replace: true });
        return;
      }
      setAccessBlockedMessage(detail || 'Não foi possível carregar as capacidades do Playground.');
    }

    try {
      const response = await playgroundApi.getMetrics();
      setMetrics(response.data);
    } catch {
      // Metrics may require admin; keep silent for non-admin users.
    }
  });

  createEffect(() => {
    if (messagesA()) {
      setTimeout(() => messagesEndRefA?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
    if (compareMode() && messagesB()) {
      setTimeout(() => messagesEndRefB?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  });

  createEffect(() => {
    if (!stateHydrated() || typeof window === 'undefined') return;

    const payload = {
      compareMode: compareMode(),
      input: input(),
      systemInstruction: systemInstruction(),
      temperature: temperature(),
      maxTokens: maxTokens(),
      jsonMode: jsonMode(),
      modelA: modelA(),
      modelB: modelB(),
      messagesA: messagesA().slice(-MAX_PERSISTED_LAB_MESSAGES),
      messagesB: messagesB().slice(-MAX_PERSISTED_LAB_MESSAGES),
    };

    try {
      window.localStorage.setItem(PLAYGROUND_LAB_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // Ignore localStorage quota issues.
    }
  });

  const streamRequest = async (
    panelLabel: string,
    modelName: string,
    currentHistory: Message[],
    setMessages: (msgs: Message[]) => void,
    setLoading: (value: boolean) => void,
    setResponseTime: (value: number) => void,
  ) => {
    setLoading(true);
    const assistantId = Date.now().toString() + Math.random().toString();
    let accumulatedText = '';
    let requestId: string | undefined;

    const initialMessages = [
      ...currentHistory,
      {
        id: assistantId,
        role: 'assistant' as const,
        content: 'Processando resposta do Playground...',
        timestamp: new Date().toISOString(),
      },
    ];
    setMessages(initialMessages);
    announcer.polite(`Streaming iniciado no ${panelLabel}.`);

    try {
      await authApi.getMe();
    } catch (error) {
      console.warn('Falha ao renovar token no Playground:', error);
    }

    try {
      const payload: Record<string, unknown> = {
        message: currentHistory[currentHistory.length - 1].content,
        history: currentHistory.slice(0, -1).map((message) => ({
          role: message.role,
          content: message.content,
        })),
        system_instruction: systemInstruction(),
        temperature: temperature(),
        max_tokens: maxTokens(),
        json_mode: jsonMode(),
        stream: true,
      };

      if (modelName && modelName !== 'server-default') {
        payload.model = modelName;
      }

      const response = await fetch('/api/v1/playground/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${sessionStorage.getItem('token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader');

      let eventBuffer = '';
      let streamCompleted = false;

      while (!streamCompleted) {
        const { done, value } = await reader.read();
        if (done) break;

        eventBuffer += decoder.decode(value, { stream: true });
        const events = eventBuffer.split('\n\n');
        eventBuffer = events.pop() ?? '';

        for (const eventChunk of events) {
          if (!eventChunk.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(eventChunk.slice(6).trim());
            if (data.type === 'token') {
              accumulatedText += data.text || '';
              setMessages(
                initialMessages.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: accumulatedText, request_id: requestId }
                    : message,
                ),
              );
            } else if (data.type === 'start') {
              requestId = data.request_id;
            } else if (data.type === 'degraded') {
              accumulatedText +=
                (accumulatedText ? '\n\n' : '') + `⚠️ Modo degradado: ${data.text}`;
              setMessages(
                initialMessages.map((message) =>
                  message.id === assistantId
                    ? {
                        ...message,
                        content: accumulatedText || `⚠️ Modo degradado: ${data.text}`,
                        request_id: requestId,
                      }
                    : message,
                ),
              );
            } else if (data.type === 'warning') {
              accumulatedText += (accumulatedText ? '\n\n' : '') + `⚠️ ${data.text}`;
              setMessages(
                initialMessages.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: accumulatedText, request_id: requestId }
                    : message,
                ),
              );
            } else if (data.type === 'done') {
              if (data.request_id) requestId = data.request_id;
              if (!accumulatedText.trim()) {
                accumulatedText = 'Sem resposta retornada pelo Playground nesta execução.';
              }
              setMessages(
                initialMessages.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: accumulatedText, request_id: requestId }
                    : message,
                ),
              );
              setResponseTime(data.metrics?.time || 0);
              streamCompleted = true;
              break;
            } else if (data.type === 'error') {
              accumulatedText =
                (accumulatedText.trim() ? `${accumulatedText}\n\n` : '') +
                `⚠️ Não foi possível concluir no Playground: ${data.text}`;
              setMessages(
                initialMessages.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: accumulatedText, request_id: requestId }
                    : message,
                ),
              );
              streamCompleted = true;
              break;
            }
          } catch {
            // Ignore JSON parse error for partial chunks.
          }
        }
      }

      try {
        await reader.cancel();
      } catch {
        // No-op.
      }
    } catch (error: any) {
      setMessages(
        initialMessages.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content: `⚠️ Falha de conexão com o Playground: ${error.message}`,
                request_id: requestId,
              }
            : message,
        ),
      );
      toastManager.error(`Falha no stream: ${error.message}`);
      announcer.assertive(`Falha de conexão com o Playground: ${error.message}`);
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
      const feedbackStatus: Message['feedback_status'] = useful ? 'useful' : 'not_useful';
      const updateMessage = (candidate: Message) =>
        candidate.id === message.id
          ? { ...candidate, feedback_status: feedbackStatus }
          : candidate;
      setMessagesA((prev) => prev.map(updateMessage));
      setMessagesB((prev) => prev.map(updateMessage));
      toastManager.success(useful ? 'Feedback útil registrado.' : 'Feedback registrado.');
      announcer.polite('Feedback registrado no Playground.');
    } catch (error) {
      console.warn('Falha ao enviar feedback Playground', error);
      toastManager.error('Não foi possível registrar o feedback.');
      announcer.assertive('Não foi possível registrar o feedback do Playground.');
    }
  };

  const exportJson = () => {
    const payload = {
      panelA: messagesA(),
      panelB: messagesB(),
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `playground-export-${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    toastManager.success('Exportação JSON iniciada.');
  };

  const exportCsv = () => {
    const rows = [...messagesA(), ...messagesB()].map((message) => ({
      id: message.id,
      role: message.role,
      timestamp: message.timestamp,
      request_id: message.request_id || '',
      content: (message.content || '').replace(/\n/g, ' ').replace(/"/g, '""'),
    }));
    const header = 'id,role,timestamp,request_id,content';
    const csv = [
      header,
      ...rows.map(
        (row) =>
          `"${row.id}","${row.role}","${row.timestamp}","${row.request_id}","${row.content}"`,
      ),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `playground-export-${Date.now()}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    toastManager.success('Exportação CSV iniciada.');
  };

  const sendMessage = async (event?: Event) => {
    event?.preventDefault();
    if (accessBlockedMessage()) return;
    if (!input().trim() || loadingA() || loadingB()) return;

    const userContent = input();
    setInput('');

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userContent,
      timestamp: new Date().toISOString(),
    };

    const newHistoryA = [...messagesA(), userMessage];
    setMessagesA(newHistoryA);
    void streamRequest('painel A', modelA(), newHistoryA, setMessagesA, setLoadingA, setResponseTimeA);

    if (compareMode()) {
      const newHistoryB = [...messagesB(), userMessage];
      setMessagesB(newHistoryB);
      void streamRequest('painel B', modelB(), newHistoryB, setMessagesB, setLoadingB, setResponseTimeB);
    }
  };

  const clearHistory = () => {
    if (!confirm('Deseja limpar o histórico?')) return;
    setMessagesA([]);
    setMessagesB([]);
    setResponseTimeA(0);
    setResponseTimeB(0);
    try {
      window.localStorage.removeItem(PLAYGROUND_LAB_STORAGE_KEY);
    } catch {
      // Ignore storage cleanup issues.
    }
    toastManager.success('Sessão do laboratório limpa.');
    announcer.polite('Sessão do laboratório limpa.');
  };

  const loadExample = (example: { system: string; prompt: string }) => {
    setSystemInstruction(example.system);
    setInput(example.prompt);
    setSystemExpanded(true);
    toastManager.info('Exemplo carregado no laboratório.', 2500);
  };

  const generateCodeSnippet = () => {
    const prompt = input().trim() || 'Explique rapidamente as vendas por loja.';
    const system = systemInstruction().trim();
    const basePayload: Record<string, unknown> = {
      message: prompt,
      history: [],
      temperature: Number(temperature().toFixed(1)),
      max_tokens: maxTokens(),
      json_mode: jsonMode(),
      stream: true,
    };

    if (system) basePayload.system_instruction = system;

    const buildSnippetPayload = (modelName: string) => ({
      ...basePayload,
      ...(modelName && modelName !== 'server-default' ? { model: modelName } : {}),
    });

    const payload = buildSnippetPayload(modelA());
    const comparePayload: Record<string, unknown> | null = compareMode()
      ? buildSnippetPayload(modelB())
      : null;

    const snippetLines = [
      "const token = sessionStorage.getItem('token');",
      '',
      `const panelA = ${JSON.stringify(payload, null, 2)};`,
      comparePayload ? `const panelB = ${JSON.stringify(comparePayload, null, 2)};` : '',
      '',
      'async function streamPlayground(panelName, payload) {',
      "  const response = await fetch('/api/v1/playground/stream', {",
      "    method: 'POST',",
      '    headers: {',
      "      'Content-Type': 'application/json',",
      '      Authorization: `Bearer ${token}`,',
      '    },',
      '    body: JSON.stringify(payload),',
      '  });',
      '',
      '  if (!response.ok) {',
      "    throw new Error(`HTTP ${response.status}`);",
      '  }',
      '',
      '  const reader = response.body?.getReader();',
      '  const decoder = new TextDecoder();',
      "  let buffer = '';",
      '',
      '  while (reader) {',
      '    const { done, value } = await reader.read();',
      '    if (done) break;',
      '    buffer += decoder.decode(value, { stream: true });',
      "    const events = buffer.split('\\n\\n');",
      "    buffer = events.pop() ?? '';",
      '',
      '    for (const eventChunk of events) {',
      "      if (!eventChunk.startsWith('data: ')) continue;",
      "      const event = JSON.parse(eventChunk.slice(6));",
      "      if (event.type === 'token') {",
      "        console.log(panelName, event.text);",
      '      }',
      "      if (event.type === 'done') {",
      "        console.log(panelName, 'done', event.metrics);",
      '      }',
      '    }',
      '  }',
      '}',
      '',
      comparePayload
        ? "await Promise.all([streamPlayground('panel-a', panelA), streamPlayground('panel-b', panelB)]);"
        : "await streamPlayground('panel-a', panelA);",
    ];

    return snippetLines.filter(Boolean).join('\n');
  };

  const totalMessages = () => messagesA().length + (compareMode() ? messagesB().length : 0);
  const usefulRate = () =>
    metrics() ? `${metrics()!.feedback_useful_rate.toFixed(0)}%` : 'Sem dados';

  const renderEmptyState = (title: string, copy: string) => (
    <div class="playground-empty">
      <div>
        <div class="playground-empty-title">{title}</div>
        <p class="playground-empty-copy">{copy}</p>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <For each={biTasks.slice(0, 4)}>
          {(task) => (
            <button class="playground-task-button" onClick={() => loadExample(task)}>
              <div class="playground-task-button-title">
                <Play size={14} />
                {task.title}
              </div>
              <div class="playground-task-button-copy">{task.copy}</div>
            </button>
          )}
        </For>
      </div>
    </div>
  );

  return (
    <div class="playground-scene h-full overflow-hidden">
      <div class="playground-shell h-full grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-4 p-4">
        <div class="playground-main-column flex flex-col gap-4">
          <section class="playground-surface playground-hero">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div class="space-y-4">
                <div class="space-y-2">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="playground-chip">
                      <Terminal size={14} />
                      <strong>Playground BI</strong>
                    </span>
                    <span class="playground-chip">
                      <Cpu size={14} />
                      {modelInfo()?.playground_mode_label || 'Local first'}
                    </span>
                    <span class="playground-chip">
                      <Clock size={14} />
                      {compareMode() ? 'Comparação ativa' : 'Single mode'}
                    </span>
                  </div>

                  <div>
                    <h1 class="text-3xl font-bold text-foreground">
                      Laboratório de prompts com leitura operacional clara
                    </h1>
                    <p class="max-w-3xl text-sm leading-7 text-muted-foreground">
                      Ajuste persona, temperatura, tokens e compare respostas sem perder o foco
                      em execução. O layout privilegia leitura, diferença entre painéis e sinais
                      de qualidade para cada rodada.
                    </p>
                  </div>
                </div>

                <div class="playground-kpi-grid">
                  <PlaygroundMetricCard
                    label="Sessões"
                    value={String(totalMessages())}
                    note={
                      compareMode()
                        ? 'Mensagens espelhadas nos dois painéis'
                        : 'Fluxo simples de inspeção'
                    }
                  />
                  <PlaygroundMetricCard
                    label="Feedback útil"
                    value={usefulRate()}
                    note={
                      metrics()
                        ? `${metrics()!.feedback_total} feedbacks acumulados`
                        : 'Sem telemetria para este perfil'
                    }
                  />
                  <PlaygroundMetricCard
                    label="Execução"
                    value={modelInfo()?.remote_llm_enabled ? 'Híbrida' : 'Local-first'}
                    note="A interface preserva streaming e fallback degradado."
                  />
                </div>
              </div>

                <div class="flex flex-col items-stretch gap-3 xl:items-end">
                  <button
                    onClick={() => navigate('/playground')}
                    class="btn btn-ghost gap-2"
                    title="Voltar ao fluxo operacional"
                    aria-label="Voltar ao fluxo operacional"
                  >
                    <ArrowLeft size={16} />
                    Fluxo Ops
                  </button>
                  <div class="playground-toggle">
                  <button
                    classList={{ active: !compareMode() }}
                    onClick={() => setCompareMode(false)}
                    aria-pressed={!compareMode()}
                  >
                    <LayoutTemplate size={14} />
                    Single
                  </button>
                  <button
                    classList={{ active: compareMode() }}
                    onClick={() => setCompareMode(true)}
                    aria-pressed={compareMode()}
                  >
                    <Split size={14} />
                    Compare
                  </button>
                </div>

                <div class="flex flex-wrap items-center gap-2 xl:justify-end">
                  <button
                    onClick={() => setShowCodeModal(true)}
                    class="btn btn-outline gap-2"
                    title="Ver snippet"
                    aria-label="Abrir snippet de integração"
                  >
                    <Code size={16} />
                    Snippet
                  </button>
                  <button onClick={exportJson} class="btn btn-outline gap-2" title="Exportar JSON">
                    <FileJson size={16} />
                    JSON
                  </button>
                  <button onClick={exportCsv} class="btn btn-primary gap-2" title="Exportar CSV">
                    <Download size={16} />
                    CSV
                  </button>
                </div>
              </div>
            </div>
          </section>

          <Show when={accessBlockedMessage()}>
            <div class="playground-note border border-destructive/20 bg-destructive/5 text-destructive" role="alert">
              {accessBlockedMessage()}
            </div>
          </Show>

          <section class="playground-surface overflow-hidden rounded-[26px]">
            <button
              onClick={() => setSystemExpanded(!systemExpanded())}
              class="w-full flex items-center justify-between px-5 py-4 text-left"
            >
              <div>
                <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Persona e instrução de sistema
                </div>
                <div class="mt-1 text-sm font-semibold text-foreground">
                  Defina o enquadramento antes de abrir uma rodada de comparação.
                </div>
              </div>
              <div class="playground-chip">
                <Settings size={14} />
                {systemExpanded() ? 'Ocultar' : 'Editar'}
                <Show when={systemExpanded()} fallback={<ChevronRight size={14} />}>
                  <ChevronDown size={14} />
                </Show>
              </div>
            </button>

            <Show when={systemExpanded()}>
              <div class="border-t px-5 pb-5 pt-1">
                <textarea
                  class="input w-full min-h-[120px] resize-none font-mono text-sm leading-6"
                  placeholder="Ex.: Você é um assistente especialista em análise de dados. Responda sempre em JSON."
                  value={systemInstruction()}
                  onInput={(event) => setSystemInstruction(event.currentTarget.value)}
                  aria-label="Instrução de sistema"
                />
                <div class="mt-3 flex flex-wrap gap-2">
                  <span class="playground-chip">
                    Temperatura <strong>{temperature().toFixed(1)}</strong>
                  </span>
                  <span class="playground-chip">
                    Max tokens <strong>{maxTokens()}</strong>
                  </span>
                  <span class="playground-chip">
                    JSON <strong>{jsonMode() ? 'on' : 'off'}</strong>
                  </span>
                </div>
              </div>
            </Show>
          </section>

          <div class="xl:hidden grid gap-3">
            <section class="playground-surface playground-sidebar-card">
              <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Deck móvel
              </div>
              <div class="mt-2 grid gap-3 sm:grid-cols-2">
                <For each={examples.slice(0, 2)}>
                  {(example) => (
                    <button class="playground-task-button" onClick={() => loadExample(example)}>
                      <div class="playground-task-button-title">
                        <Play size={14} />
                        {example.title}
                      </div>
                      <div class="playground-task-button-copy">{example.copy}</div>
                    </button>
                  )}
                </For>
              </div>
            </section>
          </div>

          <div class="flex-1 min-h-0">
            <div
              class={`grid h-full min-h-0 gap-4 ${
                compareMode()
                  ? 'grid-cols-1 2xl:grid-cols-2'
                  : 'grid-cols-1 max-w-5xl mx-auto'
              }`}
            >
              <section class="playground-panel">
                <div class="playground-panel-header px-5 py-4">
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <div class="flex items-center gap-3">
                      <span class="h-3 w-3 rounded-full bg-[var(--chart-2)] shadow-[0_0_0_6px_rgba(0,174,239,0.12)]" />
                      <div>
                        <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                          Painel A
                        </div>
                        <div class="mt-1 flex items-center gap-3">
                          <select
                            class="bg-transparent text-sm font-semibold text-foreground focus:outline-none"
                            value={modelA()}
                            onChange={(event) => setModelA(event.currentTarget.value)}
                            aria-label="Modelo do painel A"
                          >
                            <For each={models}>
                              {(model) => <option value={model.id}>{model.name}</option>}
                            </For>
                          </select>
                          <span class="text-xs text-muted-foreground">
                            {loadingA() ? 'Streaming em andamento' : 'Canal de referência'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div class="flex flex-wrap items-center gap-2">
                      <span class="playground-chip">
                        <Clock size={14} />
                        {loadingA() ? 'Processando' : `${responseTimeA().toFixed(2)}s`}
                      </span>
                      <span class="playground-chip">
                        <strong>{messagesA().length}</strong> mensagens
                      </span>
                    </div>
                  </div>
                </div>

                <div class="playground-scroll flex-1 p-5">
                  <Show
                    when={messagesA().length > 0}
                    fallback={renderEmptyState(
                      'Comece com um prompt de BI ou um caso técnico.',
                      'A superfície foi desenhada para leitura executiva primeiro e inspeção de prompt depois. Use um dos cartões abaixo para abrir a sessão com contexto útil.',
                    )}
                  >
                    <div class="space-y-5">
                      <For each={messagesA()}>
                        {(message) => (
                          <PlaygroundMessageBubble
                            message={message}
                            onApprove={() => void submitFeedback(message, true)}
                            onReject={() => void submitFeedback(message, false)}
                          />
                        )}
                      </For>
                    </div>
                  </Show>
                  <div ref={messagesEndRefA} />
                </div>
              </section>

              <Show when={compareMode()}>
                <section class="playground-panel">
                  <div class="playground-panel-header px-5 py-4">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                      <div class="flex items-center gap-3">
                        <span class="h-3 w-3 rounded-full bg-[var(--chart-3)] shadow-[0_0_0_6px_rgba(102,45,145,0.12)]" />
                        <div>
                          <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                            Painel B
                          </div>
                          <div class="mt-1 flex items-center gap-3">
                            <select
                              class="bg-transparent text-sm font-semibold text-foreground focus:outline-none"
                              value={modelB()}
                              onChange={(event) => setModelB(event.currentTarget.value)}
                              aria-label="Modelo do painel B"
                            >
                              <For each={models}>
                                {(model) => <option value={model.id}>{model.name}</option>}
                              </For>
                            </select>
                            <span class="text-xs text-muted-foreground">
                              Mesmo prompt, leitura paralela
                            </span>
                          </div>
                        </div>
                      </div>

                      <div class="flex flex-wrap items-center gap-2">
                        <span class="playground-chip">
                          <Clock size={14} />
                          {loadingB() ? 'Processando' : `${responseTimeB().toFixed(2)}s`}
                        </span>
                        <span class="playground-chip">
                          <strong>{messagesB().length}</strong> mensagens
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="playground-scroll flex-1 p-5">
                    <Show
                      when={messagesB().length > 0}
                      fallback={renderEmptyState(
                        'Compare tom, estrutura e velocidade.',
                        'O segundo painel recebe a mesma pergunta e ajuda a inspecionar diferença de framing, densidade e comportamento degradado sem mudar o contexto.',
                      )}
                    >
                      <div class="space-y-5">
                        <For each={messagesB()}>
                          {(message) => (
                            <PlaygroundMessageBubble
                              message={message}
                              onApprove={() => void submitFeedback(message, true)}
                              onReject={() => void submitFeedback(message, false)}
                            />
                          )}
                        </For>
                      </div>
                    </Show>
                    <div ref={messagesEndRefB} />
                  </div>
                </section>
              </Show>
            </div>
          </div>

          <section class="playground-compose-card p-4">
            <form onSubmit={sendMessage} class="flex flex-col gap-3 xl:flex-row xl:items-end">
              <button
                type="button"
                onClick={clearHistory}
                class="btn btn-ghost btn-icon text-muted-foreground hover:text-destructive self-start"
                title="Limpar histórico"
              >
                <Trash2 size={18} />
              </button>

              <div class="flex-1">
                <label class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Prompt principal
                </label>
                <input
                  type="text"
                  class="input mt-2 h-12 w-full pr-12 font-mono text-sm shadow-sm"
                  placeholder={
                    compareMode()
                      ? 'Envie um prompt para os dois painéis...'
                      : 'Digite sua mensagem para o Playground...'
                  }
                  value={input()}
                  onInput={(event) => setInput(event.currentTarget.value)}
                  disabled={loadingA() || loadingB()}
                  aria-label="Prompt principal do laboratório"
                />
              </div>

              <div class="flex items-center gap-2 xl:pb-[1px]">
                <span class="playground-chip">
                  <Settings size={14} />
                  {systemInstruction().trim() ? 'Persona ativa' : 'Sem persona fixa'}
                </span>
                <button
                  type="submit"
                  class="btn btn-primary h-12 gap-2 px-5 shadow-md hover:shadow-lg transition-all"
                  disabled={
                    !!accessBlockedMessage() || loadingA() || loadingB() || !input().trim()
                  }
                >
                  <Show when={!loadingA() && !loadingB()} fallback={<Clock size={18} class="animate-spin" />}>
                    <Send size={18} />
                  </Show>
                  Enviar
                </button>
              </div>
            </form>
          </section>
        </div>

        <aside class="hidden min-h-0 xl:flex xl:flex-col xl:gap-4 xl:overflow-y-auto xl:pr-1">
          <section class="playground-surface playground-sidebar-card">
            <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              Console de configuração
            </div>

            <div class="mt-4 space-y-4">
              <div>
                <div class="mb-2 flex items-center justify-between">
                  <label class="text-sm font-semibold text-foreground">Temperatura</label>
                  <span class="playground-chip">
                    <strong>{temperature().toFixed(1)}</strong>
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature()}
                  onInput={(event) => setTemperature(parseFloat(event.currentTarget.value))}
                  class="w-full accent-primary"
                />
              </div>

              <div>
                <div class="mb-2 flex items-center justify-between">
                  <label class="text-sm font-semibold text-foreground">Max tokens</label>
                  <span class="playground-chip">
                    <strong>{maxTokens()}</strong>
                  </span>
                </div>
                <input
                  type="range"
                  min="100"
                  max={modelInfo()?.max_tokens_limit || 8192}
                  step="100"
                  value={maxTokens()}
                  onInput={(event) => setMaxTokens(parseInt(event.currentTarget.value, 10))}
                  class="w-full accent-primary"
                />
              </div>

              <div class="playground-note">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <div class="text-sm font-semibold text-foreground">JSON Mode</div>
                    <div class="text-xs leading-6">
                      Força estrutura rígida para respostas comparáveis.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={jsonMode()}
                    onChange={(event) => setJsonMode(event.currentTarget.checked)}
                    class="toggle toggle-sm toggle-primary"
                    aria-label="Ativar JSON mode"
                  />
                </div>
              </div>
            </div>
          </section>

          <section class="playground-surface playground-sidebar-card">
            <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              Tarefas BI
            </div>
            <div class="mt-4 grid gap-3">
              <For each={biTasks}>
                {(task) => (
                  <button class="playground-task-button" onClick={() => loadExample(task)}>
                    <div class="playground-task-button-title">
                      <Play size={14} />
                      {task.title}
                    </div>
                    <div class="playground-task-button-copy">{task.copy}</div>
                  </button>
                )}
              </For>
            </div>
          </section>

          <section class="playground-surface playground-sidebar-card">
            <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
              Exemplos técnicos
            </div>
            <div class="mt-4 grid gap-3">
              <For each={examples}>
                {(example) => (
                  <button class="playground-task-button" onClick={() => loadExample(example)}>
                    <div class="playground-task-button-title">
                      <Play size={14} />
                      {example.title}
                    </div>
                    <div class="playground-task-button-copy">{example.copy}</div>
                  </button>
                )}
              </For>
            </div>
          </section>
        </aside>
      </div>

      <Show when={showCodeModal()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm p-4">
          <div class="playground-surface w-full max-w-3xl rounded-[28px] overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="playground-snippet-title">
            <div class="flex items-center justify-between border-b px-5 py-4">
              <div>
                <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Snippet de integração
                </div>
                <div id="playground-snippet-title" class="mt-1 flex items-center gap-2 text-lg font-bold text-foreground">
                  <Code size={18} />
                  Base atual do stream do Playground
                </div>
              </div>
              <button
                onClick={() => setShowCodeModal(false)}
                class="btn btn-ghost btn-icon btn-sm"
                aria-label="Fechar snippet"
              >
                <X size={18} />
              </button>
            </div>

            <div class="p-5">
              <pre class="rounded-[22px] bg-secondary/60 p-4 text-xs font-mono overflow-x-auto text-foreground">
                {generateCodeSnippet()}
              </pre>
            </div>

            <div class="flex justify-end gap-2 border-t px-5 py-4">
              <button onClick={() => setShowCodeModal(false)} class="btn btn-outline">
                Fechar
              </button>
              <button
                class="btn btn-primary"
                onClick={() => {
                  void navigator.clipboard.writeText(generateCodeSnippet());
                  toastManager.success('Snippet copiado.');
                  announcer.polite('Snippet copiado para a área de transferência.');
                  setShowCodeModal(false);
                }}
              >
                Copiar código
              </button>
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
}
