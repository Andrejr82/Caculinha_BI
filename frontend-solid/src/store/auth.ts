import { createSignal, createRoot } from 'solid-js';
import api from '@/lib/api';

export interface User {
  username: string;
  role: string;
  email: string;
  allowed_segments: string[];
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
      // Verificar formato JWT (deve ter 3 partes separadas por .)
      const parts = tokenString.split('.');
      if (parts.length !== 3) {
        console.error('❌ Token inválido: formato incorreto');
        return null;
      }

      // Decodificar payload (Base64Url -> Base64 -> JSON)
      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );

      const payload = JSON.parse(jsonPayload);

      // Verificar expiração
      if (payload.exp) {
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp < now) {
          console.error('❌ Token expirado');
          return null;
        }
      }

      return payload;
    } catch (e) {
      console.error('❌ Erro ao validar token:', e);
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
      if (initToken) {
        const payload = validateAndDecodeToken(initToken);

        // Verificação ESTRITA: Se o payload for nulo ou token expirado, limpar TUDO.
        if (payload) {
          // 🚨 CRITICAL FIX: Admin ALWAYS gets full access
          let allowedSegments = payload.allowed_segments || [];
          const role = payload.role || 'user';

          if (role === 'admin' && !allowedSegments.includes('*')) {
            console.warn('⚠️ Admin missing full access in token - forcing ["*"]');
            allowedSegments = ['*'];
          }

          const userData: User = {
            username: payload.username || payload.sub || 'user',
            role: role,
            email: payload.email || `${payload.username || payload.sub}@agentbi.com`,
            allowed_segments: allowedSegments
          };
          setUser(userData);
          setToken(initToken);
          setIsAuthenticated(true);
          console.log('🔄 Sessão restaurada com sucesso:', userData);
        } else {
          // Token inválido, malformado ou expirado -> Logout forçado imediato
          console.warn('⚠️ Token inválido detectado na inicialização - Limpando sessão.');
          sessionStorage.removeItem('token');
          setIsAuthenticated(false);
          setUser(null);
          setToken(null);
          // Opcional: Redirecionar se estiver numa rota protegida é responsabilidade do Router,
          // mas garantir o estado limpo previne o acesso visual indevido.
        }
      }
    } catch (error) {
      console.error('❌ Erro crítico ao inicializar autenticação:', error);
      sessionStorage.removeItem('token');
      setIsAuthenticated(false);
    }
  };

  // Executar inicialização
  initializeAuth();

  const login = async (usernameOrEmail: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      // ✅ FIX: Backend aceita 'username' que pode ser email para Supabase
      // O auth_service.py detecta se é email e usa Supabase, senão usa Parquet
      const response = await api.post('/auth/login', {
        username: usernameOrEmail,  // Pode ser email (Supabase) ou username (Parquet)
        password
      });

      const { access_token } = response.data;

      if (access_token) {
        // Validar token antes de salvar
        const payload = validateAndDecodeToken(access_token);

        if (!payload) {
          setError("Token inválido recebido do servidor");
          return false;
        }

        sessionStorage.setItem('token', access_token);
        setToken(access_token);
        setIsAuthenticated(true);

        // 🚨 CRITICAL FIX: Admin ALWAYS gets full access
        let allowedSegments = payload.allowed_segments || [];
        const role = payload.role || 'user';

        if (role === 'admin' && !allowedSegments.includes('*')) {
          console.warn('⚠️ Admin missing full access in login - forcing ["*"]');
          allowedSegments = ['*'];
        }

        // Definir dados do usuário baseado no payload do JWT
        const userData: User = {
          username: payload.username || payload.sub || usernameOrEmail.split('@')[0],
          role: role,
          email: payload.email || usernameOrEmail,
          allowed_segments: allowedSegments
        };

        console.log('✅ Login successful. User:', userData);
        setUser(userData);

        return true;
      }
      return false;
    } catch (err: any) {
      console.error("❌ Login error:", err);
      const errorMsg = err.response?.data?.detail || "Erro ao realizar login";
      setError(errorMsg);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    window.location.href = '/login';
  };

  return { user, token, isAuthenticated, login, logout, loading, error };
}

export default createRoot(createAuthStore);
