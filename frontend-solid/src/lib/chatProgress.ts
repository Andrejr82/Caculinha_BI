const TOOL_LABELS: Record<string, string> = {
  'system.thinking': 'Entendendo sua solicitacao...',
  'system.finalizing': 'Consolidando resposta executiva...',
  'tool.data_query': 'Consultando banco de dados...',
  'tool.metadata_query': 'Acessando metadados...',
  'tool.chart': 'Gerando grafico interativo...',
  'tool.dashboard': 'Montando dashboard interativo...',
  'tool.competitive_research': 'Pesquisando fontes de mercado...',
  'tool.market_research': 'Pesquisando fontes de mercado...',
  Pensando: 'Entendendo sua solicitacao...',
  consultar_dados_flexivel: 'Consultando banco de dados...',
  consultar_dados_gerais: 'Acessando metadados...',
  gerar_grafico_universal: 'Criando visualizacao...',
  gerar_grafico_universal_v2: 'Gerando grafico interativo...',
  gerar_dashboard_executivo: 'Montando dashboard interativo...',
  pesquisar_precos_concorrentes: 'Pesquisando fontes de mercado...',
  pesquisar_mercado_web: 'Pesquisando fontes de mercado...',
  'Processando resposta': 'Consolidando resposta executiva...',
};

const STATUS_PREFIXES: Record<string, string> = {
  start: 'Iniciando',
  executing: 'Executando',
  processing: 'Finalizando',
  done: 'Finalizando',
  finishing: 'Finalizando',
};

export interface ThinkingStepViewModel {
  key: string;
  text: string;
}

export function buildThinkingStep(tool: unknown, status: unknown): ThinkingStepViewModel {
  const safeTool = typeof tool === 'string' ? tool : '';
  const safeStatus = typeof status === 'string' ? status.toLowerCase() : '';
  const label = TOOL_LABELS[safeTool] || 'Executando etapa da analise...';
  const prefix = STATUS_PREFIXES[safeStatus] || 'Processando';
  const key = `${prefix}|${TOOL_LABELS[safeTool] ? safeTool : 'generic'}`;

  return {
    key,
    text: `${prefix}: ${label}`,
  };
}
