type PlotlyLike = {
  register: (modules: unknown[]) => void;
  newPlot: (...args: any[]) => Promise<any>;
  purge: (target: HTMLElement) => void;
  downloadImage: (target: HTMLElement, options: Record<string, any>) => Promise<any>;
};

type PlotlyTraceType = 'scatter' | 'bar' | 'pie' | 'histogram' | 'treemap' | 'box';

let plotlyPromise: Promise<PlotlyLike> | null = null;
let loadedPlotly: PlotlyLike | null = null;
const loadedTraceTypes = new Set<PlotlyTraceType>();

const resolveModule = <T>(mod: { default?: T } | T): T => {
  if (mod && typeof mod === 'object' && 'default' in (mod as Record<string, unknown>)) {
    return (mod as { default: T }).default;
  }
  return mod as T;
};

const traceModuleLoaders: Record<PlotlyTraceType, () => Promise<unknown>> = {
  scatter: () => import('plotly.js/lib/scatter'),
  bar: () => import('plotly.js/lib/bar'),
  pie: () => import('plotly.js/lib/pie'),
  histogram: () => import('plotly.js/lib/histogram'),
  treemap: () => import('plotly.js/lib/treemap'),
  box: () => import('plotly.js/lib/box'),
};

const traceAliases: Record<string, PlotlyTraceType> = {
  bar: 'bar',
  box: 'box',
  histogram: 'histogram',
  line: 'scatter',
  pie: 'pie',
  scatter: 'scatter',
  treemap: 'treemap',
};

const ensurePlotlyGlobals = (): void => {
  const scope = globalThis as typeof globalThis & {
    global?: typeof globalThis;
    process?: { env?: Record<string, string | undefined> };
  };

  if (!scope.global) {
    scope.global = scope;
  }

  if (!scope.process) {
    scope.process = { env: {} } as typeof scope.process;
  } else if (!scope.process.env) {
    scope.process.env = {};
  }
};

const buildPlotly = async (): Promise<PlotlyLike> => {
  ensurePlotlyGlobals();
  const coreModule = await import('plotly.js/lib/core');
  const plotly = resolveModule<PlotlyLike>(coreModule);
  loadedPlotly = plotly;
  return plotly;
};

const normalizeTraceType = (rawType: unknown): PlotlyTraceType => {
  const normalized = String(rawType || 'scatter').trim().toLowerCase();
  return traceAliases[normalized] || 'scatter';
};

const ensureTraceModules = async (
  plotly: PlotlyLike,
  traceTypes: Iterable<PlotlyTraceType>,
): Promise<void> => {
  const pending = Array.from(new Set(traceTypes)).filter((traceType) => !loadedTraceTypes.has(traceType));
  if (pending.length === 0) return;

  const modules = await Promise.all(
    pending.map(async (traceType) => {
      const mod = await traceModuleLoaders[traceType]();
      loadedTraceTypes.add(traceType);
      return resolveModule(mod);
    }),
  );

  plotly.register(modules);
};

const collectTraceTypes = (chartSpec: Record<string, any> | undefined): PlotlyTraceType[] => {
  const data = Array.isArray(chartSpec?.data) ? chartSpec.data : [];
  if (data.length === 0) {
    return [];
  }

  return data.map((trace) => normalizeTraceType(trace?.type));
};

export const getPlotly = async (traceTypes?: Iterable<PlotlyTraceType>): Promise<PlotlyLike> => {
  if (!plotlyPromise) {
    plotlyPromise = buildPlotly();
  }

  const plotly = await plotlyPromise;
  if (traceTypes) {
    await ensureTraceModules(plotly, traceTypes);
  }
  return plotly;
};

export const getPlotlyForSpec = (chartSpec: Record<string, any> | undefined): Promise<PlotlyLike> =>
  getPlotly(collectTraceTypes(chartSpec));

export const peekPlotly = (): PlotlyLike | null => loadedPlotly;
