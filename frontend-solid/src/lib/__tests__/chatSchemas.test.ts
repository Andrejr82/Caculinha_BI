import { describe, expect, it } from 'vitest';
import {
  safeParseChartSpec,
  safeParseStreamEventPayload,
  safeParseTableData,
} from '@/lib/chatSchemas';

describe('chatSchemas', () => {
  it('accepts structured final stream payloads', () => {
    const payload = safeParseStreamEventPayload({
      type: 'final',
      text: 'Relatorio pronto',
      source: 'tool.gerar_grafico_universal_v2',
      chart_data: {
        data: [{ x: ['A'], y: [10] }],
        layout: { title: 'Vendas' },
      },
      table_data: [{ segmento: 'Tecidos', valor: 100 }],
    });

    expect(payload).not.toBeNull();
    expect(payload?.type).toBe('final');
    expect(payload?.source).toBe('tool.gerar_grafico_universal_v2');
  });

  it('accepts final payloads with coerced strings and loose citation fields', () => {
    const payload = safeParseStreamEventPayload({
      type: 'final',
      text: 123,
      done: 'true',
      request_id: 999,
      confidence: '0.93',
      citations: [{ source: 'tool.test', score: 0.8, url: 12345 }],
    });

    expect(payload).not.toBeNull();
    expect(payload?.text).toBe('123');
    expect(payload?.done).toBe(true);
    expect(payload?.request_id).toBe('999');
    expect(payload?.confidence).toBe(0.93);
  });

  it('rejects malformed stream payloads', () => {
    const payload = safeParseStreamEventPayload({
      type: 'chart',
      table_data: 'nao-array',
    });

    expect(payload).toBeNull();
  });

  it('keeps only non-empty validated table data', () => {
    expect(safeParseTableData([])).toBeUndefined();
    expect(safeParseTableData([{ une: 520, valor: 123 }])).toEqual([{ une: 520, valor: 123 }]);
  });

  it('accepts valid chart specs and rejects invalid ones', () => {
    expect(safeParseChartSpec({ data: [{ x: ['A'], y: [1] }], layout: { title: 'OK' } })).toBeTruthy();
    expect(safeParseChartSpec(null)).toBeUndefined();
  });
});
