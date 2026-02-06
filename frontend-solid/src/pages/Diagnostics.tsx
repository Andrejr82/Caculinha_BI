import { createSignal, onMount, Show, For } from 'solid-js';
import { Database, Server, HardDrive, Activity, CheckCircle, AlertTriangle, RefreshCw, Settings, Play, FileText } from 'lucide-solid';

interface DBConfig {
  use_sql_server: boolean;
  use_supabase: boolean;
  database_server: string | null;
  database_name: string | null;
  database_user: string | null;
  supabase_url: string | null;
}

interface ConnectionTestResult {
  success: boolean;
  message: string;
  version: string | null;
  tables: string[] | null;
}

interface DBStatus {
  parquet: {
    status: string;
    size_mb: number;
    path: string;
  };
  sql_server: {
    status: string;
    url: string | null;
  };
  supabase: {
    status: string;
    url: string | null;
  };
}

export default function Diagnostics() {
  const [dbStatus, setDbStatus] = createSignal<DBStatus | null>(null);
  const [dbConfig, setDbConfig] = createSignal<DBConfig | null>(null);
  const [testResult, setTestResult] = createSignal<ConnectionTestResult | null>(null);
  const [isLoading, setIsLoading] = createSignal(true);
  const [isTesting, setIsTesting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  const loadDiagnostics = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = sessionStorage.getItem('token');
      if (!token) {
        throw new Error('Token não encontrado. Faça login novamente.');
      }

      const [statusRes, configRes] = await Promise.all([
        fetch('/api/v1/diagnostics/db-status', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('/api/v1/diagnostics/config', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (!statusRes.ok || !configRes.ok) {
        throw new Error('Erro ao buscar informações de diagnóstico');
      }

      const status = await statusRes.json();
      const config = await configRes.json();

      setDbStatus(status);
      setDbConfig(config);
    } catch (err: any) {
      console.error('Erro ao carregar diagnóstico:', err);
      setError(err.message || 'Erro ao conectar com o backend');
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      const token = sessionStorage.getItem('token');
      if (!token) {
        throw new Error('Token não encontrado');
      }

      const response = await fetch('/api/v1/diagnostics/test-connection', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erro ao testar conexão');
      }

      const result = await response.json();
      setTestResult(result);
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || 'Erro ao testar conexão',
        version: null,
        tables: null
      });
    } finally {
      setIsTesting(false);
    }
  };

  onMount(() => {
    loadDiagnostics();
  });

  const getStatusColor = (status: string) => {
    if (status === 'ok' || status === 'enabled') {
      return 'text-green-500 bg-green-500/10 border-green-500/30';
    }
    if (status === 'disabled') {
      return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
    }
    return 'text-red-500 bg-red-500/10 border-red-500/30';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'ok' || status === 'enabled') {
      return CheckCircle;
    }
    return AlertTriangle;
  };

  const getStatusLabel = (status: string) => {
    if (status === 'ok') return 'OK';
    if (status === 'enabled') return 'Habilitado';
    if (status === 'disabled') return 'Desabilitado';
    return 'Erro';
  };

  return (
    <div class="flex flex-col h-full p-6 gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div class="flex justify-between items-start">
        <div>
          <h2 class="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Activity size={24} />
            Diagnóstico do Sistema
          </h2>
          <p class="text-muted mt-1">Configurações e status das conexões de banco de dados</p>
        </div>
        <button onClick={loadDiagnostics} class="btn btn-outline gap-2" disabled={isLoading()}>
          <RefreshCw size={16} class={isLoading() ? 'animate-spin' : ''} />
          Atualizar
        </button>
      </div>

      {/* Error Alert */}
      <Show when={error()}>
        <div class="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 flex items-center gap-3">
          <AlertTriangle size={24} />
          <div>
            <h3 class="font-bold">Erro ao carregar diagnóstico</h3>
            <p class="text-sm opacity-80">{error()}</p>
          </div>
        </div>
      </Show>

      <Show when={!isLoading() && dbStatus() && dbConfig()} fallback={
        <div class="p-12 text-center border rounded-xl bg-card text-muted animate-pulse">
          <RefreshCw class="animate-spin mx-auto mb-4" size={32} />
          Carregando informações do sistema...
        </div>
      }>
        {/* Status Cards */}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-6 rounded-lg border bg-card">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-medium text-muted-foreground">Parquet (Dados)</span>
              <HardDrive size={18} class="text-blue-500" />
            </div>
            <div class="flex flex-col gap-2">
              {(() => {
                const status = dbStatus()?.parquet.status || 'unknown';
                const StatusIcon = getStatusIcon(status);
                return (
                  <>
                    <span class={`inline-flex items-center gap-2 rounded border px-3 py-1.5 text-sm font-medium ${getStatusColor(status)}`}>
                      <StatusIcon size={16} />
                      {getStatusLabel(status)}
                    </span>
                    <p class="text-xs text-muted-foreground mt-2">
                      Tamanho: <span class="font-mono font-medium">{dbStatus()?.parquet.size_mb} MB</span>
                    </p>
                  </>
                );
              })()}
            </div>
          </div>

          <div class="p-6 rounded-lg border bg-card">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-medium text-muted-foreground">SQL Server</span>
              <Database size={18} class="text-orange-500" />
            </div>
            <div class="flex flex-col gap-2">
              {(() => {
                const status = dbStatus()?.sql_server.status || 'unknown';
                const StatusIcon = getStatusIcon(status);
                return (
                  <span class={`inline-flex items-center gap-2 rounded border px-3 py-1.5 text-sm font-medium ${getStatusColor(status)}`}>
                    <StatusIcon size={16} />
                    {getStatusLabel(status)}
                  </span>
                );
              })()}
            </div>
          </div>

          <div class="p-6 rounded-lg border bg-card">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-medium text-muted-foreground">Supabase Auth</span>
              <Server size={18} class="text-green-500" />
            </div>
            <div class="flex flex-col gap-2">
              {(() => {
                const status = dbStatus()?.supabase.status || 'unknown';
                const StatusIcon = getStatusIcon(status);
                return (
                  <span class={`inline-flex items-center gap-2 rounded border px-3 py-1.5 text-sm font-medium ${getStatusColor(status)}`}>
                    <StatusIcon size={16} />
                    {getStatusLabel(status)}
                  </span>
                );
              })()}
            </div>
          </div>
        </div>

        {/* Configurações Detectadas */}
        <div class="p-6 rounded-lg border bg-card">
          <h3 class="font-semibold flex items-center gap-2 mb-4">
            <Settings size={18} />
            Configurações Detectadas
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-muted-foreground font-medium">Modo de Operação</label>
              <p class="font-mono text-sm mt-1 p-2 bg-secondary rounded">
                {dbConfig()?.use_sql_server ? 'SQL Server (Híbrido)' : 'Apenas Parquet (Cloud)'}
              </p>
            </div>

            <Show when={dbConfig()?.use_sql_server}>
              <div>
                <label class="text-xs text-muted-foreground font-medium">Servidor SQL</label>
                <p class="font-mono text-sm mt-1 p-2 bg-secondary rounded">
                  {dbConfig()?.database_server || 'N/A'}
                </p>
              </div>

              <div>
                <label class="text-xs text-muted-foreground font-medium">Banco de Dados</label>
                <p class="font-mono text-sm mt-1 p-2 bg-secondary rounded">
                  {dbConfig()?.database_name || 'N/A'}
                </p>
              </div>

              <div>
                <label class="text-xs text-muted-foreground font-medium">Usuário SQL</label>
                <p class="font-mono text-sm mt-1 p-2 bg-secondary rounded">
                  {dbConfig()?.database_user || 'N/A'}
                </p>
              </div>
            </Show>

            <Show when={dbConfig()?.use_supabase}>
              <div>
                <label class="text-xs text-muted-foreground font-medium">Supabase URL</label>
                <p class="font-mono text-sm mt-1 p-2 bg-secondary rounded truncate">
                  {dbConfig()?.supabase_url || 'N/A'}
                </p>
              </div>
            </Show>

            <div>
              <label class="text-xs text-muted-foreground font-medium">Path Parquet</label>
              <p class="font-mono text-xs mt-1 p-2 bg-secondary rounded truncate" title={dbStatus()?.parquet.path}>
                {dbStatus()?.parquet.path || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Teste de Conexão SQL Server */}
        <Show when={dbConfig()?.use_sql_server}>
          <div class="p-6 rounded-lg border bg-card">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-semibold flex items-center gap-2">
                <Play size={18} />
                Teste de Conexão SQL Server
              </h3>
              <button
                onClick={testConnection}
                class="btn btn-primary gap-2"
                disabled={isTesting()}
              >
                {isTesting() ? (
                  <>
                    <RefreshCw size={16} class="animate-spin" />
                    Testando...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Testar Conexão
                  </>
                )}
              </button>
            </div>

            <Show when={testResult()}>
              <div class={`p-4 rounded-lg border ${testResult()?.success ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                <div class="flex items-start gap-3">
                  {testResult()?.success ? (
                    <CheckCircle size={24} class="text-green-500 flex-shrink-0" />
                  ) : (
                    <AlertTriangle size={24} class="text-red-500 flex-shrink-0" />
                  )}
                  <div class="flex-1">
                    <p class={`font-medium ${testResult()?.success ? 'text-green-500' : 'text-red-500'}`}>
                      {testResult()?.message}
                    </p>

                    <Show when={testResult()?.version}>
                      <p class="text-sm text-muted-foreground mt-2">
                        Versão: <span class="font-mono">{testResult()?.version}</span>
                      </p>
                    </Show>

                    <Show when={testResult()?.tables && testResult()!.tables!.length > 0}>
                      <div class="mt-3">
                        <p class="text-sm font-medium mb-2 flex items-center gap-2">
                          <FileText size={14} />
                          Tabelas Disponíveis ({testResult()!.tables!.length})
                        </p>
                        <div class="max-h-48 overflow-y-auto bg-secondary/50 rounded p-2">
                          <div class="grid grid-cols-2 md:grid-cols-3 gap-1">
                            <For each={testResult()?.tables}>
                              {(table) => (
                                <span class="text-xs font-mono p-1 hover:bg-secondary rounded">
                                  {table}
                                </span>
                              )}
                            </For>
                          </div>
                        </div>
                      </div>
                    </Show>
                  </div>
                </div>
              </div>
            </Show>
          </div>
        </Show>

        {/* Instruções para Streamlit Cloud */}
        <Show when={!dbConfig()?.use_sql_server}>
          <div class="p-6 bg-blue-500/5 border border-blue-500/20 rounded-lg">
            <h4 class="font-semibold text-blue-500 mb-3">Modo Cloud (Apenas Parquet)</h4>
            <p class="text-sm text-muted-foreground mb-3">
              O sistema está rodando em modo cloud, usando apenas arquivos Parquet como fonte de dados.
              Este é o modo recomendado para deploy em Streamlit Cloud ou ambientes sem SQL Server.
            </p>
            <ul class="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Autenticação: Parquet (users.parquet) ou Supabase</li>
              <li>Dados analíticos: Parquet (admmat.parquet)</li>
              <li>Performance: Otimizado para leitura em cache</li>
              <li>Deploy: Compatível com Streamlit Cloud</li>
            </ul>
          </div>
        </Show>
      </Show>
    </div>
  );
}
