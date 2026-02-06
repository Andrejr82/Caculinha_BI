import { createSignal, onMount, Show, For, createResource } from "solid-js";
import type { Component } from "solid-js";

// --- Interfaces ---

interface KPI {
    label: string;
    value: string;
    change: number;
    trend: "up" | "down" | "neutral";
}

interface Alert {
    type: "critical" | "warning" | "info";
    message: string;
    timestamp: string;
}

interface ProductData {
    produto: string;
    descricao: string;
    vendas: number;
    faturamento?: number;
    margem?: number;
    margem_reais?: number;
    estoque: number;
    une?: number; // New
    loja?: string; // New
}

// --- Fetchers ---

const fetchTopSales = async () => {
    const res = await fetch("/api/v1/dashboard/top-vendidos");
    return (await res.json()).produtos as ProductData[];
};

const fetchTopMargin = async () => {
    const res = await fetch("/api/v1/dashboard/top-margin");
    return (await res.json()).produtos as ProductData[];
};

// --- Components ---

const TrafficLight = (props: { current: number, max?: number }) => {
    // Lógica simples de estoque: 0 = vermelho, < 10 = amarelo, >= 10 = verde
    const color = () => {
        if (props.current <= 0) return "bg-red-500";
        if (props.current < 10) return "bg-yellow-500";
        return "bg-green-500";
    };

    return (
        <div class="flex items-center gap-2" title={`Estoque: ${props.current}`}>
            <div class={`w-3 h-3 rounded-full ${color()}`}></div>
            <span class="text-xs text-gray-500 tabular-nums">{props.current} un</span>
        </div>
    );
};

const ProductResultTable = (props: {
    data: ProductData[],
    type: "sales" | "margin",
    loading: boolean
}) => {
    return (
        <div class="overflow-hidden border border-gray-100 rounded-lg">
            <table class="w-full text-sm text-left text-gray-600">
                <thead class="text-xs text-gray-700 uppercase bg-gray-50 border-b border-gray-100">
                    <tr>
                        <th class="px-4 py-3 font-semibold w-16">Loja</th>
                        <th class="px-4 py-3 font-semibold w-16">Cód</th>
                        <th class="px-4 py-3 font-semibold">Produto</th>
                        <th class="px-4 py-3 font-semibold text-right">
                            {props.type === 'sales' ? 'Vendas (30d)' : 'Margem %'}
                        </th>
                        <th class="px-4 py-3 font-semibold text-right w-24">Estoque</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                    <Show when={!props.loading} fallback={
                        <tr>
                            <td colspan="5" class="px-4 py-8 text-center text-gray-400">
                                Carregando dados...
                            </td>
                        </tr>
                    }>
                        <For each={props.data}>
                            {(item) => (
                                <tr class="hover:bg-gray-50 transition-colors">
                                    <td class="px-4 py-2 text-xs font-bold text-gray-700">
                                        {item.loja || item.une || '-'}
                                    </td>
                                    <td class="px-4 py-2 font-mono text-xs text-gray-400">
                                        {item.produto}
                                    </td>
                                    <td class="px-4 py-2">
                                        <div class="font-medium text-gray-900 truncate max-w-[200px]" title={item.descricao}>
                                            {item.descricao}
                                        </div>
                                        {/* Micro-sparkline bar placeholder */}
                                        <div class="w-full bg-gray-100 h-1 mt-1 rounded-full overflow-hidden">
                                            <div
                                                class={`h-full ${props.type === 'sales' ? 'bg-blue-500' : 'bg-emerald-500'}`}
                                                style={{ width: `${Math.min(100, (props.type === 'sales' ? item.vendas / 3 : item.margem || 0))}%` }}
                                            ></div>
                                        </div>
                                    </td>
                                    <td class="px-4 py-2 text-right font-mono font-medium">
                                        {props.type === 'sales'
                                            ? item.vendas.toLocaleString('pt-BR')
                                            : `${(item.margem || 0).toFixed(1)}%`
                                        }
                                        <div class="text-[10px] text-gray-400">
                                            {props.type === 'sales'
                                                ? `R$ ${(item.faturamento || 0).toLocaleString('pt-BR', { notation: 'compact' })}`
                                                : `R$ ${(item.margem_reais || 0).toFixed(2)}`
                                            }
                                        </div>
                                    </td>
                                    <td class="px-4 py-2 text-right">
                                        <div class="flex justify-end">
                                            <TrafficLight current={item.estoque} />
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </For>
                    </Show>
                </tbody>
            </table>
        </div>
    );
};

// --- Main Page ---

const Executive: Component = () => {
    const [kpis, setKPIs] = createSignal<KPI[]>([]);
    const [alerts, setAlerts] = createSignal<Alert[]>([]);
    const [loading, setLoading] = createSignal(true);

    const [topSales] = createResource(fetchTopSales);
    const [topMargin] = createResource(fetchTopMargin);

    onMount(async () => {
        await loadDashboardData();
    });

    const loadDashboardData = async () => {
        setLoading(true);
        try {
            const kpisResponse = await fetch("/api/v1/dashboard/metrics/executive-kpis");
            const kpisData = await kpisResponse.json();

            setKPIs([
                {
                    label: "Vendas Totais (30d)",
                    value: `R$ ${(kpisData.vendas_total || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`,
                    change: kpisData.vendas_variacao || 0,
                    trend: kpisData.vendas_variacao > 0 ? "up" : "down"
                },
                {
                    label: "Margem Média",
                    value: `${(kpisData.margem_media || 0).toFixed(1)}%`,
                    change: kpisData.margem_variacao || 0,
                    trend: kpisData.margem_variacao > 0 ? "up" : "down"
                },
                {
                    label: "Taxa de Ruptura",
                    value: `${(kpisData.taxa_ruptura || 0).toFixed(1)}%`,
                    change: kpisData.ruptura_variacao || 0,
                    trend: kpisData.ruptura_variacao < 0 ? "up" : "down"
                },
                {
                    label: "Produtos Ativos",
                    value: (kpisData.produtos_ativos || 0).toLocaleString('pt-BR'),
                    change: kpisData.produtos_variacao || 0,
                    trend: kpisData.produtos_variacao > 0 ? "up" : "down"
                }
            ]);

            const alertsResponse = await fetch("/api/v1/dashboard/alerts/critical");
            const alertsData = await alertsResponse.json();
            setAlerts(alertsData.alerts || []);

        } catch (err) {
            console.error("Erro ao carregar dashboard:", err);
        } finally {
            setLoading(false);
        }
    };

    const getTrendIcon = (trend: string) => {
        if (trend === "up") return "↗";
        if (trend === "down") return "↘";
        return "→";
    };

    const getTrendColor = (trend: string) => {
        if (trend === "up") return "text-emerald-600";
        if (trend === "down") return "text-rose-600";
        return "text-slate-600";
    };

    const getAlertColor = (type: string) => {
        if (type === "critical") return "bg-rose-50 border-rose-200 text-rose-800 shadow-sm";
        if (type === "warning") return "bg-amber-50 border-amber-200 text-amber-800 shadow-sm";
        return "bg-slate-50 border-slate-200 text-slate-700";
    };

    return (
        <div class="min-h-screen bg-gray-50/50 p-6 md:p-8">
            <div class="max-w-[1600px] mx-auto space-y-8">
                {/* Header */}
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Centro de Comando</h1>
                        <p class="text-sm text-gray-500 mt-1">Visão estratégica de compras e estoque</p>
                    </div>
                    <button
                        onClick={loadDashboardData}
                        class="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:bg-slate-800 focus:ring-4 focus:ring-slate-300 transition-all shadow-sm"
                    >
                        Atualizar Dados
                    </button>
                </div>

                <Show when={loading()}>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 animate-pulse">
                        <For each={[1, 2, 3, 4]}>{() => (
                            <div class="h-32 bg-gray-200 rounded-xl"></div>
                        )}</For>
                    </div>
                </Show>

                <Show when={!loading()}>
                    {/* Master KPIs */}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <For each={kpis()}>
                            {(kpi) => (
                                <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 transition-shadow hover:shadow-md">
                                    <div class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">{kpi.label}</div>
                                    <div class="flex items-baseline gap-2">
                                        <div class="text-3xl font-bold text-gray-900 tracking-tight">{kpi.value}</div>
                                    </div>
                                    <div class={`flex items-center mt-3 text-xs font-medium ${getTrendColor(kpi.trend)}`}>
                                        <span class="mr-1 text-base">{getTrendIcon(kpi.trend)}</span>
                                        <span>{Math.abs(kpi.change).toFixed(1)}% vs anterior</span>
                                    </div>
                                </div>
                            )}
                        </For>
                    </div>

                    {/* Main Content Grid: Asymmetric Layout (Alerts Left, Data Right) */}
                    <div class="grid grid-cols-1 xl:grid-cols-12 gap-8">

                        {/* LEFT COLUMN: Critical Alerts & Context (4 cols) */}
                        <div class="xl:col-span-4 space-y-6">
                            <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                                <div class="px-6 py-4 border-b border-gray-50 bg-gray-50/50 flex justify-between items-center">
                                    <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wide">
                                        🚨 Radares de Risco
                                    </h2>
                                    <span class="bg-rose-100 text-rose-700 text-xs px-2 py-0.5 rounded-full font-bold">
                                        {alerts().length}
                                    </span>
                                </div>
                                <div class="p-4 space-y-3">
                                    <Show
                                        when={alerts().length > 0}
                                        fallback={
                                            <div class="text-center py-12 text-gray-400 text-sm">
                                                ✅ Operação estável. Nenhum alerta crítico.
                                            </div>
                                        }
                                    >
                                        <For each={alerts()}>
                                            {(alert) => (
                                                <div class={`p-3 rounded-lg border-l-4 ${getAlertColor(alert.type)}`}>
                                                    <div class="flex gap-3">
                                                        <div class="flex-1">
                                                            <div class="font-bold text-xs mb-1 uppercase opacity-90">
                                                                {alert.type === "critical" ? "Ruptura Crítica" : "Atenção"}
                                                            </div>
                                                            <div class="text-sm font-medium leading-relaxed">
                                                                {alert.message}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="mt-2 text-[10px] uppercase tracking-wide opacity-60 text-right">
                                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                                    </div>
                                                </div>
                                            )}
                                        </For>
                                    </Show>
                                </div>
                            </div>

                            {/* Insight Box (Static for now, could be AI driven) */}
                            <div class="bg-indigo-900 rounded-xl shadow-sm p-6 text-white overflow-hidden relative">
                                <div class="relative z-10">
                                    <h3 class="text-sm font-bold text-indigo-200 uppercase mb-2">⚡ Pro-Tip</h3>
                                    <p class="text-sm leading-relaxed text-indigo-100">
                                        A taxa de ruptura aumentou 1.2% esta semana. Verifique os fornecedores dos produtos na lista de "Top Vendidos" para garantir reposição rápida.
                                    </p>
                                </div>
                                <div class="absolute -bottom-10 -right-10 w-32 h-32 bg-indigo-700 rounded-full opacity-50 blur-3xl"></div>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: High Density Tables (8 cols) */}
                        <div class="xl:col-span-8 space-y-8">

                            {/* Top Sales */}
                            <div>
                                <div class="flex items-center justify-between mb-4">
                                    <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                                        <span class="w-1.5 h-6 bg-blue-500 rounded-full"></span>
                                        Curva A (Volume)
                                    </h2>
                                    <span class="text-xs font-mono text-gray-400">TOP 10 SKUS</span>
                                </div>
                                <ProductResultTable
                                    data={topSales() || []}
                                    type="sales"
                                    loading={topSales.loading}
                                />
                            </div>

                            {/* Top Margin */}
                            <div>
                                <div class="flex items-center justify-between mb-4">
                                    <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                                        <span class="w-1.5 h-6 bg-emerald-500 rounded-full"></span>
                                        Campeões de Lucro
                                    </h2>
                                    <span class="text-xs font-mono text-gray-400">TOP MARGEM %</span>
                                </div>
                                <ProductResultTable
                                    data={topMargin() || []}
                                    type="margin"
                                    loading={topMargin.loading}
                                />
                            </div>

                        </div>
                    </div>
                </Show>
            </div>
        </div>
    );
};

export default Executive;
