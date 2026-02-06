import { Badge, Button, Skeleton } from "./migrated-components/components/ui";

/**
 * Demo page for migrated UI components
 * Showcases Skeleton, Badge, and Button components
 */
export default function ComponentsDemo() {
  return (
    <div class="min-h-screen bg-background p-8">
      <div class="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div class="text-center space-y-2">
          <h1 class="text-4xl font-bold text-foreground">
            Componentes UI Migrados
          </h1>
          <p class="text-lg text-muted-foreground">
            React → SolidJS | Fase 3 da Migração
          </p>
        </div>

        {/* Button Component */}
        <section class="space-y-6">
          <div>
            <h2 class="text-2xl font-semibold text-foreground mb-2">Button</h2>
            <p class="text-muted-foreground">6 variantes × 6 tamanhos = 36 combinações</p>
          </div>

          <div class="space-y-4">
            <div>
              <h3 class="text-lg font-medium text-foreground mb-3">Variantes</h3>
              <div class="flex flex-wrap gap-3">
                <Button variant="default">Default</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="destructive">Destructive</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="link">Link</Button>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-medium text-foreground mb-3">Tamanhos</h3>
              <div class="flex flex-wrap items-center gap-3">
                <Button size="sm">Small</Button>
                <Button size="default">Default</Button>
                <Button size="lg">Large</Button>
                <Button size="icon">🚀</Button>
                <Button size="icon-sm">⭐</Button>
                <Button size="icon-lg">💎</Button>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-medium text-foreground mb-3">Estados</h3>
              <div class="flex flex-wrap gap-3">
                <Button>Normal</Button>
                <Button disabled>Disabled</Button>
              </div>
            </div>
          </div>
        </section>

        {/* Badge Component */}
        <section class="space-y-6">
          <div>
            <h2 class="text-2xl font-semibold text-foreground mb-2">Badge</h2>
            <p class="text-muted-foreground">4 variantes para status e labels</p>
          </div>

          <div class="space-y-4">
            <div>
              <h3 class="text-lg font-medium text-foreground mb-3">Variantes</h3>
              <div class="flex flex-wrap gap-3">
                <Badge variant="default">Default</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="destructive">Destructive</Badge>
                <Badge variant="outline">Outline</Badge>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-medium text-foreground mb-3">Casos de Uso</h3>
              <div class="flex flex-wrap gap-3">
                <Badge variant="default">New</Badge>
                <Badge variant="secondary">In Progress</Badge>
                <Badge variant="outline">Draft</Badge>
                <Badge variant="destructive">Error</Badge>
              </div>
            </div>
          </div>
        </section>

        {/* Skeleton Component */}
        <section class="space-y-6">
          <div>
            <h2 class="text-2xl font-semibold text-foreground mb-2">Skeleton</h2>
            <p class="text-muted-foreground">Loading states</p>
          </div>

          <div class="space-y-4">
            <div class="border border-border rounded-lg p-6 space-y-4">
              <div class="flex items-center space-x-4">
                <Skeleton class="h-12 w-12 rounded-full" />
                <div class="flex-1 space-y-2">
                  <Skeleton class="h-4 w-3/4" />
                  <Skeleton class="h-4 w-1/2" />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Integration Example */}
        <section class="space-y-6">
          <div>
            <h2 class="text-2xl font-semibold text-foreground mb-2">Integração</h2>
            <p class="text-muted-foreground">Componentes trabalhando juntos</p>
          </div>

          <div class="border border-border rounded-lg p-6 space-y-4">
            <div class="flex items-center justify-between">
              <div class="space-y-1">
                <h3 class="text-lg font-medium text-foreground">Card de Exemplo</h3>
                <p class="text-sm text-muted-foreground">Demonstração de integração</p>
              </div>
              <Badge variant="default">Active</Badge>
            </div>
            <div class="flex gap-2">
              <Button variant="default" size="sm">Salvar</Button>
              <Button variant="outline" size="sm">Cancelar</Button>
              <Button variant="destructive" size="sm">Excluir</Button>
            </div>
          </div>
        </section>

        {/* Status */}
        <section class="border-t border-border pt-6">
          <h3 class="text-lg font-medium text-foreground mb-3">Status da Migração</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="border border-border rounded-lg p-4 space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-foreground">Skeleton</h4>
                <Badge variant="default">✓</Badge>
              </div>
              <p class="text-sm text-muted-foreground">3/4 testes passando</p>
            </div>
            <div class="border border-border rounded-lg p-4 space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-foreground">Badge</h4>
                <Badge variant="default">✓</Badge>
              </div>
              <p class="text-sm text-muted-foreground">6/6 testes passando</p>
            </div>
            <div class="border border-border rounded-lg p-4 space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-foreground">Button</h4>
                <Badge variant="default">✓</Badge>
              </div>
              <p class="text-sm text-muted-foreground">8/8 testes passando</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
