import { Accessor, createEffect, onCleanup } from 'solid-js';
import type { Chart as ChartInstance, ChartConfiguration, ChartDataset } from 'chart.js';

export interface ForecastLineChartModel {
  labels: string[];
  upperBound: number[];
  lowerBound: number[];
  adjustedForecast: number[];
  baseForecast: number[];
}

let chartPromise: Promise<typeof import('chart.js').Chart> | null = null;

const getChartJs = async (): Promise<typeof import('chart.js').Chart> => {
  if (!chartPromise) {
    chartPromise = import('chart.js').then((mod) => {
      const {
        Chart,
        CategoryScale,
        Filler,
        Legend,
        LineController,
        LineElement,
        LinearScale,
        PointElement,
        Tooltip,
      } = mod;

      Chart.register(
        LineController,
        LineElement,
        PointElement,
        CategoryScale,
        LinearScale,
        Filler,
        Tooltip,
        Legend,
      );

      return Chart;
    });
  }

  return chartPromise;
};

interface ForecastLineChartProps {
  data: Accessor<ForecastLineChartModel | null>;
}

const formatUnits = (value: number) => `${Math.round(value).toLocaleString('pt-BR')} un`;

export const ForecastLineChart = (props: ForecastLineChartProps) => {
  let canvasRef: HTMLCanvasElement | undefined;
  let chart: ChartInstance<'line'> | null = null;
  let renderVersion = 0;

  createEffect(() => {
    const model = props.data();
    const currentVersion = ++renderVersion;

    if (!canvasRef || !model) {
      chart?.destroy();
      chart = null;
      return;
    }

    void (async () => {
      const Chart = await getChartJs();
      if (!canvasRef || currentVersion !== renderVersion) return;

      chart?.destroy();

      const datasets: ChartDataset<'line'>[] = [
        {
          label: 'Max',
          data: model.upperBound,
          borderColor: 'rgba(0, 0, 0, 0)',
          backgroundColor: 'rgba(0, 0, 0, 0)',
          pointRadius: 0,
          borderWidth: 0,
        },
        {
          label: 'Confiança',
          data: model.lowerBound,
          borderColor: 'rgba(0, 0, 0, 0)',
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
          pointRadius: 0,
          borderWidth: 0,
          fill: '-1',
        },
        {
          label: 'Previsão',
          data: model.adjustedForecast,
          borderColor: '#171717',
          backgroundColor: '#171717',
          pointBackgroundColor: '#171717',
          pointBorderColor: '#171717',
          pointRadius: 3,
          pointHoverRadius: 5,
          borderWidth: 3,
          tension: 0.35,
          fill: false,
        },
        {
          label: 'Tendência Base',
          data: model.baseForecast,
          borderColor: '#F97316',
          backgroundColor: '#F97316',
          pointRadius: 0,
          pointHoverRadius: 3,
          borderDash: [6, 6],
          borderWidth: 2,
          tension: 0.2,
          fill: false,
        },
      ];

      const config: ChartConfiguration<'line'> = {
        type: 'line',
        data: {
          labels: model.labels,
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
              position: 'top',
              align: 'start',
              labels: {
                usePointStyle: true,
                boxWidth: 10,
                color: '#525252',
                font: {
                  size: 11,
                  weight: 600,
                },
                filter: (legendItem) => (legendItem.datasetIndex ?? 0) >= 2,
              },
            },
            tooltip: {
              filter: (tooltipItem) => tooltipItem.datasetIndex >= 2,
              callbacks: {
                label: (context) => `${context.dataset.label}: ${formatUnits(Number(context.parsed.y ?? 0))}`,
              },
            },
          },
          scales: {
            x: {
              grid: {
                display: false,
              },
              border: {
                color: '#E5E5E5',
              },
              ticks: {
                color: '#737373',
                font: {
                  size: 11,
                },
                maxRotation: 45,
                minRotation: 45,
              },
            },
            y: {
              grid: {
                color: '#F5F5F5',
              },
              border: {
                display: false,
              },
              ticks: {
                color: '#737373',
                font: {
                  size: 11,
                },
                callback: (tickValue) => formatUnits(Number(tickValue)),
              },
            },
          },
        },
      };

      chart = new Chart(canvasRef, config);
    })();
  });

  onCleanup(() => {
    chart?.destroy();
    chart = null;
  });

  return (
    <div class="relative h-full w-full" data-testid="forecasting-chart-canvas">
      <canvas ref={canvasRef} class="h-full w-full" />
    </div>
  );
};
