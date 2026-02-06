import { apiClient } from '@/lib/api/client';
import type { User } from '@/store/auth.store';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Use production authentication endpoint only
    return apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
  },

  async logout(): Promise<void> {
    // Connect to FastAPI backend: POST /api/v1/auth/logout
    return apiClient.post('/api/v1/auth/logout');
  },

  async getCurrentUser(): Promise<User> {
    // Connect to FastAPI backend: GET /api/v1/auth/me
    return apiClient.get<User>('/api/v1/auth/me');
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    // Connect to FastAPI backend: POST /api/v1/auth/refresh
    return apiClient.post<AuthResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
  },
};
