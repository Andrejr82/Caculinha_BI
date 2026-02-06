import { createSignal, onMount, For, Show } from 'solid-js';
import { FileText, Download, Filter, Calendar, RefreshCw, Search, Package } from 'lucide-solid';
import api from '../lib/api';

interface TransferReport {
  batch_id?: string;
  transfer_id?: string;
  modo?: string;
  solicitante_id: string;
  timestamp: string;
  total_transferencias?: number;
  transferencias?: Array<{
    produto_id: number;
    une_origem: number;
    une_destino: number;
    quantidade: number;
  }>;
  produto_id?: number;
  une_origem?: number;
  une_destino?: number;
  quantidade?: number;
}

export default function Reports() {
  const [reports, setReports] = createSignal<TransferReport[]>([]);
  const [loading, setLoading] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);

  // Filtros
  const [startDate, setStartDate] = createSignal('');
  const [endDate, setEndDate] = createSignal('');
  const [searchTerm, setSearchTerm] = createSignal('');

  const loadReports = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate()) params.append('start_date', startDate());
      if (endDate()) params.append('end_date', endDate());

      const response = await api.get<TransferReport[]>(`/transfers/report?${params.toString()}`);
      setReports(response.data);
    } catch (err: any) {
      console.error('Erro ao carregar relatórios:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar relatórios');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = (report: TransferReport) => {
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    const fileName = report.batch_id || report.transfer_id || 'transfer-report';
    link.download = `${fileName}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadAllAsCSV = () => {
    const allTransfers: any[] = [];

    reports().forEach(report => {
      if (report.transferencias) {
        // Batch transfer
        report.transferencias.forEach(t => {
          allTransfers.push({
            ...t,
            solicitante: report.solicitante_id,
            timestamp: report.timestamp,
            batch_id: report.batch_id
          });
        });
      } else {
        // Single transfer
        allTransfers.push({
          produto_id: report.produto_id,
          une_origem: report.une_origem,
          une_destino: report.une_destino,
          quantidade: report.quantidade,
          solicitante: report.solicitante_id,
          timestamp: report.timestamp,
          transfer_id: report.transfer_id
        });
      }
    });

    if (allTransfers.length === 0) {
      alert('Nenhuma transferência para exportar');
      return;
    }

    // Gerar CSV
    const headers = ['Produto ID', 'UNE Origem', 'UNE Destino', 'Quantidade', 'Solicitante', 'Data/Hora', 'ID'];
    const csv = [
      headers.join(','),
      ...allTransfers.map(t =>
        [
          t.produto_id,
          t.une_origem,
          t.une_destino,
          t.quantidade,
          t.solicitante,
          t.timestamp,
          t.batch_id || t.transfer_id || ''
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transferencias-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredReports = () => {
    if (!searchTerm()) return reports();

    return reports().filter(report => {
      const search = searchTerm().toLowerCase();
      return (
        report.solicitante_id?.toLowerCase().includes(search) ||
        report.batch_id?.toLowerCase().includes(search) ||
        report.transfer_id?.toLowerCase().includes(search)
      );
    });
  };

  const setQuickFilter = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
    loadReports();
  };

  onMount(() => {
    loadReports();
  });

  return (
    <div class="flex flex-col p-6 gap-6">
      {/* Header */}
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <FileText size={28} />
            Relatórios de Transferências
          </h2>
          <p class="text-muted">Histórico de solicitações de transferências entre UNEs</p>
        </div>
        <button
          onClick={loadReports}
          class="btn btn-outline gap-2"
          disabled={loading()}
        >
          <RefreshCw size={16} class={loading() ? 'animate-spin' : ''} />
          Atualizar
        </button>
      </div>

      {/* Filters */}
      <div class="card p-4 border">
        <div class="flex items-center gap-2 mb-4">
          <Filter size={20} />
          <h3 class="font-semibold">Filtros</h3>
        </div>

        {/* Quick Filters */}
        <div class="flex gap-2 mb-4">
          <button class="btn btn-outline text-sm" onClick={() => setQuickFilter(7)}>
            Últimos 7 dias
          </button>
          <button class="btn btn-outline text-sm" onClick={() => setQuickFilter(30)}>
            Últimos 30 dias
          </button>
          <button class="btn btn-outline text-sm" onClick={() => setQuickFilter(90)}>
            Últimos 90 dias
          </button>
        </div>

        {/* Custom Filters */}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="date"
            class="input"
            value={startDate()}
            onInput={(e) => setStartDate(e.currentTarget.value)}
            placeholder="Data Início"
          />
          <input
            type="date"
            class="input"
            value={endDate()}
            onInput={(e) => setEndDate(e.currentTarget.value)}
            placeholder="Data Fim"
          />
          <input
            type="text"
            class="input"
            placeholder="Buscar por solicitante ou ID..."
            value={searchTerm()}
            onInput={(e) => setSearchTerm(e.currentTarget.value)}
          />
          <button
            class="btn btn-primary"
            onClick={loadReports}
            disabled={loading()}
          >
            Aplicar Filtros
          </button>
        </div>
      </div>

      {/* Error State */}
      <Show when={error()}>
        <div class="card p-4 border-red-500 bg-red-500/10">
          <p class="text-red-500">{error()}</p>
        </div>
      </Show>

      {/* Stats */}
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card p-4 border">
          <div class="text-sm text-muted mb-1">Total de Solicitações</div>
          <div class="text-2xl font-bold">{filteredReports().length}</div>
        </div>

        <div class="card p-4 border">
          <div class="text-sm text-muted mb-1">Total de Transferências</div>
          <div class="text-2xl font-bold">
            {filteredReports().reduce((acc, r) => acc + (r.total_transferencias || 1), 0)}
          </div>
        </div>

        <div class="card p-4 border">
          <div class="text-sm text-muted mb-1">Ações</div>
          <button
            class="btn btn-outline w-full gap-2 text-sm"
            onClick={downloadAllAsCSV}
            disabled={filteredReports().length === 0}
          >
            <Download size={16} />
            Exportar Tudo (CSV)
          </button>
        </div>
      </div>

      {/* Loading State */}
      <Show when={loading()}>
        <div class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <RefreshCw size={48} class="mx-auto mb-4 opacity-50 animate-spin" />
            <p class="text-muted">Carregando relatórios...</p>
          </div>
        </div>
      </Show>

      {/* Reports Table */}
      <Show when={!loading()}>
        <div class="card border">
          <div class="p-4 border-b">
            <h3 class="font-semibold">
              Histórico ({filteredReports().length} {filteredReports().length === 1 ? 'solicitação' : 'solicitações'})
            </h3>
          </div>

          <Show when={filteredReports().length > 0} fallback={
            <div class="p-12 text-center text-muted">
              <Package size={48} class="mx-auto mb-4 opacity-20" />
              <p>Nenhuma solicitação encontrada</p>
              <p class="text-sm mt-2">Ajuste os filtros ou crie uma nova transferência</p>
            </div>
          }>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-muted/50">
                  <tr class="text-left text-xs font-medium text-muted uppercase">
                    <th class="p-3">ID</th>
                    <th class="p-3">Tipo</th>
                    <th class="p-3">Transferências</th>
                    <th class="p-3">Solicitante</th>
                    <th class="p-3">Data/Hora</th>
                    <th class="p-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody class="divide-y">
                  <For each={filteredReports()}>
                    {(report) => (
                      <tr class="hover:bg-muted/30 transition-colors">
                        <td class="p-3 font-mono text-xs">
                          {report.batch_id || report.transfer_id || 'N/A'}
                        </td>
                        <td class="p-3">
                          <span class={`px-2 py-1 text-xs rounded ${report.batch_id
                              ? 'bg-blue-500/10 text-blue-400'
                              : 'bg-green-500/10 text-green-400'
                            }`}>
                            {report.batch_id ? `Lote (${report.modo})` : 'Simples'}
                          </span>
                        </td>
                        <td class="p-3 font-semibold">
                          {report.total_transferencias || 1}
                        </td>
                        <td class="p-3 text-sm">{report.solicitante_id}</td>
                        <td class="p-3 text-sm font-mono text-muted">
                          {new Date(report.timestamp).toLocaleString('pt-BR')}
                        </td>
                        <td class="p-3 text-right">
                          <button
                            class="btn btn-outline btn-sm gap-2"
                            onClick={() => downloadReport(report)}
                          >
                            <Download size={14} />
                            JSON
                          </button>
                        </td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </div>
          </Show>
        </div>
      </Show>
    </div>
  );
}
