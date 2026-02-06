import { createSignal, onMount, Show, For } from 'solid-js';
import { AlertTriangle, TrendingUp, TrendingDown, Package, DollarSign, Zap, Clock } from 'lucide-solid';
import api from '../lib/api';

interface KPIMetric {
  id: string;
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  severity: 'critical' | 'warning' | 'info' | 'success';
  description: string;
  action?: string;
}

interface RealTimeKPIsData {
  critical_alerts: KPIMetric[];
  performance: KPIMetric[];
  opportunities: KPIMetric[];
  generated_at: string;
  calculation_time_ms: number;
}

export function RealTimeKPIs() {
  const [data, setData] = createSignal<RealTimeKPIsData | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);

  const loadKPIs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<RealTimeKPIsData>('/metrics/real-time-kpis');
      setData(response.data);
    } catch (err: any) {
      console.error('Erro ao carregar KPIs real-time:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar métricas');
    } finally {
      setLoading(false);
    }
  };

  onMount(() => {
    loadKPIs();
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'success': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle size={18} class="text-red-500" />;
      case 'warning': return <Clock size={18} class="text-yellow-500" />;
      case 'success': return <TrendingUp size={18} class="text-green-500" />;
      default: return <Zap size={18} class="text-blue-500" />;
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up': return <TrendingUp size={14} class="text-green-500" />;
      case 'down': return <TrendingDown size={14} class="text-red-500" />;
      default: return null;
    }
  };

  const renderMetricCard = (metric: KPIMetric) => (
    <div class={`border rounded-lg p-4 ${getSeverityColor(metric.severity)} transition-all hover:shadow-md`}>
      <div class="flex items-start justify-between mb-2">
        <div class="flex items-center gap-2">
          {getSeverityIcon(metric.severity)}
          <h4 class="font-semibold text-sm">{metric.title}</h4>
        </div>
        <Show when={metric.trend}>
          {getTrendIcon(metric.trend)}
        </Show>
      </div>

      <div class="mb-2">
        <div class="flex items-baseline gap-2">
          <span class="text-2xl font-bold">{metric.value}</span>
          <Show when={metric.change !== undefined}>
            <span class={`text-xs font-medium ${metric.change! > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metric.change! > 0 ? '+' : ''}{metric.change}%
            </span>
          </Show>
        </div>
      </div>

      <p class="text-xs opacity-80 mb-2">{metric.description}</p>

      <Show when={metric.action}>
        <button class="text-xs font-medium underline hover:no-underline">
          {metric.action}
        </button>
      </Show>
    </div>
  );

  return (
    <div class="space-y-6">
      {/* Header */}
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Zap size={24} class="text-primary" />
          <div>
            <h3 class="text-lg font-bold">Métricas em Tempo Real</h3>
            <p class="text-xs text-muted">Cálculos DuckDB - Sem consumo de tokens AI</p>
          </div>
        </div>
        <Show when={!loading() && data()}>
          <div class="text-right">
            <div class="text-xs text-muted">Calculado em</div>
            <div class="text-sm font-mono font-bold">{data()!.calculation_time_ms}ms</div>
          </div>
        </Show>
      </div>

      {/* Loading State */}
      <Show when={loading()}>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(() => (
            <div class="border rounded-lg p-4 bg-muted/20 animate-pulse">
              <div class="h-4 bg-muted rounded w-3/4 mb-3"></div>
              <div class="h-8 bg-muted rounded w-1/2 mb-2"></div>
              <div class="h-3 bg-muted rounded w-full"></div>
            </div>
          ))}
        </div>
      </Show>

      {/* Error State */}
      <Show when={error()}>
        <div class="p-4 border border-red-500/50 bg-red-500/10 rounded-lg text-red-500 flex items-center gap-3">
          <AlertTriangle size={20} />
          <div class="text-sm">{error()}</div>
        </div>
      </Show>

      {/* KPIs Content */}
      <Show when={!loading() && data()}>
        {/* Critical Alerts */}
        <Show when={data()!.critical_alerts.length > 0}>
          <div>
            <div class="flex items-center gap-2 mb-3">
              <AlertTriangle size={18} class="text-red-500" />
              <h4 class="font-semibold text-sm text-red-700">Alertas Críticos</h4>
              <span class="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                {data()!.critical_alerts.length}
              </span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <For each={data()!.critical_alerts}>
                {(metric) => renderMetricCard(metric)}
              </For>
            </div>
          </div>
        </Show>

        {/* Performance Metrics */}
        <Show when={data()!.performance.length > 0}>
          <div>
            <div class="flex items-center gap-2 mb-3">
              <TrendingUp size={18} class="text-blue-500" />
              <h4 class="font-semibold text-sm text-blue-700">Performance</h4>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <For each={data()!.performance}>
                {(metric) => renderMetricCard(metric)}
              </For>
            </div>
          </div>
        </Show>

        {/* Opportunities */}
        <Show when={data()!.opportunities.length > 0}>
          <div>
            <div class="flex items-center gap-2 mb-3">
              <DollarSign size={18} class="text-green-500" />
              <h4 class="font-semibold text-sm text-green-700">Oportunidades</h4>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <For each={data()!.opportunities}>
                {(metric) => renderMetricCard(metric)}
              </For>
            </div>
          </div>
        </Show>
      </Show>
    </div>
  );
}
