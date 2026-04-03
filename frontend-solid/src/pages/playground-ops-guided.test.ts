import { describe, expect, it } from 'vitest';

import {
  buildGuidedChatPayload,
  extractGuidedChatResolution,
} from './playground-ops-guided';

describe('playground-ops-guided', () => {
  it('maps visual mode to guided chat contract', () => {
    const payload = buildGuidedChatPayload({
      modeId: 'abastecimento',
      query: 'Quais itens em ruptura na UNE 1685 nos ultimos 30 dias?',
      sessionId: 'sess-playground-1',
      outputType: 'operational_report',
    });

    expect(payload.chat_mode).toBe('critical_stock');
    expect(payload.playbook_context).toMatchObject({
      objective: 'Priorizacao de ruptura, giro e cobertura com recorte por loja e UNE.',
      une: '1685',
      period: 'ultimos 30 dias',
    });
    expect(payload.guided_action).toMatchObject({
      source: 'playground_ops',
      playbookId: 'critical_stock',
      executionPolicy: 'real_data_only',
      outputPreference: 'operational_report',
    });
  });

  it('forces sql preference when prompt asks for sql explicitly', () => {
    const payload = buildGuidedChatPayload({
      modeId: 'mix',
      query: 'Monte uma SQL para comparar vendas por loja no segmento papelaria',
      sessionId: 'sess-playground-2',
      outputType: 'operational_report',
    });

    expect(payload.chat_mode).toBe('sales_by_store');
    expect(payload.guided_action.outputPreference).toBe('sql');
    expect(Array.isArray(payload.guided_action.toolHints)).toBe(true);
    expect(payload.guided_action.toolHints).toContain('consultar_dados_flexivel');
  });

  it('extracts product context when the prompt declares a product or sku', () => {
    const payload = buildGuidedChatPayload({
      modeId: 'promocao',
      query: 'Analise o produto caneta bic na categoria papelaria na loja 1020',
      sessionId: 'sess-playground-3',
      outputType: 'operational_report',
    });

    expect(payload.playbook_context).toMatchObject({
      product: 'caneta bic',
      une: '1020',
      segment: 'papelaria',
    });
  });

  it('extracts modern chat response contract safely', () => {
    const resolved = extractGuidedChatResolution({
      data: {
        session_id: 'sess-guided-1',
        full_agent_response: {
          request_id: 'req-guided-1',
          source: 'llm.direct',
          intent: 'analysis',
          result: {
            mensagem: '## Resumo executivo\n- Tudo certo.',
          },
        },
      },
    });

    expect(resolved).toEqual({
      text: '## Resumo executivo\n- Tudo certo.',
      requestId: 'req-guided-1',
      source: 'llm.direct',
      intent: 'analysis',
      sessionId: 'sess-guided-1',
    });
  });

  it('extracts legacy playground fallback response safely', () => {
    const resolved = extractGuidedChatResolution({
      data: {
        response: 'Modo degradado local.',
        metadata: {
          request_id: 'req-legacy-1',
          source: 'local-fallback',
          intent: 'fallback.default',
        },
      },
    });

    expect(resolved).toEqual({
      text: 'Modo degradado local.',
      requestId: 'req-legacy-1',
      source: 'local-fallback',
      intent: 'fallback.default',
      sessionId: undefined,
    });
  });
});
