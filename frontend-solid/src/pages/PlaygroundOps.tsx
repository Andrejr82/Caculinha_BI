import { createSignal, For, Show, onMount } from 'solid-js';
import { Send, Terminal } from 'lucide-solid';
import { useNavigate } from '@solidjs/router';
import { playgroundApi } from '../lib/api';

type OperationMode = {
  id: string;
  title: string;
  description: string;
};

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

type OpsAuditItem = {
  id: string;
  timestamp?: string | null;
  approval_id?: string | null;
  operation_mode?: string | null;
  output_type?: string | null;
  approval_status?: string | null;
  status: string;
};

const operationModes: OperationMode[] = [
  {
    id: 'abastecimento',
    title: 'Abastecimento (MC/Linha Verde)',
    description: 'Reposicao por ruptura, cobertura e estoque de seguranca.',
  },
  {
    id: 'mix',
    title: 'Mix de Produtos',
    description: 'Ajuste de sortimento por loja, curva e sazonalidade.',
  },
  {
    id: 'promocao',
    title: 'Promocao/Preco',
    description: 'Giro, margem e recomendacoes de campanha.',
  },
  {
    id: 'devolucao',
    title: 'Devolucao/Transferencia',
    description: 'Transferencias entre UNEs e reducao de excesso.',
  },
  {
    id: 'sazonalidade',
    title: 'Sazonalidade',
    description: 'Planejamento por periodo e comportamento historico.',
  },
  {
    id: 'opcom',
    title: 'OPCOM Rotinas',
    description: 'Execucao operacional com checklist e prazo.',
  },
];

function modeLabel(modeId: string): string {
  return operationModes.find((m) => m.id === modeId)?.title || modeId;
}

function isSqlRequest(text: string): boolean {
  const t = (text || '').toLowerCase();
  return t.includes('sql') || t.includes('query') || t.includes('consulta');
}

export default function PlaygroundOps() {
  const navigate = useNavigate();
  const [accessReady, setAccessReady] = createSignal(false);
  const [selectedMode, setSelectedMode] = createSignal<string>('abastecimento');
  const [input, setInput] = createSignal('');
  const [messages, setMessages] = createSignal<ChatMessage[]>([]);
  const [loading, setLoading] = createSignal(false);
  const [auditTrail, setAuditTrail] = createSignal<OpsAuditItem[]>([]);

  const loadOpsAudit = async () => {
    try {
      const response = await playgroundApi.getOpsAudit(10);
      setAuditTrail(response?.data?.items || []);
    } catch {
      setAuditTrail([]);
    }
  };

  onMount(async () => {
    try {
      const info = await playgroundApi.getInfo();
      if (info?.data?.playground_access_enabled !== true) {
        navigate('/dashboard', { replace: true });
        return;
      }
      setAccessReady(true);
      await loadOpsAudit();
    } catch {
      navigate('/dashboard', { replace: true });
    }
  });

  const handleModeClick = (mode: OperationMode) => {
    setSelectedMode(mode.id);
  };

  const buildSystemInstruction = (userMessage: string): string => {
    if (isSqlRequest(userMessage)) {
      return [
        'Voce e analista BI de varejo.',
        `Modo operacional ativo: ${modeLabel(selectedMode())}.`,
        'O usuario pediu SQL.',
        'Responda somente com SQL Server valido, em bloco ```sql```.',
        'Nao inclua Resumo, Tabela, Ação recomendada, checklist ou texto extra.',
        'Use nomes de tabelas/colunas plausiveis para BI de varejo e filtros por UNE quando aplicavel.',
      ].join('\n');
    }
    return [
      'Voce e analista de BI e OPCOM da Lojas Cacula.',
      `Modo operacional ativo: ${modeLabel(selectedMode())}.`,
      'Responda em 4 blocos: Resumo executivo, Tabela operacional, SQL/Python pronto, Acao operacional.',
      'Se o usuario pedir SQL ou Python explicitamente, entregue o codigo solicitado.',
      'Use linguagem objetiva e aplicada ao contexto de loja e UNE.',
    ].join('\n');
  };

  const sendMessage = async () => {
    const content = input().trim();
    if (!content || loading()) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    const newHistory = [...messages(), userMsg];
    setMessages(newHistory);
    setInput('');
    setLoading(true);

    try {
      const response = await playgroundApi.chat({
        message: content,
        history: newHistory
          .slice(0, -1)
          .map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp })),
        system_instruction: buildSystemInstruction(content),
        temperature: 0.4,
        max_tokens: 2048,
        json_mode: false,
        stream: false,
      });

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: String(response?.data?.response || '').trim() || 'Sem resposta retornada.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || 'Falha na chamada do Playground.';
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Erro: ${detail}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Show when={accessReady()} fallback={<div class="p-6 text-sm text-slate-500">Validando permissao de acesso...</div>}>
      <div class="max-w-7xl mx-auto w-full space-y-6">
        <section class="rounded-xl border bg-white p-6 shadow-sm">
          <h1 class="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Terminal class="text-emerald-600" size={22} />
            Playground BI Operacional
          </h1>
          <p class="text-sm text-slate-600 mt-1">
            Interacao por texto com contexto guiado por rotina BI/OPCOM.
          </p>
        </section>

        <section class="rounded-xl border bg-white p-6 shadow-sm">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">Modos de operacao</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            <For each={operationModes}>
              {(mode) => (
                <button
                  type="button"
                  onClick={() => handleModeClick(mode)}
                  class={`text-left rounded-lg border p-4 transition-colors ${
                    selectedMode() === mode.id
                      ? 'border-emerald-700 bg-emerald-100 shadow-sm'
                      : 'border-slate-300 bg-white hover:border-emerald-500 hover:bg-emerald-50'
                  }`}
                >
                  <div class="font-semibold text-slate-900">{mode.title}</div>
                  <div class="text-sm text-slate-700 mt-1">{mode.description}</div>
                </button>
              )}
            </For>
          </div>
          <p class="text-sm text-slate-600 mt-3">
            Modo selecionado: <strong>{modeLabel(selectedMode())}</strong>
          </p>
        </section>

        <section class="rounded-xl border bg-white p-6 shadow-sm">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">Conversa</h2>
          <div class="space-y-3 max-h-[420px] overflow-y-auto border border-slate-200 rounded-lg p-3 bg-slate-50">
            <Show when={messages().length > 0} fallback={<p class="text-sm text-slate-500">Nenhuma mensagem ainda.</p>}>
              <For each={messages()}>
                {(m) => (
                  <div class={`rounded-lg p-3 text-sm ${m.role === 'user' ? 'bg-emerald-100 text-slate-900' : 'bg-white border border-slate-200 text-slate-800'}`}>
                    <div class="text-[11px] font-semibold uppercase mb-1">{m.role === 'user' ? 'Voce' : 'Playground'}</div>
                    <pre class="whitespace-pre-wrap font-sans">{m.content}</pre>
                  </div>
                )}
              </For>
            </Show>
          </div>
          <div class="mt-3 flex gap-2">
            <textarea
              class="input w-full min-h-[90px]"
              value={input()}
              onInput={(e) => setInput(e.currentTarget.value)}
              placeholder={`Digite sua solicitacao para ${modeLabel(selectedMode())} (ex.: crie SQL de margem por categoria e outliers por UNE).`}
            />
            <button class="btn btn-primary self-end" disabled={loading() || !input().trim()} onClick={sendMessage}>
              <Send size={16} />
            </button>
          </div>
        </section>

        <section class="rounded-xl border bg-white p-6 shadow-sm">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-3">Trilha de auditoria operacional</h2>
          <Show when={auditTrail().length > 0} fallback={<p class="text-sm text-slate-500">Sem solicitacoes registradas nesta conta.</p>}>
            <div class="space-y-2">
              <For each={auditTrail()}>
                {(item) => (
                  <div class="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                    <div><strong>Protocolo:</strong> {item.approval_id || '-'}</div>
                    <div><strong>Modo:</strong> {item.operation_mode || '-'} | <strong>Saida:</strong> {(item.output_type || '-').toUpperCase()}</div>
                    <div><strong>Status:</strong> {item.approval_status || item.status}</div>
                    <div><strong>Quando:</strong> {item.timestamp || '-'}</div>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </section>
      </div>
    </Show>
  );
}
