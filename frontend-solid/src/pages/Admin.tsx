import { Shield, Users, Database, Settings, RefreshCw, CheckCircle, AlertCircle, Plus, Edit, Trash2, X } from 'lucide-solid';
import { createSignal, Show, For, createResource, createMemo } from 'solid-js';
import { adminApi, analyticsApi, UserData, CreateUserPayload, UpdateUserPayload, AuditLogItem, PlaygroundCanaryAccessItem, PlaygroundSqlAccessItem } from '@/lib/api';

export default function Admin() {
  const [syncing, setSyncing] = createSignal(false);
  const [message, setMessage] = createSignal<{ type: 'success' | 'error', text: string } | null>(null);
  const [activeTab, setActiveTab] = createSignal<'sync' | 'users'>('sync');
  const [showOnlySqlEnabled, setShowOnlySqlEnabled] = createSignal(false);
  const [showOnlyCanaryEnabled, setShowOnlyCanaryEnabled] = createSignal(false);
  const [showAuditPanel, setShowAuditPanel] = createSignal(false);
  const [showUserModal, setShowUserModal] = createSignal(false);
  const [editingUser, setEditingUser] = createSignal<UserData | null>(null);
  const [formData, setFormData] = createSignal<CreateUserPayload>({
    username: '',
    email: '',
    password: '',
    role: 'user',
    allowed_segments: []
  });

  // User Management State
  const [users, { refetch: refetchUsers }] = createResource<UserData[]>(async () => {
    try {
      const response = await adminApi.getUsers();
      return response.data;
    } catch (err) {
      console.error('Error loading users:', err);
      return [];
    }
  });

  const [sqlAccessMap, { refetch: refetchSqlAccess }] = createResource(async () => {
    try {
      const response = await adminApi.getPlaygroundSqlAccess();
      const map = new Map<string, PlaygroundSqlAccessItem>();
      response.data.forEach((item) => map.set(item.user_id, item));
      return map;
    } catch (err) {
      console.error('Error loading SQL access map:', err);
      return new Map<string, PlaygroundSqlAccessItem>();
    }
  });

  const [canaryAccessMap, { refetch: refetchCanaryAccess }] = createResource(async () => {
    try {
      const response = await adminApi.getPlaygroundCanaryAccess();
      const map = new Map<string, PlaygroundCanaryAccessItem>();
      response.data.forEach((item) => map.set(item.user_id, item));
      return map;
    } catch (err) {
      console.error('Error loading canary access map:', err);
      return new Map<string, PlaygroundCanaryAccessItem>();
    }
  });

  const [auditLogs, { refetch: refetchAuditLogs }] = createResource<AuditLogItem[], boolean>(
    showAuditPanel,
    async (visible) => {
      if (!visible) return [];
      try {
        const response = await adminApi.getAuditLogs(50);
        return response.data;
      } catch (err) {
        console.error('Error loading audit logs:', err);
        return [];
      }
    }
  );

  // Load Segment Options
  const [filterOptions] = createResource<boolean, { categorias: string[]; segmentos: string[] }>(
    showUserModal,
    async (isOpen) => {
      if (!isOpen) return { categorias: [], segmentos: [] };
      try {
        const response = await analyticsApi.getFilterOptions();
        return response.data;
      } catch (err) {
        console.error('Error loading filter options:', err);
        return { categorias: [], segmentos: [] };
      }
    }
  );

  const filteredUsers = createMemo(() => {
    const list = users() || [];
    return list.filter((u) => {
      if (showOnlySqlEnabled() && !(u.role === 'admin' || sqlAccessMap()?.get(u.id)?.active === true)) {
        return false;
      }
      if (showOnlyCanaryEnabled() && !(u.role === 'admin' || canaryAccessMap()?.get(u.id)?.enabled === true)) {
        return false;
      }
      return true;
    });
  });

  const handleSync = async () => {
    setSyncing(true);
    setMessage(null);
    try {
      await adminApi.syncParquet();
      setMessage({ type: 'success', text: 'Sincronização iniciada em segundo plano!' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Erro ao iniciar sincronização. Verifique logs.' });
    } finally {
      setSyncing(false);
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const openCreateUserModal = () => {
    setEditingUser(null);
    setFormData({ username: '', email: '', password: '', role: 'user', allowed_segments: [] });
    setShowUserModal(true);
  };

  const openEditUserModal = (user: UserData) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      role: user.role,
      allowed_segments: user.allowed_segments || []
    });
    setShowUserModal(true);
  };

  const closeUserModal = () => {
    setShowUserModal(false);
    setEditingUser(null);
    setFormData({ username: '', email: '', password: '', role: 'user', allowed_segments: [] });
  };

  const handleSubmitUser = async (e: Event) => {
    e.preventDefault();
    setMessage(null);

    try {
      const data = formData();

      if (editingUser()) {
        // Update existing user
        const updateData: UpdateUserPayload = {
          username: data.username,
          email: data.email,
          role: data.role,
          allowed_segments: data.allowed_segments
        };

        // Only include password if provided
        if (data.password) {
          updateData.password = data.password;
        }

        await adminApi.updateUser(editingUser()!.id, updateData);
        setMessage({ type: 'success', text: `Usuário ${data.username} atualizado com sucesso!` });
      } else {
        // Create new user
        await adminApi.createUser(data);
        setMessage({ type: 'success', text: `Usuário ${data.username} criado com sucesso!` });
      }

      closeUserModal();
      refetchUsers();
      refetchSqlAccess();
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      console.error('Erro ao salvar usuário:', err);
      let errorMsg = 'Erro ao salvar usuário';
      
      if (err?.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Tratar erro de validação do Pydantic (array de objetos)
          errorMsg = detail.map((e: any) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(', ');
        } else {
          errorMsg = String(detail);
        }
      }
      
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 8000); // Mais tempo para ler erros longos
    }
  };

  const handleDeleteUser = async (user: UserData) => {
    if (!confirm(`Tem certeza que deseja excluir o usuário ${user.username}?`)) {
      return;
    }

    setMessage(null);
    try {
      await adminApi.deleteUser(user.id);
      setMessage({ type: 'success', text: `Usuário ${user.username} excluído com sucesso!` });
      refetchUsers();
      refetchSqlAccess();
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao excluir usuário';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleToggleActive = async (user: UserData) => {
    setMessage(null);
    try {
      await adminApi.updateUser(user.id, { is_active: !user.is_active });
      setMessage({
        type: 'success',
        text: `Usuário ${user.username} ${!user.is_active ? 'ativado' : 'desativado'} com sucesso!`
      });
      refetchUsers();
      refetchSqlAccess();
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao atualizar status do usuário';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleToggleSqlAccess = async (user: UserData) => {
    if (user.role === 'admin') return;
    setMessage(null);
    try {
      const current = sqlAccessMap()?.get(user.id);
      const enabledNow = current?.enabled === true;
      let expiresAt: string | undefined = undefined;
      if (!enabledNow) {
        const daysRaw = window.prompt('Validade em dias para SQL completo (vazio = sem expiração):', '30');
        if (daysRaw === null) return;
        const clean = daysRaw.trim();
        if (clean.length > 0) {
          const days = Number.parseInt(clean, 10);
          if (Number.isNaN(days) || days <= 0) {
            setMessage({ type: 'error', text: 'Validade inválida. Informe dias > 0 ou deixe vazio.' });
            return;
          }
          const dt = new Date();
          dt.setDate(dt.getDate() + days);
          expiresAt = dt.toISOString();
        }
      }
      await adminApi.setPlaygroundSqlAccess(user.id, !enabledNow, expiresAt);
      setMessage({
        type: 'success',
        text: `SQL completo ${!enabledNow ? 'habilitado' : 'desabilitado'} para ${user.username}.`
      });
      refetchSqlAccess();
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao alterar permissão SQL';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleRevokeAllSqlAccess = async () => {
    if (!confirm('Revogar SQL completo de todos os usuários não-admin?')) return;
    setMessage(null);
    try {
      const response = await adminApi.revokeAllPlaygroundSqlAccess();
      setMessage({
        type: 'success',
        text: `${response.data.revoked_count} usuário(s) tiveram SQL completo revogado.`
      });
      refetchSqlAccess();
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao revogar permissões em massa';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleToggleCanaryAccess = async (user: UserData) => {
    if (user.role === 'admin') return;
    setMessage(null);
    try {
      const current = canaryAccessMap()?.get(user.id);
      const enabledNow = current?.enabled === true;
      await adminApi.setPlaygroundCanaryAccess(user.id, !enabledNow);
      setMessage({
        type: 'success',
        text: `Canário LLM remota ${!enabledNow ? 'habilitado' : 'desabilitado'} para ${user.username}.`
      });
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao alterar permissão canário';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleRevokeAllCanaryAccess = async () => {
    if (!confirm('Revogar acesso canário do Playground para todos os usuários não-admin?')) return;
    setMessage(null);
    try {
      const response = await adminApi.revokeAllPlaygroundCanaryAccess();
      setMessage({
        type: 'success',
        text: `${response.data.revoked_count} usuário(s) tiveram acesso canário revogado.`
      });
      refetchCanaryAccess();
      if (showAuditPanel()) refetchAuditLogs();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao revogar acessos canário em massa';
      setMessage({ type: 'error', text: errorMsg });
      setTimeout(() => setMessage(null), 5000);
    }
  };

  return (
    <div class="flex flex-col p-6 gap-6">
      {/* Header */}
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 class="text-2xl font-bold tracking-tight">Área Administrativa</h2>
          <p class="text-muted">Gerenciamento do sistema e usuários</p>
        </div>
      </div>

      {/* Message Alert */}
      <Show when={message()}>
        <div class={`p-3 rounded-lg flex items-center gap-2 text-sm ${message()?.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
          {message()?.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {message()?.text}
        </div>
      </Show>

      {/* Tabs */}
      <div class="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('sync')}
          class={`px-4 py-2 font-medium transition-colors ${activeTab() === 'sync' ? 'border-b-2 border-primary text-primary' : 'text-muted hover:text-foreground'
            }`}
        >
          <div class="flex items-center gap-2">
            <RefreshCw size={16} />
            Sincronização
          </div>
        </button>
        <button
          onClick={() => setActiveTab('users')}
          class={`px-4 py-2 font-medium transition-colors ${activeTab() === 'users' ? 'border-b-2 border-primary text-primary' : 'text-muted hover:text-foreground'
            }`}
        >
          <div class="flex items-center gap-2">
            <Users size={16} />
            Usuários
          </div>
        </button>
      </div>

      {/* Tab Content */}
      <div class="flex-1 overflow-auto">
        <Show when={activeTab() === 'sync'}>
          <div class="max-w-2xl mx-auto space-y-4">
            <div
              onClick={!syncing() ? handleSync : undefined}
              class={`p-6 border rounded-lg bg-card flex items-center gap-4 transition-all ${syncing() ? 'opacity-70 cursor-wait' : 'hover:border-primary/50 cursor-pointer hover:bg-secondary/30'
                }`}
            >
              <div class="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
                <RefreshCw size={24} class={syncing() ? 'animate-spin' : ''} />
              </div>
              <div class="flex-1">
                <h4 class="font-semibold text-lg">Sincronizar Dados</h4>
                <p class="text-sm text-muted">Atualizar Parquet via SQL Server</p>
              </div>
              {syncing() && <span class="text-sm text-primary animate-pulse">Processando...</span>}
            </div>
          </div>
        </Show>

        <Show when={activeTab() === 'users'}>
          <div class="space-y-4">
            {/* Header with Add Button */}
            <div class="flex flex-wrap justify-between items-center gap-3">
              <h3 class="text-lg font-semibold">Gerenciar Usuários</h3>
              <div class="flex items-center gap-2">
                <label class="text-xs text-muted flex items-center gap-2 px-3 py-2 border rounded-lg">
                  <input
                    type="checkbox"
                    checked={showOnlySqlEnabled()}
                    onChange={(e) => setShowOnlySqlEnabled(e.currentTarget.checked)}
                  />
                  Somente SQL habilitado
                </label>
                <label class="text-xs text-muted flex items-center gap-2 px-3 py-2 border rounded-lg">
                  <input
                    type="checkbox"
                    checked={showOnlyCanaryEnabled()}
                    onChange={(e) => setShowOnlyCanaryEnabled(e.currentTarget.checked)}
                  />
                  Somente Canário LLM
                </label>
                <button
                  onClick={handleRevokeAllSqlAccess}
                  class="btn btn-outline text-red-400 border-red-500/30 hover:bg-red-500/10"
                >
                  Revogar SQL de Todos
                </button>
                <button
                  onClick={handleRevokeAllCanaryAccess}
                  class="btn btn-outline text-amber-300 border-amber-500/30 hover:bg-amber-500/10"
                >
                  Revogar Canário de Todos
                </button>
                <button
                  onClick={openCreateUserModal}
                  class="btn btn-primary gap-2"
                >
                  <Plus size={16} />
                  Novo Usuário
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div class="border rounded-lg overflow-hidden bg-card">
              <table class="w-full">
                <thead class="bg-muted/50 border-b">
                  <tr>
                    <th class="text-left p-3 text-sm font-medium">Username</th>
                    <th class="text-left p-3 text-sm font-medium">Email</th>
                    <th class="text-left p-3 text-sm font-medium">Role</th>
                    <th class="text-left p-3 text-sm font-medium">Segmentos</th>
                    <th class="text-center p-3 text-sm font-medium">SQL Completo</th>
                    <th class="text-center p-3 text-sm font-medium">Canário LLM</th>
                    <th class="text-center p-3 text-sm font-medium">Status</th>
                    <th class="text-right p-3 text-sm font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  <Show when={users.loading}>
                    <tr>
                      <td colspan="8" class="text-center p-8 text-muted">
                        <RefreshCw size={24} class="animate-spin mx-auto mb-2" />
                        Carregando usuários...
                      </td>
                    </tr>
                  </Show>

                  <Show when={!users.loading && filteredUsers()}>
                    <For each={filteredUsers()}>
                      {(user) => (
                        <tr class="border-b hover:bg-muted/30 transition-colors">
                          <td class="p-3">{user.username}</td>
                          <td class="p-3 text-sm text-muted">{user.email}</td>
                          <td class="p-3">
                            <span class={`px-2 py-1 rounded text-xs font-medium ${user.role === 'admin' ? 'bg-purple-500/10 text-purple-400' :
                                user.role === 'user' ? 'bg-blue-500/10 text-blue-400' :
                                  'bg-gray-500/10 text-gray-400'
                              }`}>
                              {user.role}
                            </span>
                          </td>
                          <td class="p-3 text-sm text-muted">
                            <Show when={user.role === 'admin'} fallback={
                              user.allowed_segments && user.allowed_segments.length > 0
                                ? <span title={user.allowed_segments.join(', ')}>{user.allowed_segments.length} segmento(s)</span>
                                : <span class="text-yellow-500 text-xs">Nenhum</span>
                            }>
                              <span class="text-muted italic">Todos (Admin)</span>
                            </Show>
                          </td>
                          <td class="p-3 text-center">
                            <Show
                              when={user.role !== 'admin'}
                              fallback={<span class="px-2 py-1 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400">Sempre</span>}
                            >
                              <button
                                onClick={() => handleToggleSqlAccess(user)}
                                class={`px-2 py-1 rounded text-xs font-medium transition-colors ${sqlAccessMap()?.get(user.id)?.active
                                  ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                                  : 'bg-gray-500/10 text-gray-300 hover:bg-gray-500/20'
                                  }`}
                              >
                                {sqlAccessMap()?.get(user.id)?.active ? 'Habilitado' : 'Bloqueado'}
                              </button>
                              <Show when={sqlAccessMap()?.get(user.id)?.expires_at}>
                                <div class="text-[10px] text-muted mt-1">
                                  até {new Date(sqlAccessMap()!.get(user.id)!.expires_at as string).toLocaleString('pt-BR')}
                                </div>
                              </Show>
                            </Show>
                          </td>
                          <td class="p-3 text-center">
                            <Show
                              when={user.role !== 'admin'}
                              fallback={<span class="px-2 py-1 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400">Sempre</span>}
                            >
                              <button
                                onClick={() => handleToggleCanaryAccess(user)}
                                class={`px-2 py-1 rounded text-xs font-medium transition-colors ${canaryAccessMap()?.get(user.id)?.enabled
                                  ? 'bg-amber-500/10 text-amber-300 hover:bg-amber-500/20'
                                  : 'bg-gray-500/10 text-gray-300 hover:bg-gray-500/20'
                                  }`}
                              >
                                {canaryAccessMap()?.get(user.id)?.enabled ? 'Habilitado' : 'Bloqueado'}
                              </button>
                            </Show>
                          </td>
                          <td class="p-3 text-center">
                            <button
                              onClick={() => handleToggleActive(user)}
                              class={`px-2 py-1 rounded text-xs font-medium transition-colors ${user.is_active
                                  ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                                  : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                                }`}
                            >
                              {user.is_active ? 'Ativo' : 'Inativo'}
                            </button>
                          </td>
                          <td class="p-3">
                            <div class="flex justify-end gap-2">
                              <button
                                onClick={() => openEditUserModal(user)}
                                class="p-2 hover:bg-secondary rounded transition-colors"
                                title="Editar"
                              >
                                <Edit size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteUser(user)}
                                class="p-2 hover:bg-red-500/10 text-red-400 rounded transition-colors"
                                title="Excluir"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )}
                    </For>
                  </Show>

                  <Show when={!users.loading && (!filteredUsers() || filteredUsers()?.length === 0)}>
                    <tr>
                      <td colspan="8" class="text-center p-8 text-muted">
                        Nenhum usuário encontrado com o filtro atual
                      </td>
                    </tr>
                  </Show>
                </tbody>
              </table>
            </div>

            <div class="border rounded-lg bg-card p-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-semibold">Auditoria de Permissões Playground (Admin)</h4>
                <button
                  class="btn btn-outline btn-sm"
                  onClick={() => {
                    const next = !showAuditPanel();
                    setShowAuditPanel(next);
                    if (next) refetchAuditLogs();
                  }}
                >
                  {showAuditPanel() ? 'Ocultar' : 'Carregar'}
                </button>
              </div>
              <Show when={showAuditPanel()} fallback={<p class="text-xs text-muted">Painel de auditoria em modo sob demanda para reduzir carga.</p>}>
              <div class="overflow-auto">
                <table class="w-full text-sm">
                  <thead class="bg-muted/40">
                    <tr>
                      <th class="text-left p-2">Data/Hora</th>
                      <th class="text-left p-2">Admin</th>
                      <th class="text-left p-2">Ação</th>
                      <th class="text-left p-2">Alvo</th>
                      <th class="text-left p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <For each={(auditLogs() || []).filter((l) => l.resource === 'playground_sql_access' || l.resource === 'playground_canary_access').slice(0, 20)}>
                      {(log) => (
                        <tr class="border-b border-border/40">
                          <td class="p-2">{new Date(log.timestamp).toLocaleString('pt-BR')}</td>
                          <td class="p-2">{log.user_name}</td>
                          <td class="p-2">{log.action}</td>
                          <td class="p-2">{(log.details as any)?.target_user_id || 'massa'}</td>
                          <td class="p-2">
                            <span class={`px-2 py-0.5 rounded text-xs ${log.status === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      )}
                    </For>
                    <Show when={(auditLogs() || []).filter((l) => l.resource === 'playground_sql_access' || l.resource === 'playground_canary_access').length === 0}>
                      <tr>
                        <td colspan="5" class="p-3 text-muted">Sem eventos de auditoria para permissões do Playground.</td>
                      </tr>
                    </Show>
                  </tbody>
                </table>
              </div>
              </Show>
            </div>
          </div>
        </Show>
      </div>

      {/* User Modal */}
      <Show when={showUserModal()}>
        <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={closeUserModal}>
          <div class="bg-card border rounded-lg max-w-md w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-semibold">
                {editingUser() ? 'Editar Usuário' : 'Novo Usuário'}
              </h3>
              <button onClick={closeUserModal} class="p-1 hover:bg-secondary rounded">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmitUser} class="space-y-4">
              <div>
                <label class="block text-sm font-medium mb-1">Username</label>
                <input
                  type="text"
                  value={formData().username}
                  onInput={(e) => setFormData({ ...formData(), username: e.currentTarget.value })}
                  class="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label class="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData().email}
                  onInput={(e) => setFormData({ ...formData(), email: e.currentTarget.value })}
                  class="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label class="block text-sm font-medium mb-1">
                  Senha {editingUser() && '(deixe em branco para não alterar)'}
                </label>
                <input
                  type="password"
                  value={formData().password}
                  onInput={(e) => setFormData({ ...formData(), password: e.currentTarget.value })}
                  class="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required={!editingUser()}
                  minLength={8}
                />
              </div>

              <div>
                <label class="block text-sm font-medium mb-1">Role</label>
                <select
                  value={formData().role}
                  onChange={(e) => setFormData({ ...formData(), role: e.currentTarget.value })}
                  class="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  <option value="viewer">Viewer</option>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {/* Segment Selection */}
              <div class="space-y-2">
                <label class="block text-sm font-medium">Segmentos Permitidos</label>
                <div class="border rounded-lg p-3 max-h-48 overflow-y-auto space-y-2 bg-background">
                  <Show when={!filterOptions.loading} fallback={<span class="text-xs text-muted">Carregando segmentos...</span>}>
                    <For each={filterOptions()?.segmentos || []}>
                      {(segment) => (
                        <label class="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-1 rounded">
                          <input
                            type="checkbox"
                            checked={formData().allowed_segments?.includes(segment)}
                            onChange={(e) => {
                              const current = formData().allowed_segments || [];
                              if (e.currentTarget.checked) {
                                setFormData({ ...formData(), allowed_segments: [...current, segment] });
                              } else {
                                setFormData({ ...formData(), allowed_segments: current.filter(s => s !== segment) });
                              }
                            }}
                            class="checkbox checkbox-sm checkbox-primary"
                          />
                          <span>{segment}</span>
                        </label>
                      )}
                    </For>
                    <Show when={!filterOptions()?.segmentos?.length}>
                      <p class="text-xs text-muted">Nenhum segmento disponível encontrado.</p>
                    </Show>
                  </Show>
                </div>
                <p class="text-xs text-muted">
                  {formData().role === 'admin'
                    ? 'Admin tem acesso total independente desta seleção.'
                    : 'Se nenhum selecionado, o usuário não verá dados.'}
                </p>
              </div>

              <div class="flex gap-2 pt-4">
                <button type="button" onClick={closeUserModal} class="flex-1 btn btn-outline">
                  Cancelar
                </button>
                <button type="submit" class="flex-1 btn btn-primary">
                  {editingUser() ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </Show>
    </div>
  );
}
