import { apiClient } from '@/lib/api/client';
import type { User } from '@/store/auth';

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
    // Use canonical authentication endpoint (V1)
    return apiClient.post<AuthResponse>('/auth/login', credentials);
  },

  async logout(): Promise<void> {
    // Connect to FastAPI backend: POST /api/v1/auth/logout
    return apiClient.post('/auth/logout');
  },

  async getCurrentUser(): Promise<User> {
    // Connect to FastAPI backend: GET /api/v1/auth/me
    return apiClient.get<User>('/auth/me');
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    // Connect to FastAPI backend: POST /api/v1/auth/refresh
    return apiClient.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
  },
};
