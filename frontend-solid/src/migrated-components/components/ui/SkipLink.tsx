/**
 * SkipLink Component
 * Link de pular navegação para acessibilidade
 * Migrated from React to SolidJS (Next.js Link removed, native anchor)
 */

export function SkipLink() {
  return (
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
    >
      Pular para o conteúdo principal
    </a>
  );
}
