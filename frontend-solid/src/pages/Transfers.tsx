import { createSignal, createEffect, onMount, For, Show } from 'solid-js';
import { createStore } from 'solid-js/store';
import { Truck, Search, Plus, Trash2, ShoppingCart, AlertTriangle, CheckCircle, Package, ArrowRight, Filter, Map, Box, History, Clock } from 'lucide-solid';
import api from '../lib/api';

// Types
type TransferMode = 'UNE - UNE' | 'UNE - UNES' | 'UNES - UNES';

interface Product {
  produto_id: number;
  nome: string;
  segmento: string;
  grupo: string;
  fabricante: string;
  estoque_loja: number;
  estoque_cd: number;
  vendas_30dd: number;
}

interface UNE {
  une: number;
  total_produtos: number;
  estoque_total: number;
}

interface CartItem {
  produto_id: number;
  produto_nome: string;
  une_origem: number;
  une_destino: number[];
  quantidade: number;
  score?: number;
  nivel_urgencia?: string;
}

interface ValidatedItem extends CartItem { }

interface ValidationResult {
  status: string;
  mensagem: string;
  score_prioridade?: number;
  nivel_urgencia?: string;
}

interface TrackingItem {
  id: string;
  origem: string;
  destino: string;
  itensResumo: string;
  dataLabel: string;
  status: string;
}

export default function Transfers() {
  // --- STATE MANAGEMENT ---
  const [mode, setMode] = createSignal<TransferMode>('UNE - UNE');
  const [activeTab, setActiveTab] = createSignal<'create' | 'tracking'>('create');

  const [unes, setUnes] = createSignal<UNE[]>([]);
  const [products, setProducts] = createSignal<Product[]>([]);
  const [cart, setCart] = createStore<{ items: CartItem[] }>({ items: [] });

  // Filters & Search
  const [availableSegmentos, setAvailableSegmentos] = createSignal<string[]>([]);
  const [availableGrupos, setAvailableGrupos] = createSignal<string[]>([]);
  const [searchSegmento, setSearchSegmento] = createSignal('');
  const [searchGrupo, setSearchGrupo] = createSignal('');
  const [searchQuery, setSearchQuery] = createSignal(''); // Text search if needed

  // Selection
  const [selectedUnesOrigem, setSelectedUnesOrigem] = createSignal<number[]>([]);
  const [selectedUnesDestino, setSelectedUnesDestino] = createSignal<number[]>([]);
  const [selectedProducts, setSelectedProducts] = createSignal<Product[]>([]);
  const [quantidade, setQuantidade] = createSignal<number | ''>('');

  // UI States
  const [loading, setLoading] = createSignal(false);
  const [searching, setSearching] = createSignal(false);
  const [validating, setValidating] = createSignal(false);
  const [creating, setCreating] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [success, setSuccess] = createSignal<string | null>(null);
  const [selectedTracking, setSelectedTracking] = createSignal<TrackingItem | null>(null);

  const trackingItems: TrackingItem[] = [
    {
      id: 'REQ-885',
      origem: 'UNE 10',
      destino: 'UNE 99',
      itensResumo: '12 produtos (450 un.)',
      dataLabel: 'Hoje, 10:30',
      status: 'Aguardando Aprovação',
    },
    {
      id: 'REQ-882',
      origem: 'UNE 20',
      destino: 'Múltiplos',
      itensResumo: '5 produtos (120 un.)',
      dataLabel: 'Ontem',
      status: 'Em Separação',
    },
  ];

  // --- DATA LOADING ---
  const loadUnes = async () => {
    try {
      const response = await api.get<UNE[]>('/transfers/unes');
      setUnes(response.data);
      // Auto-select if only 1 UNE exists (rare but possible)
      if (response.data.length === 1 && selectedUnesOrigem().length === 0) {
        setSelectedUnesOrigem([response.data[0].une]);
      }
    } catch (err) {
      console.error('Failed to load UNEs', err);
    }
  };

  const loadFilters = async () => {
    try {
      const params: any = {};
      if (searchSegmento()) params.segmento = searchSegmento();
      const response = await api.get('/transfers/filters', { params });
      if (availableSegmentos().length === 0) setAvailableSegmentos(response.data.segmentos || []);
      setAvailableGrupos(response.data.grupos || []);
    } catch (err) {
      console.error('Failed to load filters', err);
    }
  };

  const searchProducts = async () => {
    setSearching(true);
    try {
      const response = await api.post<Product[]>('/transfers/products/search', {
        segmento: searchSegmento() || undefined,
        grupo: searchGrupo() || undefined,
        nome: searchQuery() || undefined,
        limit: 50
      });
      setProducts(response.data);
    } catch (err: any) {
      setError('Erro ao buscar produtos');
    } finally {
      setSearching(false);
    }
  };

  onMount(() => {
    loadUnes();
    loadFilters();
    searchProducts();
  });

  createEffect(() => loadFilters()); // Cascade filters

  // --- ACTIONS ---
  const addToManifest = async () => {
    if (selectedProducts().length === 0 || selectedUnesOrigem().length === 0 || selectedUnesDestino().length === 0 || !quantidade()) {
      setError('Configuração incompleta. Selecione Origem, Destino, Produto e Quantidade.');
      return;
    }

    setValidating(true);
    const qtd = Number(quantidade());
    const newItems: CartItem[] = [];

    try {
      // Validate/Add Logic (Simplified for UI Demo, real validation happens on backend usually)
      for (const prod of selectedProducts()) {
        for (const origem of selectedUnesOrigem()) {
          // For UNES-UNES, we might want one-to-all or one-to-one logic. 
          // Standardizing on: Every selected Origin sends to ALL selected Destinations
          // (User can refine in Manifest)
          newItems.push({
            produto_id: prod.produto_id,
            produto_nome: prod.nome,
            une_origem: origem,
            une_destino: selectedUnesDestino(),
            quantidade: qtd,
            nivel_urgencia: 'NORMAL' // Mocked validation result
          });
        }
      }
      setCart('items', [...cart.items, ...newItems]);
      setSuccess(`${newItems.length} itens adicionados ao manifesto.`);

      // Reset Selection
      setSelectedProducts([]);
      setQuantidade('');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Erro ao validar.');
    } finally {
      setValidating(false);
    }
  };

  const generateTransferRequest = async () => {
    if (cart.items.length === 0) return;
    setCreating(true);
    try {
      // Converte manifesto (com múltiplos destinos) para payload 1 registro por destino.
      const items = cart.items.flatMap((item) =>
        item.une_destino.map((destino) => ({
          produto_id: item.produto_id,
          une_origem: item.une_origem,
          une_destino: destino,
          quantidade: item.quantidade,
          // Campo exigido pelo schema backend atual; o backend substitui pelo usuário autenticado.
          solicitante_id: 'frontend',
        }))
      );

      if (items.length === 0) {
        setError('Manifesto sem destinos válidos para envio.');
        return;
      }

      const modoMap: Record<TransferMode, string> = {
        'UNE - UNE': '1→1',
        'UNE - UNES': '1→N',
        'UNES - UNES': 'N→N',
      };

      const response = await api.post('/transfers/bulk', {
        modo: modoMap[mode()],
        items,
      });

      const batchId = response.data?.batch_id;
      setSuccess(`Solicitações de Transferência criadas com sucesso!${batchId ? ` (ID: ${batchId})` : ''}`);
      setCart('items', []);
      setActiveTab('tracking'); // Auto-switch to tracking
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(detail || 'Falha ao criar solicitações.');
    } finally {
      setCreating(false);
    }
  };

  // --- RENDER HELPERS ---
  const toggleUneSelection = (uneId: number, type: 'origin' | 'dest') => {
    if (type === 'origin') {
      const current = selectedUnesOrigem();
      if (mode() === 'UNE - UNES' || mode() === 'UNE - UNE') {
        setSelectedUnesOrigem(current.includes(uneId) ? [] : [uneId]); // Single select behavior
      } else {
        setSelectedUnesOrigem(current.includes(uneId) ? current.filter(id => id !== uneId) : [...current, uneId]);
      }
    } else {
      const current = selectedUnesDestino();
      if (mode() === 'UNE - UNE') {
        setSelectedUnesDestino(current.includes(uneId) ? [] : [uneId]);
      } else {
        setSelectedUnesDestino(current.includes(uneId) ? current.filter(id => id !== uneId) : [...current, uneId]);
      }
    }
  };

  return (
    <div class="flex flex-col p-6 gap-6 max-w-[1600px] mx-auto min-h-screen">

      {/* Header & Tabs */}
      <div class="flex justify-between items-end border-b pb-4">
        <div>
          <h2 class="text-3xl font-bold flex items-center gap-3 text-slate-800 dark:text-slate-100">
            <Truck class="text-primary" size={32} />
            Central de Transferências
          </h2>
          <p class="text-muted-foreground mt-1">Gerenciamento logístico e movimentação de estoque entre unidades.</p>
        </div>
        <div class="flex gap-2">
          <button
            class={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab() === 'create' ? 'bg-primary text-primary-foreground shadow-lg' : 'hover:bg-muted text-muted-foreground'}`}
            onClick={() => setActiveTab('create')}
          >
            Nova Operação
          </button>
          <button
            class={`px-4 py-2 rounded-lg font-medium transition-all ${activeTab() === 'tracking' ? 'bg-primary text-primary-foreground shadow-lg' : 'hover:bg-muted text-muted-foreground'}`}
            onClick={() => setActiveTab('tracking')}
          >
            Rastreamento
          </button>
        </div>
      </div>

      <Show when={error()}>
        <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r shadow-sm flex items-center gap-3">
          <AlertTriangle class="text-red-500" />
          <span class="text-red-700 font-medium">{error()}</span>
          <button class="ml-auto text-red-400 hover:text-red-600" onClick={() => setError(null)}>Dismiss</button>
        </div>
      </Show>

      <Show when={success()}>
        <div class="bg-green-50 border-l-4 border-green-500 p-4 rounded-r shadow-sm flex items-center gap-3 animate-in slide-in-from-top-2">
          <CheckCircle class="text-green-500" />
          <span class="text-green-700 font-medium">{success()}</span>
        </div>
      </Show>

      {/* CREATE TAB CONTENT */}
      <Show when={activeTab() === 'create'}>
        <div class="space-y-8 animate-in fade-in duration-500">

          {/* 1. VISUAL ROUTE BUILDER */}
          <section class="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border p-6">
            <h3 class="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
              <Map size={16} /> 1. Definição de Rota
            </h3>

            <div class="flex flex-col lg:flex-row gap-8 items-stretch h-full">

              {/* ORIGIN */}
              <div class="flex-1 flex flex-col gap-3">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-lg">Origem (Saída)</span>
                  <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-mono">
                    {selectedUnesOrigem().length} selecionada(s)
                  </span>
                </div>
                <div class="flex-1 border-2 border-dashed rounded-xl p-2 bg-slate-50 dark:bg-slate-900/50 min-h-[120px] max-h-[200px] overflow-y-auto">
                  <div class="grid grid-cols-2 lg:grid-cols-3 gap-2">
                    <For each={unes()}>
                      {une => (
                        <button
                          class={`text-xs p-2 rounded border transition-all text-left ${selectedUnesOrigem().includes(une.une) ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-200' : 'bg-white hover:border-blue-300'}`}
                          onClick={() => toggleUneSelection(une.une, 'origin')}
                        >
                          <div class="font-bold">UNE {une.une}</div>
                          <div class="opacity-80 scale-90 origin-left">{une.estoque_total} un.</div>
                        </button>
                      )}
                    </For>
                  </div>
                </div>
              </div>

              {/* ROUTE ARROW (Visual Connector) */}
              <div class="flex flex-col justify-center items-center px-4 w-full lg:w-auto py-4 lg:py-0">
                <div class="flex flex-col gap-3 bg-slate-50 dark:bg-slate-800/50 p-2 rounded-xl mb-2">
                  <span class="text-[10px] font-bold text-center text-muted-foreground uppercase tracking-widest">Fluxo</span>

                  <button
                    class={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all ${mode() === 'UNE - UNE' ? 'bg-white shadow-md border-primary/20 ring-1 ring-primary/20' : 'bg-transparent border-transparent hover:bg-white/50 text-muted-foreground'}`}
                    onClick={() => setMode('UNE - UNE')}
                  >
                    <div class={`p-2 rounded-full ${mode() === 'UNE - UNE' ? 'bg-primary/10 text-primary' : 'bg-slate-200 text-slate-500'}`}>
                      <ArrowRight size={16} />
                    </div>
                    <div class="text-left">
                      <div class={`text-xs font-bold ${mode() === 'UNE - UNE' ? 'text-primary' : 'text-slate-600'}`}>Ponto a Ponto</div>
                      <div class="text-[10px] opacity-70">Direto (1 para 1)</div>
                    </div>
                  </button>

                  <button
                    class={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all ${mode() === 'UNE - UNES' ? 'bg-white shadow-md border-primary/20 ring-1 ring-primary/20' : 'bg-transparent border-transparent hover:bg-white/50 text-muted-foreground'}`}
                    onClick={() => setMode('UNE - UNES')}
                  >
                    <div class={`p-2 rounded-full ${mode() === 'UNE - UNES' ? 'bg-primary/10 text-primary' : 'bg-slate-200 text-slate-500'}`}>
                      <Box size={16} />
                    </div>
                    <div class="text-left">
                      <div class={`text-xs font-bold ${mode() === 'UNE - UNES' ? 'text-primary' : 'text-slate-600'}`}>Distribuição</div>
                      <div class="text-[10px] opacity-70">Expedição (1 para N)</div>
                    </div>
                  </button>

                  <button
                    class={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all ${mode() === 'UNES - UNES' ? 'bg-white shadow-md border-primary/20 ring-1 ring-primary/20' : 'bg-transparent border-transparent hover:bg-white/50 text-muted-foreground'}`}
                    onClick={() => setMode('UNES - UNES')}
                  >
                    <div class={`p-2 rounded-full ${mode() === 'UNES - UNES' ? 'bg-primary/10 text-primary' : 'bg-slate-200 text-slate-500'}`}>
                      <Map size={16} />
                    </div>
                    <div class="text-left">
                      <div class={`text-xs font-bold ${mode() === 'UNES - UNES' ? 'text-primary' : 'text-slate-600'}`}>Multi-Rota</div>
                      <div class="text-[10px] opacity-70">Cruzado (N para N)</div>
                    </div>
                  </button>
                </div>
                {/* Arrow removed in favor of the vertical flow selector which acts as the visual bridge */}
              </div>

              {/* DESTINATION */}
              <div class="flex-1 flex flex-col gap-3">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-lg">Destino (Entrada)</span>
                  <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-mono">
                    {selectedUnesDestino().length} selecionada(s)
                  </span>
                </div>
                <div class="flex-1 border-2 border-dashed rounded-xl p-2 bg-slate-50 dark:bg-slate-900/50 min-h-[120px] max-h-[200px] overflow-y-auto">
                  <div class="grid grid-cols-2 lg:grid-cols-3 gap-2">
                    <For each={unes()}>
                      {une => (
                        <button
                          class={`text-xs p-2 rounded border transition-all text-left ${selectedUnesDestino().includes(une.une) ? 'bg-green-600 text-white border-green-600 ring-2 ring-green-200' : 'bg-white hover:border-green-300'}`}
                          onClick={() => toggleUneSelection(une.une, 'dest')}
                          disabled={selectedUnesOrigem().includes(une.une)}
                        >
                          <div class="font-bold">UNE {une.une}</div>
                          <div class="opacity-80 scale-90 origin-left">{selectedUnesOrigem().includes(une.une) ? '(Origem)' : 'Receber'}</div>
                        </button>
                      )}
                    </For>
                  </div>
                </div>
              </div>

            </div>
          </section>

          {/* 2. PRODUCT & MANIFEST (Split View) */}
          <div class="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start h-auto">

            {/* LEFT: PRODUCT SEARCH */}
            <div class="xl:col-span-5 bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border p-6 flex flex-col h-[600px]">
              <h3 class="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <Box size={16} /> 2. Seleção de Produtos
              </h3>

              {/* Search Bar */}
              <div class="flex flex-col gap-3 mb-4">
                <div class="relative">
                  <Search class="absolute left-3 top-3 text-gray-400" size={18} />
                  <input
                    type="text"
                    placeholder="Buscar por nome ou código..."
                    class="w-full pl-10 pr-4 py-2 rounded-lg border bg-slate-50 focus:bg-white focus:ring-2 focus:ring-primary/20 transition-all outline-none"
                    value={searchQuery()}
                    onInput={(e) => setSearchQuery(e.currentTarget.value)}
                    onKeyDown={(e) => e.key === 'Enter' && searchProducts()}
                  />
                </div>
                <div class="flex gap-2">
                  <select class="input text-xs flex-1" value={searchSegmento()} onChange={e => setSearchSegmento(e.currentTarget.value)}>
                    <option value="">Todos Segmentos</option>
                    <For each={availableSegmentos()}>{s => <option value={s}>{s}</option>}</For>
                  </select>
                  <button onClick={searchProducts} class="btn btn-outline p-2" title="Atualizar"><Filter size={16} /></button>
                </div>
              </div>

              {/* Product List */}
              <div class="flex-1 overflow-y-auto pr-2 space-y-2">
                <For each={products()} fallback={<div class="text-center p-10 text-muted">Nenhum produto encontrado.</div>}>
                  {product => (
                    <div
                      class={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-sm ${selectedProducts().some(p => p.produto_id === product.produto_id) ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : 'bg-white border-slate-100 hover:border-slate-300'}`}
                      onClick={() => {
                        const exists = selectedProducts().find(p => p.produto_id === product.produto_id);
                        if (exists) setSelectedProducts(selectedProducts().filter(p => p.produto_id !== product.produto_id));
                        else setSelectedProducts([...selectedProducts(), product]);
                      }}
                    >
                      <div class="flex justify-between items-start">
                        <div>
                          <div class="font-medium text-sm text-slate-800 dark:text-slate-200 line-clamp-1">{product.nome}</div>
                          <div class="text-[10px] text-muted-foreground mt-0.5">{product.segmento} • {product.grupo}</div>
                        </div>
                        <div class="text-right">
                          <div class="text-xs font-bold text-slate-600">{product.estoque_loja} un.</div>
                          <div class="text-[10px] text-muted-foreground">Loja</div>
                        </div>
                      </div>
                    </div>
                  )}
                </For>
              </div>

              {/* Add Action */}
              <div class="pt-4 border-t mt-auto flex gap-3 items-end">
                <div class="flex-1">
                  <label class="text-[10px] font-bold uppercase text-muted-foreground mb-1 block">Quantidade</label>
                  <input
                    type="number"
                    class="w-full p-2 border rounded-lg font-mono text-center font-bold"
                    placeholder="0"
                    value={quantidade()}
                    onInput={(e) => setQuantidade(parseInt(e.currentTarget.value) || '')}
                  />
                </div>
                <button
                  class="flex-[2] btn btn-primary h-[42px]"
                  onClick={addToManifest}
                  disabled={validating() || selectedProducts().length === 0}
                >
                  <Plus size={18} class="mr-2" />
                  Adicionar ao Manifesto
                </button>
              </div>
            </div>

            {/* RIGHT: MANIFEST CART */}
            <div class="xl:col-span-7 bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border p-6 flex flex-col h-[600px]">
              <h3 class="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2 text-primary">
                <Truck size={16} /> 3. Manifesto de Carga
                <span class="ml-auto bg-primary/10 text-primary px-2 py-0.5 rounded-full text-xs">
                  {cart.items.length} itens sequenciados
                </span>
              </h3>

              <div class="flex-1 overflow-y-auto bg-slate-50 dark:bg-black/20 rounded-xl border p-4 space-y-4">
                <Show when={cart.items.length === 0}>
                  <div class="h-full flex flex-col items-center justify-center text-muted-foreground opacity-60">
                    <ShoppingCart size={48} strokeWidth={1} />
                    <p class="mt-4 text-sm font-medium">O manifesto está vazio.</p>
                    <p class="text-xs">Configure a rota e adicione produtos.</p>
                  </div>
                </Show>

                {/* Group By Route Logic would go here, simpler flat list with distinct styling for now */}
                <For each={cart.items}>
                  {(item, index) => (
                    <div class="bg-white dark:bg-zinc-800 p-3 rounded-lg shadow-sm border border-slate-100 dark:border-zinc-700 flex items-center gap-4 group">
                      <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-xs">
                        {index() + 1}
                      </div>

                      <div class="flex-1">
                        <div class="flex items-center gap-2 text-xs font-bold text-slate-500 mb-1">
                          <span class="bg-blue-50 text-blue-600 px-1.5 rounded">UNE {item.une_origem}</span>
                          <ArrowRight size={12} />
                          <span class="bg-green-50 text-green-600 px-1.5 rounded">Destinos: {item.une_destino.join(', ')}</span>
                        </div>
                        <div class="font-medium text-sm">{item.produto_nome}</div>
                      </div>

                      <div class="text-right">
                        <div class="text-lg font-bold font-mono">{item.quantidade}</div>
                        <div class="text-[10px] text-muted-foreground uppercase">Unidades</div>
                      </div>

                      <button
                        class="p-2 text-red-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        onClick={() => setCart('items', i => i.filter((_, idx) => idx !== index()))}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </For>
              </div>

              <div class="pt-4 border-t mt-auto flex justify-end">
                <button
                  class="btn btn-primary px-8 h-12 shadow-xl shadow-primary/20"
                  onClick={generateTransferRequest}
                  disabled={creating() || cart.items.length === 0}
                >
                  {creating() ? 'Processando Manifesto...' : 'Confirmar e Enviar Manifesto'}
                </button>
              </div>
            </div>

          </div>
        </div>
      </Show>

      {/* TRACKING TAB CONTENT */}
      <Show when={activeTab() === 'tracking'}>
        <div class="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border p-8 animate-in fade-in slide-in-from-bottom-4">
          <div class="flex items-center justify-between mb-8">
            <div>
              <h3 class="text-xl font-bold flex items-center gap-2">
                <History /> Torre de Controle
              </h3>
              <p class="text-muted-foreground">Monitoramento em tempo real das solicitações.</p>
            </div>
            <div class="flex gap-2 text-sm">
              <span class="flex items-center gap-1.5 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full font-medium">
                <Clock size={14} /> 2 Em Análise
              </span>
              <span class="flex items-center gap-1.5 px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                <Truck size={14} /> 5 Em Trânsito
              </span>
            </div>
          </div>

          <div class="overflow-hidden rounded-xl border">
            <table class="w-full text-sm">
              <thead class="bg-slate-50 dark:bg-zinc-800 text-left">
                <tr>
                  <th class="p-4 font-bold text-muted-foreground">ID</th>
                  <th class="p-4 font-bold text-muted-foreground">Rota</th>
                  <th class="p-4 font-bold text-muted-foreground">Itens</th>
                  <th class="p-4 font-bold text-muted-foreground">Data</th>
                  <th class="p-4 font-bold text-muted-foreground">Status</th>
                  <th class="p-4 font-bold text-muted-foreground text-right">Ação</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <For each={trackingItems}>
                  {(row) => (
                    <tr class="hover:bg-slate-50 transition-colors">
                      <td class="p-4 font-mono font-medium">{row.id}</td>
                      <td class="p-4">
                        <div class="flex items-center gap-2">
                          <span class="bg-slate-100 px-2 rounded text-xs font-bold">{row.origem}</span>
                          <ArrowRight size={12} class="text-muted-foreground" />
                          <span class="bg-slate-100 px-2 rounded text-xs font-bold">{row.destino}</span>
                        </div>
                      </td>
                      <td class="p-4">{row.itensResumo}</td>
                      <td class="p-4 text-muted-foreground">{row.dataLabel}</td>
                      <td class="p-4">
                        <Show
                          when={row.status === 'Aguardando Aprovação'}
                          fallback={
                            <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs font-bold">
                              <Truck size={12} /> {row.status}
                            </span>
                          }
                        >
                          <span class="inline-flex items-center gap-1 px-2 py-1 rounded bg-yellow-100 text-yellow-700 text-xs font-bold">
                            <Clock size={12} /> {row.status}
                          </span>
                        </Show>
                      </td>
                      <td class="p-4 text-right">
                        <button
                          class="text-blue-600 hover:underline font-medium"
                          onClick={() => setSelectedTracking(row)}
                        >
                          Detalhes
                        </button>
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>
        </div>

        <Show when={selectedTracking()}>
          <div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={(e) => e.target === e.currentTarget && setSelectedTracking(null)}>
            <div class="w-full max-w-lg bg-white rounded-xl border shadow-xl p-5">
              <div class="flex items-center justify-between mb-4">
                <h4 class="text-lg font-bold text-slate-800">Detalhes da Solicitação</h4>
                <button class="text-slate-500 hover:text-slate-700" onClick={() => setSelectedTracking(null)}>Fechar</button>
              </div>
              <div class="space-y-2 text-sm text-slate-700">
                <div><span class="font-semibold">ID:</span> {selectedTracking()?.id}</div>
                <div><span class="font-semibold">Origem:</span> {selectedTracking()?.origem}</div>
                <div><span class="font-semibold">Destino:</span> {selectedTracking()?.destino}</div>
                <div><span class="font-semibold">Itens:</span> {selectedTracking()?.itensResumo}</div>
                <div><span class="font-semibold">Data:</span> {selectedTracking()?.dataLabel}</div>
                <div><span class="font-semibold">Status:</span> {selectedTracking()?.status}</div>
              </div>
            </div>
          </div>
        </Show>
      </Show>

    </div>
  );
}
