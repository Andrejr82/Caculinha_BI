import { describe, expect, it } from 'vitest';

import { buildThinkingStep } from '@/lib/chatProgress';

describe('buildThinkingStep', () => {
  it('maps known tools to safe business-friendly labels', () => {
    expect(buildThinkingStep('tool.data_query', 'start')).toEqual({
      key: 'Iniciando|tool.data_query',
      text: 'Iniciando: Consultando banco de dados...',
    });
  });

  it('reduces unknown tool names to a generic safe label', () => {
    expect(buildThinkingStep('SELECT * FROM segredo_interno', 'executing')).toEqual({
      key: 'Executando|generic',
      text: 'Executando: Executando etapa da analise...',
    });
  });

  it('falls back to generic processing when status is not recognized', () => {
    expect(buildThinkingStep('tool.chart', 'thinking-hard')).toEqual({
      key: 'Processando|tool.chart',
      text: 'Processando: Gerando grafico interativo...',
    });
  });
});
