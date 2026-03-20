import { createSignal, createEffect, onCleanup, onMount, For, Show } from 'solid-js';
import auth from '@/store/auth';
import { authApi, chatAutomationApi } from '@/lib/api';
import {
  ThinkingProcess,
  AutoResizeTextarea,
  PlotlyChart,
  DataTable,
  FeedbackButtons,
  MessageActions,
  ExportMenu,
  ChatDashboardRenderer,
  ChatAutomationCard,
} from '@/components';
import {
  fallbackFilenameFromUrl,
  getFilenameFromContentDisposition,
  isMarketResearchDownloadLink,
} from '@/lib/marketResearchDownload';
import { buildThinkingStep } from '@/lib/chatProgress';
import { marked } from 'marked';
import { Trash2, StopCircle, Bot, Sparkles, SendHorizontal, Paperclip, History, Plus, X, Mic, Volume2 } from 'lucide-solid';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';
import type { DashboardSpec } from '@/components/ChatDashboardRenderer';
import type { ChatAutomationState } from '@/components/ChatAutomationCard';

// --- HELPERS (Sanitization & Markdown) ---
const MARKET_DOWNLOAD_PATH_PREFIX = '/api/v1/chat/market-research/download/';

const sanitizePlainText = (rawValue: unknown, maxLength = 160): string => {
  const text = String(rawValue || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[\u0000-\u001F\u007F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!text) return '';
  return text.slice(0, maxLength);
};

const sanitizeHyperlink = (rawValue: unknown, allowInternalDownload = false): string => {
  const raw = String(rawValue || '').trim();
  if (!raw) return '';
  if (/[\u0000-\u001F\u007F]/.test(raw)) return '';

  const lower = raw.toLowerCase();
  if (lower.startsWith('javascript:') || lower.startsWith('vbscript:') || lower.startsWith('data:')) {
    return '';
  }

  if (allowInternalDownload && raw.startsWith(MARKET_DOWNLOAD_PATH_PREFIX)) {
    return raw;
  }

  try {
    const parsed = new URL(raw, window.location.origin);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.toString();
    }
  } catch {
    return '';
  }

  return '';
};

const sanitizeHTML = (html: string): string => {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
      .replace(/\son\w+=(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
      .replace(/\s(?:src|href)\s*=\s*(['"])\s*(?:javascript|vbscript|data):.*?\1/gi, '');
  }

  const parser = new DOMParser();
  const documentNode = parser.parseFromString(html, 'text/html');
  documentNode.querySelectorAll('script,iframe,object,embed,style,meta,link,form,input,button,textarea,select,option,svg,math,img').forEach(node => {
    node.remove();
  });

  Array.from(documentNode.body.querySelectorAll('*')).forEach((element) => {
    for (const attributeName of element.getAttributeNames()) {
      const normalized = attributeName.toLowerCase();
      if (normalized.startsWith('on') || normalized === 'style' || normalized === 'srcdoc' || normalized === 'formaction') {
        element.removeAttribute(attributeName);
        continue;
      }

      if (normalized === 'href') {
        const safeHref = sanitizeHyperlink(element.getAttribute(attributeName), true);
        if (safeHref) {
          element.setAttribute(attributeName, safeHref);
        } else {
          element.removeAttribute(attributeName);
        }
        continue;
      }

      if (normalized === 'src') {
        element.removeAttribute(attributeName);
      }
    }

    if (element.tagName.toLowerCase() === 'a') {
      element.setAttribute('rel', 'noopener noreferrer');
      if (element.getAttribute('href')?.startsWith('http')) {
        element.setAttribute('target', '_blank');
      }
    }
  });

  return documentNode.body.innerHTML;
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
  type?: 'text' | 'chart' | 'table' | 'dashboard' | 'image' | 'audio' | 'final' | 'error' | 'loading_chart' | 'loading_table';
  chart_spec?: any;
  data?: any[];
  dashboard_spec?: DashboardSpec;
  image_asset?: {
    url: string;
    alt?: string;
    prompt?: string;
  };
  audio_asset?: {
    url: string;
    title?: string;
    mime_type?: string;
  };
  response_id?: string;
  isOptimistic?: boolean;
  source?: string;
  confidence?: number;
  mode?: string;
  citations?: Array<Record<string, any>>;
  automation_request?: ChatAutomationState;

  // New Fields for Thinking Process
  thinkingSteps?: string[];
  thinkingStepKeys?: string[];
  isThinking?: boolean;
}

interface HistoryItem {
  id?: string;
  role?: string;
  content?: string;
  timestamp?: string | number;
  metadata?: Record<string, any>;
}

interface ConversationSession {
  id: string;
  title?: string | null;
  created_at?: string;
  updated_at?: string;
  message_count?: number;
}

interface ChatHistoryResponse {
  items?: HistoryItem[];
  sessions?: ConversationSession[];
  session_id?: string | null;
  user?: string;
  capabilities?: Partial<ChatCapabilities>;
}

interface PendingAttachment {
  id: string;
  file: File;
  kind: 'document' | 'image';
}

interface ChatCapabilities {
  memory: boolean;
  multimodal: boolean;
  attachments: boolean;
  voice: boolean;
  computer_use: boolean;
}

type BasketBuilderMode = 'margin' | 'promotion' | 'basket';

interface BasketBuilderItem {
  id: string;
  sku: string;
  nome: string;
  quantidade: string;
  precoUnitario: string;
  custoUnitario: string;
  descontoPct: string;
  impostoPct: string;
  freteValor: string;
  despesaVariavelPct: string;
}

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

const CHAT_ATTACHMENT_ACCEPT = '.txt,.md,.csv,.tsv,.json,.log,.xml,.png,.jpg,.jpeg,.webp';
const MAX_CHAT_ATTACHMENTS = 5;
const MAX_CHAT_ATTACHMENT_SIZE_BYTES = 2 * 1024 * 1024;
const MAX_CHAT_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
const DEFAULT_ATTACHMENT_PROMPT = 'Analise os arquivos anexados e gere um resumo executivo com os principais pontos.';

const createBasketBuilderItem = (): BasketBuilderItem => ({
  id: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`,
  sku: '',
  nome: '',
  quantidade: '1',
  precoUnitario: '',
  custoUnitario: '',
  descontoPct: '',
  impostoPct: '',
  freteValor: '',
  despesaVariavelPct: '',
});

const parseOptionalNumber = (rawValue: string): number | undefined => {
  const normalized = String(rawValue || '').replace(',', '.').trim();
  if (!normalized) return undefined;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const normalizeImageAsset = (rawValue: unknown): Message['image_asset'] | undefined => {
  if (typeof rawValue === 'string' && rawValue.trim()) {
    return { url: rawValue.trim() };
  }
  if (!rawValue || typeof rawValue !== 'object') return undefined;

  const candidate = rawValue as Record<string, unknown>;
  const url = typeof candidate.url === 'string' ? candidate.url.trim() : '';
  if (!url) return undefined;

  return {
    url,
    alt: typeof candidate.alt === 'string' ? candidate.alt : undefined,
    prompt: typeof candidate.prompt === 'string' ? candidate.prompt : undefined,
  };
};

const normalizeAudioAsset = (rawValue: unknown): Message['audio_asset'] | undefined => {
  if (typeof rawValue === 'string' && rawValue.trim()) {
    return { url: rawValue.trim() };
  }
  if (!rawValue || typeof rawValue !== 'object') return undefined;

  const candidate = rawValue as Record<string, unknown>;
  const url = typeof candidate.url === 'string' ? candidate.url.trim() : '';
  if (!url) return undefined;

  return {
    url,
    title: typeof candidate.title === 'string' ? candidate.title : undefined,
    mime_type: typeof candidate.mime_type === 'string' ? candidate.mime_type : undefined,
  };
};

const normalizeAutomationState = (rawValue: unknown): ChatAutomationState | undefined => {
  if (!rawValue || typeof rawValue !== 'object') return undefined;
  const candidate = rawValue as Record<string, any>;
  const approvalStatus = sanitizePlainText(candidate.approval_status || candidate.status, 60);
  const action = sanitizePlainText(candidate.action, 80);
  const proposalId = sanitizePlainText(candidate.proposal_id, 120);
  const approvalId = sanitizePlainText(candidate.approval_id, 120);
  if (!approvalStatus && !action && !proposalId && !approvalId) return undefined;

  const artifactRaw = candidate.artifact && typeof candidate.artifact === 'object'
    ? candidate.artifact as Record<string, any>
    : null;
  const draftRaw = candidate.draft && typeof candidate.draft === 'object'
    ? candidate.draft as Record<string, any>
    : null;

  const artifact = artifactRaw ? {
    filename: sanitizePlainText(artifactRaw.filename, 180) || undefined,
    download_url: sanitizeHyperlink(artifactRaw.download_url),
    mime_type: sanitizePlainText(artifactRaw.mime_type, 80) || undefined,
    size_bytes: typeof artifactRaw.size_bytes === 'number' ? artifactRaw.size_bytes : undefined,
  } : undefined;

  const draft = draftRaw ? {
    channel: sanitizePlainText(draftRaw.channel, 40) || undefined,
    recipient: sanitizePlainText(draftRaw.recipient, 120) || undefined,
    subject: sanitizePlainText(draftRaw.subject, 160) || undefined,
    body: typeof draftRaw.body === 'string' ? draftRaw.body.trim().slice(0, 4000) : undefined,
  } : undefined;

  return {
    proposal_id: proposalId || undefined,
    approval_id: approvalId || undefined,
    approval_status: approvalStatus || undefined,
    action: action || undefined,
    title: sanitizePlainText(candidate.title, 160) || undefined,
    summary: sanitizePlainText(candidate.summary, 240) || undefined,
    request_text: typeof candidate.request_text === 'string' ? candidate.request_text.trim().slice(0, 1200) : undefined,
    params: candidate.params && typeof candidate.params === 'object' ? candidate.params as Record<string, any> : undefined,
    target_label: sanitizePlainText(candidate.target_label, 120) || undefined,
    review_required: candidate.review_required === true,
    follow_up_action: sanitizePlainText(candidate.follow_up_action, 80) || undefined,
    follow_up_label: sanitizePlainText(candidate.follow_up_label, 80) || undefined,
    result_summary: sanitizePlainText(candidate.result_summary, 240) || undefined,
    execution_error: sanitizePlainText(candidate.execution_error, 240) || undefined,
    artifact,
    draft,
  };
};

const normalizeCitations = (rawValue: unknown): Array<Record<string, any>> => {
  if (!Array.isArray(rawValue)) return [];

  return rawValue
    .slice(0, 8)
    .flatMap((entry, index) => {
      if (!entry || typeof entry !== 'object') return [];

      const candidate = entry as Record<string, unknown>;
      const source = sanitizePlainText(
        candidate.source || candidate.domain || candidate.competitor || `Fonte ${index + 1}`,
        140,
      );
      const domain = sanitizePlainText(candidate.domain, 80);
      const competitor = sanitizePlainText(candidate.competitor, 80);
      const documentId = sanitizePlainText(candidate.document_id, 120);
      const url = sanitizeHyperlink(candidate.url);

      if (!source && !domain && !competitor && !documentId && !url) return [];

      return [{
        source: source || undefined,
        domain: domain || undefined,
        competitor: competitor || undefined,
        document_id: documentId || undefined,
        url: url || undefined,
      }];
    });
};

const normalizeChatCapabilities = (rawValue: unknown): ChatCapabilities => {
  const candidate = rawValue && typeof rawValue === 'object' ? rawValue as Record<string, unknown> : {};
  const multimodal = candidate.multimodal !== false;
  return {
    memory: candidate.memory !== false,
    multimodal,
    attachments: multimodal && candidate.attachments !== false,
    voice: multimodal && candidate.voice !== false,
    computer_use: candidate.computer_use === true,
  };
};

const createInitialGreetingMessage = (): Message => ({
  id: '0',
  role: 'assistant',
  text: 'Olá! Sou o Caçulinha. Posso analisar vendas, estoque e tendências para você. Como posso ajudar hoje?',
  timestamp: Date.now(),
  type: 'text',
  response_id: 'initial_greeting',
  thinkingSteps: [],
  thinkingStepKeys: [],
  isThinking: false,
});

const parseHistoryTimestamp = (rawValue: string | number | undefined, fallback: number): number => {
  if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
    return rawValue;
  }
  if (typeof rawValue === 'string') {
    const parsed = Date.parse(rawValue);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return fallback;
};

const formatConversationTimestamp = (rawValue?: string): string => {
  if (!rawValue) return '';
  const parsed = Date.parse(rawValue);
  if (Number.isNaN(parsed)) return '';
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
};

const mapHistoryItemToMessage = (item: HistoryItem, index: number): Message | null => {
  const role = item?.role === 'user' || item?.role === 'assistant' || item?.role === 'system'
    ? item.role
    : null;
  if (!role) return null;

  const metadata = item?.metadata && typeof item.metadata === 'object' ? item.metadata : {};
  const uiPayload = metadata?.ui_payload && typeof metadata.ui_payload === 'object' ? metadata.ui_payload : {};
  const fallbackTimestamp = Date.now() + index;
  const responseId =
    typeof metadata?.request_id === 'string'
      ? metadata.request_id
      : typeof uiPayload?.request_id === 'string'
        ? uiPayload.request_id
        : undefined;
  const confidence =
    typeof metadata?.confidence === 'number'
      ? metadata.confidence
      : typeof uiPayload?.confidence === 'number'
        ? uiPayload.confidence
        : undefined;
  const citations = normalizeCitations(
    Array.isArray(metadata?.citations)
      ? metadata.citations
      : Array.isArray(uiPayload?.citations)
        ? uiPayload.citations
        : undefined,
  );
  const imageAsset = normalizeImageAsset(uiPayload?.image_asset);
  const audioAsset = normalizeAudioAsset(uiPayload?.audio_asset);
  const automationRequest = normalizeAutomationState(uiPayload?.automation_request);

  const message: Message = {
    id: typeof item.id === 'string' && item.id ? item.id : `history-${index}`,
    role,
    text: typeof item.content === 'string' ? item.content : '',
    timestamp: parseHistoryTimestamp(item.timestamp, fallbackTimestamp),
    type: 'text',
  };

  if (role === 'assistant') {
    message.response_id = responseId;
    message.source =
      typeof metadata?.source === 'string'
        ? metadata.source
        : typeof uiPayload?.source === 'string'
          ? uiPayload.source
          : undefined;
    message.confidence = confidence;
    message.mode =
      typeof metadata?.mode === 'string'
        ? metadata.mode
        : typeof uiPayload?.mode === 'string'
          ? uiPayload.mode
          : undefined;
    message.citations = citations;
    message.image_asset = imageAsset;
    message.audio_asset = audioAsset;
    message.automation_request = automationRequest;
    message.thinkingSteps = [];
    message.thinkingStepKeys = [];
    message.isThinking = false;

    if (uiPayload?.chart_spec && typeof uiPayload.chart_spec === 'object') {
      message.chart_spec = uiPayload.chart_spec;
      message.type = 'chart';
    }
    if (Array.isArray(uiPayload?.data) && uiPayload.data.length > 0) {
      message.data = uiPayload.data;
      if (!message.chart_spec) {
        message.type = 'table';
      }
    }
    if (uiPayload?.dashboard_spec && typeof uiPayload.dashboard_spec === 'object') {
      message.dashboard_spec = uiPayload.dashboard_spec as DashboardSpec;
      message.type = 'dashboard';
    }
    if (imageAsset && !message.chart_spec && !message.data && !message.dashboard_spec) {
      message.type = 'image';
    }
    if (audioAsset && !message.chart_spec && !message.data && !message.dashboard_spec && !imageAsset) {
      message.type = 'audio';
    }
  }

  return message;
};

// --- MAIN COMPONENT ---
export default function Chat() {
  // State
  const [messages, setMessages] = createSignal<Message[]>([createInitialGreetingMessage()]);
  const [input, setInput] = createSignal('');
  const [isStreaming, setIsStreaming] = createSignal(false);
  const [sessionId, setSessionId] = createSignal<string>('');
  const [conversationHistory, setConversationHistory] = createSignal<ConversationSession[]>([]);
  const [pendingAttachments, setPendingAttachments] = createSignal<PendingAttachment[]>([]);
  const [isUploadingAttachments, setIsUploadingAttachments] = createSignal(false);
  const [attachmentError, setAttachmentError] = createSignal('');
  const [isBasketBuilderOpen, setIsBasketBuilderOpen] = createSignal(false);
  const [basketBuilderMode, setBasketBuilderMode] = createSignal<BasketBuilderMode>('margin');
  const [basketItems, setBasketItems] = createSignal<BasketBuilderItem[]>([createBasketBuilderItem()]);
  const [basketDiscountPct, setBasketDiscountPct] = createSignal('');
  const [basketDiscountValue, setBasketDiscountValue] = createSignal('');
  const [basketUpliftPct, setBasketUpliftPct] = createSignal('');
  const [basketTransactionsText, setBasketTransactionsText] = createSignal('');
  const [basketBuilderError, setBasketBuilderError] = createSignal('');
  const [isVoiceRecording, setIsVoiceRecording] = createSignal(false);
  const [voiceError, setVoiceError] = createSignal('');
  const [speakingMessageId, setSpeakingMessageId] = createSignal('');
  const [currentEventSource, setCurrentEventSource] = createSignal<EventSource | null>(null);
  const [busyAutomationMessageId, setBusyAutomationMessageId] = createSignal<string | null>(null);
  const [chatCapabilities, setChatCapabilities] = createSignal<ChatCapabilities>({
    memory: true,
    multimodal: true,
    attachments: true,
    voice: true,
    computer_use: false,
  });

  // UI Refs
  let messagesEndRef: HTMLDivElement | undefined;
  let scrollTimeoutId: number | undefined;
  let mutationObserver: MutationObserver | null = null;
  let attachmentInputRef: HTMLInputElement | undefined;
  let speechRecognitionRef: SpeechRecognitionInstance | null = null;

  const getAuthToken = () => sessionStorage.getItem('token') || auth.token() || '';

  const sendFrontendTelemetryLog = async (
    feature: 'voice_input' | 'voice_output' | 'chat_stream',
    action: string,
    context?: Record<string, any>,
  ) => {
    try {
      const token = getAuthToken();
      const currentUser = auth.user ? auth.user() : null;
      await fetch('/api/v1/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        keepalive: true,
        body: JSON.stringify({
          logs: [
            {
              timestamp: new Date().toISOString(),
              level: 1,
              levelName: 'INFO',
              message: `chat_${feature}_${action}`,
              context: {
                feature: feature === 'chat_stream' ? 'chat_stream' : 'chat_media',
                media_type: feature === 'chat_stream' ? undefined : feature,
                action,
                session_id: sessionId(),
                ...context,
              },
              user: currentUser ? { id: currentUser.email, email: currentUser.email } : undefined,
              session: { id: sessionId() },
              page: {
                url: window.location.href,
                title: document.title,
                referrer: document.referrer,
              },
              browser: {
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform,
              },
            },
          ],
        }),
      });
    } catch (error) {
      console.debug('Falha ao enviar telemetria de mídia do frontend:', error);
    }
  };

  const fetchChatHistoryPayload = async (targetSessionId?: string): Promise<ChatHistoryResponse | null> => {
    const token = getAuthToken();
    if (!token) return null;

    const endpoint = targetSessionId
      ? `/api/v1/chat/history?session_id=${encodeURIComponent(targetSessionId)}`
      : '/api/v1/chat/history';

    const response = await fetch(endpoint, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      return null;
    }
    return response.json();
  };

  const fetchChatCapabilities = async (): Promise<ChatCapabilities | null> => {
    const token = getAuthToken();
    if (!token) return null;

    const response = await fetch('/api/v1/chat/capabilities', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    return normalizeChatCapabilities(payload?.capabilities);
  };

  const applyChatHistoryPayload = (payload: ChatHistoryResponse | null, targetSessionId?: string) => {
    if (!payload) return;
    if (payload.capabilities) {
      setChatCapabilities(normalizeChatCapabilities(payload.capabilities));
    }

    const sessions = Array.isArray(payload.sessions)
      ? payload.sessions.filter((item): item is ConversationSession => typeof item?.id === 'string' && item.id.length > 0)
      : [];
    setConversationHistory(sessions);

    if (!targetSessionId) return;

    const restoredMessages = Array.isArray(payload.items)
      ? payload.items
          .map((item: HistoryItem, index: number) => mapHistoryItemToMessage(item, index))
          .filter((item: Message | null): item is Message => item !== null)
      : [];

    setMessages(restoredMessages.length > 0 ? restoredMessages : [createInitialGreetingMessage()]);
  };

  const refreshConversationHistory = async () => {
    if (!chatCapabilities().memory) {
      setConversationHistory([]);
      return;
    }
    try {
      const payload = await fetchChatHistoryPayload();
      applyChatHistoryPayload(payload);
    } catch (error) {
      console.warn('Falha ao atualizar lista de conversas:', error);
    }
  };

  const loadPersistedHistory = async (activeSessionId: string) => {
    if (!activeSessionId || !chatCapabilities().memory) return;

    try {
      const payload = await fetchChatHistoryPayload(activeSessionId);
      applyChatHistoryPayload(payload, activeSessionId);
    } catch (error) {
      console.warn('Falha ao restaurar histórico persistido do chat:', error);
    }
  };

  const startFreshConversation = () => {
    const newSession = crypto.randomUUID();
    setMessages([createInitialGreetingMessage()]);
    setSessionId(newSession);
    setPendingAttachments([]);
    setAttachmentError('');
    localStorage.setItem('chat_session_id', newSession);
    if (chatCapabilities().memory) {
      void refreshConversationHistory();
    } else {
      setConversationHistory([]);
    }
  };

  const openConversation = async (targetSessionId: string) => {
    if (!chatCapabilities().memory || !targetSessionId || targetSessionId === sessionId()) return;
    stopGeneration();
    setPendingAttachments([]);
    setAttachmentError('');
    setSessionId(targetSessionId);
    localStorage.setItem('chat_session_id', targetSessionId);
    await loadPersistedHistory(targetSessionId);
  };

  const deleteConversation = async (targetSessionId: string) => {
    if (!chatCapabilities().memory) return;
    const token = getAuthToken();
    if (!token || !targetSessionId) return;
    if (!confirm('Excluir esta conversa persistida?')) return;

    try {
      const response = await fetch(`/api/v1/chat/history/${encodeURIComponent(targetSessionId)}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Falha ao excluir conversa (${response.status})`);
      }

      setConversationHistory(prev => prev.filter(item => item.id !== targetSessionId));
      if (targetSessionId === sessionId()) {
        startFreshConversation();
      } else {
        void refreshConversationHistory();
      }
    } catch (error) {
      console.error('Falha ao excluir conversa:', error);
    }
  };

  // Init
  onMount(async () => {
    let storedSession = localStorage.getItem('chat_session_id');
    if (!storedSession) {
      storedSession = crypto.randomUUID();
      localStorage.setItem('chat_session_id', storedSession);
    }
    setSessionId(storedSession);
    const capabilities = await fetchChatCapabilities();
    if (capabilities) {
      setChatCapabilities(capabilities);
    }
    if (capabilities?.memory !== false) {
      await loadPersistedHistory(storedSession);
    } else {
      setConversationHistory([]);
    }

    // Auto-scroll logic
    const scrollToBottom = () => {
      if (messagesEndRef) {
        messagesEndRef.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }

    // Observer for auto-scroll
    mutationObserver = new MutationObserver(scrollToBottom);
    if (messagesEndRef?.parentElement) {
      mutationObserver.observe(messagesEndRef.parentElement, { childList: true, subtree: true });
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
    mutationObserver?.disconnect();
    speechRecognitionRef?.stop();
    speechRecognitionRef = null;
    window.speechSynthesis?.cancel();
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

  createEffect(() => {
    if (!chatCapabilities().memory && conversationHistory().length > 0) {
      setConversationHistory([]);
    }
  });

  createEffect(() => {
    if (chatCapabilities().attachments) return;

    if (pendingAttachments().length > 0) {
      setPendingAttachments([]);
    }
    setAttachmentError('');
  });

  createEffect(() => {
    if (chatCapabilities().voice) return;

    if (isVoiceRecording()) {
      stopVoiceCapture();
    }
    if (speakingMessageId()) {
      window.speechSynthesis?.cancel();
      setSpeakingMessageId('');
    }
    setVoiceError('');
  });

  // --- ACTIONS ---

  const closeStreamConnection = () => {
    const es = currentEventSource();
    if (es) {
      es.close();
      setCurrentEventSource(null);
    }
  };

  const stopGeneration = () => {
    if (currentEventSource()) {
      closeStreamConnection();
      setIsStreaming(false);
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.role === 'assistant' && lastMsg.type !== 'error') {
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
      startFreshConversation();
    }
  };

  const getSpeechRecognitionConstructor = (): SpeechRecognitionConstructor | null => {
    const browserWindow = window as Window & typeof globalThis & {
      SpeechRecognition?: SpeechRecognitionConstructor;
      webkitSpeechRecognition?: SpeechRecognitionConstructor;
    };

    return browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition || null;
  };

  const mapVoiceError = (errorCode: string) => {
    switch (errorCode) {
      case 'not-allowed':
      case 'service-not-allowed':
        return 'Permissão de microfone negada.';
      case 'no-speech':
        return 'Nenhuma fala foi detectada. Tente novamente.';
      case 'audio-capture':
        return 'Não foi possível acessar o microfone.';
      default:
        return 'Falha ao transcrever o áudio nesta tentativa.';
    }
  };

  const stopVoiceCapture = () => {
    speechRecognitionRef?.stop();
    speechRecognitionRef = null;
    setIsVoiceRecording(false);
  };

  const validateAttachment = (file: File): string | null => {
    const lowerName = file.name.toLowerCase();
    const isImage = ['.png', '.jpg', '.jpeg', '.webp']
      .some(extension => lowerName.endsWith(extension));

    if (isImage && file.size > MAX_CHAT_IMAGE_SIZE_BYTES) {
      return `${file.name}: limite de 5 MB por imagem.`;
    }

    if (!isImage && file.size > MAX_CHAT_ATTACHMENT_SIZE_BYTES) {
      return `${file.name}: limite de 2 MB por arquivo.`;
    }

    const allowedExtension = ['.txt', '.md', '.csv', '.tsv', '.json', '.log', '.xml', '.png', '.jpg', '.jpeg', '.webp']
      .some(extension => lowerName.endsWith(extension));

    if (!allowedExtension) {
      return `${file.name}: formato ainda não suportado no chat.`;
    }

    return null;
  };

  const getAttachmentKind = (file: File): PendingAttachment['kind'] => {
    const lowerName = file.name.toLowerCase();
    return ['.png', '.jpg', '.jpeg', '.webp'].some(extension => lowerName.endsWith(extension))
      ? 'image'
      : 'document';
  };

  const buildAttachmentAwareUserText = (rawText: string, attachmentNames: string[]) => {
    const baseText = rawText.trim() || 'Analise os arquivos anexados.';
    if (attachmentNames.length === 0) {
      return baseText;
    }

    return `${baseText}\n\nAnexos enviados:\n${attachmentNames.map(name => `- ${name}`).join('\n')}`;
  };

  const buildAttachmentAwareQuery = (rawText: string, attachmentNames: string[]) => {
    const baseText = rawText.trim() || DEFAULT_ATTACHMENT_PROMPT;
    if (attachmentNames.length === 0) {
      return baseText;
    }

    return `${baseText}\n\nConsidere os anexos desta sessão: ${attachmentNames.join(', ')}.`;
  };

  const updateBasketItem = (itemId: string, field: keyof Omit<BasketBuilderItem, 'id'>, value: string) => {
    setBasketItems(prev => prev.map(item => (
      item.id === itemId
        ? { ...item, [field]: value }
        : item
    )));
  };

  const addBasketItem = () => {
    setBasketItems(prev => [...prev, createBasketBuilderItem()]);
  };

  const removeBasketItem = (itemId: string) => {
    setBasketItems(prev => {
      if (prev.length <= 1) return prev;
      return prev.filter(item => item.id !== itemId);
    });
  };

  const buildBasketPreparedMessage = (): { userVisibleText: string; effectiveQuery: string } | null => {
    const mode = basketBuilderMode();

    if (mode === 'basket') {
      const rows = basketTransactionsText()
        .split('\n')
        .map(line => line.split(',').map(item => item.trim()).filter(Boolean))
        .filter(items => items.length > 0);

      if (rows.length < 2) {
        setBasketBuilderError('Informe pelo menos 2 transações, uma por linha, para analisar itens que saem juntos.');
        return null;
      }

      const payload = { transacoes: rows };
      const effectiveQuery = `Quais produtos saem juntos nessas transações? Use a ferramenta determinística minerar_cestas_frequentes. JSON=${JSON.stringify(payload)}`;
      if (effectiveQuery.length > 3500) {
        setBasketBuilderError('A carga da análise ficou grande demais para o chat. Reduza a quantidade de linhas da cesta.');
        return null;
      }
      return {
        userVisibleText: `Analisar itens que saem juntos em ${rows.length} transações.`,
        effectiveQuery,
      };
    }

    const normalizedItems = basketItems()
      .map(item => ({
        sku: item.sku.trim() || undefined,
        nome: item.nome.trim() || undefined,
        quantidade: parseOptionalNumber(item.quantidade) ?? 1,
        preco_unitario: parseOptionalNumber(item.precoUnitario),
        custo_unitario: parseOptionalNumber(item.custoUnitario),
        desconto_pct: parseOptionalNumber(item.descontoPct),
        imposto_pct: parseOptionalNumber(item.impostoPct),
        frete_valor: parseOptionalNumber(item.freteValor),
        despesa_variavel_pct: parseOptionalNumber(item.despesaVariavelPct),
      }))
      .filter(item => item.preco_unitario !== undefined || item.custo_unitario !== undefined || item.nome || item.sku);

    if (normalizedItems.length === 0) {
      setBasketBuilderError('Adicione ao menos um item com preço ou custo para montar a cesta.');
      return null;
    }

    if (normalizedItems.some(item => item.preco_unitario === undefined || item.custo_unitario === undefined)) {
      setBasketBuilderError('Cada item precisa de preço unitário e custo unitário para o cálculo ficar confiável.');
      return null;
    }

    if (mode === 'promotion') {
      const descontoPct = parseOptionalNumber(basketDiscountPct());
      const descontoValor = parseOptionalNumber(basketDiscountValue());
      const upliftEstimado = parseOptionalNumber(basketUpliftPct()) ?? 0;
      if (descontoPct === undefined && descontoValor === undefined) {
        setBasketBuilderError('Informe desconto em % ou valor fixo para simular a promoção.');
        return null;
      }
      const payload = {
        itens: normalizedItems,
        ...(descontoPct !== undefined ? { desconto_pct: descontoPct } : {}),
        ...(descontoValor !== undefined ? { desconto_valor: descontoValor } : {}),
        ...(upliftEstimado ? { uplift_estimado_pct: upliftEstimado } : {}),
      };
      const effectiveQuery = `Simule o impacto promocional desta cesta de compras usando a ferramenta determinística simular_promocao_cesta. JSON=${JSON.stringify(payload)}`;
      if (effectiveQuery.length > 3500) {
        setBasketBuilderError('A carga da simulação ficou grande demais para o chat. Reduza a quantidade de itens.');
        return null;
      }
      return {
        userVisibleText: `Simular promoção da cesta com ${normalizedItems.length} itens.`,
        effectiveQuery,
      };
    }

    const payload = { itens: normalizedItems };
    const effectiveQuery = `Calcule a margem real desta cesta de compras usando a ferramenta determinística analisar_cesta_compras. JSON=${JSON.stringify(payload)}`;
    if (effectiveQuery.length > 3500) {
      setBasketBuilderError('A carga da cesta ficou grande demais para o chat. Reduza a quantidade de itens.');
      return null;
    }
    return {
      userVisibleText: `Analisar margem real da cesta com ${normalizedItems.length} itens.`,
      effectiveQuery,
    };
  };

  const submitPreparedMessage = async (userVisibleText: string, effectiveQuery: string) => {
    setInput('');
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      text: userVisibleText,
      timestamp: Date.now()
    }]);
    await processUserMessage(effectiveQuery);
  };

  const handleInsertBasketPrompt = () => {
    setBasketBuilderError('');
    const prepared = buildBasketPreparedMessage();
    if (!prepared) return;
    setInput(prepared.effectiveQuery);
    setIsBasketBuilderOpen(false);
  };

  const handleSendBasketPrompt = async () => {
    if (isStreaming() || isUploadingAttachments()) return;
    setBasketBuilderError('');
    const prepared = buildBasketPreparedMessage();
    if (!prepared) return;
    setIsBasketBuilderOpen(false);
    await submitPreparedMessage(prepared.userVisibleText, prepared.effectiveQuery);
  };

  const handleAttachmentButtonClick = () => {
    if (!chatCapabilities().attachments) {
      setAttachmentError('Anexos não estão habilitados para o seu perfil.');
      return;
    }
    if (isStreaming() || isUploadingAttachments()) return;
    attachmentInputRef?.click();
  };

  const handleAttachmentSelection = (event: Event) => {
    const target = event.currentTarget as HTMLInputElement;
    if (!chatCapabilities().attachments) {
      target.value = '';
      setAttachmentError('Anexos não estão habilitados para o seu perfil.');
      return;
    }
    const selectedFiles = Array.from(target.files || []);
    target.value = '';

    if (selectedFiles.length === 0) return;

    const currentAttachments = pendingAttachments();
    const nextAttachments = [...currentAttachments];
    const nextErrors: string[] = [];
    const existingKeys = new Set(currentAttachments.map(item => `${item.file.name}:${item.file.size}`));

    for (const file of selectedFiles) {
      if (nextAttachments.length >= MAX_CHAT_ATTACHMENTS) {
        nextErrors.push(`Limite de ${MAX_CHAT_ATTACHMENTS} anexos por envio.`);
        break;
      }

      const validationError = validateAttachment(file);
      if (validationError) {
        nextErrors.push(validationError);
        continue;
      }

      const dedupeKey = `${file.name}:${file.size}`;
      if (existingKeys.has(dedupeKey)) {
        continue;
      }

      existingKeys.add(dedupeKey);
      nextAttachments.push({
        id: crypto.randomUUID(),
        file,
        kind: getAttachmentKind(file),
      });
    }

    setPendingAttachments(nextAttachments);
    setAttachmentError(nextErrors.join(' '));
  };

  const removePendingAttachment = (attachmentId: string) => {
    setPendingAttachments(prev => prev.filter(item => item.id !== attachmentId));
    setAttachmentError('');
  };

  const uploadPendingAttachments = async (attachments: PendingAttachment[]): Promise<string[]> => {
    if (!chatCapabilities().attachments) {
      throw new Error('Anexos não estão habilitados para o seu perfil.');
    }
    const token = getAuthToken();
    if (!token) {
      throw new Error('Sessão inválida. Faça login novamente para enviar anexos.');
    }

    setIsUploadingAttachments(true);
    try {
      const uploadedNames: string[] = [];

      for (const attachment of attachments) {
        const formData = new FormData();
        formData.append('file', attachment.file);
        formData.append('tenant_id', 'default');
        formData.append('session_id', sessionId());

        const endpoint = attachment.kind === 'image'
          ? '/api/v1/ingest/image'
          : '/api/v1/ingest/file';

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!response.ok) {
          let detail = `falha no upload (${response.status})`;
          try {
            const payload = await response.json();
            detail = String(payload?.detail || detail);
          } catch {
            // Ignore parse errors and keep default detail.
          }
          throw new Error(`${attachment.file.name}: ${detail}`);
        }

        const payload = await response.json();
        if (!payload?.success) {
          throw new Error(`${attachment.file.name}: o backend não confirmou a ingestão.`);
        }

        uploadedNames.push(attachment.file.name);
      }

      setPendingAttachments([]);
      setAttachmentError('');
      return uploadedNames;
    } finally {
      setIsUploadingAttachments(false);
    }
  };

  const toggleVoiceCapture = async () => {
    if (isVoiceRecording()) {
      stopVoiceCapture();
      return;
    }

    if (isStreaming() || isUploadingAttachments()) return;
    if (!chatCapabilities().voice) {
      setVoiceError('Recursos de voz não estão habilitados para o seu perfil.');
      return;
    }

    const RecognitionCtor = getSpeechRecognitionConstructor();
    if (!RecognitionCtor) {
      setVoiceError('Reconhecimento de voz não é suportado neste navegador.');
      void sendFrontendTelemetryLog('voice_input', 'unsupported');
      return;
    }

    setVoiceError('');

    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
      }
    } catch (error) {
      console.error('Falha ao obter permissão de microfone:', error);
      setVoiceError('Permissão de microfone negada ou indisponível.');
      void sendFrontendTelemetryLog('voice_input', 'permission_denied');
      return;
    }

    const recognition = new RecognitionCtor();
    let finalTranscript = '';

    recognition.lang = 'pt-BR';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      let interimTranscript = '';
      for (let index = event.resultIndex || 0; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = String(result?.[0]?.transcript || '');
        if (result?.isFinal) {
          finalTranscript += `${transcript} `;
        } else {
          interimTranscript += transcript;
        }
      }

      const mergedTranscript = `${finalTranscript} ${interimTranscript}`.trim();
      if (mergedTranscript) {
        setInput(mergedTranscript);
      }
    };
    recognition.onerror = (event) => {
      console.error('Erro no reconhecimento de voz:', event);
      setVoiceError(mapVoiceError(String(event?.error || 'unknown')));
      setIsVoiceRecording(false);
      speechRecognitionRef = null;
      void sendFrontendTelemetryLog('voice_input', 'error', { error: String(event?.error || 'unknown') });
    };
    recognition.onend = () => {
      const transcript = finalTranscript.trim() || input().trim();
      setIsVoiceRecording(false);
      speechRecognitionRef = null;
      if (transcript) {
        setInput(transcript);
        void sendFrontendTelemetryLog('voice_input', 'submitted', { transcript_length: transcript.length });
        void handleSendMessage();
      }
    };

    speechRecognitionRef = recognition;
    recognition.start();
    setIsVoiceRecording(true);
    void sendFrontendTelemetryLog('voice_input', 'started');
  };

  const buildSpeechText = (rawText: string) => rawText
    .replace(/[`*_>#-]/g, ' ')
    .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();

  const toggleMessageSpeech = (messageId: string, rawText: string) => {
    if (!chatCapabilities().voice) {
      setVoiceError('Leitura por voz não está habilitada para o seu perfil.');
      return;
    }
    if (speakingMessageId() === messageId) {
      window.speechSynthesis?.cancel();
      setSpeakingMessageId('');
      void sendFrontendTelemetryLog('voice_output', 'stopped', { message_id: messageId });
      return;
    }

    if (!('speechSynthesis' in window)) {
      setVoiceError('Leitura por voz não é suportada neste navegador.');
      void sendFrontendTelemetryLog('voice_output', 'unsupported');
      return;
    }

    const speechText = buildSpeechText(rawText);
    if (!speechText) {
      return;
    }

    setVoiceError('');
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = 'pt-BR';
    utterance.rate = 1;
    utterance.onend = () => {
      setSpeakingMessageId(currentId => (currentId === messageId ? '' : currentId));
      void sendFrontendTelemetryLog('voice_output', 'completed', { message_id: messageId });
    };
    utterance.onerror = () => {
      setSpeakingMessageId('');
      setVoiceError('Falha ao reproduzir a resposta em voz.');
      void sendFrontendTelemetryLog('voice_output', 'error', { message_id: messageId });
    };

    setSpeakingMessageId(messageId);
    window.speechSynthesis.speak(utterance);
    void sendFrontendTelemetryLog('voice_output', 'started', { message_id: messageId });
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
      console.warn('Falha ao validar/renovar token antes do stream:', e);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        text: '⚠️ Sessão expirada. Faça login novamente para continuar.',
        type: 'error',
        timestamp: Date.now()
      }]);
      return;
    }

    // Pegar o token possivelmente renovado do store
    const currentToken = sessionStorage.getItem('token') || token;

    setIsStreaming(true);
    const assistantId = (Date.now() + 1).toString();
    let tracedRequestId = '';
    let streamEventCount = 0;
    let firstStreamEventLogged = false;
    let keepaliveLogged = false;
    const logStreamTelemetry = (action: string, context?: Record<string, any>) => {
      void sendFrontendTelemetryLog('chat_stream', action, {
        assistant_id: assistantId,
        chat_request_id: tracedRequestId || undefined,
        event_count: streamEventCount,
        ...context,
      });
    };

    // Optimistic Message with Thinking State
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      text: '',
      timestamp: Date.now(),
      type: 'text',
      isOptimistic: true,
      thinkingSteps: [],
      thinkingStepKeys: [],
      isThinking: true
    }]);

    const finalizeAssistantMessage = (opts?: {
      errorText?: string;
      markResponse?: boolean;
      responseId?: string;
      source?: string;
      confidence?: number;
      mode?: string;
      citations?: Array<Record<string, any>>;
      imageAsset?: Message['image_asset'];
      audioAsset?: Message['audio_asset'];
      automationRequest?: ChatAutomationState;
    }) => {
      closeStreamConnection();
      setIsStreaming(false);
      setMessages(prev => prev.map(msg => {
        if (msg.id !== assistantId) return msg;

        const next: Message = {
          ...msg,
          isOptimistic: false,
          isThinking: false,
          response_id: opts?.markResponse ? (opts.responseId || msg.response_id || crypto.randomUUID()) : msg.response_id,
          source: typeof opts?.source === 'string' ? opts.source : msg.source,
          confidence: typeof opts?.confidence === 'number' ? opts.confidence : msg.confidence,
          mode: typeof opts?.mode === 'string' ? opts.mode : msg.mode,
          citations: opts?.citations ? normalizeCitations(opts.citations) : msg.citations,
          image_asset: opts?.imageAsset || msg.image_asset,
          audio_asset: opts?.audioAsset || msg.audio_asset,
          automation_request: opts?.automationRequest || msg.automation_request,
        };

        if (opts?.errorText) {
          next.type = 'error';
          next.text = opts.errorText;
          return next;
        }

        if ((next.type === 'text' || !next.type) && !(next.text || '').trim()) {
          next.type = 'error';
          next.text = '⚠️ Não foi possível gerar uma resposta agora. Tente novamente.';
        }

        return next;
      }));
    };

    try {
      const tokenForHeader = sessionStorage.getItem('token') || currentToken;
      const tokenResp = await fetch('/api/v1/chat/stream-token', {
        method: 'POST',
        headers: {
          ...(tokenForHeader ? { Authorization: `Bearer ${tokenForHeader}` } : {}),
        },
      });

      if (!tokenResp.ok) {
        let detail = `falha ao criar stream (${tokenResp.status})`;
        try {
          const errPayload = await tokenResp.json();
          detail = String(errPayload?.detail || detail);
        } catch {
          // Ignore parse errors and keep default detail.
        }
        throw new Error(detail);
      }

      const tokenData = await tokenResp.json();
      const streamToken = tokenData?.stream_token || null;
      if (!streamToken) {
        throw new Error('Não foi possível obter token efêmero para o stream.');
      }

      const streamUrl = `/api/v1/chat/stream?q=${encodeURIComponent(userText)}&stream_token=${encodeURIComponent(streamToken)}&session_id=${sessionId()}`;
      logStreamTelemetry('started', {
        query_length: userText.length,
      });
      closeStreamConnection();
      const eventSource = new EventSource(streamUrl);
      setCurrentEventSource(eventSource);

      eventSource.onmessage = (event) => {
        if (currentEventSource() !== eventSource) return;
        try {
          const data = JSON.parse(event.data);
          const eventType = String(data?.type || '').toLowerCase();
          streamEventCount += 1;
          if (typeof data?.request_id === 'string' && data.request_id.trim()) {
            tracedRequestId = data.request_id;
          }
          if (!firstStreamEventLogged) {
            firstStreamEventLogged = true;
            logStreamTelemetry('first_event', { event_type: eventType || 'unknown' });
          }

          if (data?.done === true || eventType === 'final') {
            logStreamTelemetry('completed', {
              event_type: eventType || 'final',
              source: typeof data.source === 'string' ? data.source : undefined,
              mode: typeof data.mode === 'string' ? data.mode : undefined,
            });
            finalizeAssistantMessage({
              markResponse: true,
              responseId: typeof data.request_id === 'string' ? data.request_id : undefined,
              source: typeof data.source === 'string' ? data.source : undefined,
              confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
              mode: typeof data.mode === 'string' ? data.mode : undefined,
              citations: normalizeCitations(data.citations),
              imageAsset: normalizeImageAsset(data.image_asset),
              audioAsset: normalizeAudioAsset(data.audio_asset),
              automationRequest: normalizeAutomationState(data.automation_request),
            });
            window.setTimeout(() => {
              void refreshConversationHistory();
            }, 150);
            return;
          }

          if (eventType === 'keepalive') {
            if (!keepaliveLogged) {
              keepaliveLogged = true;
              logStreamTelemetry('keepalive', { event_type: 'keepalive' });
            }
            return;
          }

          if (eventType === 'tool_progress') {
            const { text: stepText, key: stepKey } = buildThinkingStep(data.tool, data.status);

            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? (() => {
                const currentSteps = msg.thinkingSteps || [];
                const currentKeys = msg.thinkingStepKeys || [];
                const lastStep = currentSteps.length > 0 ? currentSteps[currentSteps.length - 1] : '';
                if (lastStep === stepText || currentKeys.includes(stepKey)) {
                  return {
                    ...msg,
                    isThinking: true
                  };
                }
                const nextSteps = [...currentSteps, stepText].slice(-6);
                const nextKeys = [...currentKeys, stepKey].slice(-12);
                return {
                  ...msg,
                  thinkingSteps: nextSteps,
                  thinkingStepKeys: nextKeys,
                  isThinking: true
                };
              })() : msg
            ));
          }
          else if (eventType === 'text') {
            const chunk = typeof data.text === 'string' ? data.text : '';
            if (!chunk) return;
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId ? { ...msg, text: msg.text + chunk, isThinking: false } : msg
            ));
          }
          else if (eventType === 'chart' && data.chart_spec) {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId
                ? {
                    ...msg,
                    type: msg.type === 'dashboard' && msg.dashboard_spec ? 'dashboard' : 'chart',
                    chart_spec: data.chart_spec,
                    text: msg.text || 'Visualização gerada.\n\n',
                    isThinking: false
                  }
                : msg
            ));
          }
          else if (eventType === 'table' && Array.isArray(data.data)) {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId
                ? {
                    ...msg,
                    type: msg.type === 'dashboard' && msg.dashboard_spec
                      ? 'dashboard'
                      : msg.chart_spec
                        ? 'chart'
                        : 'table',
                    data: data.data,
                    text: msg.text || 'Dados tabulares:',
                    isThinking: false
                  }
                : msg
            ));
          }
          else if (eventType === 'dashboard' && data.dashboard_spec) {
            setMessages(prev => prev.map(msg =>
              msg.id === assistantId
                ? {
                    ...msg,
                    type: 'dashboard',
                    dashboard_spec: data.dashboard_spec as DashboardSpec,
                    source: typeof data.source === 'string' ? data.source : msg.source,
                    confidence: typeof data.confidence === 'number' ? data.confidence : msg.confidence,
                    citations: normalizeCitations(data.citations).length > 0 ? normalizeCitations(data.citations) : msg.citations,
                    text: msg.text || 'Dashboard interativo gerado.\n\n',
                    isThinking: false
                  }
                : msg
            ));
          }
          else if (eventType === 'image') {
            const imageAsset = normalizeImageAsset(data.image_asset || data.url || data);
            if (!imageAsset) return;

            setMessages(prev => prev.map(msg =>
              msg.id === assistantId
                ? {
                    ...msg,
                    type: 'image',
                    image_asset: imageAsset,
                    text: msg.text || 'Imagem gerada.\n\n',
                    isThinking: false,
                  }
                : msg
            ));
          }
          else if (eventType === 'audio') {
            const audioAsset = normalizeAudioAsset(data.audio_asset || data.url || data);
            if (!audioAsset) return;

            setMessages(prev => prev.map(msg =>
              msg.id === assistantId
                ? {
                    ...msg,
                    type: 'audio',
                    audio_asset: audioAsset,
                    text: msg.text || 'Áudio gerado.\n\n',
                    isThinking: false,
                  }
                : msg
            ));
          }
          else if (eventType === 'error' || data?.error) {
            const errorText = typeof data?.error === 'string' ? data.error : 'Erro inesperado no stream.';
            logStreamTelemetry('server_error', {
              event_type: eventType || 'error',
              error: errorText,
            });
            finalizeAssistantMessage({ errorText: `⚠️ Não foi possível concluir a análise: ${errorText}` });
          }
        } catch (err) {
          console.error('SSE Error', err);
          logStreamTelemetry('parse_error', {
            error: err instanceof Error ? err.message : 'invalid_sse_payload',
          });
          finalizeAssistantMessage({ errorText: '⚠️ Falha ao interpretar resposta do servidor.' });
        }
      };

      eventSource.onerror = () => {
        if (currentEventSource() !== eventSource) return;
        logStreamTelemetry('transport_error');
        finalizeAssistantMessage({
          errorText: '⚠️ Conexão interrompida. Verifique o backend e tente novamente.'
        });
      };

    } catch (err) {
      const errMessage = err instanceof Error ? err.message : 'falha desconhecida ao iniciar stream';
      logStreamTelemetry('startup_failed', { error: errMessage });
      finalizeAssistantMessage({
        errorText: `⚠️ Não foi possível iniciar a análise agora: ${errMessage}`
      });
    }
  };

  const handleSendMessage = async () => {
    const text = input();
    const attachments = pendingAttachments();

    if ((!text.trim() && attachments.length === 0) || isStreaming() || isUploadingAttachments()) return;
    if (attachments.length > 0 && !chatCapabilities().attachments) {
      setAttachmentError('Anexos não estão habilitados para o seu perfil.');
      return;
    }

    try {
      let attachmentNames = attachments.map(item => item.file.name);
      if (attachments.length > 0) {
        attachmentNames = await uploadPendingAttachments(attachments);
      }

      const userVisibleText = buildAttachmentAwareUserText(text, attachmentNames);
      const effectiveQuery = buildAttachmentAwareQuery(text, attachmentNames);

      await submitPreparedMessage(userVisibleText, effectiveQuery);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha desconhecida ao enviar anexos.';
      setAttachmentError(message);
      setMessages(prev => [...prev, {
        id: `attachment-error-${Date.now()}`,
        role: 'assistant',
        text: `⚠️ Não foi possível enviar os anexos agora: ${message}`,
        type: 'error',
        timestamp: Date.now(),
      }]);
    }
  };

  const updateMessageAutomationState = (messageId: string, automation: ChatAutomationState) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId
        ? { ...msg, automation_request: automation }
        : msg
    ));
  };

  const handleAutomationDecision = async (
    messageId: string,
    automation: ChatAutomationState | undefined,
    decision: 'approve' | 'reject' | 'follow_up',
  ) => {
    if (!automation) return;
    setBusyAutomationMessageId(messageId);

    const proposalPayload = {
      proposal_id: automation.proposal_id,
      action: automation.action,
      title: automation.title,
      summary: automation.summary,
      request_text: automation.request_text,
      session_id: sessionId(),
      params: automation.params || {},
      review_required: automation.review_required === true,
      follow_up_action: automation.follow_up_action,
      follow_up_label: automation.follow_up_label,
      target_label: automation.target_label,
    };

    try {
      const response =
        decision === 'reject'
          ? await chatAutomationApi.reject({
              approval_id: automation.approval_id || undefined,
              proposal: automation.approval_id ? undefined : proposalPayload,
            })
          : await chatAutomationApi.approve({
              approval_id: automation.approval_id || undefined,
              proposal: automation.approval_id ? undefined : proposalPayload,
              follow_up_action: decision === 'follow_up' ? automation.follow_up_action || undefined : undefined,
            });

      const nextAutomation = normalizeAutomationState(response?.data?.automation);
      if (nextAutomation) {
        updateMessageAutomationState(messageId, nextAutomation);
      }
      if (chatCapabilities().memory) {
        await refreshConversationHistory();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha ao processar a automação.';
      updateMessageAutomationState(messageId, {
        ...(automation || {}),
        approval_status: 'failed',
        execution_error: message,
      });
    } finally {
      setBusyAutomationMessageId(null);
    }
  };

  const getFeedbackPayload = (messageId: string) => {
    const currentMessages = messages();
    const targetIndex = currentMessages.findIndex(msg => msg.response_id === messageId);
    if (targetIndex < 0) {
      return {
        response_id: messageId,
        session_id: sessionId() || null,
      };
    }

    const targetMessage = currentMessages[targetIndex];
    let queryText: string | null = null;
    for (let i = targetIndex - 1; i >= 0; i -= 1) {
      if (currentMessages[i]?.role === 'user') {
        queryText = currentMessages[i].text;
        break;
      }
    }

    return {
      response_id: messageId,
      session_id: sessionId() || null,
      query_text: queryText,
      response_text: targetMessage.text || null,
      source: targetMessage.source || null,
      confidence: typeof targetMessage.confidence === 'number' ? targetMessage.confidence : null,
      mode: targetMessage.mode || null,
      citations: Array.isArray(targetMessage.citations) ? targetMessage.citations : [],
    };
  };

  const handleFeedback = async (
    messageId: string,
    feedbackType: 'positive' | 'negative' | 'partial',
    comment?: string
  ) => {
    try {
      const token = sessionStorage.getItem('token') || auth.token();
      const response = await fetch('/api/v1/chat/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          ...getFeedbackPayload(messageId),
          feedback_type: feedbackType,
          comment: comment || null,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error('Falha ao enviar feedback:', errText);
      }
    } catch (err) {
      console.error('Erro ao enviar feedback:', err);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSendMessage();
    }
  };

  const handleMarkdownClick = async (e: MouseEvent & { target: EventTarget | null }) => {
    const target = e.target;
    if (!(target instanceof Element)) return;

    const anchor = target.closest('a');
    if (!(anchor instanceof HTMLAnchorElement)) return;
    if (!isMarketResearchDownloadLink(anchor.getAttribute('href'))) return;

    e.preventDefault();
    e.stopPropagation();

    try {
      const downloadUrl = new URL(anchor.href, window.location.origin);
      const token = sessionStorage.getItem('token') || auth.token();
      const response = await fetch(downloadUrl.toString(), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });

      if (!response.ok) {
        throw new Error(`Falha no download (${response.status})`);
      }

      const blob = await response.blob();
      const fallbackName = fallbackFilenameFromUrl(downloadUrl);
      const fileName = getFilenameFromContentDisposition(
        response.headers.get('content-disposition'),
        fallbackName,
      );

      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Erro ao baixar resultado da pesquisa de mercado:', error);
      alert('Não foi possível baixar o arquivo agora. Tente novamente.');
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
      <div class="flex-1 overflow-hidden w-full">
        <div class="mx-auto flex h-full w-full max-w-7xl gap-6 px-4 py-8 pb-32">
          <Show when={chatCapabilities().memory}>
            <aside class="hidden lg:flex lg:w-80 lg:flex-col rounded-3xl border border-slate-200/70 dark:border-zinc-800 bg-slate-50/80 dark:bg-zinc-900/60 p-4 shadow-sm">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                  <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300">
                    <History size={18} />
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">Conversas</p>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Memória persistida</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={startFreshConversation}
                  class="inline-flex items-center gap-1 rounded-xl border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 hover:border-indigo-300 hover:text-indigo-600 transition-colors"
                  title="Nova conversa"
                >
                  <Plus size={14} />
                  Nova
                </button>
              </div>

              <div class="mt-4 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
                <Show
                  when={conversationHistory().length > 0}
                  fallback={<p class="rounded-2xl border border-dashed border-slate-200 dark:border-zinc-800 px-4 py-5 text-sm text-slate-500 dark:text-slate-400">As conversas persistidas aparecerão aqui.</p>}
                >
                  <For each={conversationHistory()}>
                    {(conversation) => {
                      const isActive = () => conversation.id === sessionId();
                      return (
                        <div class={`group flex items-start gap-2 rounded-2xl border px-3 py-3 transition-colors ${isActive() ? 'border-indigo-300 bg-indigo-50/70 dark:border-indigo-700 dark:bg-indigo-950/30' : 'border-slate-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-950/60 hover:border-slate-300 dark:hover:border-zinc-700'}`}>
                          <button
                            type="button"
                            onClick={() => void openConversation(conversation.id)}
                            class="flex-1 text-left"
                          >
                            <div class="text-sm font-medium text-slate-800 dark:text-slate-100 line-clamp-2">
                              {conversation.title || 'Conversa sem título'}
                            </div>
                            <div class="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
                              <span>{conversation.message_count || 0} mensagens</span>
                              <Show when={conversation.updated_at}>
                                <span>{formatConversationTimestamp(conversation.updated_at)}</span>
                              </Show>
                            </div>
                          </button>
                          <button
                            type="button"
                            onClick={() => void deleteConversation(conversation.id)}
                            class="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-red-500 dark:hover:bg-zinc-900 transition-colors"
                            title="Excluir conversa"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      );
                    }}
                  </For>
                </Show>
              </div>
            </aside>
          </Show>

          <div class="flex min-h-0 flex-1 flex-col overflow-y-auto">
            <Show when={chatCapabilities().memory && conversationHistory().length > 0}>
              <div class="mb-6 flex gap-2 overflow-x-auto pb-1 lg:hidden">
                <button
                  type="button"
                  onClick={startFreshConversation}
                  class="inline-flex shrink-0 items-center gap-1 rounded-2xl border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200"
                >
                  <Plus size={14} />
                  Nova
                </button>
                <For each={conversationHistory()}>
                  {(conversation) => {
                    const isActive = () => conversation.id === sessionId();
                    return (
                      <div class={`flex shrink-0 items-center gap-2 rounded-2xl border px-3 py-2 ${isActive() ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-950/30' : 'border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-950/60'}`}>
                        <button
                          type="button"
                          onClick={() => void openConversation(conversation.id)}
                          class="text-left"
                        >
                          <div class="max-w-[180px] truncate text-xs font-medium text-slate-800 dark:text-slate-100">
                            {conversation.title || 'Conversa sem título'}
                          </div>
                          <div class="text-[10px] text-slate-500 dark:text-slate-400">{conversation.message_count || 0} mensagens</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => void deleteConversation(conversation.id)}
                          class="rounded-xl p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                          title="Excluir conversa"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    );
                  }}
                </For>
              </div>
            </Show>

            <div class="max-w-3xl mx-auto w-full">

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
                          <Show when={(msg.isThinking || false) || (msg.thinkingSteps && msg.thinkingSteps.length > 0)}>
                            <ThinkingProcess
                              steps={msg.thinkingSteps || []}
                              isThinking={msg.isThinking || false}
                              isCollapsed={!msg.isThinking}
                            />
                          </Show>

                          {/* Error Banner */}
                          <Show when={msg.type === 'error'}>
                            <div class="bg-red-50 text-red-700 px-4 py-3 rounded-lg border border-red-200 text-sm">
                              {msg.text}
                            </div>
                          </Show>

                          {/* Charts */}
                          <Show when={msg.chart_spec}>
                            <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                              <PlotlyChart chartSpec={() => msg.chart_spec} />
                            </div>
                          </Show>

                          {/* Dashboard */}
                          <Show when={msg.type === 'dashboard' && msg.dashboard_spec}>
                            <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm p-3">
                              <ChatDashboardRenderer spec={() => msg.dashboard_spec} />
                            </div>
                          </Show>

                          {/* Tables */}
                          <Show when={msg.data}>
                            <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                              <DataTable data={() => msg.data || []} caption="Detalhes" />
                            </div>
                          </Show>

                          {/* Images */}
                          <Show when={msg.image_asset?.url}>
                            <div class="border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                              <img
                                src={msg.image_asset?.url}
                                alt={msg.image_asset?.alt || 'Imagem retornada pelo assistente'}
                                class="w-full max-h-[420px] object-contain bg-slate-50 dark:bg-zinc-950"
                              />
                            </div>
                          </Show>

                          {/* Audio */}
                          <Show when={msg.audio_asset?.url}>
                            <div class="border border-slate-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 shadow-sm px-4 py-3">
                              <Show when={msg.audio_asset?.title}>
                                <p class="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">{msg.audio_asset?.title}</p>
                              </Show>
                              <audio controls class="w-full" src={msg.audio_asset?.url}>
                                Seu navegador não suporta reprodução de áudio incorporada.
                              </audio>
                            </div>
                          </Show>

                          <Show when={msg.automation_request}>
                            <ChatAutomationCard
                              automation={msg.automation_request!}
                              disabled={busyAutomationMessageId() === msg.id}
                              onApprove={() => void handleAutomationDecision(msg.id, msg.automation_request, 'approve')}
                              onReject={() => void handleAutomationDecision(msg.id, msg.automation_request, 'reject')}
                              onExecuteFollowUp={() => void handleAutomationDecision(msg.id, msg.automation_request, 'follow_up')}
                            />
                          </Show>

                          {/* Text Response */}
                          <Show when={msg.text && msg.type !== 'error'}>
                            <div
                              class="markdown-body prose dark:prose-invert prose-indigo max-w-none 
                                                bg-transparent text-slate-700 dark:text-slate-300 leading-7 text-[15px]
                                                prose-p:leading-7 prose-li:my-0.5 prose-strong:font-bold prose-headings:font-bold prose-headings:text-slate-900 dark:prose-headings:text-slate-100"
                              onClick={handleMarkdownClick}
                              innerHTML={renderMarkdown(msg.text)}
                            />
                          </Show>

                          <Show when={msg.source || typeof msg.confidence === 'number' || (msg.citations && msg.citations.length > 0)}>
                            <div class="rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50/80 dark:bg-zinc-900/80 px-4 py-3 text-xs text-slate-600 dark:text-slate-300">
                              <div class="flex flex-wrap items-center gap-3">
                                <Show when={msg.source}>
                                  <span><strong>Fonte:</strong> {msg.source}</span>
                                </Show>
                                <Show when={typeof msg.confidence === 'number'}>
                                  <span><strong>Confiança:</strong> {Math.round((msg.confidence || 0) * 100)}%</span>
                                </Show>
                              </div>

                              <Show when={msg.citations && msg.citations.length > 0}>
                                <div class="mt-2 flex flex-col gap-1.5">
                                  <For each={(msg.citations || []).slice(0, 5)}>
                                    {(citation, index) => {
                                      const url = sanitizeHyperlink(citation?.url);
                                      const label =
                                        sanitizePlainText(
                                          citation?.source ||
                                          citation?.domain ||
                                          citation?.competitor ||
                                          `Fonte ${index() + 1}`,
                                          140,
                                        ) || `Fonte ${index() + 1}`;

                                      return url ? (
                                        <a
                                          href={url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          class="underline decoration-slate-300 underline-offset-2 hover:text-indigo-600 dark:hover:text-indigo-400"
                                        >
                                          {label}
                                        </a>
                                      ) : (
                                        <span>{label}</span>
                                      );
                                    }}
                                  </For>
                                </div>
                              </Show>
                            </div>
                          </Show>

                          {/* Actions */}
                          <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pt-1">
                            <Show when={chatCapabilities().voice && msg.text && msg.type !== 'error'}>
                              <button
                                type="button"
                                onClick={() => toggleMessageSpeech(msg.id, msg.text)}
                                class={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs transition-colors ${
                                  speakingMessageId() === msg.id
                                    ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300'
                                    : 'text-slate-500 hover:bg-slate-100 hover:text-indigo-600 dark:hover:bg-zinc-900'
                                }`}
                                title={speakingMessageId() === msg.id ? 'Parar leitura' : 'Ouvir resposta'}
                              >
                                <Volume2 size={14} />
                                {speakingMessageId() === msg.id ? 'Parar' : 'Ouvir'}
                              </button>
                            </Show>
                            <MessageActions messageText={msg.text} messageId={msg.id} canRegenerate={false} />
                            <Show when={msg.response_id}>
                              <FeedbackButtons messageId={msg.response_id!} onFeedback={handleFeedback} />
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
        </div>
      </div>

      {/* Input Area (Bottom Fixed) */}
      <div class="absolute bottom-0 w-full bg-white dark:bg-zinc-950 p-4 pt-2 z-30">
        <div class="mx-auto flex w-full max-w-7xl gap-6 px-4">
          <Show when={chatCapabilities().memory}>
            <div class="hidden lg:block lg:w-80"></div>
          </Show>
          <div class="flex-1">
            <div class="max-w-3xl mx-auto relative group">

              {/* Gradient Border/Glow effect */}
              <div class="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>

              <div class="relative flex items-end gap-2 bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-2xl shadow-sm px-3 py-3 ring-0 focus-within:ring-1 focus-within:ring-indigo-500/50 focus-within:border-indigo-500/50 transition-all">

                <Show when={chatCapabilities().attachments}>
                  <input
                    ref={attachmentInputRef}
                    type="file"
                    multiple
                    accept={CHAT_ATTACHMENT_ACCEPT}
                    class="hidden"
                    onChange={handleAttachmentSelection}
                  />

                  <button
                    type="button"
                    onClick={handleAttachmentButtonClick}
                    disabled={isStreaming() || isUploadingAttachments()}
                    class="p-2 text-slate-400 hover:text-indigo-600 rounded-full hover:bg-slate-200 disabled:text-slate-300 dark:hover:bg-zinc-800 transition-colors pb-2.5"
                    title="Anexar arquivo"
                    >
                      <Paperclip size={20} />
                    </button>
                  </Show>

                  <button
                    type="button"
                    onClick={() => {
                      setBasketBuilderError('');
                      setIsBasketBuilderOpen(current => !current);
                    }}
                    disabled={isStreaming() || isUploadingAttachments()}
                    class={`rounded-xl border px-3 py-2 text-xs font-semibold transition-colors ${
                      isBasketBuilderOpen()
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:border-indigo-400 dark:bg-indigo-950/40 dark:text-indigo-200'
                        : 'border-slate-200 text-slate-500 hover:border-indigo-300 hover:text-indigo-600 dark:border-zinc-700 dark:text-slate-300 dark:hover:border-indigo-500'
                    }`}
                    title="Montar cesta, promoção ou basket analysis"
                  >
                    Cesta
                  </button>

                <div class="flex-1">
                  <Show when={isBasketBuilderOpen()}>
                    <div class="mb-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80">
                      <div class="mb-3 flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setBasketBuilderMode('margin');
                            setBasketBuilderError('');
                          }}
                          class={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                            basketBuilderMode() === 'margin'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-100 text-slate-600 dark:bg-zinc-900 dark:text-slate-300'
                          }`}
                        >
                          Margem real
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setBasketBuilderMode('promotion');
                            setBasketBuilderError('');
                          }}
                          class={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                            basketBuilderMode() === 'promotion'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-100 text-slate-600 dark:bg-zinc-900 dark:text-slate-300'
                          }`}
                        >
                          Promoção
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setBasketBuilderMode('basket');
                            setBasketBuilderError('');
                          }}
                          class={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                            basketBuilderMode() === 'basket'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-100 text-slate-600 dark:bg-zinc-900 dark:text-slate-300'
                          }`}
                        >
                          Itens juntos
                        </button>
                      </div>

                      <Show when={basketBuilderMode() === 'basket'} fallback={
                        <>
                          <div class="grid gap-2">
                            <For each={basketItems()}>
                              {(item, index) => (
                                <div class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-zinc-800 dark:bg-zinc-900/80 lg:grid-cols-[1.2fr_1.4fr_repeat(5,minmax(0,1fr))_auto]">
                                  <input
                                    value={item.sku}
                                    onInput={(e) => updateBasketItem(item.id, 'sku', e.currentTarget.value)}
                                    placeholder={`SKU ${index() + 1}`}
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.nome}
                                    onInput={(e) => updateBasketItem(item.id, 'nome', e.currentTarget.value)}
                                    placeholder="Nome do item"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.quantidade}
                                    onInput={(e) => updateBasketItem(item.id, 'quantidade', e.currentTarget.value)}
                                    placeholder="Qtd"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.precoUnitario}
                                    onInput={(e) => updateBasketItem(item.id, 'precoUnitario', e.currentTarget.value)}
                                    placeholder="Preço"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.custoUnitario}
                                    onInput={(e) => updateBasketItem(item.id, 'custoUnitario', e.currentTarget.value)}
                                    placeholder="Custo"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.impostoPct}
                                    onInput={(e) => updateBasketItem(item.id, 'impostoPct', e.currentTarget.value)}
                                    placeholder="Imp. %"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <input
                                    value={item.freteValor}
                                    onInput={(e) => updateBasketItem(item.id, 'freteValor', e.currentTarget.value)}
                                    placeholder="Frete"
                                    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                  />
                                  <div class="flex items-start justify-end">
                                    <button
                                      type="button"
                                      onClick={() => removeBasketItem(item.id)}
                                      disabled={basketItems().length <= 1}
                                      class="rounded-xl p-2 text-slate-400 hover:bg-red-50 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-red-950/20"
                                      title="Remover item"
                                    >
                                      <X size={14} />
                                    </button>
                                  </div>
                                  <div class="lg:col-span-8 grid gap-2 md:grid-cols-2">
                                    <input
                                      value={item.descontoPct}
                                      onInput={(e) => updateBasketItem(item.id, 'descontoPct', e.currentTarget.value)}
                                      placeholder="Desconto % por item"
                                      class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                    />
                                    <input
                                      value={item.despesaVariavelPct}
                                      onInput={(e) => updateBasketItem(item.id, 'despesaVariavelPct', e.currentTarget.value)}
                                      placeholder="Despesa variável %"
                                      class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                                    />
                                  </div>
                                </div>
                              )}
                            </For>
                          </div>

                          <div class="mt-3 flex flex-wrap gap-2">
                            <button
                              type="button"
                              onClick={addBasketItem}
                              class="rounded-xl border border-dashed border-slate-300 px-3 py-2 text-xs font-semibold text-slate-600 transition-colors hover:border-indigo-400 hover:text-indigo-600 dark:border-zinc-700 dark:text-slate-300"
                            >
                              Adicionar item
                            </button>
                          </div>

                          <Show when={basketBuilderMode() === 'promotion'}>
                            <div class="mt-3 grid gap-2 md:grid-cols-3">
                              <input
                                value={basketDiscountPct()}
                                onInput={(e) => setBasketDiscountPct(e.currentTarget.value)}
                                placeholder="Desconto % da promoção"
                                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                              />
                              <input
                                value={basketDiscountValue()}
                                onInput={(e) => setBasketDiscountValue(e.currentTarget.value)}
                                placeholder="Desconto em valor"
                                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                              />
                              <input
                                value={basketUpliftPct()}
                                onInput={(e) => setBasketUpliftPct(e.currentTarget.value)}
                                placeholder="Uplift estimado %"
                                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                              />
                            </div>
                          </Show>
                        </>
                      }>
                        <div class="grid gap-2">
                          <textarea
                            value={basketTransactionsText()}
                            onInput={(e) => setBasketTransactionsText(e.currentTarget.value)}
                            rows={5}
                            placeholder={'Uma transação por linha.\nExemplo:\nfralda, cerveja\nfralda, lenço, cerveja'}
                            class="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-slate-200"
                          />
                        </div>
                      </Show>

                      <Show when={basketBuilderError()}>
                        <p class="mt-3 text-xs text-red-600 dark:text-red-400">{basketBuilderError()}</p>
                      </Show>

                      <div class="mt-3 flex flex-wrap justify-between gap-2">
                        <p class="text-[11px] text-slate-500 dark:text-slate-400">
                          Monte a carga estruturada para margem real, simulação de promoção ou itens que saem juntos.
                        </p>
                        <div class="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={handleInsertBasketPrompt}
                            class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition-colors hover:border-indigo-400 hover:text-indigo-600 dark:border-zinc-700 dark:text-slate-300"
                          >
                            Inserir no chat
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleSendBasketPrompt()}
                            class="rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
                          >
                            Enviar análise
                          </button>
                        </div>
                      </div>
                    </div>
                  </Show>

                  <Show when={pendingAttachments().length > 0 || !!attachmentError() || !!voiceError()}>
                    <div class="mb-2 flex flex-wrap items-center gap-2">
                      <For each={pendingAttachments()}>
                        {(attachment) => (
                          <div class="inline-flex items-center gap-2 rounded-full border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-1 text-xs text-slate-600 dark:text-slate-300">
                            <span class="max-w-[180px] truncate">{attachment.file.name}</span>
                            <button
                              type="button"
                              onClick={() => removePendingAttachment(attachment.id)}
                              class="text-slate-400 hover:text-red-500 transition-colors"
                              title="Remover anexo"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        )}
                      </For>

                      <Show when={isUploadingAttachments()}>
                        <span class="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                          Enviando anexos...
                        </span>
                      </Show>
                    </div>
                  </Show>

                  <Show when={attachmentError()}>
                    <p class="mb-2 text-xs text-red-600 dark:text-red-400">{attachmentError()}</p>
                  </Show>

                  <Show when={voiceError()}>
                    <p class="mb-2 text-xs text-red-600 dark:text-red-400">{voiceError()}</p>
                  </Show>

                  <AutoResizeTextarea
                    value={input()}
                    onInput={(e) => setInput(e.currentTarget.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isStreaming() || isUploadingAttachments()}
                    placeholder="Enviar mensagem para o Caçulinha..."
                    class="flex-1 w-full bg-transparent border-none outline-none focus:ring-0 text-slate-700 dark:text-slate-200 placeholder:text-slate-400 py-2 min-h-[44px] max-h-[200px] leading-relaxed"
                  />
                </div>

                <Show when={chatCapabilities().voice}>
                  <button
                    type="button"
                    onClick={() => void toggleVoiceCapture()}
                    disabled={isStreaming() || isUploadingAttachments()}
                    class={`p-2 rounded-xl mb-0.5 transition-all duration-200 ${
                      isVoiceRecording()
                        ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300'
                        : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-200 dark:hover:bg-zinc-800'
                    } disabled:text-slate-300`}
                    title={isVoiceRecording() ? 'Parar gravação' : 'Falar com o Caçulinha'}
                  >
                    <Mic size={18} class={isVoiceRecording() ? 'animate-pulse' : ''} />
                  </button>
                </Show>

                <button
                  onClick={isStreaming() ? stopGeneration : handleSendMessage}
                  disabled={(!input().trim() && pendingAttachments().length === 0 && !isStreaming()) || isUploadingAttachments()}
                  class={`p-2 rounded-xl mb-0.5 transition-all duration-200 ${(input().trim() || pendingAttachments().length > 0 || isStreaming()) && !isUploadingAttachments()
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
      </div>

    </div>
  );
}
