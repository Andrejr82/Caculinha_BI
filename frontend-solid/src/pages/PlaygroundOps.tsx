import { createEffect, createMemo, createSignal, For, Show, onMount } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import {
  ArrowUpRight,
  CheckCheck,
  Clock,
  FileText,
  Mail,
  MessageSquare,
  RefreshCcw,
  Send,
  ShieldCheck,
  Sparkles,
  TableProperties,
  Terminal,
} from 'lucide-solid';

import { playgroundApi } from '../lib/api';
import { announcer } from '../components/ScreenReaderAnnouncer';
import { toastManager } from '../components/Toast';
import {
  buildGuidedChatPayload,
  createPlaygroundSessionId,
  extractGuidedChatResolution,
  operationModes,
  type OperationMode,
} from './playground-ops-guided';
import { renderChatMarkdown } from '@/lib/chatMarkdown';
import 'github-markdown-css/github-markdown.css';
import './chat-markdown.css';
import './playground-surfaces.css';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  request_id?: string;
  source?: string;
  intent?: string;
  approval_id?: string;
  approval_status?: string;
  feedback_status?: 'useful' | 'not_useful';
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

type ApprovalDraft = {
  messageId: string;
  requestText: string;
  generatedOutput: string;
};

const approvalOutputOptions = [
  {
    id: 'operational_report',
    label: 'Relatório operacional',
    hint: 'Resumo executivo ou plano de ação estruturado.',
    icon: FileText,
  },
  {
    id: 'sql',
    label: 'Consulta SQL',
    hint: 'Envio para validação técnica ou liberação controlada.',
    icon: Terminal,
  },
  {
    id: 'spreadsheet_report',
    label: 'Planilha',
    hint: 'Base para preenchimento ou revisão manual.',
    icon: TableProperties,
  },
  {
    id: 'export_csv',
    label: 'Exportação CSV',
    hint: 'Artefato para downstream ou distribuição.',
    icon: TableProperties,
  },
  {
    id: 'email_draft',
    label: 'Rascunho de e-mail',
    hint: 'Texto para revisão antes de qualquer envio.',
    icon: Mail,
  },
  {
    id: 'message_draft',
    label: 'Rascunho de mensagem',
    hint: 'Comunicado curto para canal operacional.',
    icon: MessageSquare,
  },
];

const PLAYGROUND_OPS_STORAGE_KEY = 'playground_ops_state_v2';
const MAX_PERSISTED_OPS_MESSAGES = 14;

function loadPersistedOpsState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(PLAYGROUND_OPS_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return parsed as {
      selectedMode?: string;
      input?: string;
      messages?: ChatMessage[];
      sessionId?: string;
      selectedOutputType?: string;
      deliveryTarget?: string;
      approvalPriority?: string;
      approvalNotes?: string;
    };
  } catch {
    return null;
  }
}

function modeLabel(modeId: string): string {
  return operationModes.find((mode) => mode.id === modeId)?.title || modeId;
}

function isSqlRequest(text: string): boolean {
  const normalized = (text || '').toLowerCase();
  return normalized.includes('sql') || normalized.includes('query') || normalized.includes('consulta');
}

function formatTime(timestamp?: string | null): string {
  if (!timestamp) return '--:--';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '--:--';
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function approvalStatusLabel(status?: string | null): string {
  switch ((status || '').toLowerCase()) {
    case 'pending':
    case 'pending_user_approval':
      return 'Aguardando aprovacao';
    case 'approved':
      return 'Aprovado';
    case 'rejected':
      return 'Rejeitado';
    case 'completed':
      return 'Concluido';
    case 'failed':
      return 'Falhou';
    default:
      return 'Sem protocolo';
  }
}

function approvalStatusTone(status?: string | null): string {
  switch ((status || '').toLowerCase()) {
    case 'pending':
    case 'pending_user_approval':
      return 'is-pending';
    case 'approved':
    case 'completed':
      return 'is-success';
    case 'failed':
    case 'rejected':
      return 'is-error';
    default:
      return 'is-neutral';
  }
}

function inferOutputType(requestText: string, generatedOutput: string): string {
  const combined = `${requestText}\n${generatedOutput}`.toLowerCase();
  if (combined.includes('```sql') || isSqlRequest(combined)) return 'sql';
  if (combined.includes('csv') || combined.includes('export')) return 'export_csv';
  if (combined.includes('planilha') || combined.includes('spreadsheet')) return 'spreadsheet_report';
  if (combined.includes('e-mail') || combined.includes('email') || combined.includes('assunto')) return 'email_draft';
  if (combined.includes('whatsapp') || combined.includes('mensagem') || combined.includes('comunicado')) return 'message_draft';
  return 'operational_report';
}

function outputLabel(outputType: string): string {
  return approvalOutputOptions.find((option) => option.id === outputType)?.label || outputType;
}

function OpsMessageBubble(props: {
  message: ChatMessage;
  onRequestApproval?: () => void;
  onFeedback?: (useful: boolean) => void;
}) {
  const isAssistant = () => props.message.role === 'assistant';
  const feedbackStatusLabel = () =>
    props.message.feedback_status === 'useful' ? 'Útil registrado' : 'Não útil registrado';

  return (
    <div
      class={`playground-message ${
        isAssistant() ? 'playground-message--assistant' : 'playground-message--user'
      }`}
    >
      <div class="playground-message-label">
        <span>{isAssistant() ? 'Operação' : 'Você'}</span>
        <span class="playground-message-time">{formatTime(props.message.timestamp)}</span>
      </div>

      <div 
        class="markdown-body playground-markdown"
        innerHTML={renderChatMarkdown(props.message.content)} 
      />

      <Show when={isAssistant()}>
        <div class="playground-action-row">
          <Show when={props.message.source}>
            <span class="playground-chip">
              <Sparkles size={13} />
              {props.message.source}
            </span>
          </Show>

          <Show when={props.message.approval_status || props.message.approval_id}>
            <span class={`playground-status-pill ${approvalStatusTone(props.message.approval_status)}`}>
              <ShieldCheck size={13} />
              {approvalStatusLabel(props.message.approval_status)}
            </span>
          </Show>

          <Show when={props.message.approval_id}>
            <span class="playground-chip">
              <strong>{props.message.approval_id}</strong>
            </span>
          </Show>

          <Show when={props.message.feedback_status}>
            <span class="playground-status-pill is-success">{feedbackStatusLabel()}</span>
          </Show>

          <div class="ml-auto flex flex-wrap items-center gap-2">
            <Show when={props.message.request_id}>
              <button
                type="button"
                class="btn btn-ghost btn-xs"
                onClick={() => props.onFeedback?.(true)}
                title="Marcar resposta como util"
                aria-pressed={props.message.feedback_status === 'useful'}
                disabled={!!props.message.feedback_status}
              >
                Util
              </button>
              <button
                type="button"
                class="btn btn-ghost btn-xs"
                onClick={() => props.onFeedback?.(false)}
                title="Marcar resposta como nao util"
                aria-pressed={props.message.feedback_status === 'not_useful'}
                disabled={!!props.message.feedback_status}
              >
                Nao util
              </button>
            </Show>

            <button
              type="button"
              class="btn btn-outline btn-sm gap-2"
              onClick={() => props.onRequestApproval?.()}
              aria-label="Solicitar aprovação desta resposta"
            >
              <ShieldCheck size={14} />
              Solicitar aprovacao
            </button>
          </div>
        </div>
      </Show>
    </div>
  );
}

export default function PlaygroundOps() {
  const navigate = useNavigate();

  const [accessReady, setAccessReady] = createSignal(false);
  const [selectedMode, setSelectedMode] = createSignal<string>('abastecimento');
  const [input, setInput] = createSignal('');
  const [messages, setMessages] = createSignal<ChatMessage[]>([]);
  const [playgroundSessionId, setPlaygroundSessionId] = createSignal<string>(createPlaygroundSessionId());
  const [loading, setLoading] = createSignal(false);
  const [auditTrail, setAuditTrail] = createSignal<OpsAuditItem[]>([]);
  const [approvalDraft, setApprovalDraft] = createSignal<ApprovalDraft | null>(null);
  const [selectedOutputType, setSelectedOutputType] = createSignal('operational_report');
  const [deliveryTarget, setDeliveryTarget] = createSignal('');
  const [approvalPriority, setApprovalPriority] = createSignal('media');
  const [approvalNotes, setApprovalNotes] = createSignal('');
  const [approvalSubmitting, setApprovalSubmitting] = createSignal(false);
  const [approvalBanner, setApprovalBanner] = createSignal<string | null>(null);
  const [stateHydrated, setStateHydrated] = createSignal(false);

  let messagesEndRef: HTMLDivElement | undefined;

  const selectedModeConfig = createMemo(
    () => operationModes.find((mode) => mode.id === selectedMode()) || operationModes[0],
  );
  const pendingApprovals = createMemo(
    () =>
      auditTrail().filter(
        (item) => (item.approval_status || item.status || '').toLowerCase() === 'pending',
      ).length,
  );
  const lastAssistantMessage = createMemo(() => {
    const history = messages();
    for (let index = history.length - 1; index >= 0; index -= 1) {
      if (history[index].role === 'assistant') return history[index];
    }
    return null;
  });

  const loadOpsAudit = async () => {
    try {
      const response = await playgroundApi.getOpsAudit(12);
      setAuditTrail(response?.data?.items || []);
    } catch {
      setAuditTrail([]);
    }
  };

  onMount(async () => {
    const persistedState = loadPersistedOpsState();
    if (persistedState?.selectedMode && operationModes.some((mode) => mode.id === persistedState.selectedMode)) {
      setSelectedMode(persistedState.selectedMode);
    }
    if (typeof persistedState?.input === 'string') setInput(persistedState.input);
    if (Array.isArray(persistedState?.messages)) {
      setMessages(persistedState.messages.filter((message) => message && typeof message.content === 'string').slice(-MAX_PERSISTED_OPS_MESSAGES));
    }
    if (typeof persistedState?.sessionId === 'string' && persistedState.sessionId.trim()) {
      setPlaygroundSessionId(persistedState.sessionId.trim());
    }
    if (typeof persistedState?.selectedOutputType === 'string') setSelectedOutputType(persistedState.selectedOutputType);
    if (typeof persistedState?.deliveryTarget === 'string') setDeliveryTarget(persistedState.deliveryTarget);
    if (typeof persistedState?.approvalPriority === 'string') setApprovalPriority(persistedState.approvalPriority);
    if (typeof persistedState?.approvalNotes === 'string') setApprovalNotes(persistedState.approvalNotes);
    setStateHydrated(true);

    // Acesso otimista: habilita o Playground imediatamente.
    // Se getInfo() confirmar bloqueio explícito, redireciona.
    // Isso evita que falhas de rede/banco silenciem o usuário.
    setAccessReady(true);
    try {
      const info = await playgroundApi.getInfo();
      // Só redireciona se a API responder explicitamente com acesso negado
      if (info?.data?.playground_access_enabled === false && info?.data?.playground_access_reason) {
        // Não admin e acesso explicitamente negado pelo servidor
        navigate('/dashboard', { replace: true });
        return;
      }
      await loadOpsAudit();
    } catch {
      // Se getInfo() falhar (backend offline, rede, etc.),
      // mantém accessReady=true e deixa o usuário usar o Playground.
      // O sendMessage tem seu próprio tratamento de erro.
      console.warn('[PlaygroundOps] getInfo() falhou — modo offline/standalone ativo.');
    }
  });

  createEffect(() => {
    if (!stateHydrated() || typeof window === 'undefined') return;

    const payload = {
      selectedMode: selectedMode(),
      input: input(),
      messages: messages().slice(-MAX_PERSISTED_OPS_MESSAGES),
      sessionId: playgroundSessionId(),
      selectedOutputType: selectedOutputType(),
      deliveryTarget: deliveryTarget(),
      approvalPriority: approvalPriority(),
      approvalNotes: approvalNotes(),
    };

    try {
      window.localStorage.setItem(PLAYGROUND_OPS_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // Ignore localStorage quota issues.
    }
  });

  const buildSystemInstruction = (userMessage: string): string => {
    if (isSqlRequest(userMessage)) {
      return [
        'Voce e analista BI de varejo.',
        `Modo operacional ativo: ${modeLabel(selectedMode())}.`,
        'O usuario pediu SQL.',
        'Responda somente com SQL Server valido, em bloco ```sql```.',
        'Nao inclua Resumo executivo, Tabela operacional, Proximas acoes, checklist ou texto extra.',
        'Use nomes de tabelas e colunas plausiveis para BI de varejo e filtros por UNE quando aplicavel.',
      ].join('\n');
    }

    return [
      'Voce e analista de BI e OPCOM da Lojas Cacula.',
      `Modo operacional ativo: ${modeLabel(selectedMode())}.`,
      `Foco operacional: ${selectedModeConfig().focus}.`,
      'Responda em 4 blocos: Resumo executivo, Tabela operacional, SQL ou Python pronto, Acao operacional.',
      'Se o usuario pedir SQL ou Python explicitamente, entregue o codigo solicitado.',
      'Use linguagem objetiva, acionavel e alinhada a loja, UNE e rotina comercial.',
    ].join('\n');
  };

  /** Gera resposta local determinística quando todos os canais de API falham */
  const buildLocalFallback = (query: string): string => {
    const q = query.toLowerCase();
    const modeTitle = selectedModeConfig().title;

    if (q.includes('sql') || q.includes('ruptura')) {
      return [
        '```sql',
        '-- SQL gerado localmente (backend indisponível)',
        `-- Modo: ${modeTitle}`,
        'SELECT',
        '    UNE        AS loja,',
        '    NOMESEGMENTO AS categoria,',
        '    CAST(DT_REF AS DATE) AS periodo,',
        '    COUNT(*)   AS total_rupturas,',
        '    SUM(CASE WHEN GATILHO_CRITICO = 1 THEN 1 ELSE 0 END) AS criticos',
        'FROM admmat',
        'WHERE ESTOQUE_UNE = 0',
        '  AND DT_REF >= DATEADD(DAY, -30, GETDATE())',
        'GROUP BY UNE, NOMESEGMENTO, CAST(DT_REF AS DATE)',
        'ORDER BY total_rupturas DESC;',
        '```',
        '',
        '> ⚠️ Resposta gerada localmente. Reinicie o backend para obter análise completa via LLM.',
      ].join('\n');
    }

    return [
      `## Resumo executivo — ${modeTitle}`,
      '',
      `> Modo: ${modeTitle} | Foco: ${selectedModeConfig().focus}`,
      '',
      '## Tabela operacional',
      '| Campo | Instrução |',
      '|-------|-----------|',
      '| Produto/SKU | Informe o código ou nome do produto |',
      '| UNE/Loja | Informe a loja ou conjunto de lojas |',
      '| Período | Ex.: últimos 30 dias, semana atual |',
      '| Métrica | Ex.: ruptura, giro, margem, cobertura |',
      '',
      '## Próximas ações',
      '1. Informe produto + período + loja para análise específica.',
      '2. Se precisar de SQL, adicione a palavra "SQL" no prompt.',
      '3. Verifique se o backend está online para análise completa via LLM.',
      '',
      '> ⚠️ Resposta local — backend indisponível no momento.',
    ].join('\n');
  };

  const sendMessage = async () => {
    try {
      const content = input().trim();
      if (!content || loading()) return;

      toastManager.info('⏳ Montando bloco de instrução...', 1500);
      setLoading(true);

      const uId = createPlaygroundSessionId();
      const aId = createPlaygroundSessionId();
      
      const userMsg: ChatMessage = {
        id: uId,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      
      const pendingAssistantMsg: ChatMessage = {
        id: aId,
        role: 'assistant',
        content: '⚙️ O servidor IA está processando sua solicitação...\n\n_Dica: Consultas complexas podem levar de 10 a 60 segundos._',
        timestamp: new Date().toISOString(),
        approval_status: 'pending',
      };

      // Fazer clonagem profunda e recriar toda a array para forçar SolidJS a notificar
      const historyCopy = JSON.parse(JSON.stringify(messages()));
      const nextMessages = [...historyCopy, userMsg, pendingAssistantMsg];
      
      setMessages(nextMessages);
      setInput('');
      setApprovalBanner(null);
      
      try { announcer.polite(`Enviando pergunta no modo ${selectedModeConfig().title}.`); } catch(e){}
      
      setTimeout(() => messagesEndRef?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 50);

      let resolved: { text: string; requestId?: string; source?: string; intent?: string } | null = null;
      let finalResponseGenerated = false;

      // Chama a Camada Primaria: LLM Remoto com fallback para local.
      try {
        const payload = buildGuidedChatPayload({
          modeId: selectedMode(),
          query: content,
          sessionId: playgroundSessionId(),
          outputType: selectedOutputType(),
        });

        toastManager.info('🤖 Servidor de IA operando...', 3000);
        
        const response = await playgroundApi.guidedChat(payload);
        const resolvedText = extractGuidedChatResolution(response);
        
        if (resolvedText?.text) {
           resolved = resolvedText;
           finalResponseGenerated = true;
           toastManager.success('✅ Resposta gerada com sucesso!');
        } else {
           throw new Error('Servidor retornou resposta em branco.');
        }

      } catch (remoteError: any) {
        console.error('Falha no Provider remoto. Aplicando contingência:', remoteError);
        const errDetail = remoteError?.response?.data?.detail || remoteError?.message || 'Timeout/Falha de rede';
        setApprovalBanner(`⚠️ Usando processamento local de contingência. API Indisponível: ${errDetail}`);
        toastManager.error('⚠️ Fallback de contingência engajado.');
        
        const localT = buildLocalFallback(content);
        resolved = { text: localT, source: 'local-offline', intent: 'fallback.local' };
        finalResponseGenerated = true;
      } finally {
        if (!finalResponseGenerated || !resolved) {
          resolved = { text: 'Nao foi possivel processar a solicitacao local ou remotamente. Tente novamente mais tarde.', source: 'error', intent: 'unknown' };
        }
        
        const finalContent = String(resolved?.text || '').trim();
        
        const finalMsg: ChatMessage = {
          id: aId,
          role: 'assistant',
          content: finalContent || buildLocalFallback(content),
          timestamp: new Date().toISOString(),
          request_id: resolved?.requestId,
          source: resolved?.source || 'safeguard',
          intent: resolved?.intent || 'safeguard',
        };

        // Atualiza o Signal usando a reconstrução completa
        setMessages((prev) => prev.map(m => m.id === aId ? finalMsg : {...m}));
        
        setLoading(false);
        setTimeout(() => messagesEndRef?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 150);
      }
      
    } catch (critical: any) {
      console.error('Critical UI Error:', critical);
      setLoading(false);
      setTimeout(() => messagesEndRef?.scrollIntoView({ behavior: 'smooth' }), 120);
    }
  };

  const resolvePromptForMessage = (messageId: string): string => {
    const history = messages();
    const targetIndex = history.findIndex((message) => message.id === messageId);
    if (targetIndex <= 0) return '';

    for (let index = targetIndex - 1; index >= 0; index -= 1) {
      if (history[index].role === 'user') return history[index].content;
    }
    return '';
  };

  const openApprovalDesk = (message: ChatMessage) => {
    const requestText = resolvePromptForMessage(message.id);
    const inferredOutputType = inferOutputType(requestText, message.content);

    setSelectedOutputType(inferredOutputType);
    setDeliveryTarget('');
    setApprovalPriority('media');
    setApprovalNotes('');
    setApprovalBanner(null);
    setApprovalDraft({
      messageId: message.id,
      requestText,
      generatedOutput: message.content,
    });
    toastManager.info('Resposta carregada na mesa de aprovação.');
    announcer.polite('Resposta pronta para solicitação de aprovação.');
  };

  const submitApprovalRequest = async () => {
    const draft = approvalDraft();
    if (!draft || approvalSubmitting()) return;

    setApprovalSubmitting(true);
    try {
      const response = await playgroundApi.submitOpsApproval({
        operation_mode: selectedMode(),
        output_type: selectedOutputType(),
        request_text: draft.requestText,
        generated_output: draft.generatedOutput,
        parameters: {
          priority: approvalPriority(),
          delivery_target: deliveryTarget().trim() || undefined,
          notes: approvalNotes().trim() || undefined,
        },
      });

      const approvalId = response?.data?.approval_id;
      setMessages((prev) =>
        prev.map((message) =>
          message.id === draft.messageId
            ? { ...message, approval_id: approvalId, approval_status: 'pending' }
            : message,
        ),
      );
      setApprovalBanner(
        approvalId
          ? `Solicitacao enviada com protocolo ${approvalId}.`
          : 'Solicitacao enviada para aprovacao.',
      );
      setApprovalDraft(null);
      await loadOpsAudit();
      toastManager.success('Solicitação enviada para aprovação.');
      announcer.polite('Solicitação de aprovação registrada.');
    } catch (error: any) {
      const detail =
        error?.response?.data?.detail || error?.message || 'Falha ao registrar solicitacao de aprovacao.';
      setApprovalBanner(`Erro ao solicitar aprovacao: ${detail}`);
      toastManager.error(detail);
      announcer.assertive(`Falha ao registrar solicitação de aprovação: ${detail}`);
    } finally {
      setApprovalSubmitting(false);
    }
  };

  const submitFeedback = async (message: ChatMessage, useful: boolean) => {
    if (!message.request_id) return;
    try {
      await playgroundApi.submitFeedback({ request_id: message.request_id, useful });
      setApprovalBanner(useful ? 'Feedback util registrado.' : 'Feedback de baixa utilidade registrado.');
      const feedbackStatus: ChatMessage['feedback_status'] = useful ? 'useful' : 'not_useful';
      setMessages((prev) =>
        prev.map((candidate) =>
          candidate.id === message.id
            ? { ...candidate, feedback_status: feedbackStatus }
            : candidate,
        ),
      );
      toastManager.success(useful ? 'Feedback útil registrado.' : 'Feedback registrado.');
      announcer.polite('Feedback registrado.');
    } catch {
      setApprovalBanner('Nao foi possivel registrar o feedback desta resposta.');
      toastManager.error('Não foi possível registrar o feedback.');
      announcer.assertive('Não foi possível registrar o feedback desta resposta.');
    }
  };

  const handleComposerKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  const useStarterPrompt = (prompt: string) => {
    setInput(prompt);
    toastManager.info('Prompt sugerido carregado no composer.', 2500);
  };

  const resetWorkspace = () => {
    if (!confirm('Deseja limpar a sessão operacional salva neste navegador?')) return;
    setMessages([]);
    setInput('');
    setApprovalDraft(null);
    setApprovalBanner(null);
    setDeliveryTarget('');
    setApprovalPriority('media');
    setApprovalNotes('');
    setSelectedOutputType('operational_report');
    setPlaygroundSessionId(createPlaygroundSessionId());
    try {
      window.localStorage.removeItem(PLAYGROUND_OPS_STORAGE_KEY);
    } catch {
      // Ignore storage cleanup issues.
    }
    toastManager.success('Sessão operacional limpa.');
    announcer.polite('Sessão operacional limpa.');
  };

  return (
    <Show
      when={accessReady()}
      fallback={<div class="p-6 text-sm text-slate-500">Validando permissao de acesso...</div>}
    >
      <div class="playground-scene h-full overflow-hidden">
        <div class="playground-shell h-full grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-4 p-4">
          <div class="playground-main-column flex flex-col gap-4">
            <section class="playground-surface playground-hero">
              <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div class="space-y-4">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="playground-chip">
                      <Terminal size={14} />
                      <strong>Playground Ops</strong>
                    </span>
                    <span class="playground-chip">
                      <Sparkles size={14} />
                      {selectedModeConfig().title}
                    </span>
                    <span class="playground-chip">
                      <ShieldCheck size={14} />
                      Aprovacao explicita
                    </span>
                  </div>

                  <div>
                    <h1 class="text-3xl font-bold text-foreground">
                      Sala operacional com leitura clara e solicitacao de aprovacao
                    </h1>
                    <p class="max-w-3xl text-sm leading-7 text-muted-foreground">
                      O fluxo principal continua simples: escolha o modo, converse com o assistente
                      e, quando a resposta virar artefato operacional, registre o pedido de
                      aprovacao sem sair da conversa.
                    </p>
                  </div>

                  <div class="playground-kpi-grid">
                    <div class="playground-kpi">
                      <div class="playground-kpi-label">Modo ativo</div>
                      <div class="playground-kpi-value">{selectedModeConfig().title}</div>
                      <div class="playground-kpi-note">{selectedModeConfig().focus}</div>
                    </div>
                    <div class="playground-kpi">
                      <div class="playground-kpi-label">Interacoes</div>
                      <div class="playground-kpi-value">{messages().length}</div>
                      <div class="playground-kpi-note">
                        {lastAssistantMessage() ? 'Ultima resposta pronta para revisar' : 'Sem resposta ainda'}
                      </div>
                    </div>
                    <div class="playground-kpi">
                      <div class="playground-kpi-label">Pendentes</div>
                      <div class="playground-kpi-value">{pendingApprovals()}</div>
                      <div class="playground-kpi-note">Pedidos recentes aguardando triagem</div>
                    </div>
                  </div>
                </div>

                <div class="flex flex-col items-stretch gap-3 xl:items-end">
                  <button type="button" class="btn btn-ghost gap-2" onClick={() => void loadOpsAudit()}>
                    <RefreshCcw size={16} />
                    Atualizar auditoria
                  </button>
                  <button type="button" class="btn btn-ghost gap-2" onClick={resetWorkspace}>
                    Limpar sessao
                  </button>
                </div>
              </div>
            </section>

            <Show when={approvalBanner()}>
              <div class="playground-note" role="status" aria-live="polite" aria-atomic="true">
                {approvalBanner()}
              </div>
            </Show>

            <section class="playground-panel flex-1 min-h-0">
              <div class="playground-panel-header px-5 py-4">
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                      Conversa operacional
                    </div>
                    <div class="mt-1 text-sm font-semibold text-foreground">
                      {selectedModeConfig().title} · {selectedModeConfig().description}
                    </div>
                  </div>

                  <div class="flex flex-wrap items-center gap-2">
                    <span class="playground-chip">
                      <Clock size={14} />
                      {loading() ? 'Processando' : 'Pronto'}
                    </span>
                    <span class="playground-chip">
                      <CheckCheck size={14} />
                      {approvalDraft() ? 'Resposta selecionada para aprovacao' : 'Selecione uma resposta para aprovar'}
                    </span>
                  </div>
                </div>
              </div>

              <div class="playground-scroll flex-1 p-5">
                <Show
                  when={messages().length > 0}
                  fallback={
                    <div class="playground-empty">
                      <div>
                        <div class="playground-empty-title">Comece por uma rotina real.</div>
                        <p class="playground-empty-copy">
                          O layout privilegia uma decisao por vez: escolha o modo, dispare um
                          prompt de trabalho e so depois envie para aprovacao o que realmente virar
                          artefato operacional.
                        </p>
                      </div>

                      <div class="grid gap-3 md:grid-cols-2">
                        <For each={selectedModeConfig().prompts}>
                          {(prompt) => (
                            <button
                              type="button"
                              class="playground-task-button"
                              onClick={() => useStarterPrompt(prompt)}
                              aria-label={`Carregar prompt sugerido: ${prompt}`}
                            >
                              <div class="playground-task-button-title">
                                <Sparkles size={14} />
                                Prompt sugerido
                              </div>
                              <div class="playground-task-button-copy">{prompt}</div>
                            </button>
                          )}
                        </For>
                      </div>
                    </div>
                  }
                >
                  <div class="space-y-5">
                    <For each={messages()}>
                      {(message) => (
                        <OpsMessageBubble
                          message={message}
                          onRequestApproval={() => openApprovalDesk(message)}
                          onFeedback={(useful) => void submitFeedback(message, useful)}
                        />
                      )}
                    </For>
                  </div>
                </Show>
                <div ref={messagesEndRef} />
              </div>
            </section>

            <section class="playground-compose-card p-4">
              <div class="flex flex-col gap-3">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                      Prompt operacional
                    </div>
                    <div class="mt-1 text-sm text-foreground">
                      Enter envia. Shift + Enter quebra linha.
                    </div>
                  </div>
                  <span class="playground-chip">
                    <ShieldCheck size={14} />
                    Modo {selectedModeConfig().title}
                  </span>
                </div>

                <div class="grid gap-3 xl:grid-cols-[minmax(0,1fr)_auto]">
                  <textarea
                    class="input min-h-[132px] w-full resize-none px-4 py-3 font-mono text-sm leading-6"
                    value={input()}
                    onInput={(event) => setInput(event.currentTarget.value)}
                    onKeyDown={(event) => handleComposerKeyDown(event)}
                    placeholder={selectedModeConfig().prompts[0]}
                    aria-label="Prompt operacional"
                  />

                  <button
                    type="button"
                    class="btn btn-primary h-12 gap-2 self-end px-5"
                    disabled={loading() || !input().trim()}
                    onClick={() => void sendMessage()}
                  >
                    <Show when={!loading()} fallback={<Clock size={18} class="animate-spin" />}>
                      <Send size={18} />
                    </Show>
                    Enviar
                  </button>
                </div>
              </div>
            </section>
          </div>

          <aside class="min-h-0 flex flex-col gap-4 overflow-y-auto pr-1">
            <section class="playground-surface playground-sidebar-card">
              <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Modos de operacao
              </div>
              <div class="mt-4 grid gap-3">
                <For each={operationModes}>
                  {(mode) => (
                    <button
                      type="button"
                      class={`playground-mode-card ${selectedMode() === mode.id ? 'active' : ''}`}
                      onClick={() => setSelectedMode(mode.id)}
                      aria-pressed={selectedMode() === mode.id}
                    >
                      <div class="playground-mode-card-title">{mode.title}</div>
                      <div class="playground-mode-card-copy">{mode.description}</div>
                    </button>
                  )}
                </For>
              </div>
            </section>

            <section class="playground-surface playground-sidebar-card">
              <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Mesa de aprovacao
              </div>

              <div class="mt-4 space-y-4">
                <div>
                  <label class="text-sm font-semibold text-foreground">Tipo de saida</label>
                  <div class="playground-output-grid mt-3">
                    <For each={approvalOutputOptions}>
                      {(option) => {
                        const Icon = option.icon;
                        return (
                          <button
                            type="button"
                            class={`playground-output-card ${
                              selectedOutputType() === option.id ? 'active' : ''
                            }`}
                            onClick={() => setSelectedOutputType(option.id)}
                            aria-pressed={selectedOutputType() === option.id}
                          >
                            <div class="playground-output-card-title">
                              <Icon size={16} />
                              {option.label}
                            </div>
                            <div class="playground-output-card-copy">{option.hint}</div>
                          </button>
                        );
                      }}
                    </For>
                  </div>
                </div>

                <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <div>
                    <label class="text-sm font-semibold text-foreground">Destino ou canal</label>
                    <input
                      class="input mt-2 w-full"
                      value={deliveryTarget()}
                      onInput={(event) => setDeliveryTarget(event.currentTarget.value)}
                      placeholder="Ex.: Supervisores regionais"
                      aria-label="Destino ou canal da solicitação"
                    />
                  </div>

                  <div>
                    <label class="text-sm font-semibold text-foreground">Prioridade</label>
                    <select
                      class="input mt-2 w-full"
                      value={approvalPriority()}
                      onChange={(event) => setApprovalPriority(event.currentTarget.value)}
                      aria-label="Prioridade da solicitação"
                    >
                      <option value="baixa">Baixa</option>
                      <option value="media">Media</option>
                      <option value="alta">Alta</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label class="text-sm font-semibold text-foreground">Observacoes</label>
                  <textarea
                    class="input mt-2 min-h-[92px] w-full resize-none"
                    value={approvalNotes()}
                    onInput={(event) => setApprovalNotes(event.currentTarget.value)}
                    placeholder="Contexto adicional para quem vai aprovar."
                    aria-label="Observações da solicitação"
                  />
                </div>

                <Show
                  when={approvalDraft()}
                  fallback={
                    <div class="playground-note">
                      Selecione uma resposta do assistente para abrir a mesa de aprovacao com o
                      prompt original e o artefato gerado.
                    </div>
                  }
                >
                  {(draft) => (
                    <div class="playground-preview-card">
                      <div class="flex items-center justify-between gap-3">
                        <div class="text-sm font-semibold text-foreground">
                          Solicitar {outputLabel(selectedOutputType())}
                        </div>
                        <span class="playground-status-pill is-pending">
                          <ShieldCheck size={13} />
                          Pronto para enviar
                        </span>
                      </div>

                      <div class="mt-4 grid gap-3">
                        <div class="playground-note">
                          <strong>Pedido original:</strong>
                          <div class="mt-2 whitespace-pre-wrap break-words text-xs">
                            {draft().requestText || 'Sem prompt associado.'}
                          </div>
                        </div>
                        <div class="playground-note">
                          <strong>Saida gerada:</strong>
                          <div class="mt-2 line-clamp-6 whitespace-pre-wrap break-words text-xs">
                            {draft().generatedOutput}
                          </div>
                        </div>
                      </div>

                      <div class="mt-4 flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          class="btn btn-primary gap-2"
                          onClick={() => void submitApprovalRequest()}
                          disabled={approvalSubmitting()}
                        >
                          <Show
                            when={!approvalSubmitting()}
                            fallback={<Clock size={16} class="animate-spin" />}
                          >
                            <ShieldCheck size={16} />
                          </Show>
                          Enviar para aprovacao
                        </button>
                        <button
                          type="button"
                          class="btn btn-ghost"
                          onClick={() => setApprovalDraft(null)}
                          disabled={approvalSubmitting()}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}
                </Show>
              </div>
            </section>

            <section class="playground-surface playground-sidebar-card">
              <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Trilha de auditoria
              </div>
              <div class="mt-4 space-y-3">
                <Show
                  when={auditTrail().length > 0}
                  fallback={
                    <div class="playground-note">
                      Nenhuma solicitacao registrada ainda para esta conta.
                    </div>
                  }
                >
                  <For each={auditTrail()}>
                    {(item) => (
                      <div class="playground-audit-item">
                        <div class="flex items-start justify-between gap-3">
                          <div>
                            <div class="text-sm font-semibold text-foreground">
                              {modeLabel(item.operation_mode || '-')}
                            </div>
                            <div class="mt-1 text-xs text-muted-foreground">
                              {outputLabel(item.output_type || '-')}
                            </div>
                          </div>
                          <span class={`playground-status-pill ${approvalStatusTone(item.approval_status || item.status)}`}>
                            {approvalStatusLabel(item.approval_status || item.status)}
                          </span>
                        </div>

                        <div class="playground-audit-grid mt-3 text-xs text-muted-foreground">
                          <div>
                            <strong>Protocolo:</strong> {item.approval_id || '-'}
                          </div>
                          <div>
                            <strong>Quando:</strong> {formatTime(item.timestamp)}
                          </div>
                        </div>
                      </div>
                    )}
                  </For>
                </Show>
              </div>
            </section>

            <section class="playground-surface playground-sidebar-card">
              <div class="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Guardrails
              </div>
              <div class="playground-rule-list mt-4">
                <div class="playground-rule-item">
                  <div class="text-sm font-semibold text-foreground">Aprovacao explicita</div>
                  <div class="text-xs leading-6 text-muted-foreground">
                    Navegador, planilha, exportacao, e-mail e mensagem entram apenas como
                    solicitacao registrada.
                  </div>
                </div>
                <div class="playground-rule-item">
                  <div class="text-sm font-semibold text-foreground">Uma decisao por vez</div>
                  <div class="text-xs leading-6 text-muted-foreground">
                    O layout reduz escolhas simultaneas e separa claramente conversa, aprovacao e
                    auditoria.
                  </div>
                </div>
                <div class="playground-rule-item">
                  <div class="text-sm font-semibold text-foreground">Laboratorio separado</div>
                  <div class="text-xs leading-6 text-muted-foreground">
                    Comparacao de prompts continua disponivel no laboratorio comparativo, sem
                    misturar a trilha operacional principal.
                  </div>
                </div>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </Show>
  );
}
