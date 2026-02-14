import { createSignal, onMount, Show, For } from "solid-js";
import { PlotlyChart } from "../components/PlotlyChart";
import { dashboardApi } from "../lib/api";
import type { Component } from "solid-js";
import "../styles/micro-interactions.css";

interface ForecastData {
  produto_id: string;
  nome: string;
  forecast: number[];
  forecast_ajustado: number[];
  lower_bound: number[];
  upper_bound: number[];
  seasonal_context: any;
  accuracy: any;
  abrangencia?: {
    total_lojas: number;
    detalhes: { une: number; nome_loja: string }[];
    filtro_aplicado?: string;
  };
}

interface AllocationResult {
  alocacoes: { une: number; quantidade: number; justificativa: string }[];
  total_alocado: number;
  total_solicitado: number;
  criterio_usado: string;
}

interface EOQResult {
  eoq: number;
  pedidos_por_ano: number;
  custo_total_anual: number;
  produto: string;
  nome: string;
}

const Forecasting: Component = () => {
  // State
  const [produtoId, setProdutoId] = createSignal("");
  const [selectedProduct, setSelectedProduct] = createSignal<any | null>(null);
  const [periodos, setPeriodos] = createSignal(30);

  // Filters
  const [segmentos, setSegmentos] = createSignal<string[]>([]);
  const [grupos, setGrupos] = createSignal<string[]>([]);
  const [selectedSegmento, setSelectedSegmento] = createSignal("");
  const [selectedGrupo, setSelectedGrupo] = createSignal("");
  const [selectedLoja, setSelectedLoja] = createSignal("");
  const [lojas, setLojas] = createSignal<{ UNE: number; NOME: string }[]>([]);

  // Lists
  const [productsList, setProductsList] = createSignal<any[]>([]);
  const [listLoading, setListLoading] = createSignal(false);

  // Data
  const [forecastData, setForecastData] = createSignal<ForecastData | null>(null);
  const [eoqData, setEOQData] = createSignal<EOQResult | null>(null);
  const [allocationData, setAllocationData] = createSignal<AllocationResult | null>(null);

  // UI State
  const [showScopeDetails, setShowScopeDetails] = createSignal(false);

  // Chart
  const [chartSpec, setChartSpec] = createSignal<any>({});
  const [analysisLoading, setAnalysisLoading] = createSignal(false);
  const [error, setError] = createSignal("");

  onMount(async () => {
    // Load metadata segments and stores
    try {
      const segResp = await dashboardApi.getMetadataSegments();
      if (segResp.status === 200) setSegmentos(segResp.data);

      const storesResp = await dashboardApi.getMetadataStores();
      if (storesResp.status === 200) setLojas(storesResp.data);
    } catch (e) {
      console.error("Failed to load metadata", e);
    }
  });

  const loadGrupos = async (segmento: string) => {
    setSelectedSegmento(segmento);
    setSelectedGrupo(""); // Reset group
    setProductsList([]); // Clear list until fetch

    if (!segmento) return;

    try {
      const resp = await dashboardApi.getMetadataGroups(segmento);
      if (resp.status === 200) setGrupos(resp.data);

      // Auto-load products for the segment
      loadProducts(segmento, "");
    } catch (e) {
      console.error("Failed to load groups", e);
    }
  };

  const loadProducts = async (segmento: string, grupo: string) => {
    if (!segmento) return;
    setListLoading(true);
    try {
      const resp = await dashboardApi.getProductList(segmento, grupo);
      const data = resp.data;
      if (data.products) {
        setProductsList(data.products);
      }
    } catch (e) {
      console.error("Failed to load products", e);
    } finally {
      setListLoading(false);
    }
  };

  const renderPlotlyChart = (data: ForecastData) => {
    const dates = Array.from({ length: data.forecast.length }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() + i);
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    });

    const isSeasonalRisk = data.seasonal_context?.urgency !== "Low";

    setChartSpec({
      data: [
        // Faixa de Confiança (Área Cinza)
        {
          x: dates,
          y: data.upper_bound,
          type: 'scatter',
          mode: 'lines',
          line: { width: 0 },
          name: 'Max',
          showlegend: false,
          hoverinfo: 'skip'
        },
        {
          x: dates,
          y: data.lower_bound,
          type: 'scatter',
          mode: 'lines',
          fill: 'tonexty',
          fillcolor: 'rgba(0, 0, 0, 0.05)', // Black 5%
          line: { width: 0 },
          name: 'Confiança',
          showlegend: false,
          hoverinfo: 'skip'
        },
        // Previsão (Linha grossa preta)
        {
          x: dates,
          y: data.forecast_ajustado,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Previsão',
          line: {
            color: '#171717', // Neutral-900
            width: 3,
            shape: 'spline' // Curve suave
          },
          marker: {
            size: 6,
            color: '#171717'
          },
          hovertemplate: '<b>%{y:.0f}</b> un<extra></extra>'
        },
        // Tendência Base (Linha Laranja pontilhada)
        {
          x: dates,
          y: data.forecast,
          type: 'scatter',
          mode: 'lines',
          name: 'Tendência Base',
          line: {
            color: '#F97316', // Orange-500
            width: 2,
            dash: 'dash'
          },
          hovertemplate: '%{y:.0f} un<extra></extra>'
        }
      ],
      layout: {
        font: { family: 'Inter, sans-serif' },
        hovermode: 'x unified',
        margin: { l: 40, r: 20, t: 30, b: 40 },
        showlegend: true,
        legend: { orientation: 'h', y: 1.1, x: 0 },
        xaxis: {
          showgrid: false,
          tickfont: { size: 11, color: '#737373' },
          linecolor: '#E5E5E5'
        },
        yaxis: {
          gridcolor: '#F5F5F5',
          zeroline: false,
          tickfont: { size: 11, color: '#737373' },
        },
        // Anotação Sazonal
        annotations: isSeasonalRisk ? [
          {
            xref: 'paper', yref: 'paper',
            x: 0.98, y: 0.95,
            text: `⚠️ ${data.seasonal_context?.season?.toUpperCase()}`,
            showarrow: false,
            font: { color: '#C2410C', size: 10, weight: 'bold' },
            bgcolor: '#FFEDD5',
            borderpad: 4,
            rx: 2
          }
        ] : []
      },
      config: { responsive: true, displayModeBar: false }
    });
  };

  const handleProductSelect = async (prod: any) => {
    setSelectedProduct(prod);
    setProdutoId(prod.id);
    await runAnalysis(prod.id);
  };

  const runAnalysis = async (pid: string) => {
    if (!pid) return;

    setAnalysisLoading(true);
    setError("");
    setForecastData(null);
    setEOQData(null);
    setAllocationData(null);
    setChartSpec({});

    try {
      // 1. Forecast with Store Filter (UNE)
      const response = await dashboardApi.predictDemand({
        produto_id: pid,
        periodo_dias: periodos(),
        considerar_sazonalidade: true,
        une: selectedLoja() || null
      });
      const fData = response.data;
      if (fData.error) throw new Error(fData.error);
      setForecastData(fData);
      renderPlotlyChart(fData);

      // 2. EOQ (Only if Scope is Global/Rede - EOQ per store is too granular usually)
      if (!selectedLoja()) {
        const response = await dashboardApi.calculateEOQ({ produto_id: pid });
        const eData = response.data;

        if (!eData.error) {
          setEOQData(eData);

          // 3. Auto-Allocation
          if (eData.eoq > 0) {
            // 3. Auto-Allocation
            if (eData.eoq > 0) {
              const response = await dashboardApi.allocateStock({
                produto_id: pid,
                quantidade_total: eData.eoq,
                criterio: "prioridade_ruptura"
              });
              const aData = response.data;
              if (!aData.error) setAllocationData(aData);
            }
          }
        }
      }

    } catch (err: any) {
      setError(err.message || "Erro ao calcular análise");
    } finally {
      setAnalysisLoading(false);
    }
  };

  // UI Helpers (Typographic Style)
  const getRiskColor = (days: number) => {
    if (days <= 15) return "text-red-600 font-bold";
    if (days <= 30) return "text-orange-600 font-semibold";
    return "text-green-600"; // Minimal
  };

  return (
    <div class="h-[calc(100vh-4rem)] flex flex-col md:flex-row bg-white text-neutral-900 font-sans">

      {/* --- SIDEBAR (Left) --- */}
      <div class="w-full md:w-[380px] flex flex-col border-r border-neutral-100 h-full bg-neutral-50/50">

        {/* Header Filters */}
        <div class="p-6 border-b border-neutral-100 space-y-5">
          <h2 class="text-xs font-black uppercase tracking-widest text-neutral-400">Parâmetros de Análise</h2>

          <div class="space-y-4">
            {/* Store (Global vs Local) */}
            <div class="group">
              <label class="block text-[10px] font-bold uppercase text-neutral-500 mb-1 group-focus-within:text-orange-600 transition-colors">
                Escopo (Loja)
              </label>
              <select
                class="w-full bg-white border border-neutral-200 text-sm font-medium py-2 px-3 rounded-none focus:border-orange-500 focus:ring-0 outline-none transition-all"
                value={selectedLoja()}
                onChange={(e) => setSelectedLoja(e.currentTarget.value)}
              >
                <option value="">REDE COMPLETA (Todas as Lojas)</option>
                <For each={lojas()}>{(loja) => <option value={loja.UNE}>{loja.UNE ? `${loja.UNE} - ` : ''}{loja.NOME}</option>}</For>
              </select>
            </div>

            {/* Segment */}
            <div class="group">
              <label class="block text-[10px] font-bold uppercase text-neutral-500 mb-1 group-focus-within:text-orange-600 transition-colors">
                Segmento Comercial
              </label>
              <select
                class="w-full bg-white border border-neutral-200 text-sm font-medium py-2 px-3 rounded-none focus:border-orange-500 focus:ring-0 outline-none transition-all"
                value={selectedSegmento()}
                onChange={(e) => loadGrupos(e.currentTarget.value)}
              >
                <option value="">Selecione...</option>
                <For each={segmentos()}>{(seg) => <option value={seg}>{seg}</option>}</For>
              </select>
            </div>

            {/* Group */}
            <div class="group">
              <label class="block text-[10px] font-bold uppercase text-neutral-500 mb-1 group-focus-within:text-orange-600 transition-colors">
                Grupo de Produto
              </label>
              <select
                class="w-full bg-white border border-neutral-200 text-sm font-medium py-2 px-3 rounded-none focus:border-orange-500 focus:ring-0 outline-none transition-all"
                value={selectedGrupo()}
                onChange={(e) => {
                  setSelectedGrupo(e.currentTarget.value);
                  loadProducts(selectedSegmento(), e.currentTarget.value);
                }}
                disabled={!selectedSegmento()}
              >
                <option value="">Todos os Grupos</option>
                <For each={grupos()}>{(grp) => <option value={grp}>{grp}</option>}</For>
              </select>
            </div>
          </div>
        </div>

        {/* Product List (Minimal) */}
        <div class="flex-1 overflow-y-auto bg-white">
          <Show when={!listLoading()} fallback={<div class="p-6 text-xs text-neutral-400 uppercase animate-pulse">Carregando dados...</div>}>
            <Show when={productsList().length > 0} fallback={
              <div class="p-8 text-center">
                <span class="text-xs text-neutral-400 uppercase tracking-widest">{selectedSegmento() ? "Nenhum resultado" : "Aguardando Filtros"}</span>
              </div>
            }>
              <div class="divide-y divide-neutral-50">
                <For each={productsList()}>
                  {(prod) => (
                    <button
                      onClick={() => handleProductSelect(prod)}
                      class={`w-full text-left p-4 hover:bg-neutral-50 transition-all group relative ${selectedProduct()?.id === prod.id ? 'bg-neutral-50' : ''}`}
                    >
                      {/* Active Indicator Line */}
                      <Show when={selectedProduct()?.id === prod.id}>
                        <div class="absolute left-0 top-0 bottom-0 w-1 bg-orange-500"></div>
                      </Show>

                      <div class="flex justify-between items-start mb-1">
                        <span class="text-[10px] font-mono text-neutral-400 group-hover:text-orange-500 transition-colors">#{prod.id}</span>
                        <span class={`text-[10px] font-bold ${getRiskColor(prod.dias_cobertura)}`}>{prod.dias_cobertura.toFixed(0)}d</span>
                      </div>
                      <div class="text-sm font-bold text-neutral-800 leading-tight group-hover:text-black line-clamp-2">
                        {prod.nome}
                      </div>
                    </button>
                  )}
                </For>
              </div>
            </Show>
          </Show>
        </div>
      </div>

      {/* --- MAIN CONTENT (Right) --- */}
      <div class="flex-1 flex flex-col h-full overflow-y-auto bg-white">
        <Show when={selectedProduct()} fallback={
          <div class="flex-1 flex flex-col items-center justify-center opacity-30">
            <h1 class="text-4xl font-black tracking-tighter text-neutral-300">FORECAST</h1>
            <p class="text-sm font-mono text-neutral-400 mt-2">SELECIONE UM PRODUTO</p>
          </div>
        }>

          {/* HEADER: CLEANER TYPOGRAPHY */}
          <div class="p-8 pb-4">
            <div class="flex items-baseline gap-4 mb-2">
              <span class="text-xs font-mono bg-neutral-100 px-2 py-1 rounded text-neutral-500">ID: {selectedProduct().id}</span>
              <span class="text-xs font-mono text-neutral-400 uppercase">{selectedSegmento()} / {selectedGrupo() || 'GERAL'}</span>
            </div>

            <h1 class="text-3xl font-bold tracking-tight text-neutral-900 leading-tight mb-8 max-w-4xl">
              {selectedProduct().nome}
            </h1>

            {/* KPI STRIP */}
            <div class="grid grid-cols-2 md:grid-cols-4 gap-8 border-y border-neutral-100 py-6">

              {/* Est. Atual */}
              <div>
                <div class="text-[10px] font-bold uppercase text-neutral-400 tracking-wider mb-1">Estoque Atual</div>
                <div class="text-2xl font-bold text-neutral-900">{selectedProduct().estoque.toLocaleString()}</div>
              </div>

              {/* Vendas */}
              <div>
                <div class="text-[10px] font-bold uppercase text-neutral-400 tracking-wider mb-1">Venda (30d)</div>
                <div class="text-2xl font-bold text-neutral-900">{selectedProduct().venda_30d.toLocaleString()}</div>
              </div>

              {/* Cobertura */}
              <div>
                <div class="text-[10px] font-bold uppercase text-neutral-400 tracking-wider mb-1">Cobertura</div>
                <div class={`text-2xl font-bold ${getRiskColor(selectedProduct().dias_cobertura)} flex items-baseline gap-1`}>
                  {selectedProduct().dias_cobertura.toFixed(1)} <span class="text-sm font-medium text-neutral-400">dias</span>
                </div>
              </div>

              {/* Status */}
              <div>
                <div class="text-[10px] font-bold uppercase text-neutral-400 tracking-wider mb-1">Sazonalidade</div>
                <div class="text-2xl font-bold text-neutral-900 flex items-baseline gap-1">
                  {forecastData()?.seasonal_context?.multiplier || 1}x
                  <Show when={forecastData()?.seasonal_context?.urgency !== "Low"}>
                    <span class="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded ml-2 font-bold uppercase tracking-wide">
                      {forecastData()?.seasonal_context?.season?.replace('_', ' ')}
                    </span>
                  </Show>
                </div>
              </div>
            </div>
          </div>

          {/* ANALYSIS CONTENT */}
          <div class="flex-1 p-8 pt-2 space-y-12">

            <Show when={analysisLoading()}>
              <div class="h-64 flex items-center justify-center">
                <div class="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            </Show>

            <Show when={!analysisLoading() && forecastData()}>
              {/* 1. CHART SECTION */}
              <div class="w-full">
                <div class="flex justify-between items-end mb-6">
                  <h3 class="text-lg font-bold text-neutral-900">Projeção de Demanda</h3>
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold text-neutral-400 uppercase">Horizonte:</span>
                    <select
                      class="bg-transparent border-b border-neutral-300 text-sm font-bold focus:border-orange-500 outline-none pb-0.5"
                      value={periodos()}
                      onChange={(e) => {
                        setPeriodos(parseInt(e.currentTarget.value));
                        runAnalysis(selectedProduct().id);
                      }}
                    >
                      <option value="30">30 Dias</option>
                      <option value="60">60 Dias</option>
                      <option value="90">90 Dias</option>
                    </select>
                  </div>
                </div>

                {/* Chart Container - Fixed Height */}
                <div class="h-[400px] w-full border-l border-b border-neutral-100 relative bg-white">
                  {/* Scope Tooltip Logic */}
                  <div class="absolute top-0 right-0 z-10">
                    <button
                      onClick={() => setShowScopeDetails(!showScopeDetails())}
                      class="text-xs font-bold uppercase tracking-wider text-neutral-400 hover:text-orange-500 flex items-center gap-1 bg-white p-2 border border-transparent hover:border-neutral-100 rounded"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Escopo: {forecastData()?.abrangencia?.filtro_aplicado || "Rede"} ({forecastData()?.abrangencia?.total_lojas} Lojas)
                    </button>

                    {/* SCOPE DROPDOWN */}
                    <Show when={showScopeDetails()}>
                      <div class="absolute right-0 top-8 w-64 bg-white border border-neutral-200 shadow-xl p-4 z-50 rounded animate-in fade-in slide-in-from-top-2">
                        <h4 class="text-xs font-black uppercase text-neutral-400 mb-3 border-b border-neutral-100 pb-2">Lojas Analisadas</h4>
                        <div class="max-h-48 overflow-y-auto space-y-1">
                          <For each={forecastData()?.abrangencia?.detalhes}>
                            {(det) => (
                              <div class="text-xs flex justify-between text-neutral-600 hover:bg-neutral-50 p-1 rounded">
                                <span>Loja {det.une}</span>
                                <span class="font-medium text-neutral-900">{det.nome_loja}</span>
                              </div>
                            )}
                          </For>
                        </div>
                      </div>
                    </Show>
                  </div>

                  <Show when={Object.keys(chartSpec()).length > 0} fallback={<div class="w-full h-full flex items-center justify-center text-neutral-300">Carregando gráfico...</div>}>
                    <PlotlyChart
                      chartSpec={chartSpec}
                      height="400px"
                      expandedContent={null}
                      naked={true}
                    />
                  </Show>
                </div>
              </div>

              {/* 2. ACTION SECTION (Grid) */}
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-neutral-100">

                {/* EOQ (Action) */}
                <Show when={eoqData()}>
                  <div>
                    <h3 class="text-lg font-bold text-neutral-900 mb-4">Recomendação de Compra (EOQ)</h3>
                    <div class="flex flex-col gap-4">
                      <div class="flex items-baseline gap-2">
                        <span class="text-4xl font-bold text-orange-600 tracking-tight">{eoqData()?.eoq?.toLocaleString()}</span>
                        <span class="text-sm font-bold text-neutral-400 uppercase">Unidades</span>
                      </div>

                      <p class="text-sm text-neutral-500">
                        Quantidade ideal baseada em {eoqData()?.pedidos_por_ano} pedidos/ano com custo total de R$ {eoqData()?.custo_total_anual?.toFixed(2)}.
                      </p>

                      <button class="bg-neutral-900 text-white font-bold uppercase tracking-widest text-xs py-3 px-6 hover:bg-orange-600 transition-colors w-max rounded-sm shadow-sm hover:shadow-md">
                        Criar Pedido de Compra
                      </button>
                    </div>
                  </div>
                </Show>

                {/* Allocation (Distribution) */}
                <Show when={(allocationData()?.alocacoes?.length ?? 0) > 0}>
                  <div>
                    <h3 class="text-lg font-bold text-neutral-900 mb-4 flex justify-between items-center">
                      <span>Plano de Distribuição (Push)</span>
                      <span class="text-xs font-mono text-neutral-400">{allocationData()?.total_alocado}un TOTAL</span>
                    </h3>

                    <div class="border border-neutral-200 bg-neutral-50 rounded-lg overflow-hidden">
                      <div class="grid grid-cols-3 text-[10px] font-bold uppercase text-neutral-400 p-2 border-b border-neutral-200 bg-neutral-100">
                        <span>Destino</span>
                        <span class="text-right">Qtd</span>
                        <span class="text-right">Justificativa</span>
                      </div>
                      <div class="max-h-40 overflow-y-auto">
                        <For each={allocationData()?.alocacoes}>
                          {(aloc) => (
                            <div class="grid grid-cols-3 text-xs p-2 border-b border-neutral-100 last:border-0 hover:bg-white transition-colors">
                              <div class="font-bold text-neutral-700">Loja {aloc.une}</div>
                              <div class="text-right font-mono text-neutral-900">{aloc.quantidade}</div>
                              <div class="text-right text-neutral-500 truncate">{aloc.justificativa}</div>
                            </div>
                          )}
                        </For>
                      </div>
                    </div>
                  </div>
                </Show>
              </div>

            </Show>
          </div>

        </Show>
      </div>
    </div>
  );
};

export default Forecasting;
