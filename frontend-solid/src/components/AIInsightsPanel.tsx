import { createSignal, createResource, For, Show } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { Lightbulb, TrendingUp, AlertTriangle, Target, Sparkles, RefreshCw } from 'lucide-solid';
import api from '../lib/api';
import auth from '@/store/auth';

interface Insight {
  id: string;
  title: string;
  description: string;
  category: 'trend' | 'anomaly' | 'opportunity' | 'risk';
  severity: 'low' | 'medium' | 'high';
  recommendation: string | null;
  data_points: any[] | null;
  created_at: string;
}

interface InsightsData {
  insights: Insight[];
  total: number;
  generated_at: string;
  cached?: boolean;
  cache_age_hours?: number;
}

export function AIInsightsPanel() {
  const navigate = useNavigate();
  const [isRefreshing, setIsRefreshing] = createSignal(false);

  const fetchInsights = async (): Promise<InsightsData> => {
    try {
      // Use endpoint from insights.py: router prefix '/insights' + endpoint '/proactive'
      const response = await api.get<InsightsData>('/insights/proactive');
      return response.data;
    } catch (err) {
      console.error('Failed to fetch insights:', err);
      return {
        insights: [],
        total: 0,
        generated_at: new Date().toISOString(),
        cached: false
      };
    }
  };

  const [insights, { refetch }] = createResource(fetchInsights);

  const refreshInsights = async () => {
    setIsRefreshing(true);
    await refetch();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleInsightClick = (insight: Insight) => {
    // Smart Routing baseada na categoria do insight
    // Redireciona o gestor para a tela onde ele pode tomar ação
    switch (insight.category) {
      case 'risk':
      case 'anomaly':
        // Riscos e anomalias -> Torre de Controle (Suppliers/Rupturas)
        navigate('/suppliers');
        break;
      case 'opportunity':
        // Oportunidades -> Central de Compras (Forecasting)
        navigate('/forecasting');
        break;
      case 'trend':
        // Tendências -> Central de Compras ou Performance
        navigate('/forecasting');
        break;
      default:
        // Padrão -> Dashboard Principal (Seguro)
        navigate('/dashboard');
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'trend': return <TrendingUp size={20} />;
      case 'anomaly': return <AlertTriangle size={20} />;
      case 'opportunity': return <Target size={20} />;
      case 'risk': return <AlertTriangle size={20} />;
      default: return <Lightbulb size={20} />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'trend': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      case 'anomaly': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      case 'opportunity': return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
      case 'risk': return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-green-500/20 text-green-600 border-green-500/30',
      medium: 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30',
      high: 'bg-red-500/20 text-red-600 border-red-500/30 font-bold'
    };

    return colors[severity as keyof typeof colors] || colors.low;
  };

  return (
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex flex-col">
          <div class="flex items-center gap-2">
            <Sparkles class="text-primary" size={24} />
            <h3 class="text-xl font-bold tracking-tight">Insights Estratégicos</h3>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            Análise baseada em tendências de varejo e estoque
          </p>
        </div>
        <button
          onClick={refreshInsights}
          disabled={isRefreshing() || insights.loading}
          class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border hover:bg-muted transition-colors disabled:opacity-50 shadow-sm"
          title="Atualizar insights"
        >
          <RefreshCw size={16} class={isRefreshing() ? 'animate-spin' : ''} />
          <span>Atualizar</span>
        </button>
      </div>

      <Show when={insights.loading}>
        <div class="flex flex-col items-center justify-center py-16 border rounded-xl bg-muted/10 border-dashed">
          <div class="relative">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <Sparkles class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary/40" size={16} />
          </div>
          <p class="text-muted-foreground font-medium animate-pulse">O cérebro da IA está analisando seus dados...</p>
        </div>
      </Show>

      <Show when={insights.error}>
        <div class="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 flex items-center gap-3">
          <AlertTriangle size={24} />
          <div>
            <p class="font-semibold">Erro na análise de IA</p>
            <p class="text-sm">{insights.error.message}</p>
          </div>
        </div>
      </Show>

      <Show when={!insights.loading && !insights.error && insights()}>
        {/* Intelligence Stream (Horizontal) */}
        <div class="flex overflow-x-auto pb-4 gap-4 snap-x snap-mandatory scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
          <Show when={insights()!.insights.length === 0}>
            <div class="p-12 text-center text-muted-foreground border-2 border-dashed rounded-xl w-full">
              <Lightbulb size={48} class="mx-auto mb-3 opacity-20" />
              <p class="text-lg font-medium">Nenhum insight detectado</p>
              <p class="text-sm mt-1">A IA não encontrou anomalias ou oportunidades significativas no momento.</p>
            </div>
          </Show>

          <For each={insights()!.insights}>
            {(insight) => (
              <div
                class={`flex-shrink-0 min-w-[300px] max-w-[300px] snap-center group relative p-4 rounded-xl border transition-all hover:shadow-lg hover:-translate-y-1 cursor-pointer ${getCategoryColor(insight.category)} bg-white dark:bg-zinc-900`}
                onClick={() => handleInsightClick(insight)}
              >
                <div class="flex flex-col h-full justify-between">
                  <div>
                    <div class="flex items-start justify-between gap-2 mb-3">
                      <div class={`p-2 rounded-lg ${getCategoryColor(insight.category)} border bg-opacity-20`}>
                        {getCategoryIcon(insight.category)}
                      </div>
                      <span class={`text-[10px] px-2 py-1 rounded-full border font-bold ${getSeverityBadge(insight.severity)}`}>
                        {insight.severity.toUpperCase()}
                      </span>
                    </div>

                    <h4 class="font-bold text-base text-foreground group-hover:text-primary transition-colors line-clamp-2 mb-2">
                      {insight.title}
                    </h4>

                    <p class="text-xs text-muted-foreground leading-relaxed line-clamp-3 mb-3">
                      {insight.description}
                    </p>
                  </div>

                  <Show when={insight.recommendation}>
                    <div class="mt-auto p-2 rounded bg-primary/5 border border-primary/10 text-[10px] font-medium text-foreground">
                      <span class="text-primary font-bold mr-1">AÇÃO:</span>
                      {insight.recommendation}
                    </div>
                  </Show>

                  <div class="mt-3 flex items-center justify-between text-[10px] text-muted-foreground opacity-70">
                    <span>{new Date(insight.created_at).toLocaleDateString('pt-BR')}</span>
                    <span class="flex items-center gap-1">
                      Google Gemini 2.5
                    </span>
                  </div>
                </div>
              </div>
            )}
          </For>
        </div>

        <div class="text-xs text-muted-foreground text-center pt-6 opacity-60">
          Processados {insights()!.total} indicadores estratégicos • {new Date(insights()!.generated_at).toLocaleTimeString('pt-BR')}
        </div>
      </Show>
    </div>
  );
}

