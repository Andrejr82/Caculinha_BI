import type { ChatPlaybookContext, ChatPlaybookId } from './chatPlaybooks';

export interface ExecutiveContractView {
  headline: string | null;
  summaryBullets: string[];
  actionBullets: string[];
  tableMarkdown: string | null;
  hasExecutiveStructure: boolean;
}

export type ExecutiveActionPriority = 'alta' | 'media' | 'baixa';
export interface ExecutiveActionCta {
  label: string;
  prompt: string;
  playbookId?: ChatPlaybookId;
}

export type GuidedActionSource = 'playbook_builder' | 'executive_cta';
export type GuidedOutputPreference =
  | 'executive'
  | 'comparison'
  | 'operational_plan'
  | 'market_positioning'
  | 'forecast';

export interface GuidedActionContext {
  actionId: string;
  actionLabel: string;
  source: GuidedActionSource;
  playbookId?: ChatPlaybookId;
  prompt: string;
  directSend: boolean;
  executionPolicy: 'real_data_only';
  outputPreference: GuidedOutputPreference;
  missingDataBehavior: 'ask_minimum_required_inputs';
  toolHints: string[];
}

const normalizeHeading = (value: string): string =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();

const toActionSlug = (value: string): string =>
  normalizeHeading(value)
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'guided_action';

const PLAYBOOK_OUTPUT_PREFERENCES: Record<ChatPlaybookId, GuidedOutputPreference> = {
  executive_overview: 'executive',
  sales_by_store: 'comparison',
  critical_stock: 'operational_plan',
  promotion_margin: 'operational_plan',
  market_benchmark: 'market_positioning',
  seasonal_plan: 'forecast',
};

const PLAYBOOK_TOOL_HINTS: Record<ChatPlaybookId, string[]> = {
  executive_overview: ['consultar_dados_flexivel', 'gerar_dashboard_executivo'],
  sales_by_store: ['analisar_historico_vendas', 'gerar_grafico_universal_v2', 'consultar_dados_flexivel'],
  critical_stock: ['encontrar_rupturas_criticas', 'sugerir_transferencias_automaticas', 'consultar_dados_flexivel'],
  promotion_margin: ['calcular_mc_produto', 'analisar_cesta_compras', 'simular_promocao_cesta', 'consultar_dados_flexivel'],
  market_benchmark: ['pesquisar_precos_concorrentes', 'pesquisar_mercado_web'],
  seasonal_plan: ['prever_demanda', 'calcular_eoq', 'alocar_estoque_lojas'],
};

export const buildPlaybookActionContext = (
  playbookId: ChatPlaybookId,
  options?: {
    source?: GuidedActionSource;
    label?: string;
    prompt?: string;
    directSend?: boolean;
  },
): GuidedActionContext => {
  const actionLabel = String(options?.label || '').trim() || playbookId;
  const prompt = String(options?.prompt || '').trim() || actionLabel;

  return {
    actionId: `${playbookId}:${toActionSlug(actionLabel)}`,
    actionLabel,
    source: options?.source || 'playbook_builder',
    playbookId,
    prompt,
    directSend: Boolean(options?.directSend),
    executionPolicy: 'real_data_only',
    outputPreference: PLAYBOOK_OUTPUT_PREFERENCES[playbookId],
    missingDataBehavior: 'ask_minimum_required_inputs',
    toolHints: [...PLAYBOOK_TOOL_HINTS[playbookId]],
  };
};

const extractSection = (text: string, headings: string[]): string => {
  const lines = String(text || '').split('\n');
  const normalizedHeadings = headings.map(normalizeHeading);
  let startIndex = -1;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line.startsWith('##')) continue;
    const headingText = normalizeHeading(line.replace(/^##+\s*/, ''));
    if (normalizedHeadings.includes(headingText)) {
      startIndex = index + 1;
      break;
    }
  }

  if (startIndex < 0) return '';

  const sectionLines: string[] = [];
  for (let index = startIndex; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim().startsWith('##')) break;
    sectionLines.push(line);
  }

  return sectionLines.join('\n').trim();
};

const extractBullets = (sectionText: string): string[] =>
  String(sectionText || '')
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.startsWith('- '))
    .map(line => line.replace(/^- /, '').trim())
    .filter(Boolean);

export const parseExecutiveContract = (text: string): ExecutiveContractView => {
  const summarySection = extractSection(text, ['resumo executivo', 'resumo']);
  const tableSection = extractSection(text, ['tabela operacional', 'tabela']);
  const actionsSection = extractSection(text, ['próximas ações', 'proximas acoes', 'ação recomendada', 'acao recomendada']);

  const summaryBullets = extractBullets(summarySection);
  const actionBullets = extractBullets(actionsSection);
  const headline = summaryBullets.length > 0 ? summaryBullets[0] : null;

  return {
    headline,
    summaryBullets: summaryBullets.slice(headline ? 1 : 0),
    actionBullets,
    tableMarkdown: tableSection || null,
    hasExecutiveStructure: Boolean(summarySection || tableSection || actionsSection),
  };
};

export const formatExecutiveModeLabel = (mode?: string): string | null => {
  const normalized = normalizeHeading(mode || '');
  if (!normalized) return null;

  const labels: Record<string, string> = {
    analysis: 'Analise',
    executive: 'Executivo',
    executiveoverview: 'Resumo executivo',
    salesbystore: 'Vendas por loja',
    criticalstock: 'Ruptura',
    promotionmargin: 'Promocao e margem',
    marketbenchmark: 'Benchmark',
    seasonalplan: 'Plano sazonal',
    dashboard: 'Dashboard',
    visualization: 'Visual',
    marketresearch: 'Mercado',
    competitiveresearch: 'Concorrencia',
    inventory: 'Estoque',
    forecasting: 'Previsao',
    basket: 'Cesta',
    promotion: 'Promocao',
  };

  return labels[normalized] || String(mode).trim();
};

export const classifyConfidenceTone = (confidence?: number): 'high' | 'medium' | 'low' | null => {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) return null;
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.6) return 'medium';
  return 'low';
};

export const inferExecutiveActionPriority = (action: string): ExecutiveActionPriority => {
  const normalized = normalizeHeading(action);
  if (!normalized) return 'baixa';

  if (
    normalized.includes('imediat') ||
    normalized.includes('urg') ||
    normalized.includes('hoje') ||
    normalized.includes('agora') ||
    normalized.includes('prioriz') ||
    normalized.includes('ruptura') ||
    normalized.includes('repor')
  ) {
    return 'alta';
  }

  if (
    normalized.includes('semana') ||
    normalized.includes('revis') ||
    normalized.includes('ajust') ||
    normalized.includes('negoci') ||
    normalized.includes('acompanh') ||
    normalized.includes('monitor')
  ) {
    return 'media';
  }

  return 'baixa';
};

export const buildExecutiveActionCtas = (
  mode: string | undefined,
  actions: string[],
  headline?: string | null,
): ExecutiveActionCta[] => {
  const normalizedMode = normalizeHeading(mode || '');
  const normalizedHeadline = normalizeHeading(headline || '');
  const normalizedActions = actions.map(normalizeHeading).join(' ');

  const ctas: ExecutiveActionCta[] = [];

  if (normalizedMode.includes('criticalstock') || normalizedMode.includes('inventory') || normalizedHeadline.includes('ruptura')) {
    ctas.push(
      {
        label: 'Plano 24h',
        prompt: 'Converta essa leitura em um plano operacional das próximas 24 horas, com prioridade por loja, item e ação recomendada.',
        playbookId: 'critical_stock',
      },
      {
        label: 'Transferência',
        prompt: 'Sugira transferências entre lojas para reduzir ruptura imediata e explique por onde começar.',
        playbookId: 'critical_stock',
      },
    );
  }

  if (normalizedMode.includes('promotion') || normalizedHeadline.includes('margem') || normalizedActions.includes('desconto')) {
    ctas.push(
      {
        label: 'Simular promoção',
        prompt: 'Simule um cenário promocional conservador com foco em preservar margem e diga a condição mínima para aprovar.',
        playbookId: 'promotion_margin',
      },
      {
        label: 'Rever desconto',
        prompt: 'Diga qual ajuste de desconto ou mecânica promocional reduziria risco de erosão de margem.',
        playbookId: 'promotion_margin',
      },
    );
  }

  if (normalizedMode.includes('market') || normalizedHeadline.includes('mercado') || normalizedHeadline.includes('preco')) {
    ctas.push(
      {
        label: 'Posicionar preço',
        prompt: 'Traduza essa análise em posicionamento de preço: barato, alinhado ou caro, e qual ação você recomenda.',
        playbookId: 'market_benchmark',
      },
      {
        label: 'Nova pesquisa',
        prompt: 'Aprofunde a pesquisa de mercado e destaque os concorrentes que mais influenciam a decisão de preço.',
        playbookId: 'market_benchmark',
      },
    );
  }

  if (normalizedMode.includes('salesbystore') || normalizedHeadline.includes('loja') || normalizedActions.includes('loja')) {
    ctas.push(
      {
        label: 'Detalhar lojas',
        prompt: 'Detalhe as lojas abaixo da média, os principais gaps e onde agir primeiro.',
        playbookId: 'sales_by_store',
      },
      {
        label: 'Gerar comparativo',
        prompt: 'Gere um comparativo visual por loja com os principais líderes, cauda e amplitude entre eles.',
        playbookId: 'sales_by_store',
      },
    );
  }

  if (normalizedMode.includes('seasonal') || normalizedHeadline.includes('sazonal')) {
    ctas.push(
      {
        label: 'Plano sazonal',
        prompt: 'Transforme isso em um plano sazonal por etapa, com preparação comercial, estoque e risco principal.',
        playbookId: 'seasonal_plan',
      },
      {
        label: 'Prever demanda',
        prompt: 'Projete a demanda esperada e diga onde há maior risco de ruptura ou sobra.',
        playbookId: 'seasonal_plan',
      },
    );
  }

  ctas.push(
    {
      label: 'Plano 7 dias',
      prompt: 'Transforme essa análise em um plano de ação objetivo para os próximos 7 dias, com prioridade, impacto e responsável sugerido.',
      playbookId: 'executive_overview',
    },
    {
      label: 'Gerar gráfico',
      prompt: 'Converta essa análise em gráfico, se houver base suficiente, e destaque o principal insight visual.',
    },
  );

  const unique = new Map<string, ExecutiveActionCta>();
  for (const item of ctas) {
    if (!unique.has(item.label)) {
      unique.set(item.label, item);
    }
  }

  return Array.from(unique.values()).slice(0, 3);
};

export const hasSufficientExecutiveGuideContext = (
  targetPlaybookId: ChatPlaybookId,
  context: ChatPlaybookContext,
  activePlaybookId?: ChatPlaybookId | null,
): boolean => {
  const product = String(context.product || '').trim();
  const segment = String(context.segment || '').trim();
  const une = String(context.une || '').trim();
  const period = String(context.period || '').trim();

  const hasProduct = Boolean(product);
  const hasSegment = Boolean(segment);
  const hasUne = Boolean(une);
  const primarySignals = [product, segment, une].filter(Boolean).length;
  const hasCustomPeriod = Boolean(period) && normalizeHeading(period) !== normalizeHeading('ultimos 30 dias');
  const isSamePlaybook = activePlaybookId === targetPlaybookId;

  if (targetPlaybookId === 'promotion_margin') {
    return false;
  }

  if (targetPlaybookId === 'market_benchmark') {
    return hasProduct;
  }

  if (targetPlaybookId === 'sales_by_store') {
    return hasUne || (hasSegment && hasCustomPeriod) || (isSamePlaybook && primarySignals >= 1);
  }

  if (targetPlaybookId === 'critical_stock') {
    return (hasProduct && hasUne) || (hasUne && hasCustomPeriod) || (isSamePlaybook && hasProduct);
  }

  if (targetPlaybookId === 'seasonal_plan') {
    return hasCustomPeriod && (hasProduct || hasSegment || hasUne);
  }

  if (isSamePlaybook && primarySignals >= 1) {
    return true;
  }

  if (primarySignals >= 2) {
    return true;
  }

  return primarySignals >= 1 && hasCustomPeriod;
};

export const canDirectSendExecutiveAction = (
  cta: ExecutiveActionCta,
  context: ChatPlaybookContext,
  activePlaybookId?: ChatPlaybookId | null,
): boolean => {
  if (!cta.playbookId) {
    return true;
  }

  return hasSufficientExecutiveGuideContext(cta.playbookId, context, activePlaybookId);
};
