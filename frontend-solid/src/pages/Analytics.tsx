import { createSignal, onMount, Show, createResource, For, createEffect, createMemo, onCleanup, on } from 'solid-js';
import { BarChart3, TrendingUp, RefreshCw, Filter, X, Download, Eye } from 'lucide-solid';
import api, { analyticsApi, ABCDetailItem } from '../lib/api'; // Import analyticsApi and ABCDetailItem
import { PlotlyChart } from '../components/PlotlyChart';
import { ChartDownloadButton } from '../components/ChartDownloadButton';
import { ErrorBoundary } from '../components/ErrorBoundary';

interface SalesAnalysis {
  vendas_por_categoria: Array<{
    categoria: string;
    vendas: number;
  }>;
  chart_title?: string;
  giro_estoque: Array<{
    produto: string;
    nome: string;
    giro: number;
  }>;
  distribuicao_abc: {
    A: number;
    B: number;
    C: number;
    detalhes: Array<{
      PRODUTO: number;
      NOME: string;
      receita: number;
      perc_acumulada: number;
      classe: string;
    }>;
    receita_por_classe?: Record<string, number>;
  };
}

interface FilterOptions {
  categorias: string[];
  segmentos: string[];
  grupos: string[];
}

export default function Analytics() {
  const [data, setData] = createSignal<SalesAnalysis | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);
  const [abortController, setAbortController] = createSignal<AbortController | null>(null);

  // Filtros
  const [categoria, setCategoria] = createSignal('');
  const [segmento, setSegmento] = createSignal('');
  const [grupo, setGrupo] = createSignal('');

  // Modal ABC Details
  const [showABCModal, setShowABCModal] = createSignal(false);
  const [selectedClasse, setSelectedClasse] = createSignal<'A' | 'B' | 'C' | null>(null);
  const [abcDetails, setAbcDetails] = createSignal<ABCDetailItem[]>([]);
  const [loadingABC, setLoadingABC] = createSignal(false);

  // ✅ PERFORMANCE: Paginação para tabela ABC (evita renderizar centenas de linhas)
  const [abcPage, setAbcPage] = createSignal(1);
  const abcItemsPerPage = 50;
  const paginatedAbcDetails = createMemo(() => {
    const start = (abcPage() - 1) * abcItemsPerPage;
    const end = start + abcItemsPerPage;
    return abcDetails().slice(start, end);
  });
  const abcTotalPages = createMemo(() => Math.ceil(abcDetails().length / abcItemsPerPage));

  // Carregar opções de filtro (segmentos e todas as categorias)
  const [allFilterOptions] = createResource<FilterOptions>(async () => {
    const response = await analyticsApi.getFilterOptions();
    return response.data;
  });

  // Carregar categorias filtradas por segmento
  const [filteredCategoryOptions] = createResource(() => segmento(), async (seg) => {
    if (seg === '') {
      return allFilterOptions()?.categorias || [];
    }
    const response = await analyticsApi.getFilterOptions(seg);
    return response.data.categorias;
  });

  // Carregar grupos filtrados por segmento e categoria
  const [filteredGroupOptions] = createResource(() => ({ seg: segmento(), cat: categoria() }), async ({ seg, cat }) => {
    if (seg === '' && cat === '') {
      return allFilterOptions()?.grupos || [];
    }
    const response = await analyticsApi.getFilterOptions(seg || undefined, cat || undefined);
    return response.data.grupos;
  });

  // Efeito para resetar categoria quando o segmento muda (só quando já tinha um valor)
  createEffect((prevSegmento) => {
    const currentSegmento = segmento();
    if (prevSegmento !== undefined && prevSegmento !== currentSegmento) {
      setCategoria('');
      setGrupo('');
    }
    return currentSegmento;
  });

  // Efeito para resetar grupo quando a categoria muda (só quando já tinha um valor)
  createEffect((prevCategoria) => {
    const currentCategoria = categoria();
    if (prevCategoria !== undefined && prevCategoria !== currentCategoria) {
      setGrupo('');
    }
    return currentCategoria;
  });

  // ✅ UX: Auto-refresh quando filtros mudam (Debounced)
  // Usamos 'on' para rastrear APENAS os filtros e ignorar loading(), evitando loops
  createEffect(on([segmento, categoria, grupo], () => {
    // Evita recarregar se já estiver carregando
    if (!loading()) {
      const timer = setTimeout(() => {
        loadData();
      }, 800);
      onCleanup(() => clearTimeout(timer));
    }
  }, { defer: true })); // defer: true evita rodar na primeira montagem (conflito com onMount)

  // ✅ PERFORMANCE: Reset página quando dados ABC mudam
  createEffect(() => {
    abcDetails(); // Track changes
    setAbcPage(1); // Reset to first page
  });

  // Chart specs
  const [vendasCategoriaChart, setVendasCategoriaChart] = createSignal<any>({});
  const [giroEstoqueChart, setGiroEstoqueChart] = createSignal<any>({});
  const [distribuicaoABCChart, setDistribuicaoABCChart] = createSignal<any>({});

  const loadData = async () => {
    // Aborta qualquer requisição anterior para evitar condições de corrida
    abortController()?.abort();
    const newController = new AbortController();
    setAbortController(newController);

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (categoria()) params.append('categoria', categoria());
      if (segmento()) params.append('segmento', segmento());
      if (grupo()) params.append('grupo', grupo());

      const response = await api.get<SalesAnalysis>(`/analytics/sales-analysis?${params.toString()}`, {
        signal: newController.signal // Passa o sinal para a requisição
      });
      setData(response.data);

      // Gerar gráficos
      generateCharts(response.data);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Requisição de análise de vendas abortada.');
        return; // Não define erro para requisições abortadas
      }
      console.error('Erro ao carregar análise:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar análise de vendas');
    } finally {
      setLoading(false);
      // Limpa o controller se esta for a requisição mais recente
      if (abortController() === newController) {
        setAbortController(null);
      }
    }
  };

  // Carregar detalhes ABC ao clicar em uma classe
  const handleABCClick = async (classe: 'A' | 'B' | 'C') => {
    setSelectedClasse(classe);
    setShowABCModal(true);
    setLoadingABC(true);

    try {
      const response = await analyticsApi.getABCDetails(
        classe,
        segmento() || undefined,
        categoria() || undefined,
        grupo() || undefined
      );
      setAbcDetails(response.data);
    } catch (err: any) {
      console.error('Erro ao carregar detalhes ABC:', err);
      setAbcDetails([]);
    } finally {
      setLoadingABC(false);
    }
  };

  // Download CSV dos SKUs
  const downloadABCCSV = () => {
    const details = abcDetails();
    if (details.length === 0) return;

    const headers = ['PRODUTO', 'NOME', 'UNE', 'UNE_NOME', 'RECEITA', 'PERC_ACUMULADA', 'CLASSE'];
    const rows = details.map(item => [
      item.PRODUTO,
      item.NOME,
      item.UNE,
      item.UNE_NOME || '',
      item.receita.toFixed(2),
      item.perc_acumulada.toFixed(2),
      item.classe
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `abc_classe_${selectedClasse()}_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  const generateCharts = (analysisData: SalesAnalysis) => {
    // 1. LOJAS CAÇULA - LIGHT THEME: Vendas por Categoria
    if (analysisData.vendas_por_categoria.length > 0) {
      const vendasSpec = {
        data: [{
          type: 'bar',
          x: analysisData.vendas_por_categoria.map(c => c.categoria),
          y: analysisData.vendas_por_categoria.map(c => c.vendas),
          marker: {
            color: '#8B7355', // Marrom Caçula
            line: { color: '#E5E5E5', width: 1 }
          },
          text: analysisData.vendas_por_categoria.map(c => c.vendas.toLocaleString()),
          textposition: 'outside',
          textfont: { color: '#2D2D2D', family: 'Inter, sans-serif' },
          hovertemplate: '<b>%{x}</b><br>Vendas: %{y:,}<extra></extra>'
        }],
        layout: {
          title: {
            text: analysisData.chart_title || 'Vendas por Categoria (Top 10)',
            font: { size: 16, color: '#2D2D2D', family: 'Inter, sans-serif' }
          },
          xaxis: {
            title: '',
            tickangle: -45,
            tickfont: { size: 10, color: '#6B6B6B', family: 'Inter, sans-serif' },
            gridcolor: '#E5E5E5',
            linecolor: '#E5E5E5'
          },
          yaxis: {
            title: 'Vendas (30 dias)',
            titlefont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
            tickfont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
            gridcolor: '#E5E5E5',
            linecolor: '#E5E5E5'
          },
          plot_bgcolor: '#FFFFFF',
          paper_bgcolor: '#FAFAFA',
          margin: { l: 60, r: 20, t: 60, b: 100 },
          font: { color: '#2D2D2D', family: 'Inter, sans-serif' }
        },
        config: { responsive: true }
      };
      setVendasCategoriaChart(vendasSpec);
    }

    // 2. LOJAS CAÇULA - LIGHT THEME: Giro de Estoque (Velocity Scatter)
    if (analysisData.giro_estoque.length > 0) {
      // Color Logic for Velocity
      const colors = analysisData.giro_estoque.map(p => {
        if (p.giro >= 1.0) return '#166534'; // Green (Fast)
        if (p.giro >= 0.5) return '#CA8A04'; // Yellow (Medium)
        return '#991B1B'; // Red (Slow/Risk)
      });

      const maxGiro = Math.max(...analysisData.giro_estoque.map(p => p.giro), 1.2); // Ensure plot shows at least 1.2

      const giroSpec = {
        data: [{
          type: 'scatter',
          mode: 'markers',
          x: analysisData.giro_estoque.map((_, i) => i + 1),
          y: analysisData.giro_estoque.map(p => p.giro),
          text: analysisData.giro_estoque.map(p => p.nome),
          marker: {
            color: colors,
            size: 14,
            line: { color: '#FFFFFF', width: 2 },
            opacity: 0.9,
            symbol: 'circle'
          },
          hovertemplate: '<b>%{text}</b><br>Ranking: #%{x}<br>Giro: %{y:.2f}x/mês<br><i>%{customdata}</i><extra></extra>',
          customdata: analysisData.giro_estoque.map(p =>
            p.giro >= 1.0 ? 'Alta Rotatividade 🚀' :
              p.giro >= 0.5 ? 'Giro Moderado ⚖️' : 'Giro Lento ⚠️'
          )
        }],
        layout: {
          title: {
            text: '<b>Velocidade do Estoque</b> (Giro/Mês)',
            font: { size: 16, color: '#2D2D2D', family: 'Inter, sans-serif' }
          },
          xaxis: {
            title: 'Ranking de Vendas',
            titlefont: { size: 12, color: '#6B6B6B' },
            tickfont: { color: '#6B6B6B' },
            gridcolor: '#F1F5F9',
            showgrid: false
          },
          yaxis: {
            title: 'Giro Mensal',
            titlefont: { size: 12, color: '#6B6B6B' },
            tickfont: { color: '#6B6B6B' },
            gridcolor: '#F1F5F9',
            zeroline: true,
            range: [0, maxGiro * 1.1] // Dynamic padding
          },
          plot_bgcolor: '#FFFFFF',
          paper_bgcolor: '#FAFAFA',
          margin: { l: 60, r: 20, t: 60, b: 60 },
          shapes: [
            // Benchmark Line (1.0)
            {
              type: 'line',
              x0: 0, x1: 1, xref: 'paper',
              y0: 1.0, y1: 1.0, yref: 'y',
              line: { color: '#166534', width: 2, dash: 'dot', opacity: 0.6 },
              label: { text: 'Meta (1.0)', textposition: 'end', font: { size: 10, color: '#166534' } }
            },
            // Danger Zone (< 0.5)
            {
              type: 'rect',
              x0: 0, x1: 1, xref: 'paper',
              y0: 0, y1: 0.5, yref: 'y',
              fillcolor: 'rgba(220, 38, 38, 0.05)',
              line: { width: 0 },
              layer: 'below'
            }
          ]
        },
        config: { responsive: true, displayModeBar: false }
      };
      setGiroEstoqueChart(giroSpec);
    }

    // 3. LOJAS CAÇULA - GRÁFICO DE PARETO REAL (Zoned ABC)
    const abc = analysisData.distribuicao_abc;
    if (abc.detalhes && abc.detalhes.length > 0) {
      // Limitar aos top 25 produtos para melhor visualização
      const topProducts = abc.detalhes.slice(0, 25);

      // Calculate split indices for background zones
      const countA = topProducts.filter(p => p.classe === 'A').length;
      const countB = topProducts.filter(p => p.classe === 'B').length;
      const countC = topProducts.filter(p => p.classe === 'C').length;

      const paretoSpec = {
        data: [
          {
            type: 'bar',
            x: topProducts.map((p, i) => `${i + 1}. ${p.NOME.substring(0, 15)}`),
            y: topProducts.map(p => p.receita),
            name: 'Receita (R$)',
            marker: {
              color: topProducts.map(p =>
                p.classe === 'A' ? '#15803d' : (p.classe === 'B' ? '#d97706' : '#b91c1c')
              ),
              opacity: 0.9,
              /* Subtle gradient effect simulated with line */
              line: { color: 'rgba(255,255,255,0.3)', width: 1 }
            },
            hovertemplate: '<b>%{customdata.nome}</b><br>Receita: R$ %{y:,.2f}<br>Classe: %{customdata.classe}<br><i>%{customdata.action}</i><extra></extra>',
            customdata: topProducts.map(p => ({
              nome: p.NOME,
              classe: p.classe,
              action: p.classe === 'A' ? '🛡️ Blindar Estoque' : (p.classe === 'B' ? '⚖️ Monitorar' : '✂️ Racionalizar')
            }))
          },
          {
            type: 'scatter',
            mode: 'lines+markers',
            x: topProducts.map((p, i) => `${i + 1}. ${p.NOME.substring(0, 15)}`),
            y: topProducts.map(p => p.perc_acumulada),
            name: '% Acumulada',
            yaxis: 'y2',
            line: { color: '#334155', width: 2, shape: 'spline' },
            marker: { color: '#334155', size: 6, symbol: 'circle' },
            hovertemplate: 'Acumulado: %{y:.1f}%<extra></extra>'
          }
        ],
        layout: {
          title: {
            text: '<b>Curva de Pareto: Identificação de Prioridades</b>',
            font: { size: 16, color: '#0F172A', family: 'Inter, sans-serif' },
            x: 0.05
          },
          xaxis: {
            tickangle: -45,
            tickfont: { size: 9, color: '#64748B' },
            gridcolor: '#F1F5F9'
          },
          yaxis: {
            title: 'Receita (R$)',
            titlefont: { size: 11, color: '#64748B' },
            gridcolor: '#F1F5F9',
            showgrid: true
          },
          yaxis2: {
            title: '% Acumulada',
            titlefont: { size: 11, color: '#64748B' },
            overlaying: 'y',
            side: 'right',
            range: [0, 105],
            showgrid: false,
            tickfont: { size: 10, color: '#64748B' }
          },
          legend: {
            orientation: 'h',
            x: 0.5, y: -0.3,
            xanchor: 'center'
          },
          plot_bgcolor: '#FFFFFF',
          paper_bgcolor: '#FFFFFF',
          margin: { l: 60, r: 60, t: 80, b: 120 },
          shapes: [
            // Zone A Background
            {
              type: 'rect',
              xref: 'x', yref: 'paper',
              x0: -0.5, x1: countA - 0.5,
              y0: 0, y1: 1,
              fillcolor: 'rgba(22, 163, 74, 0.05)', // Green tint
              line: { width: 0 },
              layer: 'below'
            },
            // Zone B Background
            {
              type: 'rect',
              xref: 'x', yref: 'paper',
              x0: countA - 0.5, x1: countA + countB - 0.5,
              y0: 0, y1: 1,
              fillcolor: 'rgba(234, 179, 8, 0.05)', // Yellow tint
              line: { width: 0 },
              layer: 'below'
            },
            // Zone C Background
            {
              type: 'rect',
              xref: 'x', yref: 'paper',
              x0: countA + countB - 0.5, x1: topProducts.length - 0.5,
              y0: 0, y1: 1,
              fillcolor: 'rgba(220, 38, 38, 0.05)', // Red tint
              line: { width: 0 },
              layer: 'below'
            },
            // 80% Cutoff Line
            {
              type: 'line',
              xref: 'paper', yref: 'y2',
              x0: 0, x1: 1, y0: 80, y1: 80,
              line: { color: '#166534', width: 1, dash: 'dash' }
            }
          ],
          annotations: [
            {
              x: (countA - 1) / 2, y: 1.05, xref: 'x', yref: 'paper',
              text: 'CLASSE A', showarrow: false,
              font: { color: '#15803d', size: 10, weight: 'bold' }
            }
          ]
        },
        config: { responsive: true, displayModeBar: false }
      };
      setDistribuicaoABCChart(paretoSpec);
    }
  };

  onMount(() => {
    // Adiciona um pequeno atraso para a chamada inicial de loadData.
    // Isso permite que o createResource para allFilterOptions comece a carregar primeiro,
    // evitando que duas requisições pesadas atinjam o backend exatamente ao mesmo tempo.
    setTimeout(() => {
      loadData();
    }, 500);
  });

  return (
    <ErrorBoundary>
      <div class="flex flex-col p-6 gap-6">
        {/* Header */}
        <div class="flex justify-between items-end">
          <div>
            <h2 class="text-2xl font-bold flex items-center gap-2">
              <BarChart3 size={28} />
              Analytics Avançado
            </h2>
            <p class="text-muted">Análise de vendas, estoque e distribuição ABC</p>
          </div>
          <button
            onClick={loadData}
            class="btn btn-outline gap-2"
            disabled={loading()}
            aria-label={loading() ? 'Atualizando análise de vendas' : 'Atualizar análise de vendas'}
            aria-busy={loading()}
          >
            <RefreshCw size={16} class={loading() ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>

        {/* Filters */}
        <div class="card p-4 border" role="region" aria-label="Filtros de análise">
          <div class="flex items-center gap-2 mb-3">
            <Filter size={20} />
            <h3 class="font-semibold">Filtros</h3>
            <Show when={categoria() || segmento() || grupo()}>
              <button
                class="ml-auto text-sm text-muted hover:text-foreground flex items-center gap-1"
                onClick={() => {
                  setCategoria('');
                  setSegmento('');
                  setGrupo('');
                  loadData();
                }}
                aria-label="Limpar todos os filtros"
              >
                <X size={16} />
                Limpar Filtros
              </button>
            </Show>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Segmento */}
            {/* ✅ CORREÇÃO MOBILE: min-h-[44px] para touch-friendly */}
            <select
              class="input min-h-[44px]"
              value={segmento()}
              onChange={(e) => setSegmento(e.currentTarget.value)}
              disabled={allFilterOptions.loading}
              aria-label="Filtrar por segmento"
              aria-busy={allFilterOptions.loading}
            >
              <option value="">Todos os Segmentos</option>
              <Show when={allFilterOptions()}>
                <For each={allFilterOptions()!.segmentos}>
                  {(seg) => <option value={seg}>{seg}</option>}
                </For>
              </Show>
            </select>

            {/* Categoria (filtro dinâmico) */}
            <select
              class="input min-h-[44px]"
              value={categoria()}
              onChange={(e) => setCategoria(e.currentTarget.value)}
              disabled={filteredCategoryOptions.loading}
              aria-label="Filtrar por categoria"
              aria-busy={filteredCategoryOptions.loading}
            >
              <option value="">Todas as Categorias</option>
              <Show when={filteredCategoryOptions()}>
                <For each={filteredCategoryOptions()}>
                  {(cat) => <option value={cat}>{cat}</option>}
                </For>
              </Show>
            </select>

            {/* Grupo (filtro dinâmico) */}
            <select
              class="input min-h-[44px]"
              value={grupo()}
              onChange={(e) => setGrupo(e.currentTarget.value)}
              disabled={filteredGroupOptions.loading}
              aria-label="Filtrar por grupo"
              aria-busy={filteredGroupOptions.loading}
            >
              <option value="">Todos os Grupos</option>
              <Show when={filteredGroupOptions()}>
                <For each={filteredGroupOptions()}>
                  {(grp) => <option value={grp}>{grp}</option>}
                </For>
              </Show>
            </select>

            <button
              class="btn btn-primary min-h-[44px]"
              onClick={loadData}
              disabled={loading()}
              aria-label="Aplicar filtros selecionados"
              aria-busy={loading()}
            >
              Aplicar Filtros
            </button>
          </div>

          {/* Active Filters Display */}
          <Show when={categoria() || segmento() || grupo()}>
            <div class="flex gap-2 mt-3 flex-wrap">
              <span class="text-sm text-muted">Filtros ativos:</span>
              <Show when={segmento()}>
                <span class="px-2 py-1 bg-primary/20 text-primary rounded text-sm flex items-center gap-1">
                  Segmento: {segmento()}
                  <button
                    onClick={() => {
                      setSegmento('');
                      loadData();
                    }}
                    class="hover:bg-primary/30 rounded"
                    aria-label={`Remover filtro de segmento ${segmento()}`}
                  >
                    <X size={14} />
                  </button>
                </span>
              </Show>
              <Show when={categoria()}>
                <span class="px-2 py-1 bg-primary/20 text-primary rounded text-sm flex items-center gap-1">
                  Categoria: {categoria()}
                  <button
                    onClick={() => {
                      setCategoria('');
                      loadData();
                    }}
                    class="hover:bg-primary/30 rounded"
                    aria-label={`Remover filtro de categoria ${categoria()}`}
                  >
                    <X size={14} />
                  </button>
                </span>
              </Show>
              <Show when={grupo()}>
                <span class="px-2 py-1 bg-primary/20 text-primary rounded text-sm flex items-center gap-1">
                  Grupo: {grupo()}
                  <button
                    onClick={() => {
                      setGrupo('');
                      loadData();
                    }}
                    class="hover:bg-primary/30 rounded"
                    aria-label={`Remover filtro de grupo ${grupo()}`}
                  >
                    <X size={14} />
                  </button>
                </span>
              </Show>
            </div>
          </Show>
        </div>

        {/* Error State */}
        <Show when={error()}>
          <div class="card p-4 border-red-500 bg-red-500/10">
            <p class="text-red-500">{error()}</p>
          </div>
        </Show>

        {/* Loading State */}
        <Show when={loading()}>
          <div class="flex-1 flex items-center justify-center">
            <div class="text-center">
              <BarChart3 size={48} class="mx-auto mb-4 opacity-50 animate-pulse" />
              <p class="text-muted">Carregando análise...</p>
            </div>
          </div>
        </Show>

        {/* Charts Grid */}
        <Show when={!loading() && data()}>
          <div class="space-y-6">
            {/* Row 1: Vendas por Categoria */}
            <div class="card p-6 border" role="region" aria-label="Gráfico de vendas por categoria">
              <div class="flex justify-between items-center mb-4">
                <h3 class="font-semibold">{data()?.chart_title || "Vendas por Categoria (Top 10)"}</h3>
                <ChartDownloadButton
                  chartId="analytics-vendas-categoria-chart"
                  filename="analytics_vendas_categoria"
                  label="Baixar"
                />
              </div>
              <Show
                when={data()!.vendas_por_categoria.length > 0}
                fallback={
                  <div class="h-[400px] flex items-center justify-center text-muted">
                    <p>Nenhum dado de vendas por categoria disponível</p>
                  </div>
                }
              >
                <PlotlyChart
                  chartSpec={vendasCategoriaChart}
                  chartId="analytics-vendas-categoria-chart"
                  enableDownload={true}
                />
              </Show>
            </div>

            {/* Row 2: Two columns */}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Giro de Estoque */}
              <div class="card p-6 border" role="region" aria-label="Gráfico de giro de estoque">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="font-semibold">Giro de Estoque (Top 15)</h3>
                  <ChartDownloadButton
                    chartId="analytics-giro-estoque-chart"
                    filename="analytics_giro_estoque"
                    label="Baixar"
                  />
                </div>
                <Show
                  when={data()!.giro_estoque.length > 0}
                  fallback={
                    <div class="h-[400px] flex items-center justify-center text-muted">
                      <p>Nenhum dado de giro de estoque disponível</p>
                    </div>
                  }
                >
                  <PlotlyChart
                    chartSpec={giroEstoqueChart}
                    chartId="analytics-giro-estoque-chart"
                    enableDownload={true}
                  />
                </Show>
              </div>

              {/* Distribuição ABC */}
              <div class="card p-6 border" role="region" aria-label="Gráfico de análise ABC">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="font-semibold">Análise de Pareto (ABC por Receita)</h3>
                  <ChartDownloadButton
                    chartId="analytics-abc-chart"
                    filename="analytics_distribuicao_abc"
                    label="Baixar"
                  />
                </div>
                <Show
                  when={data()!.distribuicao_abc.detalhes && data()!.distribuicao_abc.detalhes.length > 0}
                  fallback={
                    <div class="h-[400px] flex items-center justify-center text-muted">
                      <p>Nenhum dado de distribuição ABC disponível</p>
                    </div>
                  }
                >
                  <PlotlyChart
                    chartSpec={distribuicaoABCChart}
                    chartId="analytics-abc-chart"
                    enableDownload={true}
                  />
                </Show>

                {/* Summary of ABC classes - CLICKABLE */}
                <Show when={data()!.distribuicao_abc.receita_por_classe}>
                  <div class="grid grid-cols-3 gap-2 mt-4" role="group" aria-label="Classes ABC interativas">
                    <button
                      onClick={() => handleABCClick('A')}
                      class="p-2 rounded bg-green-500/10 border border-green-500/20 text-center hover:bg-green-500/20 transition-colors cursor-pointer group"
                      aria-label={`Ver detalhes da Classe A - ${data()!.distribuicao_abc.A} produtos responsáveis por 80% da receita`}
                    >
                      <p class="text-[10px] text-green-700 font-bold uppercase">Classe A</p>
                      <p class="text-sm font-bold">{data()!.distribuicao_abc.A} SKUs</p>
                      <p class="text-[10px] text-muted-foreground">80% da Receita</p>
                      <p class="text-[9px] text-green-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                        <Eye size={10} /> Clique para detalhes
                      </p>
                    </button>
                    <button
                      onClick={() => handleABCClick('B')}
                      class="p-2 rounded bg-yellow-500/10 border border-yellow-500/20 text-center hover:bg-yellow-500/20 transition-colors cursor-pointer group"
                      aria-label={`Ver detalhes da Classe B - ${data()!.distribuicao_abc.B} produtos responsáveis por 15% da receita`}
                    >
                      <p class="text-[10px] text-yellow-700 font-bold uppercase">Classe B</p>
                      <p class="text-sm font-bold">{data()!.distribuicao_abc.B} SKUs</p>
                      <p class="text-[10px] text-muted-foreground">15% da Receita</p>
                      <p class="text-[9px] text-yellow-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                        <Eye size={10} /> Clique para detalhes
                      </p>
                    </button>
                    <button
                      onClick={() => handleABCClick('C')}
                      class="p-2 rounded bg-red-500/10 border border-red-500/20 text-center hover:bg-red-500/20 transition-colors cursor-pointer group"
                      aria-label={`Ver detalhes da Classe C - ${data()!.distribuicao_abc.C} produtos responsáveis por 5% da receita`}
                    >
                      <p class="text-[10px] text-red-700 font-bold uppercase">Classe C</p>
                      <p class="text-sm font-bold">{data()!.distribuicao_abc.C} SKUs</p>
                      <p class="text-[10px] text-muted-foreground">5% da Receita</p>
                      <p class="text-[9px] text-red-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                        <Eye size={10} /> Clique para detalhes
                      </p>
                    </button>
                  </div>
                </Show>
              </div>
            </div>

            {/* Decision Cockpit: Action Cards */}
            <div class="card p-6 border bg-zinc-50 dark:bg-zinc-900/50">
              <div class="flex items-center gap-3 mb-6">
                <div class="p-2 bg-primary/10 rounded-lg text-primary">
                  <BarChart3 size={24} />
                </div>
                <div>
                  <h4 class="font-bold text-lg leading-none">Otimização de Portfólio (Decisão)</h4>
                  <p class="text-sm text-muted-foreground mt-1">Estratégias recomendadas baseadas na classificação ABC de receita.</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Classe A - Estratégia de Proteção */}
                <div class="p-4 rounded-xl bg-green-500/5 border border-green-500/10 hover:border-green-500/30 transition-all">
                  <div class="flex justify-between items-start mb-3">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700">
                      <div class="w-1.5 h-1.5 rounded-full bg-green-600 animate-pulse"></div>
                      Classe A
                    </span>
                    <span class="text-xs font-mono text-green-700/70">80% da Receita</span>
                  </div>
                  <h5 class="font-bold text-green-900 dark:text-green-400 mb-1">Blindagem Total</h5>
                  <p class="text-xs text-green-800/70 dark:text-green-500/70 mb-4 leading-relaxed">
                    Produtos vitais. A ruptura causa prejuízo imediato e perda de clientes.
                  </p>
                  <div class="space-y-2">
                    <div class="flex items-center gap-2 text-xs font-medium text-green-800 dark:text-green-300">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Meta de Serviço: 98%
                    </div>
                    <div class="flex items-center gap-2 text-xs font-medium text-green-800 dark:text-green-300">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                      Revisão: Semanal
                    </div>
                  </div>
                </div>

                {/* Classe B - Estratégia de Manutenção */}
                <div class="p-4 rounded-xl bg-yellow-500/5 border border-yellow-500/10 hover:border-yellow-500/30 transition-all">
                  <div class="flex justify-between items-start mb-3">
                    <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-800">
                      Classe B
                    </span>
                    <span class="text-xs font-mono text-yellow-800/70">15% da Receita</span>
                  </div>
                  <h5 class="font-bold text-yellow-900 dark:text-yellow-500 mb-1">Gestão Eficiente</h5>
                  <p class="text-xs text-yellow-800/70 dark:text-yellow-600/70 mb-4 leading-relaxed">
                    Importantes para o mix, mas permitem margem de manobra. Evite excessos.
                  </p>
                  <div class="space-y-2">
                    <div class="flex items-center gap-2 text-xs font-medium text-yellow-800 dark:text-yellow-500">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                      Meta de Serviço: 95%
                    </div>
                    <div class="flex items-center gap-2 text-xs font-medium text-yellow-800 dark:text-yellow-500">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      Revisão: Quinzenal
                    </div>
                  </div>
                </div>

                {/* Classe C - Estratégia de Racionalização */}
                <div class="p-4 rounded-xl bg-red-500/5 border border-red-500/10 hover:border-red-500/30 transition-all">
                  <div class="flex justify-between items-start mb-3">
                    <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800">
                      Classe C
                    </span>
                    <span class="text-xs font-mono text-red-800/70">5% da Receita</span>
                  </div>
                  <h5 class="font-bold text-red-900 dark:text-red-400 mb-1">Racionalização</h5>
                  <p class="text-xs text-red-800/70 dark:text-red-500/70 mb-4 leading-relaxed">
                    Gerador de custo de estoque. Avaliar descontinuação ou pedido sob demanda.
                  </p>
                  <div class="space-y-2">
                    <div class="flex items-center gap-2 text-xs font-medium text-red-800 dark:text-red-400">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Estoque Mínimo
                    </div>
                    <div class="flex items-center gap-2 text-xs font-medium text-red-800 dark:text-red-400">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                      Revisão: Mensal / Corte
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Show>

        {/* Modal ABC Details */}
        <Show when={showABCModal()}>
          {/* ✅ CORREÇÃO MOBILE: p-0 no mobile para fullscreen, p-4 no desktop */}
          <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-0 md:p-4" onClick={() => setShowABCModal(false)}>
            {/* ✅ CORREÇÃO MOBILE: fullscreen no mobile (h-full rounded-none), normal no desktop */}
            <div
              class="bg-background rounded-none md:rounded-lg shadow-2xl max-w-6xl w-full h-full md:h-auto md:max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="abc-modal-title"
              aria-describedby="abc-modal-description"
            >
              {/* Header */}
              <div class="flex justify-between items-center p-6 border-b">
                <div>
                  <h3 id="abc-modal-title" class="text-xl font-bold flex items-center gap-2">
                    <span class={`inline-block w-3 h-3 rounded-full ${selectedClasse() === 'A' ? 'bg-green-500' :
                      selectedClasse() === 'B' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></span>
                    SKUs da Classe {selectedClasse()}
                  </h3>
                  <p id="abc-modal-description" class="text-sm text-muted-foreground mt-1">
                    {abcDetails().length} produtos encontrados
                  </p>
                </div>
                <div class="flex gap-2">
                  <button
                    onClick={downloadABCCSV}
                    class="btn btn-outline gap-2"
                    disabled={abcDetails().length === 0}
                    aria-label="Baixar lista de produtos em CSV"
                  >
                    <Download size={16} />
                    Baixar CSV
                  </button>
                  <button
                    onClick={() => setShowABCModal(false)}
                    class="btn btn-outline"
                    aria-label="Fechar modal"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div class="overflow-y-auto max-h-[calc(90vh-140px)]">
                <Show when={loadingABC()}>
                  <div class="flex items-center justify-center py-12">
                    <RefreshCw class="animate-spin mr-2" size={24} />
                    <span>Carregando detalhes...</span>
                  </div>
                </Show>

                <Show when={!loadingABC() && abcDetails().length === 0}>
                  <div class="flex items-center justify-center py-12 text-muted-foreground">
                    Nenhum produto encontrado para esta classe.
                  </div>
                </Show>

                <Show when={!loadingABC() && abcDetails().length > 0}>
                  {/* ✅ CORREÇÃO MOBILE: Desktop - Table, Mobile - Cards */}

                  {/* Desktop Table (hidden on mobile) */}
                  <table class="w-full hidden md:table" role="table" aria-label={`Produtos da classe ${selectedClasse()}`}>
                    <thead class="sticky top-0 bg-secondary border-b">
                      <tr>
                        <th class="text-left p-3 text-xs font-semibold uppercase">Produto</th>
                        <th class="text-left p-3 text-xs font-semibold uppercase">Nome</th>
                        <th class="text-left p-3 text-xs font-semibold uppercase">UNE</th>
                        <th class="text-left p-3 text-xs font-semibold uppercase">Loja</th>
                        <th class="text-right p-3 text-xs font-semibold uppercase">Receita</th>
                        <th class="text-right p-3 text-xs font-semibold uppercase">% Acumulada</th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* ✅ PERFORMANCE: Usa dados paginados */}
                      <For each={paginatedAbcDetails()}>
                        {(item) => (
                          <tr class="border-b hover:bg-secondary/50 transition-colors">
                            <td class="p-3 font-mono text-sm">{item.PRODUTO}</td>
                            <td class="p-3 text-sm">{item.NOME}</td>
                            <td class="p-3 font-mono text-sm">{item.UNE}</td>
                            <td class="p-3 text-sm text-muted-foreground">{item.UNE_NOME || '-'}</td>
                            <td class="p-3 text-sm text-right font-medium">
                              R$ {item.receita.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td class="p-3 text-sm text-right">
                              {item.perc_acumulada.toFixed(2)}%
                            </td>
                          </tr>
                        )}
                      </For>
                    </tbody>
                  </table>

                  {/* Mobile Cards (shown only on mobile) */}
                  <div class="md:hidden space-y-3">
                    {/* ✅ PERFORMANCE: Usa dados paginados */}
                    <For each={paginatedAbcDetails()}>
                      {(item) => (
                        <div class="bg-card border rounded-lg p-4 space-y-2">
                          <div class="flex justify-between items-start">
                            <div class="flex-1">
                              <p class="font-medium text-sm">{item.NOME}</p>
                              <p class="text-xs font-mono text-muted-foreground mt-1">SKU: {item.PRODUTO}</p>
                            </div>
                            <span class="px-2 py-1 bg-primary/10 text-primary rounded text-xs font-semibold">
                              {item.perc_acumulada.toFixed(2)}%
                            </span>
                          </div>
                          <div class="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <span class="text-muted-foreground">UNE:</span>
                              <span class="ml-1 font-mono">{item.UNE}</span>
                            </div>
                            <div>
                              <span class="text-muted-foreground">Loja:</span>
                              <span class="ml-1">{item.UNE_NOME || '-'}</span>
                            </div>
                          </div>
                          <div class="pt-2 border-t">
                            <span class="text-xs text-muted-foreground">Receita: </span>
                            <span class="text-sm font-semibold">
                              R$ {item.receita.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          </div>
                        </div>
                      )}
                    </For>
                  </div>

                  {/* ✅ PERFORMANCE: Controles de Paginação */}
                  <Show when={abcTotalPages() > 1}>
                    <div class="flex justify-between items-center px-4 py-3 border-t bg-muted/10" role="navigation" aria-label="Paginação de produtos">
                      <div class="text-sm text-muted-foreground" aria-live="polite">
                        Página {abcPage()} de {abcTotalPages()} | Total: {abcDetails().length} itens
                      </div>
                      <div class="flex gap-2">
                        <button
                          onClick={() => setAbcPage(Math.max(1, abcPage() - 1))}
                          disabled={abcPage() === 1}
                          class="px-3 py-1 text-sm bg-secondary hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed rounded"
                          aria-label="Página anterior"
                        >
                          Anterior
                        </button>
                        <button
                          onClick={() => setAbcPage(Math.min(abcTotalPages(), abcPage() + 1))}
                          disabled={abcPage() === abcTotalPages()}
                          class="px-3 py-1 text-sm bg-secondary hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed rounded"
                          aria-label="Próxima página"
                        >
                          Próxima
                        </button>
                      </div>
                    </div>
                  </Show>
                </Show>
              </div>
            </div>
          </div>
        </Show>
      </div>
    </ErrorBoundary>
  );
}
