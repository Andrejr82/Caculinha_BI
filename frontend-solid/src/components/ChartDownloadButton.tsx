// frontend-solid/src/components/ChartDownloadButton.tsx

import { Component, Show } from 'solid-js';
import { Download } from 'lucide-solid';
import Plotly from 'plotly.js-dist-min';

interface ChartDownloadButtonProps {
  chartId: string;
  filename?: string;
  format?: 'png' | 'svg' | 'jpeg';
  width?: number;
  height?: number;
  scale?: number;
  label?: string;
}

export const ChartDownloadButton: Component<ChartDownloadButtonProps> = (props) => {
  const handleDownload = async () => {
    const chartDiv = document.getElementById(props.chartId);

    if (!chartDiv) {
      alert('Gráfico não encontrado');
      return;
    }

    try {
      const filename = props.filename || `grafico_${new Date().toISOString().split('T')[0]}`;
      const format = props.format || 'png';
      const width = props.width || 1200;
      const height = props.height || 800;
      const scale = props.scale || 2;

      await Plotly.downloadImage(chartDiv, {
        format: format,
        filename: filename,
        width: width,
        height: height,
        scale: scale
      });
    } catch (error) {
      console.error("Erro ao baixar gráfico:", error);
      alert("Erro ao baixar gráfico. Tente novamente.");
    }
  };

  return (
    <button
      onClick={handleDownload}
      class="btn btn-sm btn-outline gap-2"
      title="Baixar gráfico como imagem"
    >
      <Download size={16} />
      {props.label || 'Baixar Gráfico'}
    </button>
  );
};

// Componente para download de múltiplos formatos
interface MultiFormatDownloadProps {
  chartId: string;
  filename?: string;
}

export const MultiFormatDownload: Component<MultiFormatDownloadProps> = (props) => {
  const [showMenu, setShowMenu] = [false, (v: boolean) => {}];

  const downloadFormat = async (format: 'png' | 'svg' | 'jpeg') => {
    const chartDiv = document.getElementById(props.chartId);

    if (!chartDiv) {
      alert('Gráfico não encontrado');
      return;
    }

    try {
      const filename = props.filename || `grafico_${new Date().toISOString().split('T')[0]}`;

      await Plotly.downloadImage(chartDiv, {
        format: format,
        filename: filename,
        width: 1200,
        height: 800,
        scale: 2
      });
    } catch (error) {
      console.error("Erro ao baixar gráfico:", error);
      alert("Erro ao baixar gráfico. Tente novamente.");
    }
  };

  return (
    <div class="relative inline-block">
      <button
        class="btn btn-sm btn-outline gap-2"
        title="Baixar gráfico"
      >
        <Download size={16} />
        <span>Baixar</span>
      </button>
      <div class="absolute right-0 mt-1 w-32 bg-card border rounded-lg shadow-lg z-10 py-1">
        <button
          onClick={() => downloadFormat('png')}
          class="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
        >
          PNG (Alta Qualidade)
        </button>
        <button
          onClick={() => downloadFormat('svg')}
          class="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
        >
          SVG (Vetorial)
        </button>
        <button
          onClick={() => downloadFormat('jpeg')}
          class="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
        >
          JPEG
        </button>
      </div>
    </div>
  );
};
