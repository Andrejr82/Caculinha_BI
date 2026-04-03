import { fetchEventSource } from '@microsoft/fetch-event-source';
import { safeParseStreamEventPayload, type StreamEventPayload } from '@/lib/chatSchemas';

export interface ChatStreamConnection {
  close: () => void;
}

interface OpenChatStreamOptions {
  url: string;
  onOpen?: () => void;
  onEvent: (eventType: string, payload: StreamEventPayload) => void;
  onError?: (error: Error) => void;
  onClose?: () => void;
}

const normalizeStreamError = (error: unknown): Error => {
  if (error instanceof Error) return error;
  return new Error(typeof error === 'string' ? error : 'chat_stream_transport_error');
};

export const openChatStream = ({
  url,
  onOpen,
  onEvent,
  onError,
  onClose,
}: OpenChatStreamOptions): ChatStreamConnection => {
  const controller = new AbortController();
  let settled = false;

  const finalize = () => {
    if (settled) return;
    settled = true;
    onClose?.();
  };

  void fetchEventSource(url, {
    method: 'GET',
    signal: controller.signal,
    openWhenHidden: true,
    async onopen(response) {
      if (!response.ok) {
        throw new Error(`stream_http_${response.status}`);
      }
      onOpen?.();
    },
    onmessage(message) {
      if (!message.data) return;

      let parsedJson: unknown;
      try {
        parsedJson = JSON.parse(message.data);
      } catch {
        throw new Error('invalid_stream_json');
      }

      const payload = safeParseStreamEventPayload(parsedJson);
      if (!payload) {
        throw new Error('invalid_stream_payload');
      }

      const eventType = String(payload.type || message.event || '').toLowerCase();
      onEvent(eventType, payload);
    },
    onclose() {
      finalize();
    },
    onerror(error) {
      if (controller.signal.aborted) {
        finalize();
        return;
      }
      const normalizedError = normalizeStreamError(error);
      onError?.(normalizedError);
      throw normalizedError;
    },
  }).catch((error) => {
    if (controller.signal.aborted) {
      finalize();
      return;
    }
    onError?.(normalizeStreamError(error));
    finalize();
  });

  return {
    close: () => {
      if (controller.signal.aborted) return;
      controller.abort();
      finalize();
    },
  };
};
