import { describe, expect, it } from 'vitest';
import { DEFAULT_CHAT_CAPABILITIES, normalizeChatCapabilities } from '@/lib/chatRuntime';

describe('chatRuntime', () => {
  it('normalizes capability defaults safely', () => {
    expect(normalizeChatCapabilities(null)).toEqual(DEFAULT_CHAT_CAPABILITIES);
  });

  it('disables dependent multimodal capabilities when multimodal is false', () => {
    expect(normalizeChatCapabilities({
      multimodal: false,
      attachments: true,
      voice: true,
      memory: true,
    })).toEqual({
      memory: true,
      multimodal: false,
      attachments: false,
      voice: false,
      computer_use: false,
    });
  });
});
