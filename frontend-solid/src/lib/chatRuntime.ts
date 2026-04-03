import { apiClient } from '@/lib/api/client';

export interface HistoryItem {
  id?: string;
  role?: string;
  content?: string;
  timestamp?: string | number;
  metadata?: Record<string, any>;
}

export interface ConversationSession {
  id: string;
  title?: string | null;
  created_at?: string;
  updated_at?: string;
  message_count?: number;
}

export interface ChatCapabilities {
  memory: boolean;
  multimodal: boolean;
  attachments: boolean;
  voice: boolean;
  computer_use: boolean;
}

export interface ChatHistoryResponse {
  items?: HistoryItem[];
  sessions?: ConversationSession[];
  session_id?: string | null;
  user?: string;
  capabilities?: Partial<ChatCapabilities>;
}

export const DEFAULT_CHAT_CAPABILITIES: ChatCapabilities = {
  memory: true,
  multimodal: true,
  attachments: true,
  voice: true,
  computer_use: false,
};

export const normalizeChatCapabilities = (rawValue: unknown): ChatCapabilities => {
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

export const fetchChatHistoryPayload = async (targetSessionId?: string): Promise<ChatHistoryResponse | null> => {
  const endpoint = targetSessionId
    ? `/chat/history?session_id=${encodeURIComponent(targetSessionId)}`
    : '/chat/history';

  try {
    return await apiClient.get<ChatHistoryResponse>(endpoint);
  } catch {
    return null;
  }
};

export const fetchChatCapabilities = async (): Promise<ChatCapabilities | null> => {
  try {
    const payload = await apiClient.get<{ capabilities?: Partial<ChatCapabilities> }>('/chat/capabilities');
    return normalizeChatCapabilities(payload?.capabilities);
  } catch {
    return null;
  }
};
