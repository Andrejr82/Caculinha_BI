import { A, useLocation, useNavigate } from '@solidjs/router';
import auth from '@/store/auth';
import {
  LayoutDashboard, MessageSquare, PieChart, FileText, Settings, LogOut,
  AlertTriangle, Truck, BookOpen, Terminal, Database, Lock, Shield, Lightbulb, HelpCircle, Code, Info,
  ChevronLeft, ChevronRight, TrendingUp, BarChart3, Package
} from 'lucide-solid';
import { For, Show, children, createSignal } from 'solid-js';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Logo } from '@/components';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';
import { toastManager } from '@/components/Toast';

export default function Layout(props: any) {
  const location = useLocation();
  const navigate = useNavigate();
  const userRole = () => auth.user()?.role || 'user';

  // Estado para controlar sidebar retrátil
  const [isCollapsed, setIsCollapsed] = createSignal(false);

  // ✅ ACESSIBILIDADE: Keyboard shortcuts (mantidos)
  useKeyboardShortcut([
    {
      key: 'd',
      ctrl: true,
      description: 'Ir para Dashboard',
      callback: () => {
        navigate('/dashboard');
        toastManager.info('Navegando para Dashboard');
      },
    },
    {
      key: 'k',
      ctrl: true,
      description: 'Ir para Chat BI',
      callback: () => {
        navigate('/chat');
        toastManager.info('Navegando para Chat BI');
      },
    },
    {
      key: 'r',
      ctrl: true,
      description: 'Ir para Rupturas',
      callback: () => {
        navigate('/rupturas');
        toastManager.info('Navegando para Rupturas');
      },
    },
    {
      key: 'b',
      ctrl: true,
      description: 'Alternar Sidebar',
      callback: () => {
        setIsCollapsed(!isCollapsed());
      },
    }
  ]);

  // Definição dos Itens de Menu (mantidos)
  const menuItems = [
    {
      group: 'Dashboards',
      items: [
        { href: '/dashboard', icon: LayoutDashboard, label: 'Monitoramento', roles: ['admin', 'user'] },
        { href: '/metrics', icon: PieChart, label: 'Analytics Avançado', roles: ['admin'] },
        { href: '/rupturas', icon: AlertTriangle, label: 'Rupturas Críticas', roles: ['admin', 'user'] },
        { href: '/forecasting', icon: TrendingUp, label: 'Previsão de Demanda', roles: ['admin', 'user'] },
        { href: '/executive', icon: BarChart3, label: 'Executivo', roles: ['admin'] },
        { href: '/suppliers', icon: Package, label: 'Fornecedores', roles: ['admin', 'user'] },
      ]
    },
    {
      group: 'Operacional',
      items: [
        { href: '/transfers', icon: Truck, label: 'Transferências', roles: ['admin', 'user'] },
        { href: '/reports', icon: FileText, label: 'Relatórios', roles: ['admin'] },
      ]
    },
    {
      group: 'Inteligência',
      items: [
        { href: '/chat', icon: MessageSquare, label: 'Chat BI', roles: ['admin', 'user'] },
        { href: '/code-chat', icon: Code, label: 'Code Chat', roles: ['admin'] },
        { href: '/examples', icon: Lightbulb, label: 'Exemplos', roles: ['admin'] },
        { href: '/learning', icon: BookOpen, label: 'Aprendizado', roles: ['admin'] },
        { href: '/playground', icon: Terminal, label: 'Playground', roles: ['admin'] },
      ]
    },
    {
      group: 'Sistema',
      items: [
        { href: '/diagnostics', icon: Database, label: 'Diagnóstico DB', roles: ['admin'] },
        { href: '/help', icon: HelpCircle, label: 'Ajuda', roles: ['admin', 'user'] },
        { href: '/about', icon: Info, label: 'Sobre', roles: ['admin', 'user'] },
        { href: '/profile', icon: Lock, label: 'Alterar Senha', roles: ['admin', 'user'] },
        { href: '/admin', icon: Shield, label: 'Administração', roles: ['admin'] },
      ]
    }
  ];

  const NavItem = (props: { href: string; icon: any; label: string }) => (
    <A
      href={props.href}
      class={`nav-item flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 mx-2 mb-1
        ${location.pathname.includes(props.href)
          ? 'bg-sidebar-accent text-sidebar-primary shadow-sm'
          : 'text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-primary'}
        ${isCollapsed() ? 'justify-center px-2' : ''}
      `}
      title={isCollapsed() ? props.label : ''}
    >
      <props.icon size={20} class="flex-shrink-0" />
      <Show when={!isCollapsed()}>
        <span class="whitespace-nowrap overflow-hidden text-sm font-medium">{props.label}</span>
      </Show>
    </A>
  );

  return (
    <div
      class="app-layout transition-all duration-300 ease-in-out"
      style={{
        "grid-template-columns": isCollapsed() ? "80px 1fr" : "260px 1fr"
      }}
    >
      <aside class="sidebar flex flex-col bg-sidebar-background border-r border-border h-full overflow-hidden transition-all duration-300">

        {/* Header da Sidebar */}
        <div class={`p-4 flex items-center ${isCollapsed() ? 'justify-center' : 'justify-between'} border-b border-border/50`}>
          <Show when={!isCollapsed()}>
            <div class="flex items-center gap-2 overflow-hidden">
              <Logo size="sm" />
              <div class="flex flex-col">
                <span class="font-bold text-primary text-sm tracking-tight leading-none">CAÇULINHA</span>
                <span class="text-[10px] text-muted-foreground uppercase tracking-wider">BI Solution</span>
              </div>
            </div>
          </Show>
          <Show when={isCollapsed()}>
            <Logo size="xs" />
          </Show>

          <Show when={!isCollapsed()}>
            <button
              onClick={() => setIsCollapsed(!isCollapsed())}
              class="p-1.5 rounded-md hover:bg-sidebar-accent text-muted-foreground hover:text-primary transition-colors"
              title="Recolher menu (Ctrl+B)"
            >
              <ChevronLeft size={16} />
            </button>
          </Show>
        </div>

        {/* Navegação Scrollable */}
        <nav class="flex-1 overflow-y-auto overflow-x-hidden py-4 min-h-0 w-full custom-scrollbar">
          <For each={menuItems}>
            {(group) => {
              const visibleItems = group.items.filter(item => item.roles.includes(userRole()) || item.roles.includes('*'));

              return (
                <Show when={visibleItems.length > 0}>
                  <div class="mb-6">
                    <Show when={!isCollapsed()}>
                      <div class="px-5 mb-2 text-[10px] font-bold text-muted-foreground/70 uppercase tracking-widest">
                        {group.group}
                      </div>
                    </Show>
                    <Show when={isCollapsed()}>
                      <div class="h-px w-8 bg-border mx-auto my-3 opacity-50" />
                    </Show>

                    <For each={visibleItems}>
                      {(item) => (
                        <NavItem href={item.href} icon={item.icon} label={item.label} />
                      )}
                    </For>
                  </div>
                </Show>
              );
            }}
          </For>
        </nav>

        {/* Footer da Sidebar */}
        <div class="p-3 border-t border-border mt-auto flex flex-col gap-1">
          <Show when={isCollapsed()}>
            <button
              onClick={() => setIsCollapsed(!isCollapsed())}
              class="w-full flex justify-center p-2 rounded-md hover:bg-sidebar-accent text-muted-foreground hover:text-primary transition-colors mb-2"
              title="Expandir menu"
            >
              <ChevronRight size={20} />
            </button>
          </Show>

          <button onClick={auth.logout}
            class={`flex items-center gap-3 px-3 py-2 rounded-md text-destructive/80 hover:text-destructive hover:bg-destructive/10 transition-colors w-full
                ${isCollapsed() ? 'justify-center' : ''}`}
            title="Sair do Sistema"
          >
            <LogOut size={20} />
            <Show when={!isCollapsed()}>
              <span class="text-sm font-medium">Sair</span>
            </Show>
          </button>

          <Show when={!isCollapsed()}>
            <div class="mt-2 px-2 flex items-center justify-between text-[10px] text-muted-foreground/50">
              <span>v3.1.0</span>
              <span>Context7 Ultimate</span>
            </div>
          </Show>
        </div>
      </aside>

      {/* Main Content Area */}
      <div class="flex flex-col h-full min-h-0 overflow-hidden w-full relative">
        <header class="header h-14 border-b border-border bg-background/95 backdrop-blur flex items-center justify-between px-6 z-10 shrink-0">
          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <Show when={isCollapsed()}>
              <button onClick={() => setIsCollapsed(false)} class="md:hidden mr-2">
                {/* Mobile toggle logic could go here */}
              </button>
            </Show>
            <span>Organização</span>
            <span class="text-border">/</span>
            <span class="text-foreground font-medium capitalize">{location.pathname.replace('/', '') || 'Dashboard'}</span>
          </div>

          <div class="flex items-center gap-4">
            <div class="text-right hidden md:block leading-tight">
              <div class="text-sm font-medium text-foreground">{auth.user()?.username || 'Usuário'}</div>
              <div class="text-[10px] text-muted-foreground capitalize">{userRole()}</div>
            </div>
            <div class="w-8 h-8 bg-primary/10 border border-primary/20 rounded-full flex items-center justify-center font-bold text-primary text-xs uppercase">
              {(auth.user()?.username || 'U').slice(0, 2).toUpperCase()}
            </div>
          </div>
        </header>

        <main class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden relative bg-muted/20 w-full p-6">
          <ErrorBoundary>
            {props.children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}