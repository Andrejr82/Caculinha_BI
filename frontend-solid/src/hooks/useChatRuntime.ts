import { createMemo } from 'solid-js';
import { createQuery, useQueryClient } from '@tanstack/solid-query';
import auth from '@/store/auth';
import {
  DEFAULT_CHAT_CAPABILITIES,
  fetchChatCapabilities,
  fetchChatHistoryPayload,
  type ChatCapabilities,
  type ChatHistoryResponse,
  type ConversationSession,
} from '@/lib/chatRuntime';

const CHAT_CAPABILITIES_QUERY_KEY = ['chat', 'capabilities'] as const;
const CHAT_HISTORY_SESSIONS_QUERY_KEY = ['chat', 'history', 'sessions'] as const;
const chatHistorySessionQueryKey = (sessionId: string) => ['chat', 'history', 'session', sessionId] as const;

export function useChatRuntime() {
  const queryClient = useQueryClient();
  const hasAuthToken = () => {
    if (typeof window === 'undefined') return Boolean(auth.token());
    return Boolean(sessionStorage.getItem('token') || auth.token());
  };

  const capabilitiesQuery = createQuery(() => ({
    queryKey: CHAT_CAPABILITIES_QUERY_KEY,
    queryFn: fetchChatCapabilities,
    get enabled() {
      return hasAuthToken();
    },
    staleTime: 5 * 60 * 1000,
  }));

  const sessionsQuery = createQuery(() => ({
    queryKey: CHAT_HISTORY_SESSIONS_QUERY_KEY,
    queryFn: () => fetchChatHistoryPayload(),
    get enabled() {
      return hasAuthToken() && capabilitiesQuery.data?.memory !== false;
    },
    staleTime: 30 * 1000,
  }));

  const chatCapabilities = createMemo<ChatCapabilities>(() => (
    capabilitiesQuery.data || DEFAULT_CHAT_CAPABILITIES
  ));

  const conversationHistory = createMemo<ConversationSession[]>(() => {
    if (chatCapabilities().memory === false) return [];
    const sessions = sessionsQuery.data?.sessions;
    return Array.isArray(sessions)
      ? sessions.filter((item): item is ConversationSession => typeof item?.id === 'string' && item.id.length > 0)
      : [];
  });

  const refreshCapabilities = async () => {
    const data = await capabilitiesQuery.refetch();
    return data.data || DEFAULT_CHAT_CAPABILITIES;
  };

  const refreshConversationHistory = async () => {
    const data = await sessionsQuery.refetch();
    return data.data;
  };

  const loadSessionHistory = async (sessionId: string): Promise<ChatHistoryResponse | null> => {
    if (!sessionId) return null;
    const payload = await queryClient.fetchQuery({
      queryKey: chatHistorySessionQueryKey(sessionId),
      queryFn: () => fetchChatHistoryPayload(sessionId),
      staleTime: 10 * 1000,
    });

    if (payload?.sessions) {
      queryClient.setQueryData(CHAT_HISTORY_SESSIONS_QUERY_KEY, (previous: ChatHistoryResponse | undefined) => ({
        ...(previous || {}),
        sessions: payload.sessions,
        capabilities: payload.capabilities || previous?.capabilities,
      }));
    }

    return payload;
  };

  const removeConversationFromList = (sessionId: string) => {
    queryClient.setQueryData(CHAT_HISTORY_SESSIONS_QUERY_KEY, (previous: ChatHistoryResponse | undefined) => {
      if (!previous?.sessions) return previous;
      return {
        ...previous,
        sessions: previous.sessions.filter(item => item.id !== sessionId),
      };
    });
  };

  return {
    chatCapabilities,
    conversationHistory,
    refreshCapabilities,
    refreshConversationHistory,
    loadSessionHistory,
    removeConversationFromList,
  };
}
