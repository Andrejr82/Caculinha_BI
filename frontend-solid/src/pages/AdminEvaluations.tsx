import { createSignal, onMount, Show, For } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { FileSearch, Star, ThumbsUp, ThumbsDown, ChevronLeft, ChevronRight, X } from 'lucide-solid';
import api from '@/lib/api';
import auth from '@/store/auth';

// Types
interface Evaluation {
    request_id: string;
    user_id?: string;
    overall_score: number;
    prompt_summary?: string;
    created_at: string;
    has_feedback: boolean;
}

interface EvaluationDetail {
    request_id: string;
    user_id?: string;
    tenant_id?: string;
    prompt?: string;
    response?: string;
    overall_score: number;
    dimension_scores: Record<string, number>;
    reasons: string[];
    latency_ms?: number;
    feedback: Array<{ type: string; comment?: string; timestamp: string }>;
    created_at: string;
}

export default function AdminEvaluations() {
    const navigate = useNavigate();
    const [loading, setLoading] = createSignal(true);
    const [error, setError] = createSignal<string | null>(null);

    const [evaluations, setEvaluations] = createSignal<Evaluation[]>([]);
    const [total, setTotal] = createSignal(0);
    const [offset, setOffset] = createSignal(0);
    const limit = 20;

    const [selectedEval, setSelectedEval] = createSignal<EvaluationDetail | null>(null);
    const [detailLoading, setDetailLoading] = createSignal(false);

    // Filters
    const [minScore, setMinScore] = createSignal<number | null>(null);
    const [maxScore, setMaxScore] = createSignal<number | null>(null);

    onMount(async () => {
        const user = auth.user();
        if (!user || (user.role !== 'admin' && user.username !== 'user@agentbi.com')) {
            navigate('/dashboard', { replace: true });
            return;
        }
        await loadEvaluations();
    });

    const loadEvaluations = async () => {
        setLoading(true);
        setError(null);

        try {
            let url = `/admin/evals?limit=${limit}&offset=${offset()}`;
            if (minScore() !== null) url += `&min_score=${minScore()}`;
            if (maxScore() !== null) url += `&max_score=${maxScore()}`;

            const response = await api.get<{ evaluations: Evaluation[]; total: number }>(url);
            setEvaluations(response.data.evaluations);
            setTotal(response.data.total);
        } catch (err: any) {
            if (err.response?.status === 403) {
                navigate('/dashboard', { replace: true });
                return;
            }
            setError(err.message || 'Erro ao carregar avaliações');
        } finally {
            setLoading(false);
        }
    };

    const loadDetail = async (requestId: string) => {
        setDetailLoading(true);
        try {
            const response = await api.get<EvaluationDetail>(`/admin/evals/${requestId}`);
            setSelectedEval(response.data);
        } catch (err: any) {
            console.error('Error loading detail:', err);
        } finally {
            setDetailLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 70) return 'text-green-400 bg-green-900/30';
        if (score >= 50) return 'text-yellow-400 bg-yellow-900/30';
        return 'text-red-400 bg-red-900/30';
    };

    const nextPage = () => {
        if (offset() + limit < total()) {
            setOffset(offset() + limit);
            loadEvaluations();
        }
    };

    const prevPage = () => {
        if (offset() > 0) {
            setOffset(Math.max(0, offset() - limit));
            loadEvaluations();
        }
    };

    return (
        <div class="min-h-screen bg-gray-950 text-white p-6">
            {/* Header */}
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-4">
                    <button onClick={() => navigate('/admin/dashboard')} class="p-2 hover:bg-gray-800 rounded-lg">
                        <ChevronLeft class="w-6 h-6" />
                    </button>
                    <div class="p-3 bg-gradient-to-r from-amber-600 to-orange-600 rounded-xl">
                        <FileSearch class="w-8 h-8" />
                    </div>
                    <div>
                        <h1 class="text-3xl font-bold">Avaliações de Respostas</h1>
                        <p class="text-gray-400">{total()} avaliações registradas</p>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div class="bg-gray-900 rounded-xl p-4 mb-6 flex gap-4 items-center">
                <span class="text-gray-400">Filtrar por score:</span>
                <select
                    class="bg-gray-800 text-white px-3 py-2 rounded-lg"
                    onChange={(e) => {
                        const val = e.target.value;
                        if (val === 'low') { setMinScore(0); setMaxScore(50); }
                        else if (val === 'mid') { setMinScore(50); setMaxScore(70); }
                        else if (val === 'high') { setMinScore(70); setMaxScore(100); }
                        else { setMinScore(null); setMaxScore(null); }
                        setOffset(0);
                        loadEvaluations();
                    }}
                >
                    <option value="">Todos</option>
                    <option value="low">Baixo (&lt;50)</option>
                    <option value="mid">Médio (50-70)</option>
                    <option value="high">Alto (&gt;70)</option>
                </select>
            </div>

            <Show when={error()}>
                <div class="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
                    <p class="text-red-300">{error()}</p>
                </div>
            </Show>

            <Show when={loading()}>
                <div class="flex items-center justify-center h-64">
                    <div class="animate-spin w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full"></div>
                </div>
            </Show>

            <Show when={!loading()}>
                {/* Evaluations Table */}
                <div class="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-800">
                            <tr>
                                <th class="px-4 py-3 text-left text-gray-400 font-medium">ID</th>
                                <th class="px-4 py-3 text-left text-gray-400 font-medium">Score</th>
                                <th class="px-4 py-3 text-left text-gray-400 font-medium">Prompt</th>
                                <th class="px-4 py-3 text-left text-gray-400 font-medium">Data</th>
                                <th class="px-4 py-3 text-left text-gray-400 font-medium">Feedback</th>
                            </tr>
                        </thead>
                        <tbody>
                            <For each={evaluations()}>
                                {(ev) => (
                                    <tr
                                        class="border-t border-gray-800 hover:bg-gray-800/50 cursor-pointer transition-colors"
                                        onClick={() => loadDetail(ev.request_id)}
                                    >
                                        <td class="px-4 py-3 font-mono text-sm text-gray-400">{ev.request_id.slice(0, 12)}...</td>
                                        <td class="px-4 py-3">
                                            <span class={`px-2 py-1 rounded-full text-sm font-semibold ${getScoreColor(ev.overall_score)}`}>
                                                {ev.overall_score.toFixed(1)}
                                            </span>
                                        </td>
                                        <td class="px-4 py-3 text-gray-300 max-w-xs truncate">{ev.prompt_summary || '-'}</td>
                                        <td class="px-4 py-3 text-gray-400 text-sm">{new Date(ev.created_at).toLocaleString('pt-BR')}</td>
                                        <td class="px-4 py-3">
                                            {ev.has_feedback ? (
                                                <ThumbsUp class="w-4 h-4 text-green-500" />
                                            ) : (
                                                <span class="text-gray-600">-</span>
                                            )}
                                        </td>
                                    </tr>
                                )}
                            </For>
                            <Show when={evaluations().length === 0}>
                                <tr>
                                    <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                                        Nenhuma avaliação encontrada
                                    </td>
                                </tr>
                            </Show>
                        </tbody>
                    </table>

                    {/* Pagination */}
                    <div class="bg-gray-800 px-4 py-3 flex items-center justify-between">
                        <span class="text-gray-400 text-sm">
                            Mostrando {offset() + 1}-{Math.min(offset() + limit, total())} de {total()}
                        </span>
                        <div class="flex gap-2">
                            <button
                                onClick={prevPage}
                                disabled={offset() === 0}
                                class="p-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg"
                            >
                                <ChevronLeft class="w-5 h-5" />
                            </button>
                            <button
                                onClick={nextPage}
                                disabled={offset() + limit >= total()}
                                class="p-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg"
                            >
                                <ChevronRight class="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </Show>

            {/* Detail Modal */}
            <Show when={selectedEval()}>
                <div class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
                    <div class="bg-gray-900 rounded-xl border border-gray-700 max-w-3xl w-full max-h-[80vh] overflow-y-auto">
                        <div class="sticky top-0 bg-gray-900 p-4 border-b border-gray-700 flex justify-between items-center">
                            <h2 class="text-xl font-bold">Detalhes da Avaliação</h2>
                            <button onClick={() => setSelectedEval(null)} class="p-2 hover:bg-gray-800 rounded-lg">
                                <X class="w-5 h-5" />
                            </button>
                        </div>

                        <div class="p-6 space-y-6">
                            {/* Score */}
                            <div class="flex items-center gap-4">
                                <div class={`text-4xl font-bold px-4 py-2 rounded-xl ${getScoreColor(selectedEval()!.overall_score)}`}>
                                    {selectedEval()!.overall_score.toFixed(1)}
                                </div>
                                <div>
                                    <p class="text-gray-400">Score Geral</p>
                                    <p class="text-sm text-gray-500">
                                        {(() => {
                                            const latency = selectedEval()?.latency_ms;
                                            return typeof latency === 'number' ? `${latency.toFixed(0)}ms` : '-';
                                        })()}
                                    </p>
                                </div>
                            </div>

                            {/* Dimension Scores */}
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <For each={Object.entries(selectedEval()!.dimension_scores || {})}>
                                    {([dim, score]) => (
                                        <div class="bg-gray-800 rounded-lg p-3">
                                            <p class="text-gray-400 text-sm capitalize">{dim}</p>
                                            <p class={`text-xl font-bold ${getScoreColor(score as number)}`}>{(score as number).toFixed(0)}</p>
                                        </div>
                                    )}
                                </For>
                            </div>

                            {/* Reasons */}
                            <Show when={selectedEval()!.reasons?.length}>
                                <div>
                                    <h3 class="text-lg font-semibold mb-2">Motivos</h3>
                                    <ul class="list-disc list-inside text-gray-300 space-y-1">
                                        <For each={selectedEval()!.reasons}>
                                            {(reason) => <li>{reason}</li>}
                                        </For>
                                    </ul>
                                </div>
                            </Show>

                            {/* Prompt */}
                            <div>
                                <h3 class="text-lg font-semibold mb-2">Prompt</h3>
                                <p class="bg-gray-800 rounded-lg p-4 text-gray-300 whitespace-pre-wrap">
                                    {selectedEval()!.prompt || '-'}
                                </p>
                            </div>

                            {/* Response */}
                            <div>
                                <h3 class="text-lg font-semibold mb-2">Resposta</h3>
                                <p class="bg-gray-800 rounded-lg p-4 text-gray-300 whitespace-pre-wrap max-h-64 overflow-y-auto">
                                    {selectedEval()!.response || '-'}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </Show>
        </div>
    );
}
