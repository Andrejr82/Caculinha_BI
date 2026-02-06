/**
 * useAnalytics Hook - SolidJS
 * Hook customizado para gerenciar estado e operações de analytics
 */

import { createQuery, createMutation, useQueryClient } from '@tanstack/solid-query';
import { analyticsService } from '@/services/analytics.service';
import { toast } from '@/migrated-components/components/ui/Sonner';
import type { AnalyticsFilter, ExportFormat } from '@/types/analytics';

export function useAnalytics(initialFilters?: AnalyticsFilter) {
  const queryClient = useQueryClient();

  // Query para dados
  const dataQuery = createQuery(() => ({
    queryKey: ['analytics', 'data', initialFilters],
    queryFn: () => analyticsService.getData(initialFilters),
  }));

  // Query para métricas
  const metricsQuery = createQuery(() => ({
    queryKey: ['analytics', 'metrics'],
    queryFn: analyticsService.getMetrics,
  }));

  // Mutation para exportação
  const exportMutation = createMutation(() => ({
    mutationFn: ({ format, filters }: { format: ExportFormat; filters?: AnalyticsFilter }) =>
      analyticsService.exportData(format, filters),
    onSuccess: (blob, variables) => {
      // Criar download do arquivo
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-export.${variables.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast(`Dados exportados em formato ${variables.format.toUpperCase()}`, { type: 'success' });
    },
    onError: () => {
      toast('Não foi possível exportar os dados', { type: 'error' });
    },
  }));

  return {
    data: dataQuery.data,
    metrics: metricsQuery.data,
    isLoading: dataQuery.isLoading || metricsQuery.isLoading,
    isError: dataQuery.isError || metricsQuery.isError,
    error: dataQuery.error || metricsQuery.error,
    refetch: () => {
      dataQuery.refetch();
      metricsQuery.refetch();
    },
    exportData: (format: ExportFormat, filters?: AnalyticsFilter) =>
      exportMutation.mutate({ format, filters }),
    isExporting: exportMutation.isPending,
  };
}
