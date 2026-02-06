// frontend-solid/src/lib/formatters.ts

export const formatTimestamp = (timestamp: number | Date): string => {
  const date = typeof timestamp === 'number' ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
};

// Placeholder for other formatters from T5.3.1
export const formatCurrency = (value: number): string => {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

export const formatNumber = (value: number): string => {
  return value.toLocaleString('pt-BR');
};

export const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR');
};
