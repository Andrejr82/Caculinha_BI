// frontend-solid/src/components/DownloadButton.tsx

import { Component } from 'solid-js';

interface DownloadButtonProps {
  data: any[]; // Data to be downloaded
  filename: string; // Suggested filename
  label?: string; // Optional button label
}

export const DownloadButton: Component<DownloadButtonProps> = (props) => {
  const handleDownload = () => {
    if (!props.data || props.data.length === 0) {
      alert("Nenhum dado para baixar.");
      return;
    }

    try {
      // Convert data to JSON string
      const jsonString = JSON.stringify(props.data, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = props.filename || 'data.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro ao baixar dados:", error);
      alert("Erro ao baixar dados. Tente novamente.");
    }
  };

  return (
    <button 
      onClick={handleDownload}
      class="btn btn-sm btn-outline"
      title="Baixar dados"
    >
      {props.label || 'Baixar Dados (JSON)'}
    </button>
  );
};
