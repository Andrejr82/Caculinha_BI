import { Show } from 'solid-js';

export interface ChatAutomationArtifact {
  filename?: string;
  download_url?: string;
  mime_type?: string;
  size_bytes?: number;
}

export interface ChatAutomationDraft {
  channel?: string;
  recipient?: string;
  subject?: string;
  body?: string;
}

export interface ChatAutomationState {
  proposal_id?: string;
  approval_id?: string | null;
  approval_status?: string;
  action?: string;
  title?: string;
  summary?: string;
  request_text?: string;
  params?: Record<string, any>;
  target_label?: string | null;
  review_required?: boolean;
  follow_up_action?: string | null;
  follow_up_label?: string | null;
  result_summary?: string | null;
  execution_error?: string | null;
  artifact?: ChatAutomationArtifact;
  draft?: ChatAutomationDraft;
}

const STATUS_LABELS: Record<string, string> = {
  pending_user_approval: 'Aguardando aprovação',
  approved: 'Aprovada',
  draft_ready: 'Rascunho pronto para revisão',
  completed: 'Concluída',
  rejected: 'Rejeitada',
  failed: 'Falhou',
};

export function ChatAutomationCard(props: {
  automation: ChatAutomationState;
  disabled?: boolean;
  onApprove?: () => void;
  onReject?: () => void;
  onExecuteFollowUp?: () => void;
}) {
  const statusLabel = () => STATUS_LABELS[props.automation.approval_status || ''] || 'Em processamento';
  const canApprove = () => props.automation.approval_status === 'pending_user_approval' && !!props.onApprove;
  const canReject = () => {
    const status = props.automation.approval_status;
    return (status === 'pending_user_approval' || status === 'draft_ready') && !!props.onReject;
  };
  const canExecuteFollowUp = () =>
    props.automation.approval_status === 'draft_ready' &&
    !!props.automation.follow_up_action &&
    !!props.onExecuteFollowUp;

  return (
    <div class="rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-4 text-sm text-slate-700 shadow-sm">
      <div class="flex flex-wrap items-center gap-2">
        <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-amber-700">
          Automação assistida
        </span>
        <span class="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-medium text-amber-800">
          {statusLabel()}
        </span>
      </div>

      <Show when={props.automation.title}>
        <p class="mt-3 text-base font-semibold text-slate-900">{props.automation.title}</p>
      </Show>
      <Show when={props.automation.summary}>
        <p class="mt-1 leading-6 text-slate-700">{props.automation.summary}</p>
      </Show>

      <div class="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <Show when={props.automation.action}>
          <div><strong>Ação:</strong> {props.automation.action}</div>
        </Show>
        <Show when={props.automation.target_label}>
          <div><strong>Destino:</strong> {props.automation.target_label}</div>
        </Show>
        <Show when={props.automation.approval_id}>
          <div><strong>Protocolo:</strong> {props.automation.approval_id}</div>
        </Show>
        <Show when={props.automation.review_required}>
          <div><strong>Revisão:</strong> obrigatória</div>
        </Show>
      </div>

      <Show when={props.automation.draft}>
        <div class="mt-4 rounded-xl border border-slate-200 bg-white px-3 py-3 text-xs text-slate-700">
          <p class="font-semibold text-slate-900">Rascunho</p>
          <Show when={props.automation.draft?.recipient}>
            <p class="mt-1"><strong>Destinatário:</strong> {props.automation.draft?.recipient}</p>
          </Show>
          <Show when={props.automation.draft?.subject}>
            <p class="mt-1"><strong>Assunto:</strong> {props.automation.draft?.subject}</p>
          </Show>
          <Show when={props.automation.draft?.body}>
            <pre class="mt-2 whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">{props.automation.draft?.body}</pre>
          </Show>
        </div>
      </Show>

      <Show when={props.automation.result_summary}>
        <p class="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
          {props.automation.result_summary}
        </p>
      </Show>

      <Show when={props.automation.execution_error}>
        <p class="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {props.automation.execution_error}
        </p>
      </Show>

      <Show when={props.automation.artifact?.download_url}>
        <a
          href={props.automation.artifact?.download_url}
          class="mt-4 inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:border-indigo-300 hover:text-indigo-600"
          target="_blank"
          rel="noopener noreferrer"
        >
          Baixar {props.automation.artifact?.filename || 'artefato'}
        </a>
      </Show>

      <Show when={canApprove() || canReject() || canExecuteFollowUp()}>
        <div class="mt-4 flex flex-wrap gap-2">
          <Show when={canApprove()}>
            <button
              type="button"
              onClick={() => props.onApprove?.()}
              disabled={props.disabled}
              class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Aprovar e executar
            </button>
          </Show>
          <Show when={canExecuteFollowUp()}>
            <button
              type="button"
              onClick={() => props.onExecuteFollowUp?.()}
              disabled={props.disabled}
              class="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {props.automation.follow_up_label || 'Executar ação final'}
            </button>
          </Show>
          <Show when={canReject()}>
            <button
              type="button"
              onClick={() => props.onReject?.()}
              disabled={props.disabled}
              class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:border-red-200 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Rejeitar
            </button>
          </Show>
        </div>
      </Show>
    </div>
  );
}
