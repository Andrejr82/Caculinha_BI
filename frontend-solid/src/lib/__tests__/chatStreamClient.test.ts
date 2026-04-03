import { beforeEach, describe, expect, it, vi } from 'vitest';

const { fetchEventSourceMock } = vi.hoisted(() => ({
  fetchEventSourceMock: vi.fn(),
}));

vi.mock('@microsoft/fetch-event-source', () => ({
  fetchEventSource: fetchEventSourceMock,
}));

import { openChatStream } from '@/lib/chatStreamClient';

describe('chatStreamClient', () => {
  beforeEach(() => {
    fetchEventSourceMock.mockReset();
  });

  it('parses valid events and forwards the normalized payload', async () => {
    fetchEventSourceMock.mockImplementation(async (_url: string, handlers: any) => {
      await handlers.onopen?.({ ok: true, status: 200 });
      handlers.onmessage?.({
        event: 'message',
        data: JSON.stringify({ type: 'final', text: 'ok', source: 'tool.test' }),
      });
      handlers.onclose?.();
    });

    const onEvent = vi.fn();
    openChatStream({
      url: '/api/v1/chat/stream?q=teste',
      onEvent,
    });

    await Promise.resolve();
    await Promise.resolve();

    expect(onEvent).toHaveBeenCalledWith('final', expect.objectContaining({ text: 'ok', source: 'tool.test' }));
  });

  it('reports invalid payloads as errors', async () => {
    fetchEventSourceMock.mockImplementation((_url: string, handlers: any) => Promise.resolve()
      .then(async () => {
        await handlers.onopen?.({ ok: true, status: 200 });
      })
      .then(() => handlers.onmessage?.({
        event: 'message',
        data: JSON.stringify({ type: 'table', table_data: 'invalido' }),
      })));

    const onError = vi.fn();
    openChatStream({
      url: '/api/v1/chat/stream?q=teste',
      onEvent: vi.fn(),
      onError,
    });

    await new Promise(resolve => setTimeout(resolve, 0));
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(onError).toHaveBeenCalledWith(expect.objectContaining({ message: 'invalid_stream_payload' }));
  });
});
