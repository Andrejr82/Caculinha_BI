// frontend-solid/src/components/PlotlyChart.tsx

import { createEffect, onCleanup, Accessor, createSignal, Show, onMount } from 'solid-js';
import Plotly from 'plotly.js-dist-min';
import { Maximize, Minimize } from 'lucide-solid';

const CACULA_CHART_COLORS = [
  '#8B7355', '#C9A961', '#6B7A5A', '#A68968', '#CC8B3C',
  '#5B7B9A', '#9B8875', '#B8984E', '#7A8B6F', '#B59B7A',
];

interface PlotlyChartProps {
  chartSpec: Accessor<any>;
  chartId?: string;
  onDataClick?: (data: any) => void;
  onHover?: (data: any) => void;
  height?: string;
  enableDownload?: boolean;
  expandedContent?: any; // JSX.Element
  naked?: boolean; // New prop for borderless mode
}


export const PlotlyChart = (props: PlotlyChartProps) => {
  let chartDiv: HTMLDivElement | undefined;
  let expandedChartDiv: HTMLDivElement | undefined;

  const chartId = props.chartId || `chart-${Math.random().toString(36).substr(2, 9)}`;
  const [isExpanded, setIsExpanded] = createSignal(false);

  const toggleExpand = () => {
    const newState = !isExpanded();
    setIsExpanded(newState);
    document.body.style.overflow = newState ? 'hidden' : '';

    // Pequeno delay para garantir que o DOM do modal esteja pronto
    setTimeout(renderPlot, 50);
  };

  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && isExpanded()) toggleExpand();
  };

  createEffect(() => {
    if (isExpanded()) window.addEventListener('keydown', handleEsc);
    else window.removeEventListener('keydown', handleEsc);
  });

  onCleanup(() => {
    window.removeEventListener('keydown', handleEsc);
    document.body.style.overflow = '';
    if (chartDiv) Plotly.purge(chartDiv);
    if (expandedChartDiv) Plotly.purge(expandedChartDiv);
  });

  const renderPlot = () => {
    const spec = props.chartSpec();
    const targetDiv = isExpanded() ? expandedChartDiv : chartDiv;

    if (!targetDiv || !spec || Object.keys(spec).length === 0) return;

    try {
      const caculaLayout = {
        paper_bgcolor: isExpanded() ? '#FAFAFA' : '#FAFAFA',
        plot_bgcolor: '#FFFFFF',
        font: {
          color: '#2D2D2D',
          family: 'Inter, sans-serif',
          size: isExpanded() ? 14 : 12
        },
        colorway: CACULA_CHART_COLORS,
        // Margens ajustadas para acomodar rótulos longos
        margin: isExpanded()
          ? { l: 80, r: 60, t: 80, b: 180, autoexpand: true }
          : (spec.layout?.margin || { l: 60, r: 40, t: 60, b: 120, autoexpand: true }),
        xaxis: {
          gridcolor: '#E5E5E5',
          automargin: true,
          tickangle: isExpanded() ? -45 : -45, // Rotação consistente para melhor leitura
          tickfont: {
            size: isExpanded() ? 12 : 11
          },
          ...spec.layout?.xaxis
        },
        yaxis: {
          gridcolor: '#E5E5E5',
          automargin: true,
          tickfont: {
            size: isExpanded() ? 12 : 11
          },
          ...spec.layout?.yaxis
        },
        legend: {
          bgcolor: 'rgba(255,255,255,0.8)',
          ...spec.layout?.legend
        },
        // Garantir que o gráfico se ajuste ao container
        autosize: true,
        ...spec.layout
      };

      const config = {
        responsive: true,
        displayModeBar: isExpanded(),
        displaylogo: false,
        ...spec.config
      };

      // Limpar o outro div se estiver mudando de estado
      if (isExpanded() && chartDiv) Plotly.purge(chartDiv);
      if (!isExpanded() && expandedChartDiv) Plotly.purge(expandedChartDiv);

      Plotly.newPlot(targetDiv, spec.data, caculaLayout, config);

      if (props.onDataClick) {
        (targetDiv as any).on('plotly_click', props.onDataClick);
      }
    } catch (error) {
      console.error("Plotly render error:", error);
    }
  };

  createEffect(renderPlot);

  return (
    <>
      <div
        class={`relative w-full overflow-hidden transition-shadow ${props.naked ? '' : 'rounded-xl border bg-card group shadow-sm hover:shadow-md'}`}
        style={{ height: props.height || '550px', 'min-height': '450px' }}
      >
        <div class="absolute top-3 right-3 z-10 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); toggleExpand(); }}
            class="p-2 rounded-lg bg-white/90 border shadow-sm hover:bg-white text-primary transition-colors"
            title="Ver em tela cheia"
          >
            <Maximize size={18} />
          </button>
        </div>

        <div ref={chartDiv} class="w-full h-full" id={chartId}></div>
      </div>

      <Show when={isExpanded()}>
        <div
          class="fixed inset-0 z-[10000] bg-zinc-950/60 backdrop-blur-md flex items-center justify-center p-2 md:p-6 animate-in fade-in duration-300"
          onClick={toggleExpand}
        >
          <div
            class="bg-white dark:bg-zinc-900 w-full h-full rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-10 duration-500"
            onClick={(e) => e.stopPropagation()}
          >
            <div class="p-4 border-b flex items-center justify-between bg-white dark:bg-zinc-900 flex-shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-2 h-8 bg-primary rounded-full animate-pulse"></div>
                <div>
                  <h3 class="font-bold text-xl text-gray-900 dark:text-gray-100">Análise Expandida</h3>
                  <p class="text-xs text-muted-foreground">Visão detalhada dos indicadores de performance</p>
                </div>
              </div>
              <button
                onClick={toggleExpand}
                class="group p-2 px-4 rounded-xl hover:bg-red-50 text-gray-500 hover:text-red-600 transition-all flex items-center gap-3 border border-transparent hover:border-red-100"
              >
                <span class="text-sm font-bold">FECHAR</span>
                <Minimize size={22} class="group-hover:scale-110 transition-transform" />
              </button>
            </div>

            <div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
              <div class="flex-1 p-2 md:p-4 bg-[#FAFAFA] dark:bg-zinc-950/50 relative">
                <div
                  ref={expandedChartDiv}
                  id={`${chartId}-expanded`}
                  class="w-full h-full"
                ></div>
              </div>

              <Show when={props.expandedContent}>
                <div class="w-full lg:w-96 border-l border-gray-100 bg-white p-6 overflow-y-auto shadow-inner">
                  <div class="prose prose-sm max-w-none">
                    <h4 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Métricas Detalhadas</h4>
                    {props.expandedContent}
                  </div>
                </div>
              </Show>
            </div>
          </div>
        </div>
      </Show>
    </>
  );
};