import { apiClient } from '@/lib/api/client';
import type {
  AdminStats,
  User,
  CreateUserDTO,
  UpdateUserDTO,
  AuditLog,
  SystemSettings,
} from '@/types/admin';

export const adminService = {
  async getStats(): Promise<AdminStats> {
    // Connect to FastAPI backend: GET /api/v1/admin/stats
    return apiClient.get<AdminStats>('/api/v1/admin/stats');
  },

  async getUsers(): Promise<User[]> {
    // Connect to FastAPI backend: GET /api/v1/admin/users
    return apiClient.get<User[]>('/api/v1/admin/users');
  },

  async getUser(id: string): Promise<User> {
    // Connect to FastAPI backend: GET /api/v1/admin/users/{id}
    return apiClient.get<User>(`/api/v1/admin/users/${id}`);
  },

  async createUser(user: CreateUserDTO): Promise<User> {
    // Connect to FastAPI backend: POST /api/v1/admin/users
    return apiClient.post<User>('/api/v1/admin/users', user);
  },

  async updateUser(id: string, user: UpdateUserDTO): Promise<User> {
    // Connect to FastAPI backend: PUT /api/v1/admin/users/{id}
    return apiClient.put<User>(`/api/v1/admin/users/${id}`, user);
  },

  async deleteUser(id: string): Promise<void> {
    // Connect to FastAPI backend: DELETE /api/v1/admin/users/{id}
    return apiClient.delete(`/api/v1/admin/users/${id}`);
  },

  async getAuditLogs(limit = 100): Promise<AuditLog[]> {
    // Connect to FastAPI backend: GET /api/v1/admin/audit-logs
    return apiClient.get<AuditLog[]>(`/api/v1/admin/audit-logs?limit=${limit}`);
  },

  async getSettings(): Promise<SystemSettings> {
    // Connect to FastAPI backend: GET /api/v1/admin/settings
    // TODO: Backend endpoint not implemented yet
    return apiClient.get<SystemSettings>('/api/v1/admin/settings');
  },

  async updateSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    // Connect to FastAPI backend: PUT /api/v1/admin/settings
    // TODO: Backend endpoint not implemented yet
    return apiClient.put<SystemSettings>('/api/v1/admin/settings', settings);
  },
};
