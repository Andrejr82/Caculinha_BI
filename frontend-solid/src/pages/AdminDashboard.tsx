import { createSignal, onMount, Show, For } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { Activity, Clock, AlertTriangle, Users, Zap, TrendingUp, RefreshCw, Shield } from 'lucide-solid';
import api from '@/lib/api';
import auth from '@/store/auth';

// Types
interface HealthData {
    status: string;
    environment: string;
    version: string;
    uptime_seconds: number;
    uptime_formatted: string;
    python_version: string;
}

interface TrafficData {
    total_requests: number;
    requests_per_minute: number;
    error_count: number;
    error_rate: number;
    p50_latency_ms: number;
    p95_latency_ms: number;
    p99_latency_ms: number;
}

interface UsageData {
    active_users_24h: number;
    total_queries_today: number;
    top_endpoints: Array<{ endpoint: string; count: number }>;
    top_users: Array<{ user: string; requests: number }>;
}

interface QualityData {
    total_evaluations: number;
    average_score: number;
    high_score_count: number;
    low_score_count: number;
    low_score_rate: number;
    score_distribution: Record<string, number>;
}

export default function AdminDashboard() {
    const navigate = useNavigate();
    const [loading, setLoading] = createSignal(true);
    const [error, setError] = createSignal<string | null>(null);

    const [health, setHealth] = createSignal<HealthData | null>(null);
    const [traffic, setTraffic] = createSignal<TrafficData | null>(null);
    const [usage, setUsage] = createSignal<UsageData | null>(null);
    const [quality, setQuality] = createSignal<QualityData | null>(null);

    // Check admin access
    onMount(async () => {
        const user = auth.user();
        if (!user || (user.role !== 'admin' && user.username !== 'user@agentbi.com')) {
            navigate('/dashboard', { replace: true });
            return;
        }
        await loadData();
    });

    const loadData = async () => {
        setLoading(true);
        setError(null);

        try {
            const [healthRes, trafficRes, usageRes, qualityRes] = await Promise.all([
                api.get<HealthData>('/admin/dashboard/health'),
                api.get<TrafficData>('/admin/dashboard/traffic'),
                api.get<UsageData>('/admin/dashboard/usage'),
                api.get<QualityData>('/admin/dashboard/quality')
            ]);

            setHealth(healthRes.data);
            setTraffic(trafficRes.data);
            setUsage(usageRes.data);
            setQuality(qualityRes.data);
        } catch (err: any) {
            if (err.response?.status === 403) {
                navigate('/dashboard', { replace: true });
                return;
            }
            setError(err.message || 'Erro ao carregar dados');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div class="min-h-screen bg-gray-950 text-white p-6">
            {/* Header */}
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-4">
                    <div class="p-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl">
                        <Shield class="w-8 h-8" />
                    </div>
                    <div>
                        <h1 class="text-3xl font-bold">Admin Dashboard</h1>
                        <p class="text-gray-400">Monitoramento de plataforma e qualidade</p>
                    </div>
                </div>

                <button
                    onClick={loadData}
                    class="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                >
                    <RefreshCw class={`w-4 h-4 ${loading() ? 'animate-spin' : ''}`} />
                    Atualizar
                </button>
            </div>

            <Show when={error()}>
                <div class="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
                    <p class="text-red-300">{error()}</p>
                </div>
            </Show>

            <Show when={loading()}>
                <div class="flex items-center justify-center h-64">
                    <div class="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full"></div>
                </div>
            </Show>

            <Show when={!loading() && !error()}>
                {/* KPI Cards Row 1 - Platform Health */}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* Status */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Status</span>
                            <Activity class="w-5 h-5 text-green-500" />
                        </div>
                        <p class="text-2xl font-bold text-green-400">{health()?.status?.toUpperCase()}</p>
                        <p class="text-sm text-gray-500 mt-2">{health()?.environment} | v{health()?.version}</p>
                    </div>

                    {/* Uptime */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Uptime</span>
                            <Clock class="w-5 h-5 text-blue-500" />
                        </div>
                        <p class="text-2xl font-bold">{health()?.uptime_formatted}</p>
                        <p class="text-sm text-gray-500 mt-2">Python {health()?.python_version}</p>
                    </div>

                    {/* Requests/min */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Req/min</span>
                            <Zap class="w-5 h-5 text-yellow-500" />
                        </div>
                        <p class="text-2xl font-bold">{traffic()?.requests_per_minute?.toFixed(1)}</p>
                        <p class="text-sm text-gray-500 mt-2">{traffic()?.total_requests?.toLocaleString()} total</p>
                    </div>

                    {/* Error Rate */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Error Rate</span>
                            <AlertTriangle class={`w-5 h-5 ${(traffic()?.error_rate || 0) > 5 ? 'text-red-500' : 'text-green-500'}`} />
                        </div>
                        <p class={`text-2xl font-bold ${(traffic()?.error_rate || 0) > 5 ? 'text-red-400' : 'text-green-400'}`}>
                            {traffic()?.error_rate?.toFixed(2)}%
                        </p>
                        <p class="text-sm text-gray-500 mt-2">{traffic()?.error_count} erros</p>
                    </div>
                </div>

                {/* KPI Cards Row 2 - Performance & Quality */}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* P50 Latency */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">P50 Latência</span>
                        </div>
                        <p class="text-2xl font-bold">{traffic()?.p50_latency_ms?.toFixed(0)} ms</p>
                    </div>

                    {/* P95 Latency */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">P95 Latência</span>
                        </div>
                        <p class="text-2xl font-bold">{traffic()?.p95_latency_ms?.toFixed(0)} ms</p>
                    </div>

                    {/* Avg Score */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Score Médio</span>
                            <TrendingUp class="w-5 h-5 text-purple-500" />
                        </div>
                        <p class="text-2xl font-bold text-purple-400">{quality()?.average_score?.toFixed(1)}</p>
                        <p class="text-sm text-gray-500 mt-2">{quality()?.total_evaluations} avaliações</p>
                    </div>

                    {/* Active Users */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">Usuários Ativos</span>
                            <Users class="w-5 h-5 text-cyan-500" />
                        </div>
                        <p class="text-2xl font-bold text-cyan-400">{usage()?.active_users_24h}</p>
                        <p class="text-sm text-gray-500 mt-2">{usage()?.total_queries_today} consultas hoje</p>
                    </div>
                </div>

                {/* Tables Row */}
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Top Endpoints */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <h3 class="text-lg font-semibold mb-4">Top Endpoints</h3>
                        <div class="space-y-3">
                            <For each={usage()?.top_endpoints?.slice(0, 8)}>
                                {(item) => (
                                    <div class="flex items-center justify-between py-2 border-b border-gray-800">
                                        <span class="text-gray-300 font-mono text-sm truncate max-w-[70%]">{item.endpoint}</span>
                                        <span class="text-purple-400 font-semibold">{item.count}</span>
                                    </div>
                                )}
                            </For>
                            <Show when={!usage()?.top_endpoints?.length}>
                                <p class="text-gray-500 text-center py-4">Sem dados</p>
                            </Show>
                        </div>
                    </div>

                    {/* Score Distribution */}
                    <div class="bg-gray-900 rounded-xl p-6 border border-gray-800">
                        <h3 class="text-lg font-semibold mb-4">Distribuição de Scores</h3>
                        <div class="space-y-4">
                            <For each={Object.entries(quality()?.score_distribution || {})}>
                                {([range, count]) => (
                                    <div>
                                        <div class="flex justify-between mb-1">
                                            <span class="text-gray-400">{range}</span>
                                            <span class="text-white">{count as number}</span>
                                        </div>
                                        <div class="w-full bg-gray-800 rounded-full h-2">
                                            <div
                                                class="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full"
                                                style={{ width: `${Math.min(100, ((count as number) / Math.max(1, quality()?.total_evaluations || 1)) * 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                )}
                            </For>
                            <Show when={!Object.keys(quality()?.score_distribution || {}).length}>
                                <p class="text-gray-500 text-center py-4">Sem avaliações</p>
                            </Show>
                        </div>

                        {/* Link to Evaluations */}
                        <button
                            onClick={() => navigate('/admin/evaluations')}
                            class="mt-4 w-full py-2 bg-purple-600/20 border border-purple-600/50 rounded-lg text-purple-400 hover:bg-purple-600/30 transition-colors"
                        >
                            Ver Avaliações Detalhadas →
                        </button>
                    </div>
                </div>
            </Show>
        </div>
    );
}
