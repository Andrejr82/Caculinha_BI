const MARKET_DOWNLOAD_PATH = '/api/v1/chat/market-research/download/';

export function isMarketResearchDownloadLink(href: string | null | undefined): boolean {
  if (!href) return false;
  return href.includes(MARKET_DOWNLOAD_PATH);
}

export function getFilenameFromContentDisposition(
  contentDisposition: string | null,
  fallback: string,
): string {
  if (!contentDisposition) return fallback;

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].replace(/['"]/g, '').trim());
    } catch {
      return utf8Match[1].replace(/['"]/g, '').trim() || fallback;
    }
  }

  const basicMatch = contentDisposition.match(/filename="?([^\";]+)"?/i);
  if (basicMatch?.[1]) {
    return basicMatch[1].trim();
  }

  return fallback;
}

export function fallbackFilenameFromUrl(url: URL): string {
  const format = (url.searchParams.get('format') || 'xlsx').toLowerCase();
  const ext = format === 'csv' ? 'csv' : 'xlsx';
  return `pesquisa_mercado.${ext}`;
}
