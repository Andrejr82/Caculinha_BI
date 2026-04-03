import { createSignal, createRoot } from 'solid-js';
import api from '@/lib/api';

export interface User {
  username: string;
  role: string;
  email: string;
  allowed_segments: string[];
}

function resolveEffectiveRole(payload: any): string {
  const tokenRole = String(payload?.role || '').toLowerCase();
  const metadataRole = String(payload?.user_metadata?.role || payload?.app_metadata?.role || '').toLowerCase();
  if (tokenRole && tokenRole !== 'authenticated' && tokenRole !== 'anon') return tokenRole;
  if (metadataRole) return metadataRole;
  return 'user';
}

function createAuthStore() {
  const [user, setUser] = createSignal<User | null>(null);
  const [token, setToken] = createSignal<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = createSignal<boolean>(false);
  const [loading, setLoading] = createSignal<boolean>(false);
  const [error, setError] = createSignal<string | null>(null);

  // Função para validar e decodificar token
  const validateAndDecodeToken = (tokenString: string): any | null => {
      try {
        const parts = tokenString.split('.');
        if (parts.length !== 3) {
          return null;
        }

      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );

      const payload = JSON.parse(jsonPayload);

        if (payload.exp) {
          const now = Math.floor(Date.now() / 1000);
          if (payload.exp < now) {
            return null;
          }
        }

        return payload;
      } catch {
        return null;
      }
    };

  // Restaurar user do token ao inicializar (com proteção para SSR)
  const initializeAuth = () => {
    try {
      if (typeof window === 'undefined' || !window.sessionStorage) {
        return;
      }

      const initToken = sessionStorage.getItem('token');
      const initRefreshToken = sessionStorage.getItem('refresh_token');

        if (initToken) {
          const payload = validateAndDecodeToken(initToken);

          if (payload) {
            const role = resolveEffectiveRole(payload);

            const userData: User = {
              username: payload.username || payload.sub || 'user',
              role: role,
              email: payload.email || `${payload.username || payload.sub}@agentbi.com`,
              allowed_segments: payload.allowed_segments || []
            };
            setUser(userData);
            setToken(initToken);
            setIsAuthenticated(true);
          } else {
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('refresh_token');
            setIsAuthenticated(false);
          setUser(null);
          setToken(null);
        }
        }
      } catch (error) {
        console.error('Erro ao inicializar autenticação:', error);
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('refresh_token');
        setIsAuthenticated(false);
    }
  };

  initializeAuth();

  const login = async (usernameOrEmail: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/auth/login', {
        username: usernameOrEmail,
        password
      });

      const { access_token, refresh_token } = response.data;

      if (access_token) {
        const payload = validateAndDecodeToken(access_token);

        if (!payload) {
          setError("Token inválido recebido do servidor");
          return false;
        }

        sessionStorage.setItem('token', access_token);
        if (refresh_token) sessionStorage.setItem('refresh_token', refresh_token);

        setToken(access_token);
        setIsAuthenticated(true);

        const role = resolveEffectiveRole(payload);

        const userData: User = {
          username: payload.username || payload.sub || usernameOrEmail.split('@')[0],
          role: role,
          email: payload.email || usernameOrEmail,
          allowed_segments: payload.allowed_segments || []
        };

        setUser(userData);

        return true;
      }
      return false;
    } catch (err: any) {
      console.error("Login error:", err);
      const errorMsg = err.response?.data?.detail || "Erro ao realizar login";
      setError(errorMsg);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    window.location.href = '/login';
  };

  return { user, token, isAuthenticated, login, logout, loading, error };
}

export default createRoot(createAuthStore);
