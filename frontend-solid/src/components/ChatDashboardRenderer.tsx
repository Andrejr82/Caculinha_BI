import { Accessor, For, Show } from 'solid-js';

import { DataTable } from './DataTable';
import { PlotlyChart } from './PlotlyChart';

export interface DashboardWidget {
  kind: 'kpi' | 'chart' | 'table' | 'text';
  id: string;
  title?: string;
  value?: string | number;
  subtitle?: string;
  description?: string;
  chart_spec?: Record<string, any>;
  rows?: Array<Record<string, any>>;
}

export interface DashboardSpec {
  title: string;
  subtitle?: string;
  filters?: Record<string, string | number | boolean>;
  widgets: DashboardWidget[];
}

interface ChatDashboardRendererProps {
  spec: Accessor<DashboardSpec | undefined>;
}

export const ChatDashboardRenderer = (props: ChatDashboardRendererProps) => {
  const kpiWidgets = () => (props.spec()?.widgets || []).filter((widget) => widget.kind === 'kpi');
  const visualWidgets = () => (props.spec()?.widgets || []).filter((widget) => widget.kind !== 'kpi');

  return (
    <div class="space-y-4">
      <div class="rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4">
        <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">
          {props.spec()?.title || 'Dashboard'}
        </h3>
        <Show when={props.spec()?.subtitle}>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{props.spec()?.subtitle}</p>
        </Show>
        <Show when={props.spec()?.filters && Object.keys(props.spec()?.filters || {}).length > 0}>
          <div class="mt-3 flex flex-wrap gap-2">
            <For each={Object.entries(props.spec()?.filters || {})}>
              {([key, value]) => (
                <span class="inline-flex items-center rounded-full bg-slate-100 dark:bg-zinc-800 px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300">
                  {key}: {String(value)}
                </span>
              )}
            </For>
          </div>
        </Show>
      </div>

      <Show when={kpiWidgets().length > 0}>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <For each={kpiWidgets()}>
            {(widget) => (
              <article class="rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4">
                <p class="text-xs uppercase tracking-wide text-slate-500">{widget.title || widget.id}</p>
                <p class="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                  {widget.value !== undefined ? String(widget.value) : '-'}
                </p>
                <Show when={widget.subtitle}>
                  <p class="mt-1 text-xs text-slate-500">{widget.subtitle}</p>
                </Show>
              </article>
            )}
          </For>
        </div>
      </Show>

      <For each={visualWidgets()}>
        {(widget) => (
          <div class="rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3">
            <Show when={widget.title}>
              <h4 class="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">{widget.title}</h4>
            </Show>

            <Show when={widget.kind === 'chart' && widget.chart_spec}>
              <PlotlyChart chartSpec={() => widget.chart_spec || {}} />
            </Show>

            <Show when={widget.kind === 'table' && widget.rows}>
              <DataTable data={() => widget.rows || []} caption={widget.title || 'Detalhes'} />
            </Show>

            <Show when={widget.kind === 'text'}>
              <p class="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                {widget.description || widget.value || '-'}
              </p>
            </Show>
          </div>
        )}
      </For>
    </div>
  );
};
