import { createRoot, batch, createEffect } from 'solid-js';
import { createStore } from 'solid-js/store';
import { analyticsApi, KpiMetrics, TopQueryItem } from '@/lib/api';

interface DashboardState {
  // Grid Data
  data: TopQueryItem[]; // Now uses TopQueryItem
  
  // KPI Data
  summary: KpiMetrics | null; // Now uses KpiMetrics
  
  // System State
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date | null;
  isLive: boolean; // Controle do polling
}

function createDashboardStore() {
  const [state, setState] = createStore<DashboardState>({
    data: [],
    summary: null,
    isLoading: false,
    error: null,
    lastUpdate: null,
    isLive: true
  });

  let intervalId: number;

  const fetchData = async () => {
    if (!state.data.length) setState('isLoading', true); // Só mostra loading no primeiro load
    
    try {
      // Buscar dados em paralelo dos novos endpoints
      const [kpisRes, topQueriesRes] = await Promise.all([
        analyticsApi.getKpis(),
        analyticsApi.getTopQueries(7, 10) // Top 10 queries dos últimos 7 dias para a grid
      ]);

      batch(() => {
        setState('summary', kpisRes.data); // KpiMetrics
        setState('data', topQueriesRes.data); // TopQueryItem[]
        setState('lastUpdate', new Date());
        setState('error', null);
        setState('isLoading', false);
      });
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setState('error', "Falha ao atualizar dados.");
      setState('isLoading', false);
      // Se falhar, para o polling para não floodar erros
      stopPolling(); 
    }
  };

  const startPolling = () => {
    fetchData(); // Busca imediata
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(fetchData, 5000); // Atualiza a cada 5s
    setState('isLive', true);
  };

  const stopPolling = () => {
    clearInterval(intervalId);
    setState('isLive', false);
  };

  const togglePolling = () => {
    if (state.isLive) stopPolling();
    else startPolling();
  };

  // Iniciar polling automaticamente apenas se estiver logado (verificação feita na view)
  createEffect(() => {
    const token = sessionStorage.getItem('token');
    if (token && !state.isLive) {
        startPolling();
    }
  });
  
  return { state, startPolling, stopPolling, togglePolling, fetchData };
}

export default createRoot(createDashboardStore);