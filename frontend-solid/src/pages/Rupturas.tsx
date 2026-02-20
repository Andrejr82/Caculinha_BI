import { createSignal, onMount, Show, For } from 'solid-js';
import { rupturasApi, Ruptura, RupturasSummary } from '@/lib/api';
import { AlertTriangle, RefreshCw, PackageX, ShoppingCart, Archive, Download, Filter, X, TrendingUp, Package, BarChart3, PieChart } from 'lucide-solid';
import { PlotlyChart } from '@/components/PlotlyChart';
import { ChartDownloadButton } from '@/components/ChartDownloadButton';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { EmptyStateSuccess } from '@/components/EmptyState';

export default function Rupturas() {
  const [data, setData] = createSignal<Ruptura[]>([]);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal('');
  const [summary, setSummary] = createSignal<RupturasSummary>({ total: 0, criticos: 0, valor_estimado: 0 });

  const fmtNum = (n: number) => n?.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0,00';

  // Chart specs
  const [criticidadeChart, setCriticidadeChart] = createSignal<any>({});
  const [topRupturasChart, setTopRupturasChart] = createSignal<any>({});
  const [necessidadeSegmentoChart, setNecessidadeSegmentoChart] = createSignal<any>({});
  const [selectedProduct, setSelectedProduct] = createSignal<Ruptura | null>(null);

  // Drill-down: Grupo selecionado para ver produtos
  const [selectedGroup, setSelectedGroup] = createSignal<string | null>(null);

  // Filtros
  const [segmentos, setSegmentos] = createSignal<string[]>([]);
  const [unes, setUnes] = createSignal<string[]>([]);
  const [selectedSegmento, setSelectedSegmento] = createSignal<string>('');
  const [selectedUne, setSelectedUne] = createSignal<string>('');
  const [showFilters, setShowFilters] = createSignal(false);
  const [filtersLoading, setFiltersLoading] = createSignal(false);

  const loadFilters = async () => {
    setFiltersLoading(true);
    try {
      const [segmentosRes, unesRes] = await Promise.all([
        rupturasApi.getSegmentos(),
        rupturasApi.getUnes()
      ]);
      setSegmentos(Array.isArray(segmentosRes.data) ? segmentosRes.data : []);
      setUnes(Array.isArray(unesRes.data) ? unesRes.data : []);
    } catch (err) {
      console.error("Error loading filters:", err);
      setSegmentos([]);
      setUnes([]);
    } finally {
      setFiltersLoading(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const segmento = selectedSegmento() || undefined;
      const une = selectedUne() || undefined;

      console.log('🔍 [Rupturas] Carregando dados com filtros:', { segmento, une });

      const [rupturaRes, summaryRes] = await Promise.all([
        rupturasApi.getCritical(50, segmento, une),
        rupturasApi.getSummary(segmento, une)
      ]);

      console.log('📊 [Rupturas] Dados recebidos:', rupturaRes.data.length, 'produtos');
      console.log('📊 [Rupturas] UNEs nos dados:', [...new Set(rupturaRes.data.map(r => r.UNE))]);

      setData(rupturaRes.data);
      setSummary(summaryRes.data);

      // Gerar gráficos
      generateCharts(rupturaRes.data);
    } catch (err: any) {
      console.error("Error loading rupturas:", err);
      setError(err.response?.data?.detail || "Falha ao carregar rupturas críticas.");
      setData([]);
      setSummary({ total: 0, criticos: 0, valor_estimado: 0 });
    } finally {
      setLoading(false);
    }
  };

  const generateCharts = (rupturas: Ruptura[]) => {
    if (rupturas.length === 0) return;

    // 1. Top Grupos em Ruptura Crítica - mais acionável para o comprador
    // Agrupa produtos críticos por NOMEGRUPO e mostra top 8
    const gruposContagem: { [key: string]: { total: number, criticos: number, necessidade: number } } = {};

    rupturas.forEach(r => {
      const grupo = (r as any).NOMEGRUPO || r.NOMESEGMENTO || 'SEM GRUPO';
      if (!gruposContagem[grupo]) {
        gruposContagem[grupo] = { total: 0, criticos: 0, necessidade: 0 };
      }
      gruposContagem[grupo].total++;
      gruposContagem[grupo].necessidade += r.NECESSIDADE;
      if (r.CRITICIDADE_PCT >= 75) gruposContagem[grupo].criticos++;
    });

    // Ordenar por quantidade de críticos e pegar top 8
    const topGrupos = Object.entries(gruposContagem)
      .sort((a, b) => b[1].criticos - a[1].criticos)
      .slice(0, 8);

    setCriticidadeChart({
      data: [{
        type: 'bar',
        orientation: 'h',
        y: topGrupos.map(([nome]) => nome.length > 25 ? nome.substring(0, 25) + '...' : nome),
        x: topGrupos.map(([, data]) => data.criticos),
        marker: {
          color: topGrupos.map(([, data]) => {
            const pct = data.criticos / data.total;
            if (pct >= 0.8) return '#B94343';       // 80%+ críticos = vermelho
            if (pct >= 0.5) return '#CC8B3C';       // 50%+ = laranja
            return '#C9A961';                        // menos = dourado
          }),
          line: { color: '#E5E5E5', width: 1 }
        },
        text: topGrupos.map(([, data]) => `${data.criticos} críticos (${Math.round(data.necessidade)} un)`),
        textposition: 'auto',
        textfont: { color: '#FFFFFF', size: 11, family: 'Inter, sans-serif' },
        hovertemplate: '<b>%{y}</b><br>Produtos críticos: %{x}<br>Total no grupo: %{customdata[0]}<br>Necessidade: %{customdata[1]:.0f} un<extra></extra>',
        customdata: topGrupos.map(([, data]) => [data.total, data.necessidade])
      }],
      layout: {
        title: {
          text: '<b>🔴 Top Grupos em Ruptura Crítica</b><br><span style="font-size:11px;color:#6B6B6B">Categorias com mais produtos em situação crítica (≥75%)</span>',
          font: { size: 14, color: '#2D2D2D', family: 'Inter, sans-serif' },
          x: 0.02
        },
        xaxis: {
          title: 'Produtos Críticos',
          titlefont: { color: '#6B6B6B', size: 11, family: 'Inter, sans-serif' },
          tickfont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
          gridcolor: '#E5E5E5',
          zeroline: false
        },
        yaxis: {
          tickfont: { color: '#2D2D2D', size: 10, family: 'Inter, sans-serif' },
          automargin: true
        },
        plot_bgcolor: '#FFFFFF',
        paper_bgcolor: '#FAFAFA',
        margin: { l: 150, r: 20, t: 70, b: 50 },
        font: { color: '#2D2D2D', family: 'Inter, sans-serif' },
        showlegend: false,
        bargap: 0.25
      },
      config: { responsive: true, displayModeBar: false }
    });

    // 2. Gráfico de Barras - Top 10 Produtos em Ruptura
    const top10 = rupturas
      .sort((a, b) => b.NECESSIDADE - a.NECESSIDADE)
      .slice(0, 10);

    // LOJAS CAÇULA - LIGHT THEME
    setTopRupturasChart({
      data: [{
        type: 'bar',
        x: top10.map(r => r.NOME.substring(0, 30) + '...'),
        y: top10.map(r => r.NECESSIDADE),
        marker: {
          color: top10.map(r => {
            if (r.CRITICIDADE_PCT >= 75) return '#B94343'; // Vermelho terroso
            if (r.CRITICIDADE_PCT >= 50) return '#CC8B3C'; // Laranja terroso
            if (r.CRITICIDADE_PCT >= 25) return '#C9A961'; // Dourado
            return '#5B7B9A'; // Azul acinzentado
          }),
          line: { color: '#E5E5E5', width: 1 }
        },
        text: top10.map(r => Math.round(r.NECESSIDADE)),
        textposition: 'outside',
        textfont: { color: '#2D2D2D', family: 'Inter, sans-serif' },
        hovertemplate: '<b>%{x}</b><br>Loja: %{customdata[1]}<br>Necessidade: %{y:.0f} un<extra></extra>',
        customdata: top10.map(r => [r.PRODUTO, r.UNE_NOME || 'N/A'])
      }],
      layout: {
        title: {
          text: 'Top 10 Produtos - Maior Necessidade',
          font: { size: 16, color: '#2D2D2D', family: 'Inter, sans-serif' }
        },
        xaxis: {
          title: '',
          tickangle: -45,
          tickfont: { size: 9, color: '#6B6B6B', family: 'Inter, sans-serif' },
          gridcolor: '#E5E5E5',
          linecolor: '#E5E5E5'
        },
        yaxis: {
          title: 'Necessidade (unidades)',
          titlefont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
          tickfont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
          gridcolor: '#E5E5E5',
          linecolor: '#E5E5E5'
        },
        plot_bgcolor: '#FFFFFF',
        paper_bgcolor: '#FAFAFA',
        margin: { l: 60, r: 20, t: 60, b: 120 },
        font: { color: '#2D2D2D', family: 'Inter, sans-serif' }
      },
      config: { responsive: true }
    });

    // 3. Gráfico de Barras Empilhadas - Necessidade por GRUPO (categoria de produto)
    // Agrupa por NOMEGRUPO para que o comprador possa priorizar por categoria
    const grupoData: { [key: string]: { critico: number, alto: number, medio: number, baixo: number, total: number } } = {};

    rupturas.forEach(r => {
      // Usar NOMEGRUPO se disponível, senão fallback para NOMESEGMENTO
      const grupo = (r as any).NOMEGRUPO || r.NOMESEGMENTO || 'SEM GRUPO';
      if (!grupoData[grupo]) {
        grupoData[grupo] = { critico: 0, alto: 0, medio: 0, baixo: 0, total: 0 };
      }

      const necessidade = r.NECESSIDADE;
      grupoData[grupo].total += necessidade;
      if (r.CRITICIDADE_PCT >= 75) grupoData[grupo].critico += necessidade;
      else if (r.CRITICIDADE_PCT >= 50) grupoData[grupo].alto += necessidade;
      else if (r.CRITICIDADE_PCT >= 25) grupoData[grupo].medio += necessidade;
      else grupoData[grupo].baixo += necessidade;
    });

    // Ordenar grupos por total de necessidade (mais críticos primeiro)
    const grupos = Object.keys(grupoData).sort((a, b) => grupoData[b].total - grupoData[a].total).slice(0, 10);

    // LOJAS CAÇULA - LIGHT THEME
    setNecessidadeSegmentoChart({
      data: [
        {
          type: 'bar',
          name: '🔴 CRÍTICO',
          x: grupos,
          y: grupos.map(g => grupoData[g].critico),
          marker: { color: '#B94343' },
          hovertemplate: '<b>%{x}</b><br>Crítico: %{y:.0f} un<extra></extra>'
        },
        {
          type: 'bar',
          name: '🟠 ALTO',
          x: grupos,
          y: grupos.map(g => grupoData[g].alto),
          marker: { color: '#CC8B3C' },
          hovertemplate: '<b>%{x}</b><br>Alto: %{y:.0f} un<extra></extra>'
        },
        {
          type: 'bar',
          name: '🟡 MÉDIO',
          x: grupos,
          y: grupos.map(g => grupoData[g].medio),
          marker: { color: '#C9A961' },
          hovertemplate: '<b>%{x}</b><br>Médio: %{y:.0f} un<extra></extra>'
        },
        {
          type: 'bar',
          name: '🔵 BAIXO',
          x: grupos,
          y: grupos.map(g => grupoData[g].baixo),
          marker: { color: '#5B7B9A' },
          hovertemplate: '<b>%{x}</b><br>Baixo: %{y:.0f} un<extra></extra>'
        }
      ],
      layout: {
        title: {
          text: '<b>Necessidade de Reposição por Grupo de Produtos</b><br><span style="font-size:11px;color:#6B6B6B">Top 10 grupos ordenados por volume de necessidade</span>',
          font: { size: 14, color: '#2D2D2D', family: 'Inter, sans-serif' },
          x: 0.02
        },
        barmode: 'stack',
        xaxis: {
          title: '',
          tickangle: -45,
          tickfont: { size: 10, color: '#6B6B6B', family: 'Inter, sans-serif' },
          gridcolor: '#E5E5E5',
          linecolor: '#E5E5E5'
        },
        yaxis: {
          title: 'Necessidade Total (unidades)',
          titlefont: { color: '#6B6B6B', size: 11, family: 'Inter, sans-serif' },
          tickfont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
          gridcolor: '#E5E5E5',
          linecolor: '#E5E5E5'
        },
        plot_bgcolor: '#FFFFFF',
        paper_bgcolor: '#FAFAFA',
        margin: { l: 70, r: 20, t: 80, b: 120 },
        font: { color: '#2D2D2D', family: 'Inter, sans-serif' },
        showlegend: true,
        legend: {
          orientation: 'h',
          x: 0.5,
          y: 1.12,
          xanchor: 'center',
          font: { size: 10, color: '#2D2D2D', family: 'Inter, sans-serif' },
          bgcolor: 'rgba(255,255,255,0.9)',
          bordercolor: '#E5E5E5',
          borderwidth: 1
        }
      },
      config: { responsive: true, displayModeBar: false }
    });
  };

  const handleChartClick = (clickData: any) => {
    if (clickData && clickData.points && clickData.points[0]) {
      const point = clickData.points[0];
      // Se tem customdata, é o código do produto
      if (point.customdata) {
        const produto = data().find(r => r.PRODUTO === point.customdata);
        if (produto) {
          setSelectedProduct(produto);
        }
      }
    }
  };

  // Handler para clique no gráfico de grupos - abre modal com produtos do grupo
  const handleGroupClick = (clickData: any) => {
    if (clickData && clickData.points && clickData.points[0]) {
      const point = clickData.points[0];
      // O label do eixo Y contém o nome do grupo
      const grupoName = point.y || point.label;
      if (grupoName) {
        // Remover truncagem (...) se houver
        const cleanName = grupoName.replace('...', '');
        setSelectedGroup(cleanName);
      }
    }
  };

  // Filtrar produtos pelo grupo selecionado
  const getProductsByGroup = () => {
    const grupo = selectedGroup();
    if (!grupo) return [];

    return data().filter(r => {
      const productGroup = (r as any).NOMEGRUPO || r.NOMESEGMENTO || 'SEM GRUPO';
      // Match parcial para grupos truncados
      return productGroup.toLowerCase().includes(grupo.toLowerCase()) ||
        grupo.toLowerCase().includes(productGroup.substring(0, 20).toLowerCase());
    }).sort((a, b) => b.CRITICIDADE_PCT - a.CRITICIDADE_PCT);
  };

  const clearFilters = () => {
    setSelectedSegmento('');
    setSelectedUne('');
    loadData();
  };

  const exportCSV = () => {
    const items = data();
    if (items.length === 0) return;

    const headers = ['Produto', 'Nome', 'UNE', 'Loja', 'Segmento', 'Grupo', 'Venda 30d', 'Estoque UNE', 'Estoque CD', 'Linha Verde', 'Criticidade %', 'Necessidade'];
    const rows = items.map(item => [
      item.PRODUTO,
      item.NOME,
      item.UNE,
      item.UNE_NOME || '',
      item.NOMESEGMENTO || '',
      (item as any).NOMEGRUPO || '',
      item.VENDA_30DD,
      item.ESTOQUE_UNE,
      item.ESTOQUE_CD,
      item.ESTOQUE_LV,
      item.CRITICIDADE_PCT.toFixed(1),
      item.NECESSIDADE
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rupturas_criticas_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Gerar Pedido de Compra - Exporta lista formatada para compras
  const exportPurchaseOrder = () => {
    const items = data();
    if (items.length === 0) return;

    // Agrupar por NOMEGRUPO
    const grupoData: { [key: string]: Array<typeof items[0]> } = {};
    items.forEach(item => {
      const grupo = (item as any).NOMEGRUPO || item.NOMESEGMENTO || 'SEM GRUPO';
      if (!grupoData[grupo]) grupoData[grupo] = [];
      grupoData[grupo].push(item);
    });

    // Calcular totais por grupo
    let csvContent = '=== PEDIDO DE COMPRA - REPOSIÇÃO DE RUPTURAS CRÍTICAS ===\n';
    csvContent += `Data de Geração: ${new Date().toLocaleString('pt-BR')}\n`;
    csvContent += `Total de Produtos: ${items.length}\n`;
    csvContent += `Total de Grupos: ${Object.keys(grupoData).length}\n\n`;

    Object.entries(grupoData)
      .sort((a, b) => b[1].reduce((sum, i) => sum + i.NECESSIDADE, 0) - a[1].reduce((sum, i) => sum + i.NECESSIDADE, 0))
      .forEach(([grupo, produtos]) => {
        const totalNecessidade = produtos.reduce((sum, p) => sum + p.NECESSIDADE, 0);
        const totalCriticos = produtos.filter(p => p.CRITICIDADE_PCT >= 75).length;

        csvContent += `\n--- ${grupo.toUpperCase()} ---\n`;
        csvContent += `Produtos: ${produtos.length} | Críticos: ${totalCriticos} | Necessidade Total: ${Math.round(totalNecessidade)} un\n`;
        csvContent += 'Código,Nome,Necessidade (un),Criticidade %\n';

        produtos
          .sort((a, b) => b.CRITICIDADE_PCT - a.CRITICIDADE_PCT)
          .forEach(p => {
            csvContent += `${p.PRODUTO},"${p.NOME.substring(0, 50)}",${Math.round(p.NECESSIDADE)},${p.CRITICIDADE_PCT.toFixed(0)}%\n`;
          });
      });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pedido_compra_rupturas_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  onMount(() => {
    loadFilters();
    loadData();
  });

  const getCriticidadeColor = (pct: number) => {
    if (pct >= 75) return 'bg-red-500/20 text-red-500 border-red-500/30';
    if (pct >= 50) return 'bg-orange-500/20 text-orange-500 border-orange-500/30';
    if (pct >= 25) return 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30';
    return 'bg-blue-500/20 text-blue-500 border-blue-500/30';
  };

  const getCriticidadeLabel = (pct: number) => {
    if (pct >= 75) return 'CRÍTICO';
    if (pct >= 50) return 'ALTO';
    if (pct >= 25) return 'MÉDIO';
    return 'BAIXO';
  };

  return (
    <ErrorBoundary>
      <div class="flex flex-col p-6 gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div class="flex justify-between items-start">
        <div>
          <h2 class="text-2xl font-bold tracking-tight text-red-500 flex items-center gap-2">
            <AlertTriangle size={24} />
            Rupturas Críticas
          </h2>
          <p class="text-muted mt-1">CD zerado + Estoque loja abaixo da Linha Verde</p>
        </div>
        <div class="flex gap-2">
          <button onClick={() => {
            console.log("Toggling filters:", !showFilters());
            setShowFilters(!showFilters());
          }} class="btn btn-outline gap-2" aria-label={showFilters() ? 'Ocultar filtros' : 'Mostrar filtros'} aria-expanded={showFilters()}>
            <Filter size={16} />
            Filtros
          </button>
          <button
            onClick={exportPurchaseOrder}
            class="btn gap-2"
            style="background-color: #2D7A3E; color: white;"
            disabled={data().length === 0}
            title="Gerar arquivo para pedido de compra agrupado por categoria"
            aria-label="Gerar pedido de compra agrupado por categoria"
          >
            <ShoppingCart size={16} />
            Gerar Pedido de Compra
          </button>
          <button onClick={exportCSV} class="btn btn-outline gap-2" disabled={data().length === 0} aria-label="Exportar dados em CSV">
            <Download size={16} />
            CSV
          </button>
          <button onClick={loadData} class="btn btn-outline gap-2" disabled={loading()} aria-label={loading() ? 'Atualizando rupturas críticas' : 'Atualizar rupturas críticas'} aria-busy={loading()}>
            <RefreshCw size={16} class={loading() ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Filtros */}
      <Show when={showFilters()}>
        <div class="p-4 bg-card border rounded-lg" role="region" aria-label="Filtros de rupturas">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold">Filtros</h3>
            <button onClick={() => setShowFilters(false)} class="text-muted-foreground hover:text-foreground" aria-label="Fechar filtros">
              <X size={18} />
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label for="segmento-filter" class="block text-sm font-medium mb-2">Segmento</label>
              {/* ✅ CORREÇÃO MOBILE: min-h-[44px] para touch-friendly */}
              <select
                id="segmento-filter"
                class="w-full px-3 py-2 bg-background border rounded-lg disabled:opacity-50 min-h-[44px]"
                value={selectedSegmento()}
                onChange={(e) => setSelectedSegmento(e.target.value)}
                disabled={filtersLoading()}
                aria-label="Filtrar por segmento"
                aria-busy={filtersLoading()}
              >
                <Show when={!filtersLoading()} fallback={<option>Carregando filtros...</option>}>
                  <option value="">Todos</option>
                  <For each={segmentos()} fallback={<option disabled>Nenhum segmento disponível</option>}>
                    {(seg) => <option value={seg}>{seg}</option>}
                  </For>
                </Show>
              </select>
            </div>
            <div>
              <label for="une-filter" class="block text-sm font-medium mb-2">UNE</label>
              <select
                id="une-filter"
                class="w-full px-3 py-2 bg-background border rounded-lg disabled:opacity-50 min-h-[44px]"
                value={selectedUne()}
                onChange={(e) => setSelectedUne(e.target.value)}
                disabled={filtersLoading()}
                aria-label="Filtrar por UNE (loja)"
                aria-busy={filtersLoading()}
              >
                <Show when={!filtersLoading()} fallback={<option>Carregando filtros...</option>}>
                  <option value="">Todas</option>
                  <For each={unes()} fallback={<option disabled>Nenhuma UNE disponível</option>}>
                    {(une) => <option value={une}>{une}</option>}
                  </For>
                </Show>
              </select>
            </div>
            <div class="flex items-end gap-2">
              <button onClick={loadData} class="btn btn-primary flex-1" aria-label="Aplicar filtros selecionados" aria-busy={loading()}>
                Aplicar Filtros
              </button>
              <button onClick={clearFilters} class="btn btn-outline" aria-label="Limpar todos os filtros">
                <X size={16} />
              </button>
            </div>
          </div>
        </div>
      </Show>

      {/* Resumo de Métricas */}
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4" role="region" aria-label="Resumo de métricas de rupturas">
        <div class="p-4 bg-card border rounded-lg" role="article" aria-label="Total de rupturas críticas">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-red-500/10 rounded-lg">
              <PackageX size={24} class="text-red-500" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Total de Rupturas</p>
              <p class="text-2xl font-bold">{summary().total}</p>
            </div>
          </div>
        </div>
        <div class="p-4 bg-card border rounded-lg" role="article" aria-label="Produtos com criticidade alta">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-orange-500/10 rounded-lg">
              <AlertTriangle size={24} class="text-orange-500" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Criticidade Alta (≥75%)</p>
              <p class="text-2xl font-bold">{summary().criticos}</p>
            </div>
          </div>
        </div>
        <div class="p-4 bg-card border rounded-lg" role="article" aria-label="Taxa de criticidade">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-blue-500/10 rounded-lg">
              <TrendingUp size={24} class="text-blue-500" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Taxa Crítica</p>
              <p class="text-2xl font-bold">
                {summary().total > 0 ? ((summary().criticos / summary().total) * 100).toFixed(0) : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Explicação */}
      <div class="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
        <h3 class="font-semibold text-blue-500 mb-2">O que é Ruptura Crítica?</h3>
        <p class="text-sm text-muted-foreground">
          Produtos com <strong>estoque no CD zerado (ESTOQUE_CD = 0)</strong> e <strong>estoque da loja abaixo da Linha Verde (ESTOQUE_UNE &lt; ESTOQUE_LV)</strong> que tiveram vendas nos últimos 30 dias. A criticidade é calculada pela razão entre vendas e linha verde.
        </p>
      </div>

      {/* Gráficos Interativos */}
      <Show when={!loading() && data().length > 0}>
        <div class="space-y-6">
          {/* Primeira linha - 2 colunas */}
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de Pizza - Criticidade */}
            <div class="card p-6 border" role="region" aria-label="Gráfico de top grupos em ruptura">
              <div class="flex justify-between items-center mb-4">
                <h3 class="font-semibold flex items-center gap-2">
                  <PieChart size={20} class="text-red-500" />
                  Top Grupos em Ruptura
                </h3>
                <ChartDownloadButton
                  chartId="criticidade-chart"
                  filename="rupturas_criticidade"
                  label="Baixar"
                />
              </div>
              <PlotlyChart
                chartSpec={criticidadeChart}
                chartId="criticidade-chart"
                enableDownload={true}
                height="350px"
                onDataClick={handleGroupClick}
              />
              <p class="text-xs text-muted mt-2">💡 Clique nas barras para ver produtos do grupo</p>
            </div>

            {/* Gráfico de Barras - Top 10 */}
            <div class="card p-6 border" role="region" aria-label="Gráfico de top 10 produtos em ruptura">
              <div class="flex justify-between items-center mb-4">
                <h3 class="font-semibold flex items-center gap-2">
                  <BarChart3 size={20} class="text-orange-500" />
                  Top 10 Produtos em Ruptura
                </h3>
                <ChartDownloadButton
                  chartId="top-rupturas-chart"
                  filename="rupturas_top10"
                  label="Baixar"
                />
              </div>
              <PlotlyChart
                chartSpec={topRupturasChart}
                chartId="top-rupturas-chart"
                enableDownload={true}
                height="350px"
                onDataClick={handleChartClick}
              />
              <p class="text-xs text-muted mt-2">💡 Clique nas barras para ver detalhes do produto</p>
            </div>
          </div>

          {/* Segunda linha - 1 coluna */}
          <div class="card p-6 border" role="region" aria-label="Gráfico de necessidade por segmento">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-semibold flex items-center gap-2">
                <TrendingUp size={20} class="text-green-500" />
                Necessidade por Segmento
              </h3>
              <ChartDownloadButton
                chartId="necessidade-segmento-chart"
                filename="rupturas_por_segmento"
                label="Baixar"
              />
            </div>
            <PlotlyChart
              chartSpec={necessidadeSegmentoChart}
              chartId="necessidade-segmento-chart"
              enableDownload={true}
              height="400px"
            />
          </div>
        </div>
      </Show>

      {/* Modal de Detalhes do Produto */}
      <Show when={selectedProduct()}>
        <div
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedProduct(null)}
        >
          <div
            class="bg-card border rounded-lg p-6 max-w-2xl w-full"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="product-modal-title"
          >
            <div class="flex justify-between items-start mb-4">
              <h3 id="product-modal-title" class="text-xl font-bold">Detalhes da Ruptura</h3>
              <button
                onClick={() => setSelectedProduct(null)}
                class="text-muted hover:text-foreground"
                aria-label="Fechar detalhes do produto"
              >
                <X size={20} />
              </button>
            </div>

            <div class="space-y-4">
              <div>
                <p class="text-sm text-muted">Produto</p>
                <p class="font-mono font-medium">{selectedProduct()!.PRODUTO}</p>
              </div>
              <div>
                <p class="text-sm text-muted">Nome</p>
                <p class="font-medium">{selectedProduct()!.NOME}</p>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-muted">UNE / Loja</p>
                  <p class="font-medium">{selectedProduct()!.UNE} - {selectedProduct()!.UNE_NOME || 'N/A'}</p>
                </div>
                <div>
                  <p class="text-sm text-muted">Segmento</p>
                  <p class="font-medium">{selectedProduct()!.NOMESEGMENTO || 'N/A'}</p>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-4">
                <div class="p-3 bg-green-500/10 border border-green-500/30 rounded">
                  <p class="text-xs text-muted">Vendas (30d)</p>
                  <p class="text-xl font-bold text-green-500">{fmtNum(selectedProduct()!.VENDA_30DD)}</p>
                </div>
                <div class="p-3 bg-red-500/10 border border-red-500/30 rounded">
                  <p class="text-xs text-muted">Estoque Loja</p>
                  <p class="text-xl font-bold text-red-500">{fmtNum(selectedProduct()!.ESTOQUE_UNE)}</p>
                </div>
                <div class="p-3 bg-blue-500/10 border border-blue-500/30 rounded">
                  <p class="text-xs text-muted">Linha Verde</p>
                  <p class="text-xl font-bold text-blue-500">{fmtNum(selectedProduct()!.ESTOQUE_LV)}</p>
                </div>
              </div>
              <div class="p-4 bg-orange-500/10 border border-orange-500/30 rounded">
                <p class="text-sm text-muted mb-2">Necessidade de Reposição</p>
                <p class="text-3xl font-bold text-orange-500">{fmtNum(selectedProduct()!.NECESSIDADE)} unidades</p>
                <div class="mt-3">
                  <div class="flex justify-between text-sm mb-1">
                    <span>Criticidade</span>
                    <span class="font-medium">{selectedProduct()!.CRITICIDADE_PCT.toFixed(0)}%</span>
                  </div>
                  <div class="w-full bg-gray-700 rounded-full h-2">
                    <div
                      class={`h-2 rounded-full ${selectedProduct()!.CRITICIDADE_PCT >= 75 ? 'bg-red-500' :
                        selectedProduct()!.CRITICIDADE_PCT >= 50 ? 'bg-orange-500' :
                          selectedProduct()!.CRITICIDADE_PCT >= 25 ? 'bg-yellow-500' : 'bg-blue-500'
                        }`}
                      style={`width: ${selectedProduct()!.CRITICIDADE_PCT}%`}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedProduct(null)}
                class="btn btn-primary"
                aria-label="Fechar modal de detalhes"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      </Show>

      {/* Modal Drill-Down - Produtos do Grupo Selecionado */}
      <Show when={selectedGroup()}>
        {/* ✅ CORREÇÃO MOBILE: p-0 no mobile para fullscreen */}
        <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-[9998] p-0 md:p-4" onClick={(e) => e.target === e.currentTarget && setSelectedGroup(null)}>
          {/* ✅ CORREÇÃO MOBILE: fullscreen no mobile (h-full rounded-none), normal no desktop */}
          <div
            class="bg-background rounded-none md:rounded-xl shadow-xl max-w-4xl w-full h-full md:h-auto md:max-h-[85vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            role="dialog"
            aria-modal="true"
            aria-labelledby="group-modal-title"
            aria-describedby="group-modal-description"
          >
            {/* Header */}
            <div class="p-4 border-b bg-gradient-to-r from-red-500/10 to-orange-500/10">
              <div class="flex justify-between items-center">
                <div>
                  <h3 id="group-modal-title" class="text-xl font-bold flex items-center gap-2">
                    <Package size={24} class="text-red-500" />
                    Produtos em Ruptura: {selectedGroup()}
                  </h3>
                  <p id="group-modal-description" class="text-sm text-muted mt-1">
                    {getProductsByGroup().length} produtos | {getProductsByGroup().filter(p => p.CRITICIDADE_PCT >= 75).length} críticos
                  </p>
                </div>
                <button onClick={() => setSelectedGroup(null)} class="p-2 hover:bg-muted rounded-full" aria-label="Fechar modal de produtos do grupo">
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Tabela de Produtos */}
            <div class="overflow-auto max-h-[60vh] p-4">
              {/* ✅ CORREÇÃO MOBILE: Desktop - Table, Mobile - Cards */}

              {/* Desktop Table (hidden on mobile) */}
              <table class="w-full text-sm hidden md:table" role="table" aria-label={`Produtos em ruptura do grupo ${selectedGroup()}`}>
                <thead class="sticky top-0 bg-background">
                  <tr class="border-b">
                    <th class="text-left p-2 font-semibold">Código</th>
                    <th class="text-left p-2 font-semibold">Produto</th>
                    <th class="text-left p-2 font-semibold">UNE / Loja</th>
                    <th class="text-right p-2 font-semibold">Criticidade</th>
                    <th class="text-right p-2 font-semibold">Necessidade</th>
                    <th class="text-right p-2 font-semibold">Venda 30d</th>
                    <th class="text-right p-2 font-semibold">Estoque</th>
                  </tr>
                </thead>
                <tbody>
                  <For each={getProductsByGroup()}>
                    {(produto) => (
                      <tr class="border-b hover:bg-muted/50 transition-colors">
                        <td class="p-2 font-mono text-xs">{produto.PRODUTO}</td>
                        <td class="p-2 max-w-[200px] truncate" title={produto.NOME}>{produto.NOME}</td>
                        <td class="p-2">
                          <div class="flex flex-col">
                            <span class="text-xs font-mono">{produto.UNE}</span>
                            <span class="text-[10px] text-muted-foreground truncate max-w-[100px]" title={produto.UNE_NOME}>{produto.UNE_NOME}</span>
                          </div>
                        </td>
                        <td class="p-2 text-right">
                          <span class={`px-2 py-0.5 rounded text-xs font-bold ${produto.CRITICIDADE_PCT >= 75 ? 'bg-red-500/20 text-red-500' :
                            produto.CRITICIDADE_PCT >= 50 ? 'bg-orange-500/20 text-orange-500' :
                              produto.CRITICIDADE_PCT >= 25 ? 'bg-yellow-500/20 text-yellow-500' :
                                'bg-blue-500/20 text-blue-500'
                            }`}>
                            {produto.CRITICIDADE_PCT.toFixed(0)}%
                          </span>
                        </td>
                        <td class="p-2 text-right font-semibold text-red-500">{fmtNum(produto.NECESSIDADE)} un</td>
                        <td class="p-2 text-right">{fmtNum(produto.VENDA_30DD)}</td>
                        <td class="p-2 text-right text-muted">{fmtNum(produto.ESTOQUE_UNE)} / {fmtNum(produto.ESTOQUE_LV)}</td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>

              {/* Mobile Cards (shown only on mobile) */}
              <div class="md:hidden space-y-3">
                <For each={getProductsByGroup()}>
                  {(produto) => (
                    <div class="bg-card border rounded-lg p-3 space-y-2">
                      <div class="flex justify-between items-start">
                        <div class="flex-1">
                          <p class="font-medium text-sm leading-tight">{produto.NOME}</p>
                          <p class="text-xs font-mono text-muted-foreground mt-1">SKU: {produto.PRODUTO}</p>
                        </div>
                        <span class={`px-2 py-1 rounded text-xs font-bold shrink-0 ml-2 ${produto.CRITICIDADE_PCT >= 75 ? 'bg-red-500/20 text-red-500' :
                          produto.CRITICIDADE_PCT >= 50 ? 'bg-orange-500/20 text-orange-500' :
                            produto.CRITICIDADE_PCT >= 25 ? 'bg-yellow-500/20 text-yellow-500' :
                              'bg-blue-500/20 text-blue-500'
                          }`}>
                          {produto.CRITICIDADE_PCT.toFixed(0)}%
                        </span>
                      </div>
                      <div class="grid grid-cols-2 gap-2 text-xs pt-2 border-t">
                        <div>
                          <span class="text-muted-foreground">UNE:</span>
                          <span class="ml-1 font-mono">{produto.UNE}</span>
                        </div>
                        <div class="truncate">
                          <span class="text-muted-foreground">Loja:</span>
                          <span class="ml-1 text-xs">{produto.UNE_NOME}</span>
                        </div>
                      </div>
                      <div class="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span class="text-muted-foreground">Necessidade:</span>
                          <span class="ml-1 font-semibold text-red-500">{fmtNum(produto.NECESSIDADE)} un</span>
                        </div>
                        <div>
                          <span class="text-muted-foreground">Venda 30d:</span>
                          <span class="ml-1">{fmtNum(produto.VENDA_30DD)}</span>
                        </div>
                      </div>
                      <div class="text-xs pt-2 border-t">
                        <span class="text-muted-foreground">Estoque UNE / LV:</span>
                        <span class="ml-1">{fmtNum(produto.ESTOQUE_UNE)} / {fmtNum(produto.ESTOQUE_LV)}</span>
                      </div>
                    </div>
                  )}
                </For>
              </div>

              <Show when={getProductsByGroup().length === 0}>
                <div class="text-center py-8 text-muted">
                  <Package size={48} class="mx-auto mb-2 opacity-50" />
                  <p>Nenhum produto encontrado para este grupo</p>
                </div>
              </Show>
            </div>

            {/* Footer */}
            <div class="p-4 border-t flex justify-between items-center bg-muted/30">
              <div class="text-sm text-muted">
                Necessidade total: <strong class="text-red-500">{fmtNum(getProductsByGroup().reduce((sum, p) => sum + p.NECESSIDADE, 0))} un</strong>
              </div>
              <button
                onClick={() => setSelectedGroup(null)}
                class="btn btn-primary"
                aria-label="Fechar modal"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      </Show>

      {/* Tabela */}
      <Show when={!loading()} fallback={
        <div class="p-12 text-center border rounded-xl bg-card text-muted animate-pulse">
          <PackageX class="animate-spin mx-auto mb-4" size={32} />
          Identificando rupturas críticas...
        </div>
      }>
        <Show when={!error()} fallback={
          <div class="p-6 bg-red-900/10 border border-red-900/30 rounded-lg text-red-300 flex items-center gap-3">
            <AlertTriangle size={24} />
            <div>
              <h3 class="font-bold">Erro ao carregar dados</h3>
              <p class="text-sm opacity-80">{error()}</p>
            </div>
          </div>
        }>
          <Show when={data().length > 0} fallback={
            <div class="border border-dashed rounded-xl">
              {/* ✅ USABILIDADE: Empty State ilustrado */}
              <EmptyStateSuccess
                title="Nenhuma ruptura crítica detectada!"
                description="Todos os produtos de alta venda possuem estoque adequado."
              />
            </div>
          }>
            {/* ✅ CORREÇÃO MOBILE: Desktop - Table, Mobile - Cards */}

            {/* Desktop Table (hidden on mobile) */}
            <div class="border rounded-lg overflow-hidden bg-card shadow-sm hidden md:block" role="region" aria-label="Tabela de rupturas críticas">
              <div class="overflow-x-auto">
                <table class="w-full text-sm text-left" role="table" aria-label="Lista completa de rupturas críticas">
                  <thead class="bg-muted/50 text-xs uppercase font-medium text-muted-foreground border-b">
                    <tr>
                      <th class="px-4 py-3">Produto</th>
                      <th class="px-4 py-3">UNE</th>
                      <th class="px-4 py-3 text-right">Venda (30d)</th>
                      <th class="px-4 py-3 text-right">Est. Loja</th>
                      <th class="px-4 py-3 text-right">Est. CD</th>
                      <th class="px-4 py-3 text-right">Linha Verde</th>
                      <th class="px-4 py-3 text-right">Necessidade</th>
                      <th class="px-4 py-3 text-center">Criticidade</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y">
                    <For each={data()}>
                      {(item) => (
                        <tr class="hover:bg-muted/30 transition-colors">
                          <td class="px-4 py-3">
                            <div class="font-medium">{item.NOME}</div>
                            <div class="text-xs text-muted-foreground font-mono">{item.PRODUTO}</div>
                          </td>
                          <td class="px-4 py-3">
                            <div class="flex flex-col">
                              <span class="px-2 py-1 bg-secondary rounded text-xs font-mono w-fit">{item.UNE}</span>
                              <span class="text-[10px] text-muted-foreground mt-1 truncate max-w-[120px]" title={item.UNE_NOME}>{item.UNE_NOME}</span>
                            </div>
                          </td>
                          <td class="px-4 py-3 text-right font-medium">
                            <div class="flex items-center justify-end gap-1 text-green-500">
                              <ShoppingCart size={14} />
                              {Math.round(item.VENDA_30DD)}
                            </div>
                          </td>
                          <td class="px-4 py-3 text-right font-medium text-red-500">
                            <div class="flex items-center justify-end gap-1">
                              <Archive size={14} />
                              {Math.round(item.ESTOQUE_UNE)}
                            </div>
                          </td>
                          <td class="px-4 py-3 text-right font-medium text-red-500">
                            {Math.round(item.ESTOQUE_CD)}
                          </td>
                          <td class="px-4 py-3 text-right font-medium text-blue-500">
                            {Math.round(item.ESTOQUE_LV)}
                          </td>
                          <td class="px-4 py-3 text-right font-bold text-orange-500">
                            {Math.round(item.NECESSIDADE)} un
                          </td>
                          <td class="px-4 py-3 text-center">
                            <div class="flex flex-col items-center gap-1">
                              <span class={`px-2 py-1 rounded-full text-xs font-bold border ${getCriticidadeColor(item.CRITICIDADE_PCT)}`}>
                                {getCriticidadeLabel(item.CRITICIDADE_PCT)}
                              </span>
                              <div class="w-full bg-gray-700 rounded-full h-1.5 mt-1">
                                <div
                                  class={`h-1.5 rounded-full ${item.CRITICIDADE_PCT >= 75 ? 'bg-red-500' : item.CRITICIDADE_PCT >= 50 ? 'bg-orange-500' : item.CRITICIDADE_PCT >= 25 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                                  style={`width: ${item.CRITICIDADE_PCT}%`}
                                />
                              </div>
                              <span class="text-xs text-muted-foreground">{item.CRITICIDADE_PCT.toFixed(0)}%</span>
                            </div>
                          </td>
                        </tr>
                      )}
                    </For>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Mobile Cards (shown only on mobile) */}
            <div class="md:hidden space-y-3">
              <For each={data()}>
                {(item) => (
                  <div class="bg-card border-2 rounded-lg p-4 space-y-3 border-red-500/30">
                    {/* Header with Product and Criticidade */}
                    <div class="flex justify-between items-start gap-2">
                      <div class="flex-1">
                        <p class="font-semibold text-sm leading-tight">{item.NOME}</p>
                        <p class="text-xs font-mono text-muted-foreground mt-1">SKU: {item.PRODUTO}</p>
                      </div>
                      <span class={`px-2 py-1 rounded-full text-xs font-bold border shrink-0 ${getCriticidadeColor(item.CRITICIDADE_PCT)}`}>
                        {getCriticidadeLabel(item.CRITICIDADE_PCT)}
                      </span>
                    </div>

                    {/* UNE Badge */}
                    <div class="flex items-center gap-2">
                      <span class="px-2 py-1 bg-secondary rounded text-xs font-mono">{item.UNE}</span>
                      <span class="text-xs text-muted-foreground truncate">{item.UNE_NOME}</span>
                    </div>

                    {/* Criticidade Progress */}
                    <div class="pt-2 border-t">
                      <div class="flex justify-between items-center mb-1">
                        <span class="text-xs text-muted-foreground">Criticidade</span>
                        <span class="text-xs font-semibold">{item.CRITICIDADE_PCT.toFixed(0)}%</span>
                      </div>
                      <div class="w-full bg-gray-300 dark:bg-gray-700 rounded-full h-2">
                        <div
                          class={`h-2 rounded-full ${item.CRITICIDADE_PCT >= 75 ? 'bg-red-500' : item.CRITICIDADE_PCT >= 50 ? 'bg-orange-500' : item.CRITICIDADE_PCT >= 25 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                          style={`width: ${item.CRITICIDADE_PCT}%`}
                        />
                      </div>
                    </div>

                    {/* Metrics Grid */}
                    <div class="grid grid-cols-2 gap-3 pt-2 border-t text-xs">
                      <div class="space-y-1">
                        <div class="flex items-center gap-1 text-green-500">
                          <ShoppingCart size={12} />
                          <span class="text-muted-foreground">Venda 30d</span>
                        </div>
                        <p class="font-semibold">{Math.round(item.VENDA_30DD)} un</p>
                      </div>
                      <div class="space-y-1">
                        <div class="flex items-center gap-1 text-red-500">
                          <Archive size={12} />
                          <span class="text-muted-foreground">Est. Loja</span>
                        </div>
                        <p class="font-semibold text-red-500">{Math.round(item.ESTOQUE_UNE)} un</p>
                      </div>
                      <div class="space-y-1">
                        <span class="text-muted-foreground">Est. CD</span>
                        <p class="font-semibold text-red-500">{Math.round(item.ESTOQUE_CD)} un</p>
                      </div>
                      <div class="space-y-1">
                        <span class="text-muted-foreground">Linha Verde</span>
                        <p class="font-semibold text-blue-500">{Math.round(item.ESTOQUE_LV)} un</p>
                      </div>
                    </div>

                    {/* Necessidade Highlight */}
                    <div class="pt-2 border-t bg-orange-500/10 -mx-4 -mb-4 px-4 py-3 rounded-b-lg">
                      <div class="flex justify-between items-center">
                        <span class="text-xs font-medium text-muted-foreground">Necessidade de Transferência</span>
                        <span class="text-lg font-bold text-orange-500">{Math.round(item.NECESSIDADE)} un</span>
                      </div>
                    </div>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </Show>
      </Show>
      </div>
    </ErrorBoundary>
  );
}
