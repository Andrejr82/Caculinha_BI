import { For, Show, createMemo, createResource, createSignal } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { dashboardApi } from '../lib/api';

type Summary = {
  revenue_30d_mi: number;
  margin_avg_pct: number;
  critical_coverage_skus: number;
  selling_rupture_skus: number;
  transferable_skus: number;
  revenue_at_risk_mi: number;
  captured_revenue_mi: number;
  critical_coverage_revenue_mi: number;
  total_unes: number;
  total_segments: number;
  abc_top_100_share_pct: number;
};

type TrendPoint = {
  label: string;
  value_mi: number;
  is_partial: boolean;
};

type SegmentShare = {
  segmento: string;
  share_receita_pct: number;
  ruptura_pct: number;
};

type HeatmapCell = {
  une: string;
  segmento: string;
  receita_mi: number;
  ruptura_pct: number;
};

type Opportunity = {
  une: string;
  segmento: string;
  revenue_mi: number;
  ruptura_pct: number;
};

type StoreOption = {
  UNE?: string | number;
  une?: string | number;
  NOME?: string;
  nome?: string;
};

type MasterOverviewResponse = {
  summary: Summary;
  period_trend: TrendPoint[];
  segment_share: SegmentShare[];
  heatmap: {
    unes: string[];
    segments: string[];
    cells: HeatmapCell[];
  };
  opportunities: Opportunity[];
  abc: {
    top_10_pct: number;
    top_50_pct: number;
    top_100_pct: number;
    top_500_pct: number;
  };
};

const emptyOverview: MasterOverviewResponse = {
  summary: {
    revenue_30d_mi: 0,
    margin_avg_pct: 0,
    critical_coverage_skus: 0,
    selling_rupture_skus: 0,
    transferable_skus: 0,
    revenue_at_risk_mi: 0,
    captured_revenue_mi: 0,
    critical_coverage_revenue_mi: 0,
    total_unes: 0,
    total_segments: 0,
    abc_top_100_share_pct: 0,
  },
  period_trend: [],
  segment_share: [],
  heatmap: {
    unes: [],
    segments: [],
    cells: [],
  },
  opportunities: [],
  abc: {
    top_10_pct: 0,
    top_50_pct: 0,
    top_100_pct: 0,
    top_500_pct: 0,
  },
};

const segmentAlias = (value: string) => {
  const aliases: Record<string, string> = {
    'ARMARINHO E CONFECÇÃO': 'Armarinho',
    'CASA E DECORAÇÃO': 'CASA/DECO',
  };
  return aliases[value.toUpperCase()] || value;
};

const formatMi = (value: number) =>
  new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);

const formatPct = (value: number) =>
  `${new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)}%`;

const formatInt = (value: number) => new Intl.NumberFormat('pt-BR').format(value);

const trendLabelDisplay = (value: string) => {
  const labels: Record<string, string> = {
    'Mês -3': '3 meses atrás',
    'Mês -2': '2 meses atrás',
    'Último mês fechado': 'Último mês',
    'Mês atual parcial': 'Mês atual',
  };
  return labels[value] || value;
};

function Panel(props: { title: string; subtitle: string; children: any; dark?: boolean }) {
  return (
    <section
      class={`min-w-0 rounded-[1.75rem] border px-5 py-5 shadow-sm ${
        props.dark ? 'border-slate-900 bg-slate-950 text-white' : 'border-[#d8ddd7] bg-white'
      }`}
    >
      <div class="mb-5">
        <h2 class={`text-[1.55rem] font-black tracking-tight ${props.dark ? 'text-white' : 'text-[#20322a]'}`}>
          {props.title}
        </h2>
        <p class={`mt-1 text-sm ${props.dark ? 'text-white/70' : 'text-[#66756d]'}`}>{props.subtitle}</p>
      </div>
      {props.children}
    </section>
  );
}

function KpiCard(props: { title: string; value: string; note: string; accent: string; tint: string }) {
  return (
    <article class="rounded-3xl border border-[#d8ddd7] bg-white p-4 shadow-sm">
      <div
        class="mb-3 inline-flex max-w-full rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em]"
        style={{ color: props.accent, background: props.tint }}
      >
        {props.title}
      </div>
      <div class="whitespace-nowrap text-[1.7rem] font-black leading-none tracking-tight text-[#20322a] xl:text-[1.85rem]">
        {props.value}
      </div>
      <p class="mt-1 text-sm text-[#66756d]">{props.note}</p>
    </article>
  );
}

function SkeletonCard() {
  return <div class="h-32 animate-pulse rounded-3xl border border-[#d8ddd7] bg-white/70" />;
}

export default function PainelAnaliticoMestre() {
  const navigate = useNavigate();
  const [selectedSegment, setSelectedSegment] = createSignal('');
  const [selectedUne, setSelectedUne] = createSignal('');

  const [segments] = createResource(async () => {
    const response = await dashboardApi.getMetadataSegments();
    return (response.data || []) as string[];
  });
  const normalizedSegments = createMemo(() =>
    (segments() || [])
      .map((segment) => String(segment || '').trim())
      .filter((segment) => segment.length > 0),
  );

  const [stores] = createResource(async () => {
    const response = await dashboardApi.getMetadataStores();
    return (response.data || []) as StoreOption[];
  });

  const overviewParams = createMemo(() => ({
    segmento: selectedSegment() || undefined,
    une: selectedUne() || undefined,
  }));

  const [overview] = createResource(overviewParams, async (params) => {
    const response = await dashboardApi.getMasterOverview(params);
    return response.data as MasterOverviewResponse;
  });

  const data = createMemo(() => overview() || emptyOverview);

  const maxTrend = createMemo(() => Math.max(...data().period_trend.map((item) => item.value_mi), 1));

  const heatmapMap = createMemo(() => {
    const map = new Map<string, HeatmapCell>();
    data().heatmap.cells.forEach((cell) => map.set(`${cell.une}:${cell.segmento}`, cell));
    return map;
  });
  const heatmapGridTemplate = createMemo(
    () => `4.75rem repeat(${Math.max(data().heatmap.segments.length, 1)}, minmax(0, 1fr))`,
  );

  const topSegments = createMemo(() => data().segment_share.slice(0, 2).map((item) => segmentAlias(item.segmento)));

  const topOpportunity = createMemo(() => data().opportunities[0] || null);
  const scopeLabel = createMemo(() => {
    const segment = selectedSegment();
    const une = selectedUne();
    if (segment && une) return `${segmentAlias(segment)} • UNE ${une}`;
    if (segment) return segmentAlias(segment);
    if (une) return `UNE ${une}`;
    return 'Rede completa';
  });

  const agenda = createMemo(() => {
    const opportunity = topOpportunity();
    const firstSegment = topSegments()[0] || 'os segmentos líderes';
    const secondSegment = topSegments()[1] || 'as frentes secundárias';

    return [
      {
        title: 'Tendência',
        text: 'Usar o último mês fechado como principal referência de comparação e acompanhar o mês atual apenas como leitura parcial.',
      },
      {
        title: 'Receita em risco',
        text: `Levar R$ ${formatMi(data().summary.revenue_at_risk_mi)} mi de perda potencial para a pauta diária.`,
      },
      {
        title: 'Calor operacional',
        text: opportunity
          ? `Abrir ${segmentAlias(opportunity.segmento)} na UNE ${opportunity.une}, onde receita e ruptura estão comprimidas.`
          : 'Abrir os blocos com maior ruptura relativa nas UNEs líderes.',
      },
      {
        title: 'Defesa comercial',
        text: `Blindar profundidade de mix em ${firstSegment} e ${secondSegment}.`,
      },
      {
        title: 'Supply',
        text: `Usar ${formatInt(data().summary.transferable_skus)} transferíveis antes de ampliar compra.`,
      },
      {
        title: 'Exceções',
        text: 'Separar sazonalidade da narrativa principal para não distorcer a leitura executiva.',
      },
    ];
  });

  const audienceCards = createMemo(() => {
    const opportunity = topOpportunity();
    const firstSegment = topSegments()[0] || 'os segmentos líderes';
    const secondSegment = topSegments()[1] || 'o segundo bloco comercial';

    return [
      {
        title: 'Stakeholders',
        bg: '#e6f0ea',
        fg: '#1e6b4c',
        text: `Receita capturada em R$ ${formatMi(data().summary.captured_revenue_mi)} mi, mas ainda existe R$ ${formatMi(data().summary.revenue_at_risk_mi)} mi em risco por disponibilidade.`,
      },
      {
        title: 'Comercial',
        bg: '#e8eff7',
        fg: '#2f5b8c',
        text: `Proteger profundidade de mix em ${firstSegment} e ${secondSegment} nas UNEs de maior peso comercial.`,
      },
      {
        title: 'Compradores',
        bg: '#f7ecd0',
        fg: '#93660e',
        text: `Atuar primeiro sobre ${formatInt(data().summary.critical_coverage_skus)} SKUs em cobertura crítica, ruptura vendendo e transferência disponível.`,
      },
      {
        title: 'Operação',
        bg: '#f8e1dd',
        fg: '#b1493f',
        text: opportunity
          ? `Priorizar ${segmentAlias(opportunity.segmento)} na UNE ${opportunity.une} e revisar execução local nas demais UNEs líderes.`
          : 'Priorizar os combos de maior receita com ruptura elevada.',
      },
    ];
  });

  const executiveSummaryParagraphs = createMemo(() => {
    const opportunity = topOpportunity();
    const firstSegment = topSegments()[0] || 'os segmentos líderes';
    const secondSegment = topSegments()[1] || 'as demais frentes de maior representatividade';

    if (opportunity) {
      return [
        `Leitura de atualização diária baseada na janela móvel dos últimos 30 dias. No recorte atual, a rede registra R$ ${formatMi(data().summary.revenue_30d_mi)} mi de receita, com R$ ${formatMi(data().summary.revenue_at_risk_mi)} mi expostos por indisponibilidade e ${formatInt(data().summary.critical_coverage_skus)} SKUs em cobertura crítica.`,
        `A concentração comercial permanece em ${firstSegment} e ${secondSegment}, enquanto o principal desvio observável está em ${segmentAlias(opportunity.segmento)} na UNE ${opportunity.une}, combinando R$ ${formatMi(opportunity.revenue_mi)} mi com ruptura de ${formatPct(opportunity.ruptura_pct)}.`,
        `Esta síntese deve ser revisada diariamente, e não apenas no fechamento mensal, para sustentar a priorização do BI junto às áreas parceiras.`,
        `Como alavanca de curto prazo, o painel aponta ${formatInt(data().summary.transferable_skus)} SKUs com possibilidade de transferência e indica que os 100 itens de maior peso concentram ${formatPct(data().summary.abc_top_100_share_pct)} da receita.`,
        `Para o BI, isso reforça a necessidade de separar o que é desvio estrutural de mix, o que é ruptura recorrente e o que pode ser resolvido com reequilíbrio entre UNEs.`,
      ];
    }

    return [
      `Leitura de atualização diária baseada na janela móvel dos últimos 30 dias. No recorte atual, a rede registra R$ ${formatMi(data().summary.revenue_30d_mi)} mi de receita, com R$ ${formatMi(data().summary.revenue_at_risk_mi)} mi expostos por indisponibilidade e ${formatInt(data().summary.critical_coverage_skus)} SKUs em cobertura crítica.`,
      `A concentração comercial permanece em ${firstSegment} e ${secondSegment}.`,
      `Esta síntese deve ser revisada diariamente, e não apenas no fechamento mensal, para sustentar a priorização do BI junto às áreas parceiras.`,
      `Como alavanca de curto prazo, o painel aponta ${formatInt(data().summary.transferable_skus)} SKUs com possibilidade de transferência e indica que os 100 itens de maior peso concentram ${formatPct(data().summary.abc_top_100_share_pct)} da receita.`,
      `Para o BI, isso reforça a necessidade de separar o que é desvio estrutural de mix, o que é ruptura recorrente e o que pode ser resolvido com reequilíbrio entre UNEs.`,
    ];
  });

  const curvePoints = createMemo(() => {
    const points = [
      { label: '0,1%', x: 0.18, y: data().abc.top_10_pct },
      { label: '0,5%', x: 0.38, y: data().abc.top_50_pct },
      { label: '1%', x: 0.54, y: data().abc.top_100_pct },
      { label: '5%', x: 0.78, y: data().abc.top_500_pct },
      { label: '100%', x: 1, y: 100 },
    ];

    return points.map((point) => ({
      ...point,
      px: 30 + point.x * 470,
      py: 250 - (point.y / 100) * 190,
    }));
  });

  const normalizedStores = createMemo(() =>
    (stores() || []).map((store) => ({
      une: String(store.une ?? store.UNE ?? ''),
      nome: String(store.nome ?? store.NOME ?? `UNE ${store.une ?? store.UNE ?? ''}`),
    }))
  );

  const resetFilters = () => {
    setSelectedSegment('');
    setSelectedUne('');
  };

  const openDrilldown = (target: 'rupturas' | 'suppliers' | 'forecasting' | 'transfers', segment?: string, une?: string) => {
    const params = new URLSearchParams();
    if (segment) params.set('segmento', segment);
    if (une) params.set('une', une);
    const qs = params.toString();
    navigate(`/${target}${qs ? `?${qs}` : ''}`);
  };

  return (
    <div class="min-h-full w-full overflow-x-hidden bg-[#f6f5ef] text-[#20322a]">
      <div class="mx-auto grid max-w-[1800px] gap-[1.125rem] pb-6">
        <section class="rounded-[2rem] border border-[#d8ddd7] bg-white px-5 py-5 shadow-sm">
          <div class="rounded-[1.75rem] border border-[#ebece6] bg-[#fbfbf8] px-6 py-5">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div class="flex-1">
                <div class="mb-3 flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-[#e6f0ea] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#1e6b4c]">
                    Gestão orientada por dados
                  </span>
                  <span class="rounded-full bg-[#f7ecd0] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#93660e]">
                    Comercial e abastecimento
                  </span>
                  <span class="rounded-full bg-[#e8eff7] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#2f5b8c]">
                    Base operacional da rede
                  </span>
                </div>
                <h1 class="text-[2.25rem] font-black tracking-tight text-[#20322a]">Painel corporativo de monitoramento BI</h1>
                <p class="mt-2 max-w-5xl text-sm leading-7 text-[#66756d]">
                  Visão consolidada da rede Lojas Caçula para acompanhamento de desempenho, risco comercial, abastecimento e
                  prioridades de execução, com acesso direto aos recortes analíticos de aprofundamento.
                </p>
                <div class="mt-4 rounded-full bg-[#f4f1e5] px-4 py-2 text-[12px] font-semibold text-[#6b624a]">
                  Escopo ativo: <span class="text-[#20322a]">{scopeLabel()}</span>
                </div>
              </div>

              <div class="min-w-[18rem] rounded-[1.5rem] bg-[#f8f7f2] px-4 py-4">
                <div class="text-sm font-bold text-[#1e6b4c]">Rotina BI</div>
                <div class="mt-2 text-[13px] leading-6 text-[#66756d]">
                  1. Consolidar o desempenho da rede
                  <br />
                  2. Avaliar risco comercial e ruptura
                  <br />
                  3. Definir prioridades de atuação
                  <br />
                  4. Comunicar encaminhamentos
                </div>
                <div class="mt-3 text-[12px] text-[#66756d]">• Base de referência: 31/03/2026</div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-[1.5rem] border border-[#d8ddd7] bg-white px-4 py-3 shadow-sm">
          <div class="flex flex-col gap-3">
            <span class="rounded-full bg-[#e6f0ea] px-3 py-1 text-[12px] font-semibold text-[#1e6b4c] xl:self-start">
              Objetivo: orientar comercial, stakeholders, compradores e operação.
            </span>
            <div class="flex flex-wrap items-center gap-3">
              <For
                each={[
                  ['Período', 'Últimos 30 dias'],
                  ['Modo', 'Janela móvel + tendência mensal'],
                  ['Escopo', scopeLabel()],
                  ['Recorte', 'Segmento + UNE'],
                  ['Período parcial', 'Somente na tendência'],
                ]}
              >
                {([label, value]) => (
                  <span class="rounded-full bg-[#f4f1e5] px-3 py-1 text-[12px] font-semibold text-[#6b624a]">
                    {label}: <span class="text-[#20322a]">{value}</span>
                  </span>
                )}
              </For>
            </div>
          </div>

          <div class="mt-4 grid gap-3 xl:grid-cols-[minmax(0,18rem)_minmax(0,18rem)_auto_minmax(0,1fr)] xl:items-end">
            <label class="grid gap-1.5 text-[12px] font-semibold text-[#66756d]">
              Segmento
              <select
                data-testid="dashboard-segment-filter"
                class="h-[3rem] rounded-2xl border border-[#d8ddd7] bg-[#fcfcfa] px-3 text-sm text-[#20322a] outline-none focus:border-[#1e6b4c]"
                value={selectedSegment()}
                onInput={(event) => setSelectedSegment(event.currentTarget.value)}
              >
                <option value="">Todos os segmentos</option>
                <For each={normalizedSegments()}>
                  {(segment) => <option value={segment}>{segmentAlias(segment)}</option>}
                </For>
              </select>
            </label>

            <label class="grid gap-1.5 text-[12px] font-semibold text-[#66756d]">
              UNE
              <select
                data-testid="dashboard-une-filter"
                class="h-[3rem] rounded-2xl border border-[#d8ddd7] bg-[#fcfcfa] px-3 text-sm text-[#20322a] outline-none focus:border-[#1e6b4c]"
                value={selectedUne()}
                onInput={(event) => setSelectedUne(event.currentTarget.value)}
              >
                <option value="">Todas as UNEs</option>
                <For each={normalizedStores()}>
                  {(store) => <option value={store.une}>{store.nome}</option>}
                </For>
              </select>
            </label>

            <button
              type="button"
              data-testid="dashboard-clear-filters"
              class="h-[3rem] rounded-2xl border border-[#d8ddd7] bg-white px-4 text-sm font-semibold text-[#20322a] transition hover:border-[#1e6b4c] hover:text-[#1e6b4c] xl:self-end"
              onClick={resetFilters}
            >
              Limpar filtros
            </button>

            <div class="grid gap-2 sm:grid-cols-2 xl:self-end xl:grid-cols-4 xl:justify-end">
              <button
                type="button"
                class="h-[3rem] rounded-2xl bg-[#e6f0ea] px-4 text-sm font-semibold text-[#1e6b4c] transition hover:brightness-95"
                onClick={() => openDrilldown('rupturas', selectedSegment() || undefined, selectedUne() || undefined)}
              >
                Abrir Rupturas
              </button>
              <button
                type="button"
                class="h-[3rem] rounded-2xl bg-[#e8eff7] px-4 text-sm font-semibold text-[#2f5b8c] transition hover:brightness-95"
                onClick={() => openDrilldown('suppliers', selectedSegment() || undefined)}
              >
                Abrir Fornecedores
              </button>
              <button
                type="button"
                class="h-[3rem] rounded-2xl bg-[#f7ecd0] px-4 text-sm font-semibold text-[#93660e] transition hover:brightness-95"
                onClick={() => openDrilldown('forecasting', selectedSegment() || undefined)}
              >
                Abrir Previsão
              </button>
              <button
                type="button"
                class="h-[3rem] rounded-2xl bg-[#f4f1e5] px-4 text-sm font-semibold text-[#6b624a] transition hover:brightness-95"
                onClick={() => openDrilldown('transfers', selectedSegment() || undefined, selectedUne() || undefined)}
              >
                Abrir Transferências
              </button>
            </div>
          </div>
        </section>

        <Show
          when={!overview.loading}
          fallback={
            <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              <For each={Array.from({ length: 6 })}>{() => <SkeletonCard />}</For>
            </section>
          }
        >
          <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6" data-testid="dashboard-kpis">
            <KpiCard
              title="Receita 30d"
              value={`R$ ${formatMi(data().summary.revenue_30d_mi)} mi`}
              note="motor comercial"
              accent="#1e6b4c"
              tint="#e6f0ea"
            />
            <KpiCard
              title="Margem média"
              value={formatPct(data().summary.margin_avg_pct)}
              note="qualidade da venda"
              accent="#2f5b8c"
              tint="#e8eff7"
            />
            <KpiCard
              title="Cobertura crítica"
              value={formatInt(data().summary.critical_coverage_skus)}
              note="<= 50% linha verde"
              accent="#b1493f"
              tint="#f8e1dd"
            />
            <KpiCard
              title="Ruptura vendendo"
              value={formatInt(data().summary.selling_rupture_skus)}
              note="estoque zero com venda"
              accent="#a74637"
              tint="#fcefe8"
            />
            <KpiCard
              title="Transferíveis"
              value={formatInt(data().summary.transferable_skus)}
              note="CD abastece loja"
              accent="#93660e"
              tint="#f7ecd0"
            />
            <KpiCard
              title="Receita em risco"
              value={`R$ ${formatMi(data().summary.revenue_at_risk_mi)} mi`}
              note="perda potencial capturável"
              accent="#7b6c3e"
              tint="#f4f1e5"
            />
          </section>

          <section class="grid gap-[1.125rem]">
            <Panel title="Heatmap UNE x segmento" subtitle="Receita dos últimos 30 dias por célula, com cor orientada pela ruptura.">
            
              <div class="flex h-full min-h-0 flex-col gap-5">
                <div class="custom-scrollbar max-h-[31rem] overflow-auto pb-3 pr-1">
                  <div class="min-w-full">
                    <div class="grid min-w-full gap-2" style={{ 'grid-template-columns': heatmapGridTemplate() }}>
                      <div />
                      <For each={data().heatmap.segments}>
                        {(segment) => (
                          <div class="min-w-0 px-1 text-center text-[9px] font-bold uppercase leading-4 tracking-[0.1em] text-[#66756d]">
                            {segmentAlias(segment)}
                          </div>
                        )}
                      </For>

                      <For each={data().heatmap.unes}>
                        {(une) => (
                          <>
                            <div class="flex items-center text-[11px] font-bold text-[#20322a]">UNE {une}</div>
                            <For each={data().heatmap.segments}>
                              {(segment) => {
                                const cell = createMemo(() => heatmapMap().get(`${une}:${segment}`));
                                const tint = () => {
                                  const rupture = cell()?.ruptura_pct || 0;
                                  if (rupture >= 35) return ['#f8e1dd', '#b1493f'];
                                  if (rupture >= 30) return ['#f7ecd0', '#93660e'];
                                  return ['#e6f0ea', '#1e6b4c'];
                                };

                                return (
                                  <div
                                    class="min-w-0 rounded-[1rem] px-1.5 py-2"
                                    style={{ background: tint()[0], color: tint()[1] }}
                                  >
                                    <div class="truncate text-[10px] font-black text-[#20322a]">R$ {formatMi(cell()?.receita_mi || 0)}</div>
                                    <div class="mt-1 truncate text-[9px] font-semibold">{formatPct(cell()?.ruptura_pct || 0)} rup</div>
                                  </div>
                                );
                              }}
                            </For>
                          </>
                        )}
                      </For>
                    </div>
                  </div>
                </div>

                <div class="rounded-[1.25rem] bg-[#f8f7f2] px-4 py-4 text-sm leading-7 text-[#20322a]">
                  Calor principal: {data().opportunities.slice(0, 3).map((item) => `${segmentAlias(item.segmento)} na UNE ${item.une}`).join(', ')}.
                </div>
              </div>
            </Panel>
          </section>

          <section class="grid items-stretch gap-[1.125rem] xl:grid-cols-3">
            <Panel title="Tendência e captura" subtitle="Comparativo entre meses fechados e o mês atual apresentado de forma parcial.">
              <div class="custom-scrollbar flex h-full min-h-0 flex-col gap-5 overflow-auto pr-1 xl:max-h-[35rem]">
                <div class="grid min-h-[16rem] grid-cols-4 items-end gap-4 rounded-[1.5rem] bg-[#fcfcfa] px-4 pb-4 pt-6">
                  <For each={data().period_trend}>
                    {(item) => (
                      <div class="flex flex-col items-center gap-2">
                        <div class="text-[11px] font-semibold text-[#66756d]">R$ {formatMi(item.value_mi)} mi</div>
                        <div class="flex h-44 items-end">
                          <div
                            class={`w-14 rounded-t-2xl ${item.is_partial ? 'bg-[#d9a441]' : 'bg-[#2e8b57]'}`}
                            style={{ height: `${Math.max((item.value_mi / maxTrend()) * 11, 2)}rem` }}
                          >
                            <Show when={item.is_partial}>
                              <div class="flex h-full flex-col justify-evenly px-2 py-2">
                                <div class="h-1 rounded-full bg-[#f9e3a9]" />
                                <div class="h-1 rounded-full bg-[#f9e3a9]" />
                                <div class="h-1 rounded-full bg-[#f9e3a9]" />
                                <div class="h-1 rounded-full bg-[#f9e3a9]" />
                              </div>
                            </Show>
                          </div>
                        </div>
                        <div class="text-center text-[11px] font-bold leading-5 text-[#66756d]">{trendLabelDisplay(item.label)}</div>
                      </div>
                    )}
                  </For>
                </div>

                <div class="rounded-[1.5rem] bg-[#f8f7f2] px-4 py-4">
                  <div class="mb-3 text-sm font-bold">Receita capturada x receita em risco</div>
                  <div class="h-7 overflow-hidden rounded-full bg-[#eaece8]">
                    <div class="flex h-full">
                      <div
                        class="h-full bg-[#2e8b57]"
                        style={{
                          width: `${(data().summary.captured_revenue_mi / Math.max(data().summary.revenue_30d_mi, 1)) * 100}%`,
                        }}
                      />
                      <div
                        class="h-full bg-[#b1493f]"
                        style={{
                          width: `${(data().summary.revenue_at_risk_mi / Math.max(data().summary.revenue_30d_mi, 1)) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div class="mt-3 flex flex-wrap gap-4 text-sm">
                    <span class="font-semibold text-[#1e6b4c]">Capturada R$ {formatMi(data().summary.captured_revenue_mi)} mi</span>
                    <span class="font-semibold text-[#b1493f]">Em risco R$ {formatMi(data().summary.revenue_at_risk_mi)} mi</span>
                    <span class="font-semibold text-[#7b6c3e]">Cobertura crítica R$ {formatMi(data().summary.critical_coverage_revenue_mi)} mi</span>
                  </div>
                </div>

                <div class="rounded-[1.25rem] bg-[#f8f7f2] px-4 py-4 text-sm leading-7 text-[#20322a]">
                  Leitura BI: neste card, `Mês -3` e `Mês -2` representam os meses fechados anteriores, `Último mês fechado`
                  corresponde ao fechamento mensal mais recente, e `Mês atual parcial` mostra apenas o acumulado do mês em curso.
                </div>
              </div>
            </Panel>

            <Panel title="ABC e concentração por segmento" subtitle="Concentração da receita na janela móvel dos últimos 30 dias.">
              <div class="custom-scrollbar flex h-full min-h-0 flex-col gap-5 overflow-auto pr-1 xl:max-h-[35rem]">
                <div class="overflow-hidden rounded-[1.5rem] bg-[#fcfcfa] px-3 py-4">
                  <svg viewBox="0 0 540 280" class="h-[17rem] w-full">
                    <line x1="30" y1="250" x2="500" y2="250" stroke="#d8ddd7" stroke-width="2" />
                    <line x1="30" y1="40" x2="30" y2="250" stroke="#d8ddd7" stroke-width="2" />
                    <polyline
                      fill="none"
                      stroke="#2f5b8c"
                      stroke-width="4"
                      points={curvePoints()
                        .map((point) => `${point.px},${point.py}`)
                        .join(' ')}
                    />
                    <For each={curvePoints()}>
                      {(point) => (
                        <>
                          <circle cx={point.px} cy={point.py} r="4.5" fill="#2f5b8c" />
                          <Show when={point.label !== '100%'}>
                            <text x={point.px - 8} y={point.py - 14} font-size="10" fill="#66756d">
                              {point.label}
                            </text>
                            <text x={point.px + 8} y={point.py - 2} font-size="11" fill="#20322a">
                              {formatPct(point.y)}
                            </text>
                          </Show>
                        </>
                      )}
                    </For>
                  </svg>
                </div>

                <div class="grid gap-3">
                  <For each={data().segment_share}>
                    {(segment) => (
                      <div class="grid grid-cols-[7.5rem_1fr_3.5rem] items-center gap-3">
                        <div class="text-sm font-semibold text-[#20322a]">{segmentAlias(segment.segmento)}</div>
                        <div class="h-3 overflow-hidden rounded-full bg-[#eef1ed]">
                          <div class="h-full rounded-full bg-[#2f5b8c]" style={{ width: `${Math.min(segment.share_receita_pct, 100)}%` }} />
                        </div>
                        <div class="text-right text-[12px] font-bold text-[#20322a]">{formatPct(segment.share_receita_pct)}</div>
                      </div>
                    )}
                  </For>
                </div>

                <div class="rounded-[1.25rem] bg-[#f8f7f2] px-4 py-4 text-sm leading-7 text-[#20322a]">
                  Leitura BI: top 100 SKUs somam {formatPct(data().summary.abc_top_100_share_pct)} da receita na janela móvel dos
                  últimos 30 dias. A análise não representa fechamento mensal calendário.
                </div>
              </div>
            </Panel>

            <Panel title="Oportunidades e drilldown" subtitle="Combos UNE x segmento priorizados com base nos últimos 30 dias.">
              <div class="custom-scrollbar flex h-full min-h-0 flex-col gap-5 overflow-auto pr-1 xl:max-h-[35rem]">
                <div class="grid gap-3">
                  <For each={data().opportunities}>
                    {(item) => {
                      const isCritical = item.ruptura_pct >= 33;
                        return (
                        <article
                          class="cursor-pointer rounded-[1.25rem] border border-[#d8ddd7] bg-[#fcfcfa] px-4 py-4 transition hover:border-[#1e6b4c]"
                          onClick={() => openDrilldown('rupturas', item.segmento, item.une)}
                        >
                          <div class="flex items-start justify-between gap-3">
                            <div>
                              <span
                                class="inline-block rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em]"
                                style={{
                                  background: isCritical ? '#f8e1dd' : '#e6f0ea',
                                  color: isCritical ? '#b1493f' : '#1e6b4c',
                                }}
                              >
                                UNE {item.une}
                              </span>
                              <div class="mt-3 text-sm font-bold text-[#20322a]">{segmentAlias(item.segmento)}</div>
                            </div>
                            <div class="text-right">
                              <div class="text-sm font-black text-[#20322a]">R$ {formatMi(item.revenue_mi)} mi</div>
                              <div
                                class="mt-2 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em]"
                                style={{
                                  background: isCritical ? '#f8e1dd' : '#f7ecd0',
                                  color: isCritical ? '#b1493f' : '#93660e',
                                }}
                              >
                                {formatPct(item.ruptura_pct)} rup
                              </div>
                            </div>
                          </div>
                        </article>
                      );
                    }}
                  </For>
                </div>

                <div class="rounded-[1.25rem] bg-[#f8f7f2] px-4 py-4">
                  <div class="mb-3 text-sm font-bold">Cortes sugeridos para abrir no produto</div>
                  <div class="grid gap-2 text-sm text-[#20322a]">
                    <For each={data().opportunities.slice(0, 4)}>
                      {(item, index) => (
                        <button
                          type="button"
                          class="flex items-start gap-3 text-left transition hover:text-[#1e6b4c]"
                          onClick={() => openDrilldown('rupturas', item.segmento, item.une)}
                        >
                          <span class="mt-1 h-2.5 w-2.5 rounded-full bg-[#1e6b4c]" />
                          <span>
                            {index() + 1}. Segmento &gt; {segmentAlias(item.segmento)} | UNE &gt; {item.une}
                          </span>
                        </button>
                      )}
                    </For>
                  </div>
                </div>
              </div>
            </Panel>
          </section>

          <section class="grid items-stretch gap-[1.125rem] xl:grid-cols-3">
            <Panel title="Agenda diária do BI" subtitle="Ritual da manhã com ordem clara de leitura e ação.">
              <div class="custom-scrollbar flex h-full min-h-0 flex-col gap-3 overflow-auto pr-1 xl:max-h-[35rem]">
                <For each={agenda()}>
                  {(item, index) => (
                    <article class="rounded-[1.25rem] border border-[#d8ddd7] bg-[#fcfcfa] px-4 py-4">
                      <div class="flex items-start gap-3">
                        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#1e6b4c] text-sm font-black text-white">
                          {index() + 1}
                        </div>
                        <div>
                          <div class="text-sm font-black text-[#20322a]">{item.title}</div>
                          <p class="mt-1 text-[13px] leading-6 text-[#66756d]">{item.text}</p>
                        </div>
                      </div>
                    </article>
                  )}
                </For>

                <div class="rounded-[1.25rem] border border-[#d8ddd7] bg-[#f8f7f2] px-4 py-4 text-sm leading-7 text-[#20322a]">
                  Prioridade final do dia: capturar receita em risco sem perder profundidade de mix nos segmentos líderes.
                </div>
              </div>
            </Panel>

            <Panel title="Tradução por público" subtitle="A mesma leitura entregue na linguagem certa para cada área.">
              <div class="custom-scrollbar grid min-h-0 gap-4 overflow-auto pr-1 xl:max-h-[35rem]">
                <For each={audienceCards()}>
                  {(card) => (
                    <article class="rounded-[1.25rem] border border-[#d8ddd7] bg-[#fcfcfa] px-4 py-4">
                      <span class="inline-block rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em]" style={{ background: card.bg, color: card.fg }}>
                        {card.title}
                      </span>
                      <p class="mt-4 text-sm leading-7 text-[#20322a]">{card.text}</p>
                    </article>
                  )}
                </For>
              </div>
            </Panel>

            <Panel
              title="Síntese executiva"
              subtitle="Leitura gerencial diária para fechamento da análise."
              dark
            >
              <div class="text-sm leading-7 text-white/85">
                <For each={executiveSummaryParagraphs()}>
                  {(paragraph, index) => (
                    <p class={index() === 0 ? 'text-sm leading-7 text-white/85' : 'mt-4 text-sm leading-7 text-white/85'}>
                      {paragraph}
                    </p>
                  )}
                </For>
              </div>
            </Panel>
          </section>
        </Show>

        <Show when={overview.error}>
          <div class="rounded-[1.5rem] border border-[#f0b7b1] bg-[#fff4f2] px-5 py-4 text-sm text-[#8b3a33]">
            Não foi possível carregar o dashboard mestre. Verifique a integração com os dados e tente novamente.
          </div>
        </Show>
      </div>
    </div>
  );
}
