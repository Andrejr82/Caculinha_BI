import { For, Match, Show, Switch, createEffect, createMemo, createSignal, onMount } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import {
  AlertTriangle,
  BarChart3,
  Clock,
  DollarSign,
  FileText,
  Package,
  RefreshCw,
  Shield,
  Sparkles,
  Store,
  TrendingUp,
  Users,
} from 'lucide-solid';
import api from '../lib/api';
import { PlotlyChart } from '../components/PlotlyChart';
import { ChartDownloadButton } from '../components/ChartDownloadButton';

type Status = 'healthy' | 'warning' | 'critical' | 'loading';
type SupplierStatus = 'excellent' | 'good' | 'warning' | 'critical';
type TrendStatus = 'up' | 'stable' | 'down';
type InsightType = 'success' | 'warning' | 'info';
type InsightPriority = 'Alta' | 'Média' | 'Baixa';
type InsightSeverity = 'critical' | 'warning' | 'info' | 'success';
type KpiSeverity = 'critical' | 'warning' | 'info' | 'success';
type InsightScope = 'procurement' | 'products' | 'both';

type InsightItem = {
  type: InsightType;
  title: string;
  description: string;
  action: string;
  priority: InsightPriority;
  source: string;
  generatedAt: string;
  scope: InsightScope;
};

type TopProduct = { produto: string; nome: string; vendas: number };
type SpendPoint = { label: string; sales: number; stock: number };
type OperationBucket = { label: string; count: number; value: number; color: string };

type DashboardData = {
  kpis: {
    receitaTotal: number;
    margemMedia: number;
    activeSuppliers: number;
    alertasCriticos: number;
    totalProdutos: number;
    totalLojas: number;
    produtosRuptura: number;
    valorEstoque: number;
    taxaRupturaPercent: number;
    produtosAtivos: number;
  };
  spendAnalysis: SpendPoint[];
  suppliers: {
    id: string;
    name: string;
    onTimeDelivery: number;
    qualityScore: number;
    leadTimeDays: number;
    status: SupplierStatus;
    trend: TrendStatus;
  }[];
  purchaseOrders: OperationBucket[];
  topProdutos: TopProduct[];
  vendasPorCategoria: { categoria: string; vendas: number; produtos: number }[];
  insights: InsightItem[];
};

type SummaryResponse = { revenue: number };
type BusinessKpisResponse = {
  total_produtos: number;
  total_unes: number;
  produtos_ruptura: number;
  valor_estoque: number;
  top_produtos: { produto: string; nome: string; vendas: number }[];
  vendas_por_categoria: { categoria: string; vendas: number; produtos: number }[];
};
type TopProductsResponse = { product: string; productName: string; totalSales: number; revenue: number }[];
type SalesAnalysisResponse = {
  vendas_por_categoria: { categoria: string; vendas: number }[];
};
type SupplierMetricsResponse = {
  suppliers: {
    nome: string;
    lead_time_medio: number;
    taxa_ruptura: number;
    custo_medio: number;
    produtos_fornecidos: number;
    ultima_entrega: string;
  }[];
};
type ExecutiveKpisResponse = {
  vendas_total: number;
  margem_media: number;
  taxa_ruptura: number;
  produtos_ativos: number;
};
type CriticalAlertsResponse = { alerts: { type: string; message: string; timestamp: string }[] };
type TopVendidosResponse = {
  produtos: { produto: string; descricao: string; vendas: number; estoque: number; une: number; loja: string }[];
};
type RealTimeMetric = {
  id: string;
  title: string;
  value: string | number;
  severity: KpiSeverity;
  description: string;
  action?: string | null;
};
type RealTimeKpisResponse = {
  critical_alerts: RealTimeMetric[];
  performance: RealTimeMetric[];
  opportunities: RealTimeMetric[];
};

const EMPTY_DATA: DashboardData = {
  kpis: {
    receitaTotal: 0,
    margemMedia: 0,
    activeSuppliers: 0,
    alertasCriticos: 0,
    totalProdutos: 0,
    totalLojas: 0,
    produtosRuptura: 0,
    valorEstoque: 0,
    taxaRupturaPercent: 0,
    produtosAtivos: 0,
  },
  spendAnalysis: [],
  suppliers: [],
  purchaseOrders: [],
  topProdutos: [],
  vendasPorCategoria: [],
  insights: [],
};

const statusClass = (status: Status) =>
  status === 'healthy'
    ? 'bg-emerald-100 text-emerald-700'
    : status === 'warning'
      ? 'bg-amber-100 text-amber-700'
      : status === 'critical'
        ? 'bg-red-100 text-red-700'
        : 'bg-slate-100 text-slate-600';

const supplierLabel = (s: SupplierStatus) =>
  s === 'excellent' ? 'Excelente' : s === 'good' ? 'Bom' : s === 'warning' ? 'Atenção' : 'Crítico';

const supplierClass = (s: SupplierStatus) =>
  s === 'excellent'
    ? 'bg-emerald-100 text-emerald-700'
    : s === 'good'
      ? 'bg-sky-100 text-sky-700'
      : s === 'warning'
        ? 'bg-amber-100 text-amber-700'
        : 'bg-red-100 text-red-700';

const compactCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);

const money = (value: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(value);

const toNumber = (value: unknown): number => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

const bucketColor = (index: number) => {
  const colors = ['bg-amber-500', 'bg-emerald-500', 'bg-indigo-500', 'bg-sky-500', 'bg-rose-500'];
  return colors[index % colors.length];
};

const severityToInsightType = (severity: InsightSeverity): InsightType =>
  severity === 'success' ? 'success' : severity === 'critical' || severity === 'warning' ? 'warning' : 'info';

export default function DashboardPrototype() {
  const navigate = useNavigate();
  const [data, setData] = createSignal<DashboardData>(EMPTY_DATA);
  const [loading, setLoading] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [activeTab, setActiveTab] = createSignal<'procurement' | 'products'>('procurement');
  const [lastUpdate, setLastUpdate] = createSignal<Date>(new Date());
  const [selectedCategory, setSelectedCategory] = createSignal<string | null>(null);
  const [categoryBreakdown, setCategoryBreakdown] = createSignal<{ categoria: string; vendas: number }[]>([]);
  const [categoryLoading, setCategoryLoading] = createSignal(false);
  const [insightsGeneratedAt, setInsightsGeneratedAt] = createSignal<string>(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));
  const [insightsLoading, setInsightsLoading] = createSignal(false);
  const [insightsOffset, setInsightsOffset] = createSignal(0);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        summaryRes,
        businessRes,
        topProductsRes,
        salesAnalysisRes,
        supplierMetricsRes,
        executiveRes,
        criticalAlertsRes,
        topVendidosRes,
        realTimeRes,
      ] = await Promise.allSettled([
        api.get<SummaryResponse>('/metrics/summary'),
        api.get<BusinessKpisResponse>('/metrics/business-kpis'),
        api.get<TopProductsResponse>('/metrics/top-products?limit=10'),
        api.get<SalesAnalysisResponse>('/analytics/sales-analysis'),
        api.get<SupplierMetricsResponse>('/dashboard/suppliers/metrics'),
        api.get<ExecutiveKpisResponse>('/dashboard/metrics/executive-kpis'),
        api.get<CriticalAlertsResponse>('/dashboard/alerts/critical'),
        api.get<TopVendidosResponse>('/dashboard/top-vendidos'),
        api.get<RealTimeKpisResponse>('/metrics/real-time-kpis'),
      ]);

      const summary = summaryRes.status === 'fulfilled' ? summaryRes.value.data : null;
      const business = businessRes.status === 'fulfilled' ? businessRes.value.data : null;
      const topProducts = topProductsRes.status === 'fulfilled' ? topProductsRes.value.data : [];
      const salesAnalysis = salesAnalysisRes.status === 'fulfilled' ? salesAnalysisRes.value.data : null;
      const supplierMetrics = supplierMetricsRes.status === 'fulfilled' ? supplierMetricsRes.value.data.suppliers : [];
      const executive = executiveRes.status === 'fulfilled' ? executiveRes.value.data : null;
      const criticalAlerts = criticalAlertsRes.status === 'fulfilled' ? criticalAlertsRes.value.data.alerts : [];
      const topVendidos = topVendidosRes.status === 'fulfilled' ? topVendidosRes.value.data.produtos : [];
      const realTime = realTimeRes.status === 'fulfilled' ? realTimeRes.value.data : null;

      const supplierRows = supplierMetrics.map((item, index) => {
        const rupture = toNumber(item.taxa_ruptura);
        const status: SupplierStatus =
          rupture >= 20 ? 'critical' : rupture >= 12 ? 'warning' : rupture >= 6 ? 'good' : 'excellent';
        const trend: TrendStatus = status === 'excellent' || status === 'good' ? 'up' : 'down';
        const quality = Math.max(0, 100 - Math.round(rupture));
        return {
          id: `${index}-${item.nome}`,
          name: item.nome || `Fornecedor ${index + 1}`,
          onTimeDelivery: quality,
          qualityScore: quality,
          leadTimeDays: Math.max(0, Math.round(toNumber(item.lead_time_medio))),
          status,
          trend,
        };
      });

      const salesByStoreMap = new Map<string, SpendPoint>();
      for (const row of topVendidos) {
        const store = (row.loja || `UNE ${row.une || '-'}`).trim();
        const previous = salesByStoreMap.get(store) ?? { label: store, sales: 0, stock: 0 };
        previous.sales += toNumber(row.vendas);
        previous.stock += toNumber(row.estoque);
        salesByStoreMap.set(store, previous);
      }
      const spendAnalysis = Array.from(salesByStoreMap.values())
        .sort((a, b) => b.sales - a.sales)
        .slice(0, 6);

      const operationBuckets: OperationBucket[] = [
        {
          label: 'Alertas críticos',
          count: realTime?.critical_alerts.length ?? criticalAlerts.length,
          value: realTime?.critical_alerts.reduce((acc, item) => acc + toNumber(item.value), 0) ?? 0,
          color: bucketColor(0),
        },
        {
          label: 'Indicadores performance',
          count: realTime?.performance.length ?? 0,
          value: realTime?.performance.reduce((acc, item) => acc + toNumber(item.value), 0) ?? 0,
          color: bucketColor(1),
        },
        {
          label: 'Oportunidades',
          count: realTime?.opportunities.length ?? 0,
          value: realTime?.opportunities.reduce((acc, item) => acc + toNumber(item.value), 0) ?? 0,
          color: bucketColor(2),
        },
        {
          label: 'Top produtos monitorados',
          count: topProducts.length,
          value: topProducts.reduce((acc, item) => acc + toNumber(item.totalSales), 0),
          color: bucketColor(3),
        },
        {
          label: 'Fornecedores ativos',
          count: supplierRows.length,
          value: supplierRows.reduce((acc, item) => acc + toNumber(item.onTimeDelivery), 0),
          color: bucketColor(4),
        },
      ];

      const mappedTopProducts =
        topProducts.length > 0
          ? topProducts.map((item) => ({
              produto: item.product,
              nome: item.productName,
              vendas: toNumber(item.totalSales),
            }))
          : (business?.top_produtos ?? []).map((item) => ({
              produto: item.produto,
              nome: item.nome,
              vendas: toNumber(item.vendas),
            }));

      const categoryMap = new Map<string, { categoria: string; vendas: number; produtos: number }>();
      for (const item of business?.vendas_por_categoria ?? []) {
        categoryMap.set(item.categoria, {
          categoria: item.categoria,
          vendas: toNumber(item.vendas),
          produtos: toNumber(item.produtos),
        });
      }
      for (const item of salesAnalysis?.vendas_por_categoria ?? []) {
        const prev = categoryMap.get(item.categoria);
        categoryMap.set(item.categoria, {
          categoria: item.categoria,
          vendas: toNumber(item.vendas),
          produtos: prev?.produtos ?? 0,
        });
      }
      const vendasPorCategoria = Array.from(categoryMap.values())
        .sort((a, b) => b.vendas - a.vendas)
        .slice(0, 10);

      const produtosRuptura = toNumber(business?.produtos_ruptura) || Math.round(toNumber(executive?.taxa_ruptura));
      const totalProdutos = Math.max(1, toNumber(business?.total_produtos));
      const taxaRupturaPercent = (produtosRuptura / totalProdutos) * 100;
      const receitaTotal = toNumber(summary?.revenue) || toNumber(executive?.vendas_total);
      const margemMedia = toNumber(executive?.margem_media);
      const alertasCriticos = realTime?.critical_alerts.length ?? criticalAlerts.length;
      const topCategory = vendasPorCategoria[0];
      const lowestSupplier = [...supplierRows].sort((a, b) => a.onTimeDelivery - b.onTimeDelivery)[0];

      const dynamicInsights: InsightItem[] = [];
      for (const item of [...(realTime?.critical_alerts ?? []), ...(realTime?.performance ?? []), ...(realTime?.opportunities ?? [])]) {
        dynamicInsights.push({
          type: severityToInsightType(item.severity),
          title: item.title,
          description: item.description,
          action: item.action || 'Validar indicador e executar plano operacional.',
          priority: item.severity === 'critical' ? 'Alta' : item.severity === 'warning' ? 'Média' : 'Baixa',
          source: 'metrics/real-time-kpis',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: item.id.includes('perf') ? 'products' : 'procurement',
        });
      }

      for (const item of criticalAlerts) {
        dynamicInsights.push({
          type: item.type === 'critical' ? 'warning' : 'info',
          title: 'Alerta operacional',
          description: item.message,
          action: 'Priorizar análise do SKU/UNE alertado e abrir tratativa no time de compras.',
          priority: item.type === 'critical' ? 'Alta' : 'Média',
          source: 'dashboard/alerts/critical',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'procurement',
        });
      }

      if (taxaRupturaPercent >= 12) {
        dynamicInsights.push({
          type: 'warning',
          title: 'Ruptura acima do limite',
          description: `Taxa atual em ${taxaRupturaPercent.toFixed(1)}% (meta sugerida: <= 10%).`,
          action: 'Priorizar reposição dos grupos com maior impacto de venda nas próximas 24h.',
          priority: 'Alta',
          source: 'business-kpis',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'procurement',
        });
      }

      if (margemMedia > 0 && margemMedia < 25) {
        dynamicInsights.push({
          type: 'warning',
          title: 'Margem pressionada',
          description: `Margem média atual em ${margemMedia.toFixed(1)}%.`,
          action: 'Revisar negociação dos itens líderes e campanhas de baixo retorno.',
          priority: 'Média',
          source: 'executive-kpis',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'products',
        });
      }

      if (topCategory && topCategory.vendas > 0) {
        dynamicInsights.push({
          type: 'success',
          title: `Categoria destaque: ${topCategory.categoria}`,
          description: `Maior contribuição de vendas no momento (${topCategory.vendas.toLocaleString('pt-BR')}).`,
          action: `Garantir cobertura de estoque e ampliar exposição da categoria ${topCategory.categoria}.`,
          priority: 'Baixa',
          source: 'sales-analysis',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'products',
        });
      }

      if (lowestSupplier && (lowestSupplier.status === 'critical' || lowestSupplier.status === 'warning')) {
        dynamicInsights.push({
          type: 'warning',
          title: `Risco fornecedor: ${lowestSupplier.name}`,
          description: `Pontualidade em ${lowestSupplier.onTimeDelivery}% e lead time de ${lowestSupplier.leadTimeDays}d.`,
          action: 'Avaliar fornecedor alternativo e ajustar janela de pedido deste parceiro.',
          priority: lowestSupplier.status === 'critical' ? 'Alta' : 'Média',
          source: 'suppliers/metrics',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'procurement',
        });
      }

      if (receitaTotal > 0 && alertasCriticos <= 3) {
        dynamicInsights.push({
          type: 'success',
          title: 'Operação comercial estável',
          description: `Receita monitorada em ${compactCurrency(receitaTotal)} com baixo volume de alertas críticos.`,
          action: 'Manter rotina diária e concentrar melhorias em margem por categoria.',
          priority: 'Baixa',
          source: 'summary+alerts',
          generatedAt: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          scope: 'both',
        });
      }

      const priorityWeight: Record<InsightPriority, number> = { Alta: 3, Média: 2, Baixa: 1 };
      const dedupMap = new Map<string, InsightItem>();
      for (const insight of dynamicInsights) {
        const key = `${insight.title}|${insight.description}`;
        const existing = dedupMap.get(key);
        if (!existing || priorityWeight[insight.priority] > priorityWeight[existing.priority]) dedupMap.set(key, insight);
      }
      const insights = Array.from(dedupMap.values())
        .sort((a, b) => priorityWeight[b.priority] - priorityWeight[a.priority])
        .slice(0, 8);

      setData({
        kpis: {
          receitaTotal,
          margemMedia,
          activeSuppliers: supplierRows.length,
          alertasCriticos,
          totalProdutos,
          totalLojas: toNumber(business?.total_unes),
          produtosRuptura,
          valorEstoque: toNumber(business?.valor_estoque),
          taxaRupturaPercent,
          produtosAtivos: toNumber(executive?.produtos_ativos),
        },
        spendAnalysis,
        suppliers: supplierRows,
        purchaseOrders: operationBuckets,
        topProdutos: mappedTopProducts,
        vendasPorCategoria,
        insights,
      });
      setLastUpdate(new Date());
      setInsightsGeneratedAt(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));
    } catch {
      setError('Erro ao carregar métricas reais. Verifique backend e autenticação.');
    } finally {
      setLoading(false);
    }
  };

  onMount(() => {
    void loadDashboardData();
  });

  const businessStatus = createMemo<Status>(() => {
    if (loading()) return 'loading';
    const k = data().kpis;
    if (k.alertasCriticos > 20 || k.taxaRupturaPercent > 20) return 'critical';
    if (k.alertasCriticos > 5 || k.taxaRupturaPercent > 10) return 'warning';
    return 'healthy';
  });

  const handleRefresh = async () => {
    await loadDashboardData();
  };

  const handleInsightsRefresh = async () => {
    setInsightsLoading(true);
    await loadDashboardData();
    setInsightsOffset((prev) => {
      const total = data().insights.length;
      const maxStart = Math.max(0, total - 5);
      if (maxStart === 0) return 0;
      return prev >= maxStart ? 0 : prev + 1;
    });
    setInsightsLoading(false);
  };

  const loadCategoryBreakdown = async (categoria: string) => {
    setSelectedCategory(categoria);
    setCategoryLoading(true);
    try {
      const res = await api.get<SalesAnalysisResponse>(`/analytics/sales-analysis?categoria=${encodeURIComponent(categoria)}`);
      const breakdown = (res.data.vendas_por_categoria ?? []).sort((a, b) => toNumber(b.vendas) - toNumber(a.vendas)).slice(0, 10);
      setCategoryBreakdown(breakdown);
    } catch {
      setCategoryBreakdown([]);
    } finally {
      setCategoryLoading(false);
    }
  };

  const maxSpend = createMemo(() => Math.max(...data().spendAnalysis.map((x) => Math.max(x.sales, x.stock)), 1));
  const maxTop = createMemo(() => Math.max(...data().topProdutos.map((x) => x.vendas), 1));
  const maxCategory = createMemo(() => Math.max(...data().vendasPorCategoria.map((x) => x.vendas), 1));
  const categoryBreakdownChart = createMemo(() => {
    const rows = categoryBreakdown();
    if (!rows.length) return {};
    const labels = rows.map((r) => r.categoria);
    const values = rows.map((r) => toNumber(r.vendas));
    return {
      data: [
        {
          type: 'bar',
          orientation: 'h',
          y: labels,
          x: values,
          marker: { color: '#10b981' },
          text: values.map((v) => v.toLocaleString('pt-BR')),
          textposition: 'outside',
          hovertemplate: '<b>%{y}</b><br>Vendas: %{x:,.0f}<extra></extra>',
        },
      ],
      layout: {
        title: {
          text: `Detalhamento da Categoria: ${selectedCategory() || ''}`,
          font: { size: 14, color: '#0f172a' },
          x: 0.02,
        },
        margin: { l: 170, r: 20, t: 45, b: 30 },
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#ffffff',
        xaxis: { gridcolor: '#e2e8f0', tickfont: { size: 11 } },
        yaxis: { automargin: true, tickfont: { size: 11 } },
      },
      config: { responsive: true, displayModeBar: false },
    };
  });

  const insightsPool = createMemo(() => {
    const all = data().insights;
    const scoped = all.filter((insight) => insight.scope === 'both' || insight.scope === activeTab());
    if (scoped.length > 0) return scoped;
    const shared = all.filter((insight) => insight.scope === 'both');
    if (shared.length > 0) return shared;
    return all;
  });

  createEffect(() => {
    const total = insightsPool().length;
    const maxStart = Math.max(0, total - 5);
    if (insightsOffset() > maxStart) setInsightsOffset(0);
  });

  createEffect(() => {
    activeTab();
    setInsightsOffset(0);
  });

  const visibleInsights = createMemo(() => insightsPool().slice(insightsOffset(), insightsOffset() + 5));

  return (
    <div class="relative min-h-screen bg-slate-50 overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-100/40 via-white to-amber-100/30 pointer-events-none" />

      <div class="relative z-10 max-w-[1600px] mx-auto p-6 space-y-6">
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-slate-200/70">
          <div>
            <h1 class="text-3xl font-bold text-slate-900">Olá, Comprador</h1>
            <div class="flex items-center gap-3 mt-3">
              <span class={`px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass(businessStatus())}`}>
                <Switch>
                  <Match when={businessStatus() === 'healthy'}>Operação Saudável</Match>
                  <Match when={businessStatus() === 'warning'}>Atenção Operacional</Match>
                  <Match when={businessStatus() === 'critical'}>Operação Crítica</Match>
                  <Match when={true}>Carregando...</Match>
                </Switch>
              </span>
              <span class="text-sm text-slate-500">Central de Compras • Dashboard Estratégico</span>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <div class="hidden md:flex items-center gap-2 text-xs text-slate-500">
              <Clock size={14} />
              Atualizado às{' '}
              <span class="font-medium text-slate-700">
                {lastUpdate().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <button
              class="h-10 w-10 rounded-lg border border-slate-200 bg-white flex items-center justify-center hover:bg-slate-50 disabled:opacity-60"
              onClick={handleRefresh}
              disabled={loading()}
              aria-label="Atualizar"
            >
              <RefreshCw size={18} class={loading() ? 'animate-spin text-emerald-600' : 'text-slate-600'} />
            </button>
          </div>
        </header>

        <Show when={error()}>
          <div class="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error()}</div>
        </Show>

        <section class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <article class="rounded-xl border bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">Receita Total</p><p class="text-2xl font-bold mt-1">{compactCurrency(data().kpis.receitaTotal)}</p><p class="text-xs text-slate-500 mt-1">Base /metrics/summary</p></article>
          <article class="rounded-xl border border-emerald-200 bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">Margem Média</p><p class="text-2xl font-bold mt-1">{data().kpis.margemMedia.toFixed(1)}%</p><p class="text-xs text-slate-500 mt-1">Base /dashboard/executive-kpis</p></article>
          <article class="rounded-xl border bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">Valor Estoque</p><p class="text-2xl font-bold mt-1">{compactCurrency(data().kpis.valorEstoque)}</p><p class="text-xs text-slate-500 mt-1">Capital imobilizado</p></article>
          <article class="rounded-xl border border-amber-200 bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">Rupturas</p><p class="text-2xl font-bold mt-1">{data().kpis.produtosRuptura}</p><p class="text-xs text-slate-500 mt-1">Atenção</p></article>
          <article class="rounded-xl border bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">Fornecedores</p><p class="text-2xl font-bold mt-1">{data().kpis.activeSuppliers}</p><p class="text-xs text-slate-500 mt-1">{data().kpis.alertasCriticos} alertas críticos</p></article>
          <article class="rounded-xl border bg-white p-4 shadow-sm"><p class="text-xs text-slate-500">UNEs Ativas</p><p class="text-2xl font-bold mt-1">{data().kpis.totalLojas}</p><p class="text-xs text-slate-500 mt-1">{data().kpis.produtosAtivos} produtos ativos</p></article>
        </section>

        <section>
          <div class="inline-grid grid-cols-2 p-1 rounded-xl border bg-white shadow-sm mb-6">
            <button
              class={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 ${activeTab() === 'procurement' ? 'bg-slate-900 text-white' : 'text-slate-700'}`}
              onClick={() => setActiveTab('procurement')}
            >
              <Shield size={16} /> Compras & Fornecedores
            </button>
            <button
              class={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 ${activeTab() === 'products' ? 'bg-slate-900 text-white' : 'text-slate-700'}`}
              onClick={() => setActiveTab('products')}
            >
              <TrendingUp size={16} /> Produtos & Vendas
            </button>
          </div>

          <Show when={activeTab() === 'procurement'}>
            <div class="space-y-6">
              <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <article class="lg:col-span-2 rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Vendas por UNE (Top 6)</h3>
                  <p class="text-xs text-slate-500">Consolidado real a partir de /dashboard/top-vendidos</p>
                  <div class="h-56 flex items-end gap-3 mt-4">
                    <For each={data().spendAnalysis}>
                      {(point) => (
                        <div class="flex-1 flex flex-col items-center gap-2">
                          <div class="w-full grid grid-cols-2 gap-1 items-end h-44">
                            <div class="bg-slate-300 rounded-t" style={{ height: `${(point.stock / maxSpend()) * 100}%` }} />
                            <div class="bg-emerald-400 rounded-t" style={{ height: `${(point.sales / maxSpend()) * 100}%` }} />
                          </div>
                          <div class="text-xs text-slate-600 truncate max-w-[90px]">{point.label}</div>
                        </div>
                      )}
                    </For>
                  </div>
                  <div class="mt-2 text-xs text-slate-500">Cinza: estoque | Verde: vendas</div>
                </article>

                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Resumo Executivo</h3>
                  <p class="text-xs text-slate-500">Indicadores reais de vendas e ruptura</p>
                  <div class="mt-4 text-2xl font-bold">{money(data().kpis.receitaTotal)}</div>
                  <div class="text-xs text-slate-500">Receita monitorada no período</div>
                  <div class="grid grid-cols-2 gap-2 mt-4 text-sm">
                    <div class="rounded-lg border p-2"><p class="text-xs text-slate-500">Margem Média</p><p class="font-semibold">{data().kpis.margemMedia.toFixed(1)}%</p></div>
                    <div class="rounded-lg border p-2"><p class="text-xs text-slate-500">Taxa Ruptura</p><p class="font-semibold">{data().kpis.taxaRupturaPercent.toFixed(1)}%</p></div>
                  </div>
                  <p class="text-xs text-emerald-700 mt-3">Base consolidada por APIs internas.</p>
                </article>
              </section>

              <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Fila Operacional</h3>
                  <p class="text-xs text-slate-500">Eventos reais consolidados por tipo</p>
                  <div class="space-y-3 mt-4">
                    <For each={data().purchaseOrders}>
                      {(p) => {
                        const total = data().purchaseOrders.reduce((acc, i) => acc + i.count, 0) || 1;
                        const width = (p.count / total) * 100;
                        const formattedValue = Math.round(p.value).toLocaleString('pt-BR');
                        const detailText =
                          p.label === 'Alertas críticos'
                            ? `${formattedValue} de impacto agregado`
                            : p.label === 'Indicadores performance'
                              ? `${formattedValue} de score agregado`
                              : p.label === 'Oportunidades'
                                ? `${formattedValue} de potencial estimado`
                                : p.label === 'Top produtos monitorados'
                                  ? `${formattedValue} vendas acumuladas`
                                  : `${p.count > 0 ? (p.value / p.count).toFixed(1) : '0.0'}% média de pontualidade`;
                        const countText =
                          p.label === 'Alertas críticos'
                            ? `${p.count} alertas`
                            : p.label === 'Indicadores performance'
                              ? `${p.count} indicadores`
                              : p.label === 'Oportunidades'
                                ? `${p.count} oportunidades`
                                : p.label === 'Top produtos monitorados'
                                  ? `${p.count} produtos`
                                  : `${p.count} fornecedores`;
                        return (
                          <div>
                            <div class="flex justify-between text-sm"><span>{p.label}</span><span>{countText}</span></div>
                            <div class="text-xs text-slate-500 mt-0.5">{detailText}</div>
                            <div class="h-2 mt-1 bg-slate-100 rounded-full overflow-hidden"><div class={`h-full ${p.color}`} style={{ width: `${width}%` }} /></div>
                          </div>
                        );
                      }}
                    </For>
                  </div>
                </article>

                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Taxa de Ruptura</h3>
                  <p class="text-xs text-slate-500">Percentual de itens em ruptura no portfólio</p>
                  <div class="mt-4 flex justify-center">
                    <div
                      class="w-28 h-28 rounded-full grid place-items-center"
                      style={{
                        background: `conic-gradient(#f59e0b ${Math.min(data().kpis.taxaRupturaPercent, 100) * 3.6}deg, #e2e8f0 0deg)`,
                      }}
                    >
                      <div class="w-20 h-20 rounded-full bg-white grid place-items-center">
                        <span class="text-xl font-bold">{data().kpis.taxaRupturaPercent.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3">
                    <p class="text-xs text-amber-700">Produtos em Ruptura</p>
                    <p class="text-sm font-semibold text-amber-800">{data().kpis.produtosRuptura} de {data().kpis.totalProdutos}</p>
                  </div>
                </article>

                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Performance de Fornecedores</h3>
                  <p class="text-xs text-slate-500">Top fornecedores ativos (visão resumida)</p>
                  <div class="space-y-3 mt-4 max-h-[420px] overflow-y-auto pr-1">
                    <For each={data().suppliers.slice(0, 10)}>
                      {(s) => (
                        <div class="rounded-lg border border-slate-200 p-3 hover:border-slate-300 transition-colors">
                          <div class="flex items-center justify-between">
                            <p class="font-semibold text-sm text-slate-800">{s.name}</p>
                            <span class={`text-[11px] font-semibold px-2 py-1 rounded-full ${supplierClass(s.status)}`}>{supplierLabel(s.status)}</span>
                          </div>
                          <div class="mt-2 space-y-1.5 text-xs text-slate-600">
                            <div class="flex justify-between"><span>Pontualidade</span><span>{s.onTimeDelivery}%</span></div>
                            <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden"><div class="h-full bg-emerald-500" style={{ width: `${s.onTimeDelivery}%` }} /></div>
                            <div class="flex justify-between"><span>Qualidade</span><span>{s.qualityScore}%</span></div>
                            <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden"><div class="h-full bg-sky-500" style={{ width: `${s.qualityScore}%` }} /></div>
                            <div class="flex justify-between"><span>Lead Time</span><span>{s.leadTimeDays}d</span></div>
                          </div>
                        </div>
                      )}
                    </For>
                  </div>
                </article>
              </section>
            </div>
          </Show>

          <Show when={activeTab() === 'products'}>
            <div class="space-y-6">
              <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Quais produtos impulsionam as vendas?</h3>
                  <p class="text-xs text-slate-500">Volume de vendas nos últimos 30 dias</p>
                  <div class="space-y-2 mt-4">
                    <For each={data().topProdutos.slice(0, 8)}>
                      {(p) => (
                        <div>
                          <div class="flex justify-between text-xs"><span class="truncate max-w-[70%]">{p.nome}</span><span>{p.vendas.toLocaleString('pt-BR')}</span></div>
                          <div class="h-2 bg-slate-100 rounded-full overflow-hidden mt-1"><div class="h-full bg-emerald-500" style={{ width: `${(p.vendas / maxTop()) * 100}%` }} /></div>
                        </div>
                      )}
                    </For>
                  </div>
                </article>

                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Como as vendas estão distribuídas?</h3>
                  <p class="text-xs text-slate-500">Participação por categoria de produto</p>
                  <div class="space-y-2 mt-4">
                    <For each={data().vendasPorCategoria}>
                      {(c) => (
                        <div>
                          <div class="flex justify-between text-xs"><span>{c.categoria}</span><span>{c.vendas.toLocaleString('pt-BR')}</span></div>
                          <div class="h-2 bg-slate-100 rounded-full overflow-hidden mt-1"><div class="h-full bg-indigo-500" style={{ width: `${(c.vendas / maxCategory()) * 100}%` }} /></div>
                        </div>
                      )}
                    </For>
                  </div>
                </article>
              </section>

              <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <article class="lg:col-span-2 rounded-xl border bg-white p-6 shadow-sm">
                  <div class="flex items-center gap-3 mb-6">
                    <div class="p-2 rounded-lg bg-emerald-100"><Package size={20} class="text-emerald-700" /></div>
                    <div>
                      <h3 class="font-semibold text-slate-900">Análise de Categorias</h3>
                      <p class="text-sm text-slate-500">Performance por segmento de produto</p>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <For each={data().vendasPorCategoria.slice(0, 4)}>
                      {(cat) => (
                        <button
                          class={`p-4 rounded-xl bg-slate-50 border text-left hover:border-emerald-300 transition-colors cursor-pointer ${selectedCategory() === cat.categoria ? 'border-emerald-400 ring-2 ring-emerald-100' : 'border-slate-200'}`}
                          onClick={() => loadCategoryBreakdown(cat.categoria)}
                        >
                          <p class="text-sm font-medium text-slate-800">{cat.categoria}</p>
                          <p class="text-2xl font-bold text-slate-900 mt-2">{cat.vendas.toLocaleString('pt-BR')}</p>
                          <p class="text-xs text-slate-500 mt-1">{cat.produtos} produtos</p>
                        </button>
                      )}
                    </For>
                  </div>
                  <Show when={selectedCategory()}>
                    <div class="mt-5 border-t pt-4">
                      <div class="flex items-center justify-between mb-3">
                        <p class="text-sm font-semibold text-slate-800">Detalhamento: {selectedCategory()}</p>
                        <Show when={categoryLoading()}>
                          <span class="text-xs text-slate-500">Carregando...</span>
                        </Show>
                      </div>
                      <Show
                        when={!categoryLoading() && categoryBreakdown().length > 0}
                        fallback={<div class="text-xs text-slate-500 mt-2">Sem detalhamento disponível para esta categoria.</div>}
                      >
                        <div class="rounded-lg border border-slate-200 bg-white p-3">
                          <div class="flex justify-end mb-2">
                            <ChartDownloadButton chartId="dashboard-category-drilldown-chart" filename="dashboard_categoria_detalhamento" label="Baixar" />
                          </div>
                          <PlotlyChart chartSpec={categoryBreakdownChart} chartId="dashboard-category-drilldown-chart" height="320px" />
                        </div>
                      </Show>
                    </div>
                  </Show>
                </article>

                <article class="rounded-xl border bg-white p-5 shadow-sm">
                  <h3 class="font-semibold text-slate-900">Top Produtos</h3>
                  <p class="text-xs text-slate-500 mb-3">Ranking dos mais vendidos</p>
                  <div class="space-y-2">
                    <For each={data().topProdutos.slice(0, 8)}>
                      {(p, i) => (
                        <div class="rounded-lg border border-slate-200 p-2">
                          <div class="flex justify-between text-xs">
                            <span class="font-semibold text-slate-700">#{i() + 1} {p.produto}</span>
                            <span>{p.vendas.toLocaleString('pt-BR')}</span>
                          </div>
                          <p class="text-xs text-slate-500 mt-1 truncate">{p.nome}</p>
                        </div>
                      )}
                    </For>
                  </div>
                </article>
              </section>
            </div>
          </Show>
        </section>

        <section class="rounded-xl border bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between gap-3 mb-6">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-gradient-to-br from-emerald-100 to-sky-100"><Sparkles size={20} class="text-emerald-700" /></div>
              <div>
                <h3 class="font-semibold text-slate-900">Insights para Decisão</h3>
                <p class="text-sm text-slate-500">Recomendações dinâmicas com base nos KPIs atuais • atualizado às {insightsGeneratedAt()}</p>
              </div>
            </div>
            <button
              class="h-9 px-3 rounded-lg border border-slate-200 bg-white flex items-center gap-2 hover:bg-slate-50 disabled:opacity-60 text-sm"
              onClick={handleInsightsRefresh}
              disabled={insightsLoading()}
            >
              <RefreshCw size={14} class={insightsLoading() ? 'animate-spin text-emerald-600' : 'text-slate-600'} />
              Atualizar Insights
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            <For each={visibleInsights()}>
              {(insight) => {
                const box =
                  insight.type === 'success'
                    ? 'bg-emerald-50 border-emerald-200 hover:border-emerald-300'
                    : insight.type === 'warning'
                      ? 'bg-amber-50 border-amber-200 hover:border-amber-300'
                      : 'bg-sky-50 border-sky-200 hover:border-sky-300';
                const dot = insight.type === 'success' ? 'bg-emerald-500' : insight.type === 'warning' ? 'bg-amber-500' : 'bg-sky-500';
                const priorityClass =
                  insight.priority === 'Alta'
                    ? 'bg-red-100 text-red-700'
                    : insight.priority === 'Média'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-slate-100 text-slate-600';
                return (
                  <div class={`p-4 rounded-xl border transition-all hover:shadow-sm cursor-pointer ${box}`}>
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <div class="flex items-center gap-2">
                        <div class={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                        <span class={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${priorityClass}`}>{insight.priority}</span>
                      </div>
                      <span class="text-[10px] text-slate-500">{insight.source}</span>
                    </div>
                    <div class="flex items-start gap-3">
                      <div>
                        <p class="font-medium text-slate-800 text-sm">{insight.title}</p>
                        <p class="text-xs text-slate-600 mt-1 line-clamp-2">{insight.description}</p>
                        <p class="text-[11px] text-slate-700 mt-2"><span class="font-semibold">Ação:</span> {insight.action}</p>
                      </div>
                    </div>
                  </div>
                );
              }}
            </For>
          </div>
          <Show when={visibleInsights().length === 0}>
            <div class="text-sm text-slate-500 mt-2">Sem insights disponíveis no momento.</div>
          </Show>
        </section>

        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button class="group flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 hover:border-emerald-300 hover:shadow-sm transition-all">
            <div class="p-2 rounded-lg bg-emerald-100"><FileText size={18} class="text-emerald-700" /></div>
            <span class="font-medium text-slate-800">Novo Pedido</span>
          </button>
          <button
            class="group flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 hover:border-sky-300 hover:shadow-sm transition-all"
            onClick={() => navigate('/suppliers')}
          >
            <div class="p-2 rounded-lg bg-sky-100"><Users size={18} class="text-sky-700" /></div>
            <span class="font-medium text-slate-800">Fornecedores</span>
          </button>
          <button
            class="group flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 hover:border-indigo-300 hover:shadow-sm transition-all"
            onClick={() => navigate('/reports')}
          >
            <div class="p-2 rounded-lg bg-indigo-100"><BarChart3 size={18} class="text-indigo-700" /></div>
            <span class="font-medium text-slate-800">Relatórios</span>
          </button>
          <button class="group flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 hover:border-amber-300 hover:shadow-sm transition-all">
            <div class="p-2 rounded-lg bg-amber-100"><AlertTriangle size={18} class="text-amber-700" /></div>
            <span class="font-medium text-slate-800">Alertas</span>
          </button>
        </section>
      </div>
    </div>
  );
}
