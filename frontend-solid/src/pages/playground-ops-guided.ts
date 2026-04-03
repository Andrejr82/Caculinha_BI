export type GuidedChatMode =
  | 'executive_overview'
  | 'sales_by_store'
  | 'critical_stock'
  | 'promotion_margin'
  | 'market_benchmark'
  | 'seasonal_plan';

export type OperationMode = {
  id: string;
  title: string;
  description: string;
  focus: string;
  prompts: string[];
  chatMode: GuidedChatMode;
  toolHints: string[];
};

export type GuidedChatPayload = {
  query: string;
  session_id: string;
  chat_mode: GuidedChatMode;
  playbook_context: Record<string, string>;
  guided_action: Record<string, unknown>;
};

export type GuidedChatResolution = {
  text: string;
  requestId?: string;
  source?: string;
  intent?: string;
  sessionId?: string;
};

export const operationModes: OperationMode[] = [
  {
    id: 'abastecimento',
    title: 'Abastecimento',
    description: 'Reposicao por ruptura, cobertura e estoque de seguranca.',
    focus: 'Priorizacao de ruptura, giro e cobertura com recorte por loja e UNE.',
    prompts: [
      'Monte uma SQL para ruptura por loja, categoria e periodo.',
      'Crie um plano operacional para itens abaixo do estoque de seguranca.',
    ],
    chatMode: 'critical_stock',
    toolHints: ['encontrar_rupturas_criticas', 'consultar_dados_flexivel'],
  },
  {
    id: 'mix',
    title: 'Mix de Produtos',
    description: 'Ajuste de sortimento por loja, curva e sazonalidade.',
    focus: 'Decisao de sortimento com leitura por curva, margem e regionalidade.',
    prompts: [
      'Quero um roteiro para revisar mix por curva ABC e margem.',
      'Monte SQL para achar categorias sem giro e com excesso de espaco.',
    ],
    chatMode: 'sales_by_store',
    toolHints: ['consultar_dados_flexivel', 'gerar_grafico_universal_v2'],
  },
  {
    id: 'promocao',
    title: 'Promocao e Preco',
    description: 'Giro, margem e recomendacoes de campanha.',
    focus: 'Leitura tatico-comercial com elasticidade, margem e estoque disponivel.',
    prompts: [
      'Estruture uma analise de ROI para campanha por categoria.',
      'Crie uma consulta SQL para margem e giro antes e depois de promocao.',
    ],
    chatMode: 'promotion_margin',
    toolHints: ['simular_promocao_cesta', 'consultar_dados_flexivel'],
  },
  {
    id: 'devolucao',
    title: 'Devolucao e Transferencia',
    description: 'Transferencias entre UNEs e reducao de excesso.',
    focus: 'Equilibrio entre excesso, cobertura e oportunidade de transferencia.',
    prompts: [
      'Preciso de uma SQL para sugerir transferencia entre lojas com excesso e falta.',
      'Monte um checklist operacional para devolucao de itens parados.',
    ],
    chatMode: 'critical_stock',
    toolHints: ['consultar_dados_flexivel', 'alocar_estoque_lojas'],
  },
  {
    id: 'sazonalidade',
    title: 'Sazonalidade',
    description: 'Planejamento por periodo e comportamento historico.',
    focus: 'Planejamento com historico, eventos, calendario comercial e ruptura.',
    prompts: [
      'Sugira um roteiro para previsao semanal por loja e categoria.',
      'Crie uma estrutura para medir sazonalidade e cobertura antes do pico.',
    ],
    chatMode: 'seasonal_plan',
    toolHints: ['prever_demanda_produto', 'consultar_dados_flexivel'],
  },
  {
    id: 'opcom',
    title: 'OPCOM Rotinas',
    description: 'Execucao operacional com checklist e prazo.',
    focus: 'Rotina de execucao, follow-up e entregavel acionavel para operacao.',
    prompts: [
      'Monte um checklist diario de OPCOM com SLA e dono por etapa.',
      'Crie um rascunho de mensagem para cobrar plano de acao das lojas.',
    ],
    chatMode: 'executive_overview',
    toolHints: ['consultar_dados_flexivel'],
  },
];

const periodPatterns: Array<[RegExp, string]> = [
  [/\bultimos?\s+7\s+dias\b/i, 'ultimos 7 dias'],
  [/\bultimos?\s+30\s+dias\b/i, 'ultimos 30 dias'],
  [/\bultimos?\s+90\s+dias\b/i, 'ultimos 90 dias'],
  [/\bsemana(?:l)?\b/i, 'semana atual'],
  [/\bmes(?:al)?\b/i, 'mes atual'],
  [/\bhoje\b/i, 'hoje'],
  [/\bontem\b/i, 'ontem'],
];

function normalizeOutputPreference(outputType: string, query: string): string {
  if (/\b(sql|query|consulta)\b/i.test(query)) return 'sql';
  return outputType || 'operational_report';
}

function extractPeriod(query: string): string | undefined {
  for (const [pattern, label] of periodPatterns) {
    if (pattern.test(query)) return label;
  }
  return undefined;
}

function extractUne(query: string): string | undefined {
  const match = query.match(/\b(?:une|loja)\s+([a-z0-9-]{2,12})\b/i);
  return match?.[1]?.trim();
}

function extractProduct(query: string): string | undefined {
  const match = query.match(
    /\b(?:produto|item|sku)\s+([a-z0-9\s&./-]{2,60}?)(?=\s+(?:na|no)\s+(?:categoria|segmento|loja)\b|\s+une\b|\s+nos?\b|\s+ultimos?\b|[?.!,]|$)/i,
  );
  return match?.[1]?.trim();
}

function extractSegment(query: string): string | undefined {
  const match = query.match(
    /\b(?:segmento|categoria)\s+([a-z0-9\s&/-]{3,40}?)(?=\s+(?:na|no)\s+loja\b|\s+une\b|\s+nos?\b|\s+ultimos?\b|[?.!,]|$)/i,
  );
  return match?.[1]?.trim();
}

function pickMode(modeId: string): OperationMode {
  return operationModes.find((mode) => mode.id === modeId) || operationModes[0];
}

export function createPlaygroundSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `playground-${Date.now()}-${Math.round(Math.random() * 1_000_000)}`;
}

export function buildGuidedChatPayload(args: {
  modeId: string;
  query: string;
  sessionId: string;
  outputType: string;
}): GuidedChatPayload {
  const mode = pickMode(args.modeId);
  const query = String(args.query || '').trim();
  const period = extractPeriod(query);
  const une = extractUne(query);
  const product = extractProduct(query);
  const segment = extractSegment(query);
  const outputPreference = normalizeOutputPreference(args.outputType, query);
  const toolHints = [...mode.toolHints];

  if (outputPreference === 'sql' && !toolHints.includes('consultar_dados_flexivel')) {
    toolHints.unshift('consultar_dados_flexivel');
  }

  const playbook_context: Record<string, string> = {
    objective: mode.focus,
  };
  if (product) playbook_context.product = product;
  if (period) playbook_context.period = period;
  if (une) playbook_context.une = une;
  if (segment) playbook_context.segment = segment;

  return {
    query,
    session_id: args.sessionId,
    chat_mode: mode.chatMode,
    playbook_context,
    guided_action: {
      actionId: `${mode.chatMode}:${outputPreference}`,
      actionLabel: mode.title,
      source: 'playground_ops',
      playbookId: mode.chatMode,
      prompt: query,
      directSend: true,
      executionPolicy: 'real_data_only',
      outputPreference,
      missingDataBehavior: 'ask_minimum_required_inputs',
      toolHints,
    },
  };
}

export function extractGuidedChatResolution(payload: any): GuidedChatResolution {
  // payload é o objeto retornado pelo axios: { data: { response, model_info, metadata } }
  const body = payload?.data ?? payload ?? {};

  // Suporte ao retorno do /playground/chat: { response, model_info, metadata }
  // E ao retorno do /chat (SSE agent): { full_agent_response: { result: { mensagem } } }
  const full = body?.full_agent_response ?? {};
  const result = full?.result ?? {};
  const metadata = body?.metadata ?? full?.metadata ?? full?._internal_meta ?? {};
  const modelInfo = body?.model_info ?? {};

  const textCandidates = [
    // Formato /playground/chat (principal)
    typeof body?.response === 'string' ? body.response : '',
    // Formato agente BI legacy
    typeof result?.mensagem === 'string' ? result.mensagem : '',
    typeof result === 'string' ? result : '',
    typeof full?.mensagem === 'string' ? full.mensagem : '',
  ];
  const text = textCandidates.find((item) => String(item || '').trim().length > 0) || '';

  return {
    text: String(text || '').trim(),
    requestId: String(metadata?.request_id || full?.request_id || '').trim() || undefined,
    source: String(modelInfo?.model || full?.source || metadata?.source || body?.model_info?.model || '').trim() || undefined,
    intent: String(modelInfo?.intent || full?.intent || metadata?.intent || '').trim() || undefined,
    sessionId: String(body?.session_id || metadata?.session_id || '').trim() || undefined,
  };
}
