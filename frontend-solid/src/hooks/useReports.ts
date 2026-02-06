/**
 * useReports Hook - SolidJS
 * Hook para gerenciar estado e operações de relatórios
 */

import { createQuery, createMutation, useQueryClient } from '@tanstack/solid-query';
import { reportsService } from '@/services/reports.service';
import { toast } from '@/migrated-components/components/ui/Sonner';
import { useNavigate } from '@solidjs/router';
import type { CreateReportDTO, UpdateReportDTO } from '@/types/reports';

export function useReports() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Queries
  const reportsQuery = createQuery(() => ({
    queryKey: ['reports'],
    queryFn: reportsService.getAll,
  }));

  const templatesQuery = createQuery(() => ({
    queryKey: ['reports', 'templates'],
    queryFn: reportsService.getTemplates,
  }));

  // Mutations
  const createMutation = createMutation(() => ({
    mutationFn: reportsService.create,
    onSuccess: (newReport) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast('Relatório criado com sucesso!', { type: 'success' });
      navigate(`/reports/${newReport.id}/edit`);
    },
    onError: () => {
      toast('Erro ao criar relatório', { type: 'error' });
    }
  }));

  const updateMutation = createMutation(() => ({
    mutationFn: ({ id, data }: { id: string; data: UpdateReportDTO }) => 
      reportsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast('Relatório salvo com sucesso!', { type: 'success' });
    },
    onError: () => {
      toast('Erro ao salvar relatório', { type: 'error' });
    }
  }));

  const deleteMutation = createMutation(() => ({
    mutationFn: reportsService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast('Relatório removido', { type: 'success' });
    },
  }));

  const generatePDFMutation = createMutation(() => ({
    mutationFn: reportsService.generatePDF,
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      toast('PDF gerado com sucesso!', { type: 'success' });
    },
  }));

  return {
    reports: reportsQuery.data,
    templates: templatesQuery.data,
    isLoading: reportsQuery.isLoading,
    createReport: createMutation.mutate,
    updateReport: updateMutation.mutate,
    deleteReport: deleteMutation.mutate,
    generatePDF: generatePDFMutation.mutate,
    isCreating: createMutation.isPending,
    isSaving: updateMutation.isPending,
    isGenerating: generatePDFMutation.isPending,
  };
}

export function useReport(id: string) {
  return createQuery(() => ({
    queryKey: ['reports', id],
    queryFn: () => reportsService.getById(id),
    get enabled() {
      return !!id;
    },
  }));
}
