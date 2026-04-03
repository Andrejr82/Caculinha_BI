import { describe, expect, it } from 'vitest';

import {
  buildPlaybookActionContext,
  buildExecutiveActionCtas,
  canDirectSendExecutiveAction,
  classifyConfidenceTone,
  formatExecutiveModeLabel,
  hasSufficientExecutiveGuideContext,
  inferExecutiveActionPriority,
  parseExecutiveContract,
} from './chatExecutive';

describe('parseExecutiveContract', () => {
  it('extracts headline, findings, actions and table markdown', () => {
    const parsed = parseExecutiveContract(`## Resumo executivo
- Margem pressionada em papelaria
- O desconto atual reduz rentabilidade
- Lojas com menor cobertura perderam giro

## Tabela operacional
| Indicador | Leitura |
|---|---|
| Margem | Em queda |

## Próximas ações
- Revisar desconto por loja
- Repor itens de maior giro`);

    expect(parsed.hasExecutiveStructure).toBe(true);
    expect(parsed.headline).toBe('Margem pressionada em papelaria');
    expect(parsed.summaryBullets).toEqual([
      'O desconto atual reduz rentabilidade',
      'Lojas com menor cobertura perderam giro',
    ]);
    expect(parsed.actionBullets).toEqual([
      'Revisar desconto por loja',
      'Repor itens de maior giro',
    ]);
    expect(parsed.tableMarkdown).toContain('| Indicador | Leitura |');
  });

  it('returns non executive structure for plain text', () => {
    const parsed = parseExecutiveContract('Resposta simples sem seções estruturadas.');

    expect(parsed.hasExecutiveStructure).toBe(false);
    expect(parsed.headline).toBeNull();
    expect(parsed.summaryBullets).toEqual([]);
    expect(parsed.actionBullets).toEqual([]);
    expect(parsed.tableMarkdown).toBeNull();
  });

  it('formats mode labels and action priorities', () => {
    expect(formatExecutiveModeLabel('market_research')).toBe('Mercado');
    expect(inferExecutiveActionPriority('Priorizar reposicao ainda hoje')).toBe('alta');
    expect(inferExecutiveActionPriority('Revisar desconto na semana')).toBe('media');
    expect(inferExecutiveActionPriority('Acompanhar desempenho mensal')).toBe('media');
    expect(classifyConfidenceTone(0.84)).toBe('high');
    expect(classifyConfidenceTone(0.67)).toBe('medium');
    expect(classifyConfidenceTone(0.42)).toBe('low');
  });

  it('builds contextual executive action ctas', () => {
    const ctas = buildExecutiveActionCtas(
      'critical_stock',
      ['Priorizar reposição ainda hoje'],
      'Ruptura crítica em papelaria',
    );

    expect(ctas.map(item => item.label)).toContain('Plano 24h');
    expect(ctas.map(item => item.label)).toContain('Transferência');
  });

  it('builds structured guided action context for real execution', () => {
    const action = buildPlaybookActionContext('critical_stock', {
      source: 'executive_cta',
      label: 'Plano 24h',
      prompt: 'Converta essa leitura em um plano operacional das próximas 24 horas.',
      directSend: true,
    });

    expect(action.playbookId).toBe('critical_stock');
    expect(action.source).toBe('executive_cta');
    expect(action.executionPolicy).toBe('real_data_only');
    expect(action.outputPreference).toBe('operational_plan');
    expect(action.toolHints).toContain('encontrar_rupturas_criticas');
    expect(action.directSend).toBe(true);
  });

  it('detects when guided context is strong enough for direct send', () => {
    expect(
      hasSufficientExecutiveGuideContext(
        'critical_stock',
        {
          product: 'Fita adesiva',
          segment: '',
          une: '1685',
          period: 'ultimos 30 dias',
          objective: 'Plano 24h',
        },
        null,
      ),
    ).toBe(true);

    expect(
      hasSufficientExecutiveGuideContext(
        'critical_stock',
        {
          product: '',
          segment: '',
          une: '',
          period: 'ultimos 30 dias',
          objective: 'Plano 24h',
        },
        null,
      ),
    ).toBe(false);
  });

  it('only direct sends when the playbook has real operating context', () => {
    expect(
      canDirectSendExecutiveAction(
        {
          label: 'Simular promoção',
          prompt: 'Simule um cenário promocional conservador.',
          playbookId: 'promotion_margin',
        },
        {
          product: 'Fita adesiva',
          segment: 'papelaria',
          une: '1685',
          period: 'ultimos 15 dias',
          objective: 'Proteger margem',
        },
        null,
      ),
    ).toBe(false);

    expect(
      canDirectSendExecutiveAction(
        {
          label: 'Posicionar preço',
          prompt: 'Traduzir benchmark em posicionamento de preço.',
          playbookId: 'market_benchmark',
        },
        {
          product: '',
          segment: 'papelaria',
          une: '',
          period: 'ultimos 15 dias',
          objective: 'Avaliar preço',
        },
        null,
      ),
    ).toBe(false);

    expect(
      canDirectSendExecutiveAction(
        {
          label: 'Posicionar preço',
          prompt: 'Traduzir benchmark em posicionamento de preço.',
          playbookId: 'market_benchmark',
        },
        {
          product: 'Caderno universitário',
          segment: 'papelaria',
          une: '',
          period: 'ultimos 15 dias',
          objective: 'Avaliar preço',
        },
        null,
      ),
    ).toBe(true);

    expect(
      canDirectSendExecutiveAction(
        {
          label: 'Plano sazonal',
          prompt: 'Transforme isso em um plano sazonal.',
          playbookId: 'seasonal_plan',
        },
        {
          product: '',
          segment: 'papelaria',
          une: '',
          period: 'ultimos 30 dias',
          objective: 'Preparar volta às aulas',
        },
        null,
      ),
    ).toBe(false);

    expect(
      canDirectSendExecutiveAction(
        {
          label: 'Plano sazonal',
          prompt: 'Transforme isso em um plano sazonal.',
          playbookId: 'seasonal_plan',
        },
        {
          product: '',
          segment: 'papelaria',
          une: '',
          period: 'janela volta às aulas 2026',
          objective: 'Preparar volta às aulas',
        },
        null,
      ),
    ).toBe(true);
  });
});
