import { createSignal, Show, ErrorBoundary as SolidErrorBoundary } from 'solid-js';

interface ErrorBoundaryProps {
  children: any;
}

export function ErrorBoundary(props: ErrorBoundaryProps) {
  return (
    <SolidErrorBoundary
      fallback={(err, reset) => (
        <div class="flex flex-col items-center justify-center h-[50vh] text-center p-8 space-y-4">
          <div class="text-red-500 text-5xl">⚠️</div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100">Ops! Algo deu errado.</h2>
          <div class="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg max-w-lg overflow-auto text-sm font-mono">
            {err.toString()}
          </div>
          <div class="flex gap-4">
             <button 
              onClick={() => reset()}
              class="px-4 py-2 bg-primary text-primary-foreground rounded hover:opacity-90 transition-opacity"
            >
              Tentar Novamente
            </button>
            <button 
              onClick={() => window.location.reload()}
              class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              Recarregar Página
            </button>
          </div>
        </div>
      )}
    >
      {props.children}
    </SolidErrorBoundary>
  );
}
