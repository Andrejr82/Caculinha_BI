import { describe, expect, it } from 'vitest';
import {
  fallbackFilenameFromUrl,
  getFilenameFromContentDisposition,
  isMarketResearchDownloadLink,
} from '@/lib/marketResearchDownload';

describe('marketResearchDownload helpers', () => {
  it('detects market download links', () => {
    expect(isMarketResearchDownloadLink('/api/v1/chat/market-research/download/abc123?format=xlsx')).toBe(true);
    expect(isMarketResearchDownloadLink('/api/v1/chat/market-research/download/abc123?format=csv')).toBe(true);
    expect(isMarketResearchDownloadLink('/chat')).toBe(false);
    expect(isMarketResearchDownloadLink(null)).toBe(false);
  });

  it('extracts filename from content-disposition header', () => {
    expect(
      getFilenameFromContentDisposition('attachment; filename=pesquisa_mercado_123.xlsx', 'fallback.xlsx'),
    ).toBe('pesquisa_mercado_123.xlsx');

    expect(
      getFilenameFromContentDisposition(
        "attachment; filename*=UTF-8''pesquisa_mercado_123.csv",
        'fallback.csv',
      ),
    ).toBe('pesquisa_mercado_123.csv');
  });

  it('builds fallback filename based on format', () => {
    expect(fallbackFilenameFromUrl(new URL('https://app.local/api/v1/chat/market-research/download/123?format=csv'))).toBe(
      'pesquisa_mercado.csv',
    );
    expect(fallbackFilenameFromUrl(new URL('https://app.local/api/v1/chat/market-research/download/123?format=xlsx'))).toBe(
      'pesquisa_mercado.xlsx',
    );
    expect(fallbackFilenameFromUrl(new URL('https://app.local/api/v1/chat/market-research/download/123'))).toBe(
      'pesquisa_mercado.xlsx',
    );
  });
});
