import { createSignal, onMount, Show, For, createEffect } from "solid-js";
import { PlotlyChart } from "../components/PlotlyChart";
import type { Component } from "solid-js";

interface SegmentMetrics {
    nome: string;
    lead_time_medio: number;
    taxa_ruptura: number;
    custo_medio: number;
    produtos_fornecidos: number;
    ultima_entrega: string;
}

interface GroupMetrics {
    grupo: string;
    segmento: string;
    taxa_ruptura: number;
    custo_medio: number;
    produtos: number;
    estoque_total: number;
    vendas_30d: number;
}

const Suppliers: Component = () => {
    // Dados principais
    const [segments, setSegments] = createSignal<SegmentMetrics[]>([]);
    const [groups, setGroups] = createSignal<GroupMetrics[]>([]);

    // Estados de UI
    const [loading, setLoading] = createSignal(true);
    const [loadingGroups, setLoadingGroups] = createSignal(false);
    const [activeTab, setActiveTab] = createSignal<"segments" | "groups">("segments");

    // Filtros
    const [segmentOptions, setSegmentOptions] = createSignal<string[]>([]);
    const [selectedSegment, setSelectedSegment] = createSignal<string>("");

    // Ordenação
    const [sortBy, setSortBy] = createSignal<string>("taxa_ruptura");
    const [sortOrder, setSortOrder] = createSignal<"asc" | "desc">("desc");

    // Charts
    const [treemapSpec, setTreemapSpec] = createSignal<any>({});

    onMount(async () => {
        await loadSegments();
        await loadSegmentOptions();
    });

    // Carregar quando segmento selecionado mudar
    createEffect(() => {
        const seg = selectedSegment();
        if (seg && activeTab() === "groups") {
            loadGroups(seg);
        }
    });

    const generateTreemap = (data: SegmentMetrics[]) => {
        if (!data || data.length === 0) return;

        const labels = data.map(s => s.nome);
        const parents = data.map(() => "Todas as Categorias");
        const values = data.map(s => s.produtos_fornecidos); // Tamanho = Volume de produtos
        const colors = data.map(s => s.taxa_ruptura); // Cor = Risco
        const customdata = data.map(s => [s.custo_medio]);

        // Adicionar nó raiz
        labels.push("Todas as Categorias");
        parents.push("");
        values.push(0);
        colors.push(0);
        customdata.push([0]);

        setTreemapSpec({
            data: [{
                type: "treemap",
                labels: labels,
                parents: parents,
                values: values,
                marker: {
                    colors: colors,
                    colorscale: [
                        [0, "#10B981"], // Green-500 (Baixo risco)
                        [0.2, "#34D399"],
                        [0.4, "#FBBF24"], // Yellow-400
                        [0.6, "#FB923C"], // Orange-400
                        [1, "#EF4444"]    // Red-500 (Crítico)
                    ],
                    showscale: true,
                    colorbar: { title: "Ruptura %", len: 0.8 }
                },
                textinfo: "label+value+percent parent",
                hovertemplate: "<b>%{label}</b><br>Produtos: %{value}<br>Ruptura: %{color:.1f}%<br>Custo Médio: R$ %{customdata[0]:.2f}<extra></extra>",
                customdata: customdata
            }],
            layout: {
                title: {
                    text: "<b>Mapa de Calor de Risco (Treemap)</b><br><span style='font-size:12px;color:gray'>Tamanho = Qtd Produtos | Cor = Taxa de Ruptura (Vermelho = Crítico)</span>",
                    font: { size: 16, color: '#1F2937' }
                },
                margin: { l: 20, r: 20, t: 60, b: 20 },
                height: 450,
                paper_bgcolor: "white"
            },
            config: { responsive: true }
        });
    };

    const loadSegments = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/v1/dashboard/suppliers/metrics");
            const data = await response.json();
            const segs = data.suppliers || [];
            setSegments(segs);
            generateTreemap(segs);
        } catch (err) {
            console.error("Erro ao carregar segmentos:", err);
        } finally {
            setLoading(false);
        }
    };

    const loadSegmentOptions = async () => {
        try {
            const response = await fetch("/api/v1/dashboard/metadata/segments");
            if (response.ok) {
                const data = await response.json();
                setSegmentOptions(data || []);
            }
        } catch (err) {
            console.error("Erro ao carregar opções de segmentos:", err);
        }
    };

    const loadGroups = async (segmento: string) => {
        if (!segmento) return;
        setLoadingGroups(true);
        try {
            const response = await fetch(`/api/v1/dashboard/suppliers/groups?segmento=${encodeURIComponent(segmento)}`);
            if (response.ok) {
                const data = await response.json();
                setGroups(data.groups || []);
            }
        } catch (err) {
            console.error("Erro ao carregar grupos:", err);
            setGroups([]);
        } finally {
            setLoadingGroups(false);
        }
    };

    const sortedSegments = () => {
        const sorted = [...segments()];
        sorted.sort((a, b) => {
            const aVal = a[sortBy() as keyof SegmentMetrics];
            const bVal = b[sortBy() as keyof SegmentMetrics];
            const multiplier = sortOrder() === "asc" ? 1 : -1;
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return (aVal - bVal) * multiplier;
            }
            return String(aVal).localeCompare(String(bVal)) * multiplier;
        });
        return sorted;
    };

    const sortedGroups = () => {
        const sorted = [...groups()];
        sorted.sort((a, b) => {
            const aVal = a[sortBy() as keyof GroupMetrics];
            const bVal = b[sortBy() as keyof GroupMetrics];
            const multiplier = sortOrder() === "asc" ? 1 : -1;
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return (aVal - bVal) * multiplier;
            }
            return String(aVal).localeCompare(String(bVal)) * multiplier;
        });
        return sorted;
    };

    const handleSort = (column: string) => {
        if (sortBy() === column) {
            setSortOrder(sortOrder() === "asc" ? "desc" : "asc");
        } else {
            setSortBy(column);
            setSortOrder("desc");
        }
    };

    const handleSegmentClick = (segmentName: string) => {
        setSelectedSegment(segmentName.trim());
        setActiveTab("groups");
    };

    const handleExport = (segmento: string, grupo: string | null) => {
        const url = `/api/v1/dashboard/suppliers/export_ruptures?segmento=${encodeURIComponent(segmento)}${grupo ? `&grupo=${encodeURIComponent(grupo)}` : ''}`;
        window.open(url, '_blank');
    };

    const getRupturaColor = (taxa: number) => {
        if (taxa > 40) return "text-red-600 font-bold";
        if (taxa > 25) return "text-orange-500 font-semibold";
        if (taxa > 15) return "text-yellow-600";
        return "text-green-600";
    };

    const getRupturaBackground = (taxa: number) => {
        if (taxa > 40) return "bg-red-50";
        if (taxa > 25) return "bg-orange-50";
        if (taxa > 15) return "bg-yellow-50";
        return "bg-green-50";
    };

    return (
        <div class="max-w-7xl mx-auto flex flex-col gap-6">
            {/* Cabeçalho */}
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">Torre de Controle de Suprimentos</h1>
                    <p class="text-gray-500 mt-1">Monitoramento estratégico de risco de ruptura e performance de categorias em tempo real</p>
                </div>
                <button
                    onClick={loadSegments}
                    class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Atualizar
                </button>
            </div>

            {/* Tabs */}
            <div class="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
                <button
                    onClick={() => setActiveTab("segments")}
                    class={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab() === "segments"
                        ? "bg-white text-blue-600 shadow-sm"
                        : "text-gray-600 hover:text-gray-800"
                        }`}
                >
                    Por Segmento
                </button>
                <button
                    onClick={() => setActiveTab("groups")}
                    class={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab() === "groups"
                        ? "bg-white text-blue-600 shadow-sm"
                        : "text-gray-600 hover:text-gray-800"
                        }`}
                >
                    Por Grupo
                </button>
            </div>

            {/* Filtro de Segmento (para aba de Grupos) */}
            <Show when={activeTab() === "groups"}>
                <div class="bg-white rounded-lg shadow p-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Selecione um Segmento para ver os Grupos
                    </label>
                    <select
                        value={selectedSegment()}
                        onChange={(e) => setSelectedSegment(e.currentTarget.value)}
                        class="w-full md:w-80 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="">-- Escolha um Segmento --</option>
                        <For each={segmentOptions()}>
                            {(seg) => <option value={seg}>{seg}</option>}
                        </For>
                    </select>
                </div>
            </Show>

            <Show when={loading()}>
                <div class="text-center py-12">
                    <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    <p class="mt-4 text-gray-600">Carregando dados...</p>
                </div>
            </Show>

            {/* Tab: Segmentos */}
            <Show when={!loading() && activeTab() === "segments"}>
                {/* Visualização de Risco (Treemap) */}
                <div class="bg-white rounded-lg shadow p-6 border border-gray-100">
                    <PlotlyChart chartSpec={treemapSpec} height="400px" />
                </div>

                {/* Métricas Resumidas */}
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="text-xs font-bold text-gray-400 uppercase tracking-wide">Segmentos Ativos</div>
                                <div class="text-3xl font-bold text-gray-800 mt-1">{segments().length}</div>
                            </div>
                            <span class="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded font-medium">+2 novos</span>
                        </div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="text-xs font-bold text-gray-400 uppercase tracking-wide">Ruptura Média</div>
                                <div class="text-3xl font-bold text-orange-600 mt-1">
                                    {(segments().reduce((acc, s) => acc + s.taxa_ruptura, 0) / segments().length || 0).toFixed(1)}%
                                </div>
                            </div>
                            <span class="bg-red-50 text-red-600 text-xs px-2 py-1 rounded font-medium flex items-center gap-1">
                                <span>↑</span> 1.2%
                            </span>
                        </div>
                        <div class="w-full bg-gray-100 h-1 mt-3 rounded-full overflow-hidden">
                            <div class="bg-orange-500 h-1" style={`width: ${(segments().reduce((acc, s) => acc + s.taxa_ruptura, 0) / segments().length || 0)}%`}></div>
                        </div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-emerald-500">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="text-xs font-bold text-gray-400 uppercase tracking-wide">Custo Médio</div>
                                <div class="text-3xl font-bold text-gray-800 mt-1">
                                    R$ {(segments().reduce((acc, s) => acc + s.custo_medio, 0) / segments().length || 0).toFixed(0)}
                                </div>
                            </div>
                            <span class="bg-emerald-50 text-emerald-600 text-xs px-2 py-1 rounded font-medium flex items-center gap-1">
                                <span>↓</span> 0.5%
                            </span>
                        </div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-indigo-500">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="text-xs font-bold text-gray-400 uppercase tracking-wide">Total de SKUs</div>
                                <div class="text-3xl font-bold text-indigo-600 mt-1">
                                    {segments().reduce((acc, s) => acc + s.produtos_fornecidos, 0).toLocaleString()}
                                </div>
                            </div>
                            <div class="p-2 bg-indigo-50 rounded text-indigo-600">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabela de Segmentos */}
                <div class="bg-white rounded-lg shadow overflow-hidden border border-gray-200">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th onClick={() => handleSort("nome")} class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors">
                                    Segmento {sortBy() === "nome" && (sortOrder() === "asc" ? "↑" : "↓")}
                                </th>
                                <th onClick={() => handleSort("taxa_ruptura")} class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors w-1/3">
                                    Risco de Ruptura (Estoque Crítico) {sortBy() === "taxa_ruptura" && (sortOrder() === "asc" ? "↑" : "↓")}
                                </th>
                                <th onClick={() => handleSort("custo_medio")} class="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors">
                                    Custo Médio {sortBy() === "custo_medio" && (sortOrder() === "asc" ? "↑" : "↓")}
                                </th>
                                <th onClick={() => handleSort("produtos_fornecidos")} class="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors">
                                    Produtos {sortBy() === "produtos_fornecidos" && (sortOrder() === "asc" ? "↑" : "↓")}
                                </th>
                                <th class="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">
                                    Ações
                                </th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <For each={sortedSegments()}>
                                {(segment) => (
                                    <tr class="hover:bg-blue-50/30 transition-colors group">
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <div class="text-sm font-bold text-gray-700">{segment.nome.trim()}</div>
                                            <div class="text-xs text-gray-400">Última entrega: {segment.ultima_entrega || "N/A"}</div>
                                        </td>
                                        <td class="px-6 py-4 align-middle">
                                            <div class="w-full">
                                                <div class="flex justify-between text-xs mb-1">
                                                    <span class={`font-bold ${getRupturaColor(segment.taxa_ruptura)}`}>
                                                        {segment.taxa_ruptura.toFixed(1)}%
                                                    </span>
                                                    <span class="text-gray-400">Meta: &lt;10%</span>
                                                </div>
                                                <div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                                                    <div
                                                        class={`h-2.5 rounded-full ${segment.taxa_ruptura > 40 ? 'bg-red-500' :
                                                            segment.taxa_ruptura > 25 ? 'bg-orange-400' :
                                                                segment.taxa_ruptura > 15 ? 'bg-yellow-400' : 'bg-emerald-500'
                                                            }`}
                                                        style={`width: ${Math.min(segment.taxa_ruptura, 100)}%`}
                                                    ></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-right">
                                            <div class="text-sm font-mono text-gray-600">R$ {segment.custo_medio.toFixed(2)}</div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-right">
                                            <div class="text-sm font-bold text-gray-800">{segment.produtos_fornecidos.toLocaleString()}</div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-center">
                                            <div class="flex justify-center gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => handleSegmentClick(segment.nome)}
                                                    class="p-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 border border-blue-200"
                                                    title="Detalhar Grupo"
                                                >
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
                                                </button>
                                                <button
                                                    onClick={() => handleExport(segment.nome, null)}
                                                    class="p-2 bg-green-50 text-green-600 rounded hover:bg-green-100 border border-green-200"
                                                    title="Baixar Pedido"
                                                >
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </For>
                        </tbody>
                    </table>
                </div>
            </Show>

            {/* Tab: Grupos */}
            <Show when={!loading() && activeTab() === "groups"}>
                <Show when={!selectedSegment()}>
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
                        <svg class="w-12 h-12 mx-auto text-yellow-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 class="text-lg font-medium text-yellow-800">Selecione um Segmento</h3>
                        <p class="text-yellow-600 mt-1">Escolha um segmento acima para visualizar os grupos de produtos.</p>
                    </div>
                </Show>

                <Show when={selectedSegment() && loadingGroups()}>
                    <div class="text-center py-12">
                        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        <p class="mt-4 text-gray-600">Carregando grupos de {selectedSegment()}...</p>
                    </div>
                </Show>

                <Show when={selectedSegment() && !loadingGroups()}>
                    <div class="mb-4 flex justify-between items-center">
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                            Segmento: {selectedSegment()}
                        </span>

                        <button
                            onClick={() => handleExport(selectedSegment(), null)}
                            class="bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 text-sm font-medium flex items-center gap-2 shadow-sm"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Baixar Rupturas do Segmento Completo
                        </button>
                    </div>

                    <Show when={groups().length === 0}>
                        <div class="bg-gray-50 border rounded-lg p-8 text-center">
                            <p class="text-gray-600">Nenhum grupo encontrado para este segmento.</p>
                            <p class="text-sm text-gray-500 mt-2">O endpoint de grupos pode precisar ser implementado.</p>
                        </div>
                    </Show>

                    <Show when={groups().length > 0}>
                        <div class="bg-white rounded-lg shadow overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-200">
                                <thead class="bg-gray-100 shadow-sm">
                                    <tr>
                                        <th
                                            onClick={() => handleSort("grupo")}
                                            class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 sticky top-0 bg-gray-100 z-10"
                                        >
                                            Grupo {sortBy() === "grupo" && (sortOrder() === "asc" ? "↑" : "↓")}
                                        </th>
                                        <th
                                            onClick={() => handleSort("taxa_ruptura")}
                                            class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100 z-10 w-1/3"
                                        >
                                            Taxa Ruptura {sortBy() === "taxa_ruptura" && (sortOrder() === "asc" ? "↑" : "↓")}
                                        </th>
                                        <th
                                            onClick={() => handleSort("custo_medio")}
                                            class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 sticky top-0 bg-gray-100 z-10"
                                        >
                                            Custo Médio {sortBy() === "custo_medio" && (sortOrder() === "asc" ? "↑" : "↓")}
                                        </th>
                                        <th
                                            onClick={() => handleSort("produtos")}
                                            class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 sticky top-0 bg-gray-100 z-10"
                                        >
                                            Produtos {sortBy() === "produtos" && (sortOrder() === "asc" ? "↑" : "↓")}
                                        </th>
                                        <th
                                            onClick={() => handleSort("vendas_30d")}
                                            class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 sticky top-0 bg-gray-100 z-10"
                                        >
                                            Vendas 30D {sortBy() === "vendas_30d" && (sortOrder() === "asc" ? "↑" : "↓")}
                                        </th>
                                        <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider sticky top-0 bg-gray-100 z-10">
                                            Ações
                                        </th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                                    <For each={sortedGroups()}>

                                        {(group) => (
                                            <tr class={`hover:bg-gray-50 ${getRupturaBackground(group.taxa_ruptura)}`}>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <div class="text-sm font-medium text-gray-900">{group.grupo}</div>
                                                </td>
                                                <td class="px-6 py-4 align-middle">
                                                    <div class="w-full">
                                                        <div class="flex justify-between text-xs mb-1">
                                                            <span class={`font-bold ${getRupturaColor(group.taxa_ruptura)}`}>
                                                                {group.taxa_ruptura.toFixed(1)}%
                                                            </span>
                                                        </div>
                                                        <div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                                                            <div
                                                                class={`h-2.5 rounded-full ${group.taxa_ruptura > 40 ? 'bg-red-500' :
                                                                    group.taxa_ruptura > 25 ? 'bg-orange-400' :
                                                                        group.taxa_ruptura > 15 ? 'bg-yellow-400' : 'bg-emerald-500'
                                                                    }`}
                                                                style={`width: ${Math.min(group.taxa_ruptura, 100)}%`}
                                                            ></div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <div class="text-sm text-gray-900">R$ {group.custo_medio.toFixed(2)}</div>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <div class="text-sm text-gray-900">{group.produtos.toLocaleString()}</div>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <div class="text-sm text-gray-900">{group.vendas_30d?.toLocaleString() || 0}</div>
                                                </td>
                                                <td class="px-6 py-4 whitespace-nowrap">
                                                    <button
                                                        onClick={() => handleExport(group.segmento, group.grupo)}
                                                        class="text-green-600 hover:text-green-800 p-2 rounded-full hover:bg-green-100 transition-colors"
                                                        title={`Baixar rupturas: ${group.grupo}`}
                                                    >
                                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                        </svg>
                                                    </button>
                                                </td>
                                            </tr>
                                        )}
                                    </For>
                                </tbody>
                            </table>
                        </div>
                    </Show>
                </Show>
            </Show>
        </div>
    );
};

export default Suppliers;
