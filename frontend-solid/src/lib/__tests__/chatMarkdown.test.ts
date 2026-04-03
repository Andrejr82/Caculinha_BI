import { describe, expect, it } from 'vitest';
import { renderChatMarkdown, sanitizeChatHtml } from '@/lib/chatMarkdown';

describe('chatMarkdown', () => {
  it('removes dangerous script content from html', () => {
    const html = sanitizeChatHtml('<div>ok</div><script>alert(1)</script>');
    expect(html).toContain('<div>ok</div>');
    expect(html).not.toContain('<script>');
    expect(html).not.toContain('alert(1)');
  });

  it('removes dangerous javascript links', () => {
    const html = renderChatMarkdown('[clique](javascript:alert(1))');
    expect(html).not.toContain('javascript:alert(1)');
  });

  it('keeps safe http links with noopener', () => {
    const html = renderChatMarkdown('[site](https://lojascacula.com.br)');
    expect(html).toContain('https://lojascacula.com.br');
    expect(html).toContain('noopener noreferrer');
  });
});
