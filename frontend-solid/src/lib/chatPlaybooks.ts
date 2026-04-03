export type ChatPlaybookId =
  | 'executive_overview'
  | 'sales_by_store'
  | 'critical_stock'
  | 'promotion_margin'
  | 'market_benchmark'
  | 'seasonal_plan';

export interface ChatPlaybookContext {
  product: string;
  segment: string;
  une: string;
  period: string;
  objective: string;
}

export interface ChatPlaybookDefinition {
  id: ChatPlaybookId;
  title: string;
  description: string;
  cta: string;
}

export interface ChatFollowUpSuggestion {
  label: string;
  prompt: string;
}

export const CHAT_PLAYBOOKS: ChatPlaybookDefinition[] = [
  {
    id: 'executive_overview',
    title: 'Resumo executivo',
    description: 'Consolida leitura de negocio, prioridades e proximos passos.',
    cta: 'Gerar leitura executiva',
  },
  {
    id: 'sales_by_store',
    title: 'Vendas por loja',
    description: 'Compara UNEs, identifica lideres, cauda e gaps operacionais.',
    cta: 'Comparar performance',
  },
  {
    id: 'critical_stock',
    title: 'Ruptura e reposicao',
    description: 'Prioriza itens criticos, cobertura e transferencia urgente.',
    cta: 'Mapear risco de ruptura',
  },
  {
    id: 'promotion_margin',
    title: 'Promocao e margem',
    description: 'Simula desconto, rentabilidade e volume adicional necessario.',
    cta: 'Avaliar promocao',
  },
  {
    id: 'market_benchmark',
    title: 'Benchmark de mercado',
    description: 'Pesquisa referencia externa e posicionamento de preco.',
    cta: 'Pesquisar mercado',
  },
  {
    id: 'seasonal_plan',
    title: 'Plano sazonal',
    description: 'Prepara abastecimento e acao comercial para janelas de demanda.',
    cta: 'Planejar sazonalidade',
  },
];

const withFallback = (value: string, fallback: string) => {
  const normalized = String(value || '').trim();
  return normalized || fallback;
};

export const createEmptyPlaybookContext = (): ChatPlaybookContext => ({
  product: '',
  segment: '',
  une: '',
  period: '',
  objective: '',
});

export const buildPlaybookPrompt = (
  playbookId: ChatPlaybookId,
  context: ChatPlaybookContext,
): string => {
  const product = withFallback(context.product, 'nao informado');
  const segment = withFallback(context.segment, 'todos os segmentos relevantes');
  const une = withFallback(context.une, 'todas as lojas/UNEs relevantes');
  const period = withFallback(context.period, 'ultimos 30 dias');
  const objective = withFallback(context.objective, 'orientar decisao com base em impacto e urgencia');

  if (playbookId === 'executive_overview') {
    return [
      'Monte um resumo executivo completo do negocio.',
      `Periodo: ${period}.`,
      `Segmento: ${segment}.`,
      `Escopo de lojas: ${une}.`,
      `Objetivo principal: ${objective}.`,
      'Entregue: 1. resumo executivo; 2. tabela operacional com numeros-chave; 3. proximas acoes priorizadas.',
      'Se houver concentracao relevante, destaque lideres, cauda e gaps.',
    ].join(' ');
  }

  if (playbookId === 'sales_by_store') {
    return [
      'Compare vendas por loja/UNE com foco em decisao comercial.',
      `Periodo: ${period}.`,
      `Segmento: ${segment}.`,
      `Produto ou foco: ${product}.`,
      `Escopo de lojas: ${une}.`,
      'Entregue top performers, lojas abaixo da media, amplitude entre lider e cauda e plano de acao em 7 dias.',
      'Se fizer sentido, gere grafico comparativo por UNE.',
    ].join(' ');
  }

  if (playbookId === 'critical_stock') {
    return [
      'Analise ruptura, cobertura e reposicao com prioridade operacional.',
      `Periodo de referencia: ${period}.`,
      `Segmento: ${segment}.`,
      `Produto ou SKU: ${product}.`,
      `Lojas/UNEs: ${une}.`,
      'Entregue itens criticos, risco de perda de venda, recomendacao de transferencia/reposicao e prazo de acao.',
      'Priorize o que precisa acontecer nas proximas 24 horas.',
    ].join(' ');
  }

  if (playbookId === 'promotion_margin') {
    return [
      'Avalie promocao com foco em margem e rentabilidade.',
      `Produto ou SKU: ${product}.`,
      `Segmento: ${segment}.`,
      `Periodo: ${period}.`,
      `Objetivo comercial: ${objective}.`,
      'Entregue impacto esperado, risco de margem, condicoes para aprovar a promocao e volume adicional necessario para compensar.',
      'Se faltar dado critico, diga exatamente o que precisa ser confirmado.',
    ].join(' ');
  }

  if (playbookId === 'market_benchmark') {
    return [
      'Faca benchmark de mercado e posicione nossa estrategia de preco.',
      `Produto ou SKU: ${product}.`,
      `Segmento: ${segment}.`,
      `Periodo: ${period}.`,
      `Objetivo: ${objective}.`,
      'Entregue faixa de mercado, leitura de posicionamento, concorrentes observados e recomendacao pratica.',
      'Se houver evidencia externa, cite as fontes relevantes.',
    ].join(' ');
  }

  return [
    'Monte um plano sazonal para abastecimento e acao comercial.',
    `Periodo ou janela: ${period}.`,
    `Segmento: ${segment}.`,
    `Produto ou foco: ${product}.`,
    `Lojas/UNEs: ${une}.`,
    `Objetivo: ${objective}.`,
    'Entregue riscos, oportunidades, preparacao operacional e proximos passos por prioridade.',
  ].join(' ');
};

export const buildFollowUpSuggestions = (message: {
  text?: string;
  type?: string;
  source?: string;
  citations?: Array<Record<string, any>>;
  chart_spec?: unknown;
  data?: unknown[];
  dashboard_spec?: unknown;
}): ChatFollowUpSuggestion[] => {
  const suggestions: ChatFollowUpSuggestion[] = [];
  const text = String(message.text || '').toLowerCase();
  const hasChart = Boolean(message.chart_spec);
  const hasTable = Array.isArray(message.data) && message.data.length > 0;
  const hasDashboard = Boolean(message.dashboard_spec);
  const hasMarketEvidence = Array.isArray(message.citations) && message.citations.length > 0;

  if (hasChart || hasDashboard) {
    suggestions.push({
      label: 'Plano de acao',
      prompt: 'Transforme essa analise em um plano de acao objetivo para os proximos 7 dias, com prioridade, impacto e responsavel sugerido.',
    });
  }

  if (hasTable || text.includes('loja') || text.includes('une') || text.includes('segment')) {
    suggestions.push({
      label: 'Detalhar gaps',
      prompt: 'Detalhe os maiores gaps operacionais e diga exatamente onde devo agir primeiro.',
    });
  }

  if (text.includes('margem') || text.includes('promo') || text.includes('desconto')) {
    suggestions.push({
      label: 'Simular promocao',
      prompt: 'Com base nessa leitura, simule um cenario promocional conservador e diga a condicao minima para nao destruir margem.',
    });
  }

  if (text.includes('estoque') || text.includes('ruptura') || text.includes('cobertura')) {
    suggestions.push({
      label: 'Reposicao imediata',
      prompt: 'Converta isso em um plano de reposicao ou transferencia com prioridade das proximas 24 horas.',
    });
  }

  if (hasMarketEvidence || text.includes('mercado') || text.includes('concorr')) {
    suggestions.push({
      label: 'Posicionamento de preco',
      prompt: 'Agora traduza essa pesquisa em posicionamento de preco: estamos baratos, alinhados ou caros, e qual acao voce recomenda?',
    });
  }

  suggestions.push({
    label: 'Gerar grafico',
    prompt: 'Converta essa analise em grafico, se houver base suficiente, e destaque o principal insight visual.',
  });

  const unique = new Map<string, ChatFollowUpSuggestion>();
  for (const item of suggestions) {
    if (!unique.has(item.label)) {
      unique.set(item.label, item);
    }
  }
  return Array.from(unique.values()).slice(0, 4);
};
