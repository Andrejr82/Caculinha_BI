/* src/index.tsx - Versão ULTRA SIMPLIFICADA sem verificação de versão */
import { render } from 'solid-js/web';
import { Router, Route, Navigate } from '@solidjs/router';
import { Show, lazy, Suspense } from 'solid-js';
import { QueryClient, QueryClientProvider } from '@tanstack/solid-query';
import './index.css';

// ✅ PERFORMANCE: Eager imports (rotas públicas - carregadas imediatamente)
import Layout from './Layout';
import Login from './pages/Login';
import SharedConversation from './pages/SharedConversation';

// ✅ PERFORMANCE: Lazy imports (code splitting - carregadas sob demanda)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DashboardV2 = lazy(() => import('./pages/DashboardV2'));
const Chat = lazy(() => import('./pages/Chat'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Reports = lazy(() => import('./pages/Reports'));
const Learning = lazy(() => import('./pages/Learning'));
const Playground = lazy(() => import('./pages/Playground'));
const Profile = lazy(() => import('./pages/Profile'));
const Admin = lazy(() => import('./pages/Admin'));
const Rupturas = lazy(() => import('./pages/Rupturas'));
const Transfers = lazy(() => import('./pages/Transfers'));
const Diagnostics = lazy(() => import('./pages/Diagnostics'));
const Examples = lazy(() => import('./pages/Examples'));
const Help = lazy(() => import('./pages/Help'));
const CodeChat = lazy(() => import('./pages/CodeChat'));
const About = lazy(() => import('./pages/About'));

// ✅ NEW 2026-01-22: Advanced Dashboards
const Forecasting = lazy(() => import('./pages/Forecasting'));
const Executive = lazy(() => import('./pages/Executive'));
const Suppliers = lazy(() => import('./pages/Suppliers'));

// ✅ NEW 2026-02-08: Admin-Only Pages
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const AdminEvaluations = lazy(() => import('./pages/AdminEvaluations'));

// Importar Store de Autenticação
import auth from './store/auth';

// ✅ USABILIDADE: Toast Notifications & Confirm Dialogs
import { ToastContainer } from './components/Toast';
import { ConfirmDialogContainer } from './components/ConfirmDialog';

// ✅ ACESSIBILIDADE: Screen Reader Announcer
import { ScreenReaderAnnouncer } from './components/ScreenReaderAnnouncer';

console.log('✅ All imports loaded successfully');

// Componente de Proteção de Rotas
// ✅ PERFORMANCE: Adiciona Suspense para lazy loading
function PrivateRoute(props: { component: any }) {
  return (
    <Show
      when={auth.isAuthenticated()}
      fallback={<Navigate href="/login" />}
    >
      <Suspense fallback={<PageLoader />}>
        {props.component}
      </Suspense>
    </Show>
  );
}

// Componente de Proteção de Rotas com RBAC
// 🔧 FIX: Admin SEMPRE tem acesso total a todas as rotas
// ✅ PERFORMANCE: Adiciona Suspense para lazy loading
function RoleRoute(props: { component: any; requiredRole: string }) {
  return (
    <Show
      when={auth.isAuthenticated()}
      fallback={<Navigate href="/login" />}
    >
      <Show
        when={
          auth.user()?.role === 'admin' ||
          auth.user()?.role === props.requiredRole ||
          auth.user()?.allowed_segments?.includes('*')
        }
        fallback={
          <div class="flex items-center justify-center min-h-screen flex-col gap-4 p-8">
            <h1 class="text-4xl font-bold text-destructive">Acesso Negado</h1>
            <p class="text-lg text-muted-foreground">Você não tem permissão para acessar esta página.</p>
            <p class="text-sm text-muted-foreground">403 - Forbidden</p>
            <p class="text-xs text-muted mt-4">Role: {auth.user()?.role || 'desconhecido'}</p>
          </div>
        }
      >
        <Suspense fallback={<PageLoader />}>
          {props.component}
        </Suspense>
      </Show>
    </Show>
  );
}

// ✅ PERFORMANCE: Loading component para lazy routes
function PageLoader() {
  return (
    <div class="flex items-center justify-center min-h-screen">
      <div class="flex flex-col items-center gap-4">
        <div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p class="text-sm text-muted-foreground">Carregando...</p>
      </div>
    </div>
  );
}

// Componente Principal da Aplicação
function App() {
  console.log('✅ App component created');
  return (
    <Router>
      {/* Rotas Públicas */}
      <Route path="/login" component={Login} />
      <Route path="/shared/:share_id" component={SharedConversation} />

      {/* Rota raiz - redireciona baseado em autenticação */}
      <Route path="/" component={() => {
        return (
          <Show
            when={auth.isAuthenticated()}
            fallback={<Navigate href="/login" />}
          >
            <Navigate href="/dashboard" />
          </Show>
        );
      }} />

      {/* Rotas Protegidas - Dentro do Layout */}
      <Route path="/" component={Layout}>
        <Route path="/dashboard" component={() => <PrivateRoute component={<Dashboard />} />} />
        <Route path="/dashboard-v2" component={() => <PrivateRoute component={<DashboardV2 />} />} />
        <Route path="/metrics" component={() => <RoleRoute component={<Analytics />} requiredRole="admin" />} />
        <Route path="/rupturas" component={() => <PrivateRoute component={<Rupturas />} />} />
        <Route path="/transfers" component={() => <PrivateRoute component={<Transfers />} />} />
        <Route path="/reports" component={() => <RoleRoute component={<Reports />} requiredRole="admin" />} />
        <Route path="/chat" component={() => <PrivateRoute component={<Chat />} />} />
        <Route path="/examples" component={() => <RoleRoute component={<Examples />} requiredRole="admin" />} />
        <Route path="/learning" component={() => <RoleRoute component={<Learning />} requiredRole="admin" />} />
        <Route path="/playground" component={() => <RoleRoute component={<Playground />} requiredRole="admin" />} />
        <Route path="/code-chat" component={() => <RoleRoute component={<CodeChat />} requiredRole="admin" />} />
        <Route path="/diagnostics" component={() => <RoleRoute component={<Diagnostics />} requiredRole="admin" />} />
        <Route path="/help" component={() => <PrivateRoute component={<Help />} />} />
        <Route path="/about" component={() => <PrivateRoute component={<About />} />} />
        <Route path="/profile" component={() => <PrivateRoute component={<Profile />} />} />
        <Route path="/admin" component={() => <RoleRoute component={<Admin />} requiredRole="admin" />} />

        {/* ✅ NEW 2026-01-22: Advanced Dashboards */}
        <Route path="/forecasting" component={() => <PrivateRoute component={<Forecasting />} />} />
        <Route path="/executive" component={() => <PrivateRoute component={<Executive />} />} />
        <Route path="/suppliers" component={() => <PrivateRoute component={<Suppliers />} />} />

        {/* ✅ NEW 2026-02-08: Admin-Only Dashboard & Evaluations */}
        <Route path="/admin/dashboard" component={() => <RoleRoute component={<AdminDashboard />} requiredRole="admin" />} />
        <Route path="/admin/evaluations" component={() => <RoleRoute component={<AdminEvaluations />} requiredRole="admin" />} />
      </Route>

      {/* Fallback */}
      <Route path="*" component={() => (
        <Show
          when={auth.isAuthenticated()}
          fallback={<Navigate href="/login" />}
        >
          <Navigate href="/dashboard" />
        </Show>
      )} />
    </Router>
  );
}

// Renderizar a Aplicação no DOM
const root = document.getElementById('root');

if (!root) {
  console.error('❌ ROOT ELEMENT NOT FOUND!');
  throw new Error('Root element not found');
}

console.log('✅ Root element found:', root);

// Create QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

console.log('✅ QueryClient created');

// Render app
try {
  render(() => (
    <QueryClientProvider client={queryClient}>
      <App />
      {/* ✅ USABILIDADE: Global UI Components */}
      <ToastContainer />
      <ConfirmDialogContainer />
      {/* ✅ ACESSIBILIDADE: Screen Reader Announcer */}
      <ScreenReaderAnnouncer />
    </QueryClientProvider>
  ), root);
  console.log('✅ App rendered successfully!');
} catch (error) {
  console.error('❌ Error rendering app:', error);
  document.body.innerHTML = `
    <div style="padding: 20px; color: white; background: #1a1a1a; font-family: sans-serif;">
      <h1 style="color: #ef4444;">❌ Erro ao Renderizar Aplicação</h1>
      <pre style="background: #2a2a2a; padding: 10px; border-radius: 5px; overflow: auto;">${error}</pre>
      <p>Verifique o console do navegador (F12) para mais detalhes.</p>
    </div>
  `;
}