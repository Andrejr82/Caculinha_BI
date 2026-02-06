import axios from 'axios';

// --- Type Definitions ---

export interface KpiMetrics {
  total_queries: number;
  total_errors: number;
  success_rate_feedback: number;
  cache_hit_rate: number;
  average_response_time_ms: string | number;
}

export interface ErrorTrendItem {
  date: string;
  error_count: number;
}

export interface TopQueryItem {
  query: string;
  count: number;
}

export interface Report {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface LearningResponse {
  insights: string[];
  feedback_stats: {
    total: number;
    positive: number;
    negative: number;
    partial: number;
    success_rate: number;
  };
  common_patterns: string[];
}

export interface TransferValidationPayload {
  produto_id: number;
  une_origem: number;
  une_destino: number;
  quantidade: number;
}

export interface TransferValidationResponse {
  status: string; // "sucesso", "falha", "alerta"
  mensagem: string;
}

export interface TransferSuggestion {
  produto_id: number;
  une_origem: number;
  une_destino: number;
  quantidade_sugerida: number;
  mensagem: string;
}

export interface TransferRequestPayload {
  produto_id: number;
  une_origem: number;
  une_destino: number;
  quantidade: number;
  solicitante_id: string;
}

export interface TransferReportQuery {
  start_date?: string;
  end_date?: string;
}

// Old Transfer interface is removed as it's replaced by TransferSuggestion or others.
// export interface Transfer { ... }

export interface Ruptura {
  PRODUTO: string;
  NOME: string;
  UNE: string;
  UNE_NOME?: string;
  ESTOQUE_UNE: number;
  ESTOQUE_CD: number;
  ESTOQUE_LV: number;
  VENDA_30DD: number;
  CRITICIDADE_PCT: number;
  NECESSIDADE: number;
  NOMESEGMENTO?: string;
  NOMEGRUPO?: string;
  NOMEFABRICANTE?: string;
  // New rupture alert fields
  PERC_ABAST: number;           // % Abastecimento (UNE/LV)
  GATILHO_CRITICO: number;      // 1 if %ABAST <= 50%
  FALHA_GATILHO: number;        // 1 if critical + no pending dispatch
  DEFICIT_PARAMETRO: number;    // 1 if MC > GONDOLA and TRAVA=SIM
  PISO_VIOLADO: number;         // 1 if LV < GONDOLA
}

export interface RupturasSummary {
  total: number;
  criticos: number;
  valor_estimado: number;
}

// --- API Client ---

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response && error.response.status === 401) {
    console.warn('⚠️ 401 Unauthorized - Token inválido ou expirado. Deslogando usuário...');
    sessionStorage.removeItem('token');
    // Forçar recarregamento para limpar estados
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
});

// --- API Methods ---

export interface ABCDetailItem {
  PRODUTO: string;
  NOME: string;
  UNE: string;
  UNE_NOME?: string;
  receita: number;
  perc_acumulada: number;
  classe: string;
}

export const analyticsApi = {
  getKpis: (days: number = 7) => api.get<KpiMetrics>(`/analytics/kpis?days=${days}`),
  getErrorTrend: (days: number = 30) => api.get<ErrorTrendItem[]>(`/analytics/error-trend?days=${days}`),
  getTopQueries: (days: number = 7, limit: number = 10) => api.get<TopQueryItem[]>(`/analytics/top-queries?days=${days}&limit=${limit}`),
  getFilterOptions: (segmento?: string, categoria?: string) => {
    const params = new URLSearchParams();
    if (segmento) params.append('segmento', segmento);
    if (categoria) params.append('categoria', categoria);
    return api.get<{ categorias: string[], segmentos: string[], grupos: string[] }>(`/analytics/filter-options?${params.toString()}`);
  },
  getABCDetails: (classe: string, segmento?: string, categoria?: string, grupo?: string) => {
    const params = new URLSearchParams({ classe });
    if (segmento) params.append('segmento', segmento);
    if (categoria) params.append('categoria', categoria);
    if (grupo) params.append('grupo', grupo);
    return api.get<ABCDetailItem[]>(`/analytics/abc-details?${params.toString()}`);
  },
};

export const reportsApi = {
  getAll: () => api.get<Report[]>('/reports'),
};

export interface UserData {
  id: string;
  username: string;
  email: string;
  role: string;
  full_name?: string;
  is_active: boolean;
  allowed_segments?: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  role: string;
  allowed_segments?: string[];
}

export interface UpdateUserPayload {
  username?: string;
  email?: string;
  password?: string;
  role?: string;
  is_active?: boolean;
  allowed_segments?: string[];
}

export const adminApi = {
  syncParquet: () => api.post('/admin/sync-parquet'),

  // User Management
  getUsers: () => api.get<UserData[]>('/admin/users'),
  getUser: (userId: string) => api.get<UserData>(`/admin/users/${userId}`),
  createUser: (userData: CreateUserPayload) => api.post<UserData>('/admin/users', userData),
  updateUser: (userId: string, userData: UpdateUserPayload) => api.put<UserData>(`/admin/users/${userId}`, userData),
  deleteUser: (userId: string) => api.delete(`/admin/users/${userId}`),
};

export const learningApi = {
  getInsights: () => api.get<LearningResponse>('/learning/insights'),
};

export const transfersApi = {
  validateTransfer: (payload: TransferValidationPayload) => api.post<TransferValidationResponse>('/transfers/validate', payload),
  getSuggestions: (segmento?: string, une_origem_excluir?: number, limit: number = 5) => api.get<TransferSuggestion[]>(`/transfers/suggestions`, { params: { segmento, une_origem_excluir, limit } }),
  createTransferRequest: (payload: TransferRequestPayload) => api.post<{ message: string, transfer_id: string }>('/transfers', payload),
  getReport: (query?: TransferReportQuery) => api.get<TransferRequestPayload[]>(`/transfers/report`, { params: query }),
};

export const rupturasApi = {
  getCritical: (limit = 50, segmento?: string, une?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (segmento) params.append('segmento', segmento);
    if (une) params.append('une', une);
    return api.get<Ruptura[]>(`/rupturas/critical?${params.toString()}`);
  },
  getSegmentos: () => api.get<string[]>('/rupturas/filters/segmentos'),
  getUnes: () => api.get<string[]>('/rupturas/filters/unes'),
  getSummary: (segmento?: string, une?: string) => {
    const params = new URLSearchParams();
    if (segmento) params.append('segmento', segmento);
    if (une) params.append('une', une);
    return api.get<RupturasSummary>(`/rupturas/summary?${params.toString()}`);
  },
};

export default api;