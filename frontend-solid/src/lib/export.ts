import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const escapeCsvCell = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  const raw = String(value);
  if (raw.includes(',') || raw.includes('"') || raw.includes('\n')) {
    return `"${raw.replace(/"/g, '""')}"`;
  }
  return raw;
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

export const exportToCsv = (data: Record<string, unknown>[], filename: string) => {
  if (!Array.isArray(data) || data.length === 0) return;

  const headers = Object.keys(data[0]);
  const rows = data.map((row) => headers.map((header) => escapeCsvCell(row[header])).join(','));
  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, filename.toLowerCase().endsWith('.csv') ? filename : `${filename}.csv`);
};

export const formatDateTime = (value: Date | string | number) =>
  format(new Date(value), "dd/MM/yyyy HH:mm", { locale: ptBR });

