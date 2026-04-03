import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { sanitizeHyperlink } from '@/lib/chatPayload';

marked.setOptions({
  gfm: true,
  breaks: true,
});

const fallbackSanitizeHtml = (html: string): string => {
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/\son\w+=(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/\s(?:src|href)\s*=\s*(['"])\s*(?:javascript|vbscript|data):.*?\1/gi, '');
};

export const sanitizeChatHtml = (html: string): string => {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return fallbackSanitizeHtml(html);
  }

  const sanitized = DOMPurify.sanitize(html, {
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'style', 'meta', 'link', 'form', 'input', 'button', 'textarea', 'select', 'option', 'svg', 'math', 'img'],
    FORBID_ATTR: ['style', 'srcdoc', 'formaction'],
  });

  const parser = new DOMParser();
  const documentNode = parser.parseFromString(sanitized, 'text/html');
  documentNode.querySelectorAll('script,iframe,object,embed,style,meta,link,form,input,button,textarea,select,option,svg,math,img').forEach(node => {
    node.remove();
  });

  Array.from(documentNode.body.querySelectorAll('*')).forEach((element) => {
    for (const attributeName of element.getAttributeNames()) {
      const normalized = attributeName.toLowerCase();
      if (normalized.startsWith('on')) {
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

const normalizeChatMarkdownText = (text: string): string => {
  return String(text || '')
    .replace(/^\s*Dados\s+tabulares:\s*(?=##\s)/i, '')
    .trimStart();
};

export const renderChatMarkdown = (text: string): string => {
  try {
    const rawHtml = marked.parse(normalizeChatMarkdownText(text)) as string;
    return sanitizeChatHtml(rawHtml);
  } catch (error) {
    console.error('Erro ao renderizar Markdown do chat:', error);
    return sanitizeChatHtml(normalizeChatMarkdownText(text));
  }
};
