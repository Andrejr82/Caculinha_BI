import { describe, expect, it } from 'vitest';
import {
  applyStructuredStreamEventToMessage,
  type ChatMessageLike,
  buildAttachmentAwareQuery,
  buildAttachmentAwareUserText,
  mergeStructuredPayloadIntoMessage,
  normalizeChartSpec,
  normalizeTableData,
} from '@/lib/chatPayload';

describe('chatPayload helpers', () => {
  it('does not contaminate effective query with attachment names', () => {
    const query = buildAttachmentAwareQuery(
      'me gere um gráfico de vendas dos segmentos da une 520',
      ['csv_basket_realista_baseado_no_parquet_12000_linhas.csv'],
    );

    expect(query).toBe('me gere um gráfico de vendas dos segmentos da une 520');
    expect(query).not.toContain('Considere os anexos desta sessão');
    expect(query).not.toContain('csv_basket');
  });

  it('builds user visible attachment text without changing business intent', () => {
    const text = buildAttachmentAwareUserText('quais produtos saem juntos neste anexo?', ['cesta.csv']);

    expect(text).toContain('quais produtos saem juntos neste anexo?');
    expect(text).toContain('Anexos enviados:');
    expect(text).toContain('- cesta.csv');
  });

  it('normalizes chart spec from JSON string', () => {
    const normalized = normalizeChartSpec('{"data":[{"x":["A"],"y":[10]}],"layout":{"title":"Teste"}}');

    expect(normalized).toBeTruthy();
    expect(normalized?.layout?.title).toBe('Teste');
  });

  it('normalizes only non-empty table payloads', () => {
    expect(normalizeTableData([])).toBeUndefined();
    expect(normalizeTableData([{ une: 520, valor: 123 }])).toEqual([{ une: 520, valor: 123 }]);
  });

  it('merges final structured payload into assistant message', () => {
    const merged = mergeStructuredPayloadIntoMessage(
      {
        text: 'Resposta parcial',
        type: 'text',
      } as ChatMessageLike,
      {
        source: 'tool.gerar_grafico_universal_v2',
        confidence: 0.92,
        chart_data: { data: [{ x: ['SEG A'], y: [100] }], layout: { title: 'Vendas' } },
      },
    );

    expect(merged.type).toBe('chart');
    expect(merged.source).toBe('tool.gerar_grafico_universal_v2');
    expect(merged.confidence).toBe(0.92);
    expect(merged.chart_spec?.layout?.title).toBe('Vendas');
  });

  it('applies chart stream events without losing existing dashboard priority', () => {
    const next = applyStructuredStreamEventToMessage(
      {
        text: '',
        type: 'dashboard',
        dashboard_spec: { title: 'Painel', widgets: [] },
      } as ChatMessageLike,
      'chart',
      {
        chart_spec: { data: [{ x: ['A'], y: [10] }], layout: { title: 'Grafico' } },
      },
    );

    expect(next.type).toBe('dashboard');
    expect(next.chart_spec?.layout?.title).toBe('Grafico');
    expect(next.dashboard_spec?.title).toBe('Painel');
  });

  it('applies table stream events preserving chart context', () => {
    const next = applyStructuredStreamEventToMessage(
      {
        text: '',
        type: 'chart',
        chart_spec: { data: [{ x: ['A'], y: [10] }], layout: { title: 'Grafico' } },
      } as ChatMessageLike,
      'table',
      {
        table_data: [{ segmento: 'A', valor: 10 }],
      },
    );

    expect(next.type).toBe('chart');
    expect(next.data).toEqual([{ segmento: 'A', valor: 10 }]);
  });

  it('applies dashboard stream events with default text', () => {
    const next = applyStructuredStreamEventToMessage(
      {
        text: '',
        type: 'text',
      } as ChatMessageLike,
      'dashboard',
      {
        dashboard_spec: { title: 'Painel Executivo', widgets: [] },
      },
    );

    expect(next.type).toBe('dashboard');
    expect(next.text).toContain('Dashboard interativo');
  });
});
