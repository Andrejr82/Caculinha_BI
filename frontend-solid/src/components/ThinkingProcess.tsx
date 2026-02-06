import { createSignal, createEffect, onCleanup, For, Show } from 'solid-js';
import { ChevronDown, ChevronRight, BrainCircuit, CheckCircle2, Loader2 } from 'lucide-solid';

interface ThinkingProcessProps {
    steps: string[];
    isThinking: boolean;
    isCollapsed?: boolean;
    onToggleCollapse?: () => void;
}

export function ThinkingProcess(props: ThinkingProcessProps) {
    const [elapsedTime, setElapsedTime] = createSignal(0);
    const [internalCollapsed, setInternalCollapsed] = createSignal(props.isCollapsed ?? true);

    let timer: number;

    createEffect(() => {
        if (props.isThinking) {
            const start = Date.now();
            timer = window.setInterval(() => {
                setElapsedTime(Math.floor((Date.now() - start) / 1000));
            }, 1000);
        } else {
            clearInterval(timer);
        }
    });

    onCleanup(() => clearInterval(timer));

    const toggleCollapse = () => {
        if (props.onToggleCollapse) {
            props.onToggleCollapse();
        } else {
            setInternalCollapsed(!internalCollapsed());
        }
    };

    const isCollapsed = () => props.isCollapsed ?? internalCollapsed();

    return (
        <div class="my-4 border border-slate-200 dark:border-zinc-800 rounded-lg bg-slate-50/50 dark:bg-zinc-900/50 overflow-hidden text-sm">
            {/* Header */}
            <button
                onClick={toggleCollapse}
                class="w-full flex items-center justify-between p-3 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors text-slate-600 dark:text-slate-400"
            >
                <div class="flex items-center gap-2">
                    <Show when={props.isThinking} fallback={<BrainCircuit size={16} />}>
                        <BrainCircuit size={16} class="animate-pulse text-indigo-500" />
                    </Show>
                    <span class="font-medium">
                        {props.isThinking ? 'Pensando...' : 'Raciocínio concluído'}
                    </span>
                    <span class="text-xs opacity-70 ml-1">
                        {props.isThinking ? `(${elapsedTime()}s)` : ''}
                    </span>
                </div>
                <div class="flex items-center gap-2">
                    <Show when={isCollapsed()} fallback={<ChevronDown size={16} />}>
                        <ChevronRight size={16} />
                    </Show>
                </div>
            </button>

            {/* Content */}
            <Show when={!isCollapsed()}>
                <div class="p-4 pt-0 border-t border-slate-100 dark:border-zinc-800 space-y-2 animate-in slide-in-from-top-2">
                    <For each={props.steps}>
                        {(step, index) => (
                            <div class="flex items-start gap-2.5 text-slate-600 dark:text-slate-300">
                                <div class="mt-0.5 min-w-[16px]">
                                    <Show
                                        when={index() === props.steps.length - 1 && props.isThinking}
                                        fallback={<CheckCircle2 size={14} class="text-green-500 mt-0.5" />}
                                    >
                                        <Loader2 size={14} class="animate-spin text-indigo-500 mt-0.5" />
                                    </Show>
                                </div>
                                <span class="leading-relaxed">{step}</span>
                            </div>
                        )}
                    </For>
                    <Show when={props.steps.length === 0 && props.isThinking}>
                        <div class="pl-7 italic text-slate-400 text-xs">Iniciando análise...</div>
                    </Show>
                </div>
            </Show>
        </div>
    );
}
