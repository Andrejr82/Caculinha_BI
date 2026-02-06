import { Skeleton } from "./migrated-components/components/ui/Skeleton";

/**
 * Demo page for Skeleton component
 * Tests visual rendering and different use cases
 */
export default function SkeletonDemo() {
  return (
    <div class="min-h-screen bg-background p-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 class="text-3xl font-bold text-foreground mb-2">
            Skeleton Component Demo
          </h1>
          <p class="text-muted-foreground">
            Componente migrado do React para SolidJS - Fase 3 Piloto
          </p>
        </div>

        {/* Basic Skeleton */}
        <section class="space-y-4">
          <h2 class="text-2xl font-semibold text-foreground">Basic Skeleton</h2>
          <div class="space-y-2">
            <Skeleton class="h-4 w-full" />
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-4 w-1/2" />
          </div>
        </section>

        {/* Card Skeleton */}
        <section class="space-y-4">
          <h2 class="text-2xl font-semibold text-foreground">Card Skeleton</h2>
          <div class="border border-border rounded-lg p-6 space-y-4">
            <Skeleton class="h-12 w-12 rounded-full" />
            <div class="space-y-2">
              <Skeleton class="h-4 w-full" />
              <Skeleton class="h-4 w-4/5" />
            </div>
          </div>
        </section>

        {/* List Skeleton */}
        <section class="space-y-4">
          <h2 class="text-2xl font-semibold text-foreground">List Skeleton</h2>
          <div class="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div class="flex items-center space-x-4">
                <Skeleton class="h-10 w-10 rounded-full" />
                <div class="flex-1 space-y-2">
                  <Skeleton class="h-3 w-3/4" />
                  <Skeleton class="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Table Skeleton */}
        <section class="space-y-4">
          <h2 class="text-2xl font-semibold text-foreground">Table Skeleton</h2>
          <div class="space-y-2">
            <Skeleton class="h-8 w-full" />
            {[...Array(4)].map((_, i) => (
              <Skeleton class="h-12 w-full" />
            ))}
          </div>
        </section>

        {/* Status */}
        <section class="border-t border-border pt-6">
          <h3 class="text-lg font-medium text-foreground mb-2">Status da Migração</h3>
          <ul class="space-y-1 text-sm text-muted-foreground">
            <li>✅ Componente migrado do React para SolidJS</li>
            <li>✅ Tipagem TypeScript correta</li>
            <li>✅ Props funcionando (class, data-*, aria-*)</li>
            <li>✅ Animação pulse ativa</li>
            <li>✅ Integração com função cn()</li>
            <li>⚠️  3/4 testes passando (1 teste com issue no matcher)</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
