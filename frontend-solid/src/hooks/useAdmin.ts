/**
 * useAdmin Hook - SolidJS
 * Hook para gerenciar operações administrativas
 */

import { createQuery, createMutation, useQueryClient } from '@tanstack/solid-query';
import { adminService } from '@/services/admin.service';
import { toast } from '@/migrated-components/components/ui/Sonner';
import type { CreateUserDTO, UpdateUserDTO, SystemSettings } from '@/types/admin';

export function useAdmin() {
  const queryClient = useQueryClient();

  // Queries
  const statsQuery = createQuery(() => ({
    queryKey: ['admin', 'stats'],
    queryFn: adminService.getStats,
  }));

  const usersQuery = createQuery(() => ({
    queryKey: ['admin', 'users'],
    queryFn: adminService.getUsers,
  }));

  const auditLogsQuery = createQuery(() => ({
    queryKey: ['admin', 'audit'],
    queryFn: () => adminService.getAuditLogs(),
  }));

  const settingsQuery = createQuery(() => ({
    queryKey: ['admin', 'settings'],
    queryFn: adminService.getSettings,
  }));

  // Mutations
  const createUserMutation = createMutation(() => ({
    mutationFn: adminService.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast('Usuário criado com sucesso!', { type: 'success' });
    },
    onError: () => {
      toast('Erro ao criar usuário', { type: 'error' });
    }
  }));

  const updateUserMutation = createMutation(() => ({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserDTO }) => 
      adminService.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast('Usuário atualizado com sucesso!', { type: 'success' });
    },
    onError: () => {
      toast('Erro ao atualizar usuário', { type: 'error' });
    }
  }));

  const deleteUserMutation = createMutation(() => ({
    mutationFn: adminService.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast('Usuário removido', { type: 'success' });
    },
  }));

  const updateSettingsMutation = createMutation(() => ({
    mutationFn: adminService.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] });
      toast('Configurações salvas com sucesso!', { type: 'success' });
    },
  }));

  return {
    stats: statsQuery.data,
    users: usersQuery.data,
    auditLogs: auditLogsQuery.data,
    settings: settingsQuery.data,
    isLoadingStats: statsQuery.isLoading,
    isLoadingUsers: usersQuery.isLoading,
    createUser: createUserMutation.mutate,
    updateUser: updateUserMutation.mutate,
    deleteUser: deleteUserMutation.mutate,
    updateSettings: updateSettingsMutation.mutate,
    isCreatingUser: createUserMutation.isPending,
    isUpdatingUser: updateUserMutation.isPending,
    isSavingSettings: updateSettingsMutation.isPending,
  };
}
