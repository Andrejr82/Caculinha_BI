import { Accessor, Show, createEffect, createMemo, createSignal, onCleanup } from 'solid-js';
import { PlotlyChart } from './PlotlyChart';
import type { Chart as ChartInstance, ChartConfiguration, ChartDataset } from 'chart.js';

type SimpleChartKind = 'bar' | 'line' | 'pie';

type SimpleChartModel = {
  kind: SimpleChartKind;
  config: ChartConfiguration<'bar' | 'line' | 'doughnut'>;
};

const DEFAULT_COLORS = ['#8B7355', '#C9A961', '#6B7A5A', '#CC8B3C', '#5B7B9A', '#9B8875', '#B8984E'];

let chartPromise: Promise<typeof import('chart.js').Chart> | null = null;

const getChartJs = async (): Promise<typeof import('chart.js').Chart> => {
  if (!chartPromise) {
    chartPromise = import('chart.js').then((mod) => {
      const {
        ArcElement,
        BarController,
        BarElement,
        CategoryScale,
        Chart,
        DoughnutController,
        Filler,
        Legend,
        LineController,
        LineElement,
        LinearScale,
        PointElement,
        Tooltip,
      } = mod;

      Chart.register(
        ArcElement,
        BarController,
        BarElement,
        CategoryScale,
        DoughnutController,
        Filler,
        Legend,
        LineController,
        LineElement,
        LinearScale,
        PointElement,
        Tooltip,
      );

      return Chart;
    });
  }

  return chartPromise;
};

const normalizeTraceType = (trace: Record<string, any>): string => String(trace?.type || '').toLowerCase();
const normalizeMode = (trace: Record<string, any>): string => String(trace?.mode || '').toLowerCase();

const isPlainObject = (value: unknown): value is Record<string, any> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const normalizeRawChartSpec = (rawValue: unknown): Record<string, any> | undefined => {
  if (!rawValue) return undefined;

  if (typeof rawValue === 'string') {
    try {
      return normalizeRawChartSpec(JSON.parse(rawValue));
    } catch {
      return undefined;
    }
  }

  if (!isPlainObject(rawValue)) return undefined;

  if (rawValue.chart_spec !== undefined) {
    return normalizeRawChartSpec(rawValue.chart_spec);
  }

  if (rawValue.chart_data !== undefined) {
    return normalizeRawChartSpec(rawValue.chart_data);
  }

  return rawValue;
};

const hasSubplotLayout = (layout: Record<string, any> | undefined): boolean => {
  if (!layout || !isPlainObject(layout)) return false;
  return Object.keys(layout).some((key) => /^xaxis\d+|^yaxis\d+|^scene\d+/.test(key)) || isPlainObject(layout.grid);
};

const toColor = (value: unknown, fallback: string | string[]): string | string[] => {
  if (Array.isArray(value)) {
    const colors = value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
    return colors.length > 0 ? colors : fallback;
  }
  return typeof value === 'string' && value.trim().length > 0 ? value : fallback;
};

const transparentize = (hexColor: string, alpha: string): string => {
  if (!hexColor.startsWith('#') || (hexColor.length !== 7 && hexColor.length !== 4)) return hexColor;
  if (hexColor.length === 4) {
    const [_, r, g, b] = hexColor;
    return `#${r}${r}${g}${g}${b}${b}${alpha}`;
  }
  return `${hexColor}${alpha}`;
};

const buildPieConfig = (trace: Record<string, any>, layout: Record<string, any> | undefined): SimpleChartModel | null => {
  const labels = Array.isArray(trace.labels) ? trace.labels.map((label) => String(label)) : [];
  const values = Array.isArray(trace.values) ? trace.values.map((value) => Number(value ?? 0)) : [];
  if (labels.length === 0 || labels.length !== values.length) return null;

  const colors = toColor(trace?.marker?.colors, DEFAULT_COLORS);
  const cutout = typeof trace.hole === 'number' && trace.hole > 0 ? `${Math.round(trace.hole * 100)}%` : '0%';

  return {
    kind: 'pie',
    config: {
      type: 'doughnut',
      data: {
        labels,
        datasets: [
          {
            label: trace.name || layout?.title?.text || 'Distribuição',
            data: values,
            backgroundColor: colors,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        cutout,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#525252',
              font: {
                size: 11,
              },
            },
          },
        },
      },
    },
  };
};

const buildBarConfig = (traces: Record<string, any>[], layout: Record<string, any> | undefined): SimpleChartModel | null => {
  const orientation = traces[0]?.orientation === 'h' ? 'h' : 'v';
  const labels = (orientation === 'h' ? traces[0]?.y : traces[0]?.x) ?? [];
  if (!Array.isArray(labels) || labels.length === 0) return null;

  const datasets: ChartDataset<'bar'>[] = [];
  traces.forEach((trace, index) => {
    const data = orientation === 'h' ? trace?.x : trace?.y;
    if (!Array.isArray(data)) return;
    const color = toColor(trace?.marker?.color, DEFAULT_COLORS[index % DEFAULT_COLORS.length]);
    datasets.push({
      label: trace.name || `Série ${index + 1}`,
      data: data.map((value: unknown) => Number(value ?? 0)),
      backgroundColor: color,
      borderColor: Array.isArray(color) ? color : color,
      borderWidth: 1,
      borderRadius: 6,
      maxBarThickness: 28,
    });
  });

  if (datasets.length === 0) return null;

  const stacked = layout?.barmode === 'stack';
  const indexAxis = orientation === 'h' ? 'y' : 'x';

  return {
    kind: 'bar',
    config: {
      type: 'bar',
      data: {
        labels: labels.map((label: unknown) => String(label)),
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        indexAxis,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: datasets.length > 1,
            labels: {
              color: '#525252',
              font: {
                size: 11,
              },
            },
          },
        },
        scales: {
          x: {
            stacked,
            grid: {
              color: indexAxis === 'x' ? '#F5F5F5' : 'transparent',
            },
            ticks: {
              color: '#737373',
              font: {
                size: 11,
              },
            },
          },
          y: {
            stacked,
            grid: {
              color: indexAxis === 'y' ? '#F5F5F5' : 'transparent',
            },
            ticks: {
              color: '#737373',
              font: {
                size: 11,
              },
            },
          },
        },
      },
    },
  };
};

const buildLineConfig = (traces: Record<string, any>[]): SimpleChartModel | null => {
  const labels = traces[0]?.x;
  if (!Array.isArray(labels) || labels.length === 0) return null;

  const datasets: ChartDataset<'line'>[] = [];
  traces.forEach((trace, index) => {
    if (!Array.isArray(trace?.y)) return;
    const lineColor = typeof trace?.line?.color === 'string'
      ? trace.line.color
      : DEFAULT_COLORS[index % DEFAULT_COLORS.length];
    const fillColor = typeof trace?.fillcolor === 'string'
      ? trace.fillcolor
      : transparentize(lineColor, '33');
    const mode = normalizeMode(trace);
    datasets.push({
      label: trace.name || `Série ${index + 1}`,
      data: trace.y.map((value: unknown) => Number(value ?? 0)),
      borderColor: lineColor,
      backgroundColor: fillColor,
      borderWidth: Number(trace?.line?.width ?? 2),
      borderDash: trace?.line?.dash === 'dash' ? [6, 6] : undefined,
      tension: trace?.line?.shape === 'spline' ? 0.35 : 0.2,
      pointRadius: mode.includes('markers') ? 3 : 0,
      pointHoverRadius: mode.includes('markers') ? 5 : 3,
      fill: trace?.fill === 'tonexty' ? '-1' : Boolean(trace?.fill && trace.fill !== 'none'),
      spanGaps: true,
    });
  });

  if (datasets.length === 0) return null;

  return {
    kind: 'line',
    config: {
      type: 'line',
      data: {
        labels: labels.map((label: unknown) => String(label)),
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          filler: {
            propagate: false,
          },
          legend: {
            labels: {
              color: '#525252',
              font: {
                size: 11,
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: '#737373',
              font: {
                size: 11,
              },
            },
          },
          y: {
            grid: {
              color: '#F5F5F5',
            },
            ticks: {
              color: '#737373',
              font: {
                size: 11,
              },
            },
          },
        },
      },
    },
  };
};

const buildLegacySeriesConfig = (chartSpec: Record<string, any>): SimpleChartModel | null => {
  const series = Array.isArray(chartSpec.series) ? chartSpec.series.filter(isPlainObject) : [];
  const labels = Array.isArray(chartSpec?.xAxis?.data) ? chartSpec.xAxis.data.map((label: unknown) => String(label)) : [];
  if (series.length === 0 || labels.length === 0) return null;

  const seriesTypes = series.map((trace) => String(trace.type || '').toLowerCase());

  if (seriesTypes.every((type) => type === 'bar')) {
    const traces = series.map((trace) => ({
      ...trace,
      type: 'bar',
      x: labels,
      y: Array.isArray(trace.data) ? trace.data : [],
    }));
    return buildBarConfig(traces, undefined);
  }

  if (seriesTypes.every((type) => type === 'line')) {
    const traces = series.map((trace) => ({
      ...trace,
      type: 'scatter',
      mode: 'lines',
      x: labels,
      y: Array.isArray(trace.data) ? trace.data : [],
    }));
    return buildLineConfig(traces);
  }

  return null;
};

const getSimpleChartModel = (chartSpec: Record<string, any> | undefined): SimpleChartModel | null => {
  if (!chartSpec || !isPlainObject(chartSpec)) return null;
  if ((!Array.isArray(chartSpec.data) || chartSpec.data.length === 0) && Array.isArray(chartSpec.series)) {
    return buildLegacySeriesConfig(chartSpec);
  }
  if (!Array.isArray(chartSpec.data) || chartSpec.data.length === 0) return null;
  const traces = chartSpec.data.filter(isPlainObject);
  if (traces.length === 0) return null;

  const layout = isPlainObject(chartSpec.layout) ? chartSpec.layout : undefined;
  if (hasSubplotLayout(layout) || chartSpec.frames) return null;

  const types = traces.map(normalizeTraceType);

  if (types.every((type) => type === 'pie')) {
    return buildPieConfig(traces[0], layout);
  }

  if (types.every((type) => type === 'bar')) {
    return buildBarConfig(traces, layout);
  }

  if (types.every((type) => type === 'scatter' || type === 'line' || type === '')) {
    const allRenderableAsLine = traces.every((trace) => {
      const mode = normalizeMode(trace);
      return !mode || mode.includes('lines');
    });

    if (allRenderableAsLine) {
      return buildLineConfig(traces);
    }
  }

  return null;
};

interface AdaptiveChartProps {
  chartSpec: Accessor<any>;
  height?: string;
}

export const AdaptiveChart = (props: AdaptiveChartProps) => {
  const [canvasRef, setCanvasRef] = createSignal<HTMLCanvasElement | undefined>(undefined);
  let chart: ChartInstance<'bar' | 'line' | 'doughnut'> | null = null;
  let renderVersion = 0;

  const normalizedSpec = createMemo(() => normalizeRawChartSpec(props.chartSpec()));
  const simpleModel = createMemo(() => getSimpleChartModel(normalizedSpec()));

  createEffect(() => {
    const model = simpleModel();
    const canvas = canvasRef();
    const currentVersion = ++renderVersion;

    if (!model || !canvas) {
      chart?.destroy();
      chart = null;
      return;
    }

    void (async () => {
      const Chart = await getChartJs();
      if (!canvasRef() || currentVersion !== renderVersion) return;

      chart?.destroy();
      chart = new Chart(canvas, model.config as ChartConfiguration<'bar' | 'line' | 'doughnut'>);
    })();
  });

  onCleanup(() => {
    chart?.destroy();
    chart = null;
  });

  return (
    <div class="w-full" data-testid="adaptive-chart">
      <Show
        when={simpleModel()}
        fallback={<PlotlyChart chartSpec={() => normalizedSpec() || {}} height={props.height} />}
      >
        <div class="relative w-full" style={{ height: props.height || '420px', 'min-height': '320px' }}>
          <canvas ref={setCanvasRef} class="h-full w-full" data-testid="adaptive-chart-canvas" />
        </div>
      </Show>
    </div>
  );
};
