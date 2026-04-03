import type { DashboardSpec } from '@/components/ChatDashboardRenderer';
import type { ChatAutomationState } from '@/components/ChatAutomationCard';
import {
  safeParseAudioAsset,
  safeParseAutomationState,
  safeParseChartSpec,
  safeParseCitations,
  safeParseDashboardSpec,
  safeParseImageAsset,
  safeParseTableData,
} from '@/lib/chatSchemas';

const MARKET_DOWNLOAD_PATH_PREFIX = '/api/v1/chat/market-research/download/';

export type ChatImageAsset = {
  url: string;
  alt?: string;
  prompt?: string;
};

export type ChatAudioAsset = {
  url: string;
  title?: string;
  mime_type?: string;
};

export type ChatMessageType =
  | 'text'
  | 'chart'
  | 'table'
  | 'dashboard'
  | 'image'
  | 'audio'
  | 'final'
  | 'error'
  | 'loading_chart'
  | 'loading_table';

export type StructuredStreamEventType = 'chart' | 'table' | 'dashboard' | 'image' | 'audio';

export interface ChatMessageLike {
  text: string;
  type?: ChatMessageType;
  chart_spec?: any;
  data?: any[];
  dashboard_spec?: DashboardSpec;
  image_asset?: ChatImageAsset;
  audio_asset?: ChatAudioAsset;
  source?: string;
  confidence?: number;
  mode?: string;
  citations?: Array<Record<string, any>>;
  automation_request?: ChatAutomationState;
}

export const sanitizePlainText = (rawValue: unknown, maxLength = 160): string => {
  const text = String(rawValue || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[\u0000-\u001F\u007F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!text) return '';
  return text.slice(0, maxLength);
};

export const sanitizeHyperlink = (rawValue: unknown, allowInternalDownload = false): string => {
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
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
    const parsed = new URL(raw, origin);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.toString();
    }
  } catch {
    return '';
  }

  return '';
};

export const normalizeImageAsset = (rawValue: unknown): ChatImageAsset | undefined => {
  const normalizedInput = typeof rawValue === 'string' && rawValue.trim()
    ? { url: rawValue.trim() }
    : rawValue;
  const candidate = safeParseImageAsset(normalizedInput);
  if (!candidate) return undefined;
  const url = candidate.url.trim();
  if (!url) return undefined;

  return {
    url,
    alt: typeof candidate.alt === 'string' ? sanitizePlainText(candidate.alt, 240) || undefined : undefined,
    prompt: typeof candidate.prompt === 'string' ? candidate.prompt.trim().slice(0, 2000) || undefined : undefined,
  };
};

export const normalizeAudioAsset = (rawValue: unknown): ChatAudioAsset | undefined => {
  const normalizedInput = typeof rawValue === 'string' && rawValue.trim()
    ? { url: rawValue.trim() }
    : rawValue;
  const candidate = safeParseAudioAsset(normalizedInput);
  if (!candidate) return undefined;
  const url = candidate.url.trim();
  if (!url) return undefined;

  return {
    url,
    title: typeof candidate.title === 'string' ? sanitizePlainText(candidate.title, 200) || undefined : undefined,
    mime_type: typeof candidate.mime_type === 'string' ? sanitizePlainText(candidate.mime_type, 120) || undefined : undefined,
  };
};

export const normalizeAutomationState = (rawValue: unknown): ChatAutomationState | undefined => {
  const candidate = safeParseAutomationState(rawValue);
  if (!candidate) return undefined;
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

export const normalizeCitations = (rawValue: unknown): Array<Record<string, any>> => {
  const citations = safeParseCitations(rawValue);
  return citations
    .slice(0, 8)
    .flatMap((entry, index) => {
      const source = sanitizePlainText(
        entry.source || entry.domain || entry.competitor || `Fonte ${index + 1}`,
        140,
      );
      const domain = sanitizePlainText(entry.domain, 80);
      const competitor = sanitizePlainText(entry.competitor, 80);
      const documentId = sanitizePlainText(entry.document_id, 120);
      const url = sanitizeHyperlink(entry.url);

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

export const normalizeChartSpec = (rawValue: unknown): any | undefined => {
  if (!rawValue) return undefined;
  if (typeof rawValue === 'string') {
    try {
      const parsedJson = JSON.parse(rawValue);
      return safeParseChartSpec(parsedJson);
    } catch {
      return undefined;
    }
  }
  if (typeof rawValue === 'object') {
    return safeParseChartSpec(rawValue);
  }
  return undefined;
};

export const normalizeTableData = (rawValue: unknown): any[] | undefined => {
  return safeParseTableData(rawValue);
};

export const buildAttachmentAwareUserText = (rawText: string, attachmentNames: string[]) => {
  const baseText = rawText.trim() || 'Analise os arquivos anexados.';
  if (attachmentNames.length === 0) {
    return baseText;
  }

  return `${baseText}\n\nAnexos enviados:\n${attachmentNames.map(name => `- ${name}`).join('\n')}`;
};

export const buildAttachmentAwareQuery = (
  rawText: string,
  _attachmentNames: string[],
  defaultAttachmentPrompt = 'Analise os arquivos anexados e gere um resumo executivo com os principais pontos.',
) => {
  return rawText.trim() || defaultAttachmentPrompt;
};

export const mergeStructuredPayloadIntoMessage = <T extends ChatMessageLike>(
  message: T,
  payload: Record<string, any>,
): T => {
  const chartSpec = normalizeChartSpec(payload.chart_spec || payload.chart_data);
  const tableData = normalizeTableData(payload.table_data || payload.data);
  const dashboardSpec = safeParseDashboardSpec(payload.dashboard_spec) as DashboardSpec | undefined;
  const imageAsset = normalizeImageAsset(payload.image_asset);
  const audioAsset = normalizeAudioAsset(payload.audio_asset);
  const automationRequest = normalizeAutomationState(payload.automation_request);
  const normalizedCitations = normalizeCitations(payload.citations);

  const next: T = {
    ...message,
    source: typeof payload.source === 'string' ? payload.source : message.source,
    confidence: typeof payload.confidence === 'number' ? payload.confidence : message.confidence,
    mode: typeof payload.mode === 'string' ? payload.mode : message.mode,
    citations: normalizedCitations.length > 0 ? normalizedCitations : message.citations,
    image_asset: imageAsset || message.image_asset,
    audio_asset: audioAsset || message.audio_asset,
    automation_request: automationRequest || message.automation_request,
    chart_spec: chartSpec || message.chart_spec,
    data: tableData || message.data,
    dashboard_spec: dashboardSpec || message.dashboard_spec,
  };

  if (next.dashboard_spec) {
    next.type = 'dashboard';
  } else if (next.chart_spec) {
    next.type = 'chart';
  } else if (Array.isArray(next.data) && next.data.length > 0) {
    next.type = 'table';
  } else if (next.image_asset && !next.audio_asset) {
    next.type = 'image';
  } else if (next.audio_asset && !next.image_asset) {
    next.type = 'audio';
  }

  return next;
};

export const applyStructuredStreamEventToMessage = <T extends ChatMessageLike & Record<string, any>>(
  message: T,
  eventType: StructuredStreamEventType,
  payload: Record<string, any>,
): T => {
  const next = mergeStructuredPayloadIntoMessage(message, payload) as T;

  if (eventType === 'chart') {
    if (!next.chart_spec) return message;
    return {
      ...next,
      type: next.dashboard_spec ? 'dashboard' : 'chart',
      text: next.text || 'Visualização gerada.\n\n',
    };
  }

  if (eventType === 'table') {
    if (!Array.isArray(next.data) || next.data.length === 0) return message;
    return {
      ...next,
      type: next.dashboard_spec ? 'dashboard' : next.chart_spec ? 'chart' : 'table',
      text: next.text || 'Dados tabulares:',
    };
  }

  if (eventType === 'dashboard') {
    if (!next.dashboard_spec) return message;
    return {
      ...next,
      type: 'dashboard',
      text: next.text || 'Dashboard interativo gerado.\n\n',
    };
  }

  if (eventType === 'image') {
    if (!next.image_asset) return message;
    return {
      ...next,
      type: 'image',
      text: next.text || 'Imagem gerada.\n\n',
    };
  }

  if (eventType === 'audio') {
    if (!next.audio_asset) return message;
    return {
      ...next,
      type: 'audio',
      text: next.text || 'Áudio gerado.\n\n',
    };
  }

  return next;
};
