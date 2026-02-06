import { Shield, Users, Database, Settings, RefreshCw, CheckCircle, AlertCircle, Plus, Edit, Trash2, X } from 'lucide-solid';
import { createSignal, Show, For, createResource, onMount } from 'solid-js';
import { adminApi, analyticsApi, UserData, CreateUserPayload, UpdateUserPayload } from '@/lib/api';

export default function Admin() {
  const [syncing, setSyncing] = createSignal(false);
  const [message, setMessage] = createSignal<{ type: 'success' | 'error', text: string } | null>(null);
  const [activeTab, setActiveTab] = createSignal<'sync' | 'users'>('sync');

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

  // Load Segment Options
  const [filterOptions] = createResource(async () => {
    try {
      const response = await analyticsApi.getFilterOptions();
      return response.data;
    } catch (err) {
      console.error('Error loading filter options:', err);
      return { categorias: [], segmentos: [] };
    }
  });

  const [showUserModal, setShowUserModal] = createSignal(false);
  const [editingUser, setEditingUser] = createSignal<UserData | null>(null);
  const [formData, setFormData] = createSignal<CreateUserPayload>({
    username: '',
    email: '',
    password: '',
    role: 'user',
    allowed_segments: []
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
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Erro ao atualizar status do usuário';
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
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-semibold">Gerenciar Usuários</h3>
              <button
                onClick={openCreateUserModal}
                class="btn btn-primary gap-2"
              >
                <Plus size={16} />
                Novo Usuário
              </button>
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
                    <th class="text-center p-3 text-sm font-medium">Status</th>
                    <th class="text-right p-3 text-sm font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  <Show when={users.loading}>
                    <tr>
                      <td colspan="6" class="text-center p-8 text-muted">
                        <RefreshCw size={24} class="animate-spin mx-auto mb-2" />
                        Carregando usuários...
                      </td>
                    </tr>
                  </Show>

                  <Show when={!users.loading && users()}>
                    <For each={users()}>
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

                  <Show when={!users.loading && (!users() || users()?.length === 0)}>
                    <tr>
                      <td colspan="6" class="text-center p-8 text-muted">
                        Nenhum usuário encontrado
                      </td>
                    </tr>
                  </Show>
                </tbody>
              </table>
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
