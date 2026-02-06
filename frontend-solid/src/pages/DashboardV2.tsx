import { createSignal, onMount, Show, For, createMemo } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { ShoppingCart, Package, AlertTriangle, DollarSign, RefreshCw, TrendingUp, CheckCircle, BarChart3, ArrowRight } from 'lucide-solid';
import api from '../lib/api';
import { PlotlyChart } from '../components/PlotlyChart';
import { ChartDownloadButton } from '../components/ChartDownloadButton';
import { AIInsightsPanel } from '../components/AIInsightsPanel';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { SkeletonKPI, SkeletonChart } from '../components/Skeleton';
import auth from '@/store/auth';

// Import Modern Components
import { ModernCard } from '../components/modern/ModernCard';
import { StatCard } from '../components/modern/StatCard';
import { ModernButton } from '../components/modern/ModernButton';
import { SectionHeader } from '../components/modern/SectionHeader';

interface BusinessKPIs {
  total_produtos: number;
  total_unes: number;
  produtos_ruptura: number;
  valor_estoque: number;
  top_produtos: Array<{
    produto: string;
    nome: string;
    vendas: number;
  }>;
  vendas_por_categoria: Array<{
    categoria: string;
    vendas: number;
    produtos: number;
  }>;
}

export default function DashboardV2() {
  const navigate = useNavigate();
  const [kpis, setKpis] = createSignal<BusinessKPIs | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);
  const [lastUpdate, setLastUpdate] = createSignal<Date | null>(null);
  const [showFullRanking, setShowFullRanking] = createSignal(false);

  // Chart specs para Plotly
  const [topProdutosChart, setTopProdutosChart] = createSignal<any>({});
  const [vendasCategoriaChart, setVendasCategoriaChart] = createSignal<any>({});

  // Context7 Logic: Derived State
  const businessStatus = createMemo(() => {
    if (!kpis()) return 'loading';
    const ruptureRate = kpis()!.produtos_ruptura / (kpis()!.total_produtos || 1);
    if (kpis()!.produtos_ruptura > 50 || ruptureRate > 0.1) return 'critical';
    if (kpis()!.produtos_ruptura > 0) return 'warning';
    return 'healthy';
  });

  const loadKPIs = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get<BusinessKPIs>('/metrics/business-kpis');
      setKpis(response.data);
      setLastUpdate(new Date());

      // Context7 Storytelling: Chart 1 - "Who is leading?"
      if (response.data.top_produtos.length > 0) {
        const topProduct = response.data.top_produtos[0];
        // MODERN THEME - CAÇULA
        const topProdutosSpec = {
          data: [{
            type: 'bar',
            x: response.data.top_produtos.map(p => `${p.produto} - ${p.nome.substring(0, 30)}`),
            y: response.data.top_produtos.map(p => p.vendas),
            marker: {
              color: response.data.top_produtos.map((_, i) => i === 0 ? '#78B928' : '#B2DB75'), // Caçula Green
              line: { color: 'transparent', width: 0 },
              cornerradius: 4
            },
            text: response.data.top_produtos.map(p => p.vendas.toLocaleString()),
            textposition: 'auto',
            textfont: { color: '#182508', family: 'Inter, sans-serif', weight: 600 },
            hovertemplate: '<b>Produto:</b> %{customdata.produto}<br><b>Nome:</b> %{customdata.nome}<br><b>Vendas:</b> %{y:,}<extra></extra>',
            customdata: response.data.top_produtos.map(p => ({ produto: p.produto, nome: p.nome, vendas: p.vendas }))
          }],
          layout: {
            title: {
              text: '<b>Líderes de Vendas</b><br><span style="font-size:12px;color:#6B6B6B">Top 10 produtos por volume nos últimos 30 dias</span>',
              font: { size: 16, color: '#182508', family: 'Inter, sans-serif' },
              x: 0.05,
            },
            xaxis: {
              title: '',
              tickangle: -45,
              tickfont: { size: 10, color: '#6B6B6B', family: 'Inter, sans-serif' },
              gridcolor: 'transparent',
              linecolor: '#E5E5E5'
            },
            yaxis: {
              title: '',
              tickfont: { color: '#6B6B6B', family: 'Inter, sans-serif' },
              gridcolor: '#F2F9E8', // Light green grid
              linecolor: 'transparent'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 40, r: 20, t: 80, b: 100 },
            font: { color: '#182508', family: 'Inter, sans-serif' },
            bargap: 0.3
          },
          config: { responsive: true, displayModeBar: false }
        };
        setTopProdutosChart(topProdutosSpec);
      }

      // Context7 Storytelling: Chart 2 - "Composition"
      if (response.data.vendas_por_categoria.length > 0) {
        // MODERN THEME - CAÇULA
        const vendasCategoriaSpec = {
          data: [{
            type: 'pie',
            labels: response.data.vendas_por_categoria.map(c => c.categoria),
            values: response.data.vendas_por_categoria.map(c => c.vendas),
            hovertemplate: '<b>%{label}</b><br>Vendas: %{value:,}<br>%{percent}<extra></extra>',
            marker: {
              colors: [
                '#78B928',  // Verde Principal
                '#FDB913',  // Amarelo
                '#ED1C24',  // Vermelho Accent
                '#99CF47',  // Verde Claro
                '#CA940F',  // Amarelo Escuro
                '#BE161D',  // Vermelho Escuro
                '#B2DB75',  // Verde Pastel
                '#486F18',  // Verde Escuro
                '#FFF3CB',  // Amarelo Pastel
                '#FDD1D3'   // Vermelho Pastel
              ],
              line: { color: '#FFFFFF', width: 2 }
            },
            textinfo: 'percent',
            textposition: 'inside',
            textfont: { size: 11, color: '#FFFFFF', family: 'Inter, sans-serif', weight: 'bold' },
            hole: 0.6
          }],
          layout: {
            title: {
              text: '<b>Distribuição por Categoria</b><br><span style="font-size:12px;color:#6B6B6B">Participação no volume total de vendas</span>',
              font: { size: 16, color: '#182508', family: 'Inter, sans-serif' },
              x: 0.05
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 20, r: 20, t: 80, b: 20 },
            font: { color: '#182508', family: 'Inter, sans-serif' },
            showlegend: true,
            legend: {
              orientation: 'v',
              x: 1,
              y: 0.5,
              font: { size: 11, color: '#4B5563', family: 'Inter, sans-serif' },
              bgcolor: 'rgba(255,255,255,0.5)',
              bordercolor: 'transparent'
            }
          },
          config: { responsive: true, displayModeBar: false }
        };
        setVendasCategoriaChart(vendasCategoriaSpec);
      }

    } catch (err: any) {
      console.error('Erro ao carregar KPIs:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar métricas');
    } finally {
      setLoading(false);
    }
  };

  onMount(() => {
    loadKPIs();
  });

  return (
    <ErrorBoundary>
      <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6 md:p-8 font-sans text-gray-900 dark:text-gray-100">
        <div class="max-w-7xl mx-auto space-y-8">
          
          {/* 1. Header Moderno */}
          <SectionHeader 
            title={`Olá, ${auth.user()?.username || 'Gestor'}`}
            subtitle="Visão geral do desempenho e saúde do negócio"
            gradient
            action={
              <div class="flex items-center gap-3">
                <span class="text-xs text-gray-500 font-medium hidden md:block">
                  Atualizado às {lastUpdate()?.toLocaleTimeString()}
                </span>
                <ModernButton 
                  variant="outline" 
                  size="sm" 
                  icon={<RefreshCw size={16} class={loading() ? 'animate-spin' : ''} />} 
                  onClick={loadKPIs}
                  disabled={loading()}
                >
                  Atualizar
                </ModernButton>
              </div>
            }
          />

          {/* 2. KPIs Cards */}
          <Show when={loading() && !kpis()}>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <SkeletonKPI /><SkeletonKPI /><SkeletonKPI /><SkeletonKPI />
            </div>
          </Show>

          <Show when={kpis() && !loading()}>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <StatCard
                title="Valor em Estoque"
                value={kpis()!.valor_estoque.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                subtitle="Capital imobilizado"
                icon={<DollarSign size={24} />}
                variant="primary"
                trend="up"
                trendValue="+2.5%"
              />
              
              <StatCard
                title="Rupturas"
                value={kpis()!.produtos_ruptura}
                subtitle={kpis()!.produtos_ruptura > 0 ? 'Produtos críticos' : 'Estoque saudável'}
                icon={<AlertTriangle size={24} />}
                variant={kpis()!.produtos_ruptura > 0 ? 'accent' : 'primary'}
                trend={kpis()!.produtos_ruptura > 0 ? 'down' : 'neutral'}
                trendValue={kpis()!.produtos_ruptura > 0 ? 'Crítico' : 'Estável'}
              />
              
              <StatCard
                title="Mix Ativo"
                value={kpis()!.total_produtos}
                subtitle="SKUs no catálogo"
                icon={<Package size={24} />}
                variant="secondary"
              />
              
              <StatCard
                title="Cobertura"
                value={kpis()!.total_unes}
                subtitle="Lojas monitoradas"
                icon={<ShoppingCart size={24} />}
                variant="neutral"
              />
            </div>

            {/* 3. Charts Section */}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150">
              <ModernCard variant="glass" class="p-1 min-h-[450px] flex flex-col">
                <div class="flex-1 rounded-2xl overflow-hidden">
                  <PlotlyChart
                    chartSpec={topProdutosChart}
                    chartId="top-produtos-v2"
                    enableDownload={false}
                    height="400px"
                  />
                </div>
                <div class="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm rounded-b-3xl">
                  <span class="text-xs text-gray-500 font-medium">Top 10 produtos</span>
                  <ChartDownloadButton chartId="top-produtos-v2" filename="top_produtos" label="" size="sm" />
                </div>
              </ModernCard>

              <ModernCard variant="glass" class="p-1 min-h-[450px] flex flex-col">
                <div class="flex-1 rounded-2xl overflow-hidden">
                  <PlotlyChart
                    chartSpec={vendasCategoriaChart}
                    chartId="vendas-categoria-v2"
                    enableDownload={false}
                    height="400px"
                  />
                </div>
                <div class="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm rounded-b-3xl">
                  <span class="text-xs text-gray-500 font-medium">Share por categoria</span>
                  <ChartDownloadButton chartId="vendas-categoria-v2" filename="vendas_categoria" label="" size="sm" />
                </div>
              </ModernCard>
            </div>

            {/* 4. AI Insights & Highlights */}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
              <div class="lg:col-span-2">
                <ModernCard variant="gradient" class="h-full">
                  <AIInsightsPanel />
                </ModernCard>
              </div>

              <ModernCard variant="elevated" class="h-full flex flex-col">
                <div class="p-6 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50">
                  <div class="flex items-center gap-3">
                    <div class="p-2 bg-cacula-green-100 dark:bg-cacula-green-900/30 rounded-lg text-cacula-green-600 dark:text-cacula-green-400">
                      <BarChart3 size={20} />
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">Destaques</h3>
                  </div>
                </div>
                
                <div class="flex-1 overflow-auto p-2">
                  <table class="w-full text-sm">
                    <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                      <For each={kpis()!.top_produtos.slice(0, 5)}>
                        {(produto, i) => (
                          <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group">
                            <td class="p-4 text-center">
                              <span class={`
                                inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold
                                ${i() === 0 ? 'bg-yellow-100 text-yellow-700' : 
                                  i() === 1 ? 'bg-gray-100 text-gray-600' : 
                                  i() === 2 ? 'bg-orange-100 text-orange-700' : 'text-gray-400'}
                              `}>
                                {i() + 1}
                              </span>
                            </td>
                            <td class="p-4">
                              <div class="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-cacula-green-600 transition-colors">{produto.nome}</div>
                              <div class="text-xs text-gray-500 font-mono mt-0.5">{produto.produto}</div>
                            </td>
                            <td class="p-4 text-right font-bold text-gray-900 dark:text-white">
                              {produto.vendas.toLocaleString()}
                            </td>
                          </tr>
                        )}
                      </For>
                    </tbody>
                  </table>
                </div>
                
                <div class="p-4 bg-gray-50/80 dark:bg-gray-800/80 border-t border-gray-100 dark:border-gray-800">
                  <ModernButton variant="ghost" fullWidth onClick={() => setShowFullRanking(true)} size="sm">
                    Ver Ranking Completo <ArrowRight size={16} class="ml-2" />
                  </ModernButton>
                </div>
              </ModernCard>
            </div>
          </Show>
        </div>
      </div>
    </ErrorBoundary>
  );
}
