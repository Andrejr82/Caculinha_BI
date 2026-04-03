import { createSignal, Show } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import auth from '@/store/auth';
import { LogIn, Loader2 } from 'lucide-solid';
import { Logo } from '@/components/Logo';
import { toastManager } from '@/components/Toast';

export default function Login() {
  const [email, setEmail] = createSignal('');
  const [password, setPassword] = createSignal('');
  const [showForgotModal, setShowForgotModal] = createSignal(false);
  const navigate = useNavigate();

  // Helpers
  const loading = () => auth.loading();
  const error = () => auth.error();

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const inputEmail = email().trim();
    const inputPassword = password();

    if (!inputEmail || !inputPassword) {
      toastManager.warning('Por favor, preencha email e senha');
      return;
    }

    // Auto-convert username to email if no '@' present
    let finalEmail = inputEmail;
    if (!inputEmail.includes('@')) {
      finalEmail = `${inputEmail}@agentbi.com`;
    }

    // Validate email format
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(finalEmail)) {
      toastManager.warning('Por favor, digite um email válido');
      return;
    }

    try {
      const success = await auth.login(finalEmail, inputPassword);

      if (success) {
        toastManager.success('Login realizado com sucesso!');
        // ✅ CORREÇÃO: Usar navigate() do SolidJS Router para manter SPA behavior
        setTimeout(() => navigate('/dashboard', { replace: true }), 500);
      } else {
        toastManager.error('Email ou senha inválidos');
      }
    } catch (error) {
      console.error('Login error:', error);
      toastManager.error('Erro ao fazer login. Tente novamente.');
    }
  };

  return (
    <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 via-orange-50 to-stone-100 p-4">
      {/* Background Effects - Lojas Caçula (warm tones) */}
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s"></div>
      </div>

      {/* Login Card - Lojas Caçula */}
      <div class="relative w-full max-w-md">
        <div class="bg-white/95 backdrop-blur-xl border-2 border-primary/20 rounded-2xl shadow-2xl p-8 space-y-6">
          {/* Header */}
          <div class="text-center space-y-4">
            <div class="flex justify-center mb-4">
              <Logo size="xl" className="filter drop-shadow-lg" />
            </div>
            <div class="space-y-2">
              <h1 class="text-3xl font-bold text-primary">
                CAÇULINHA BI
              </h1>
              <p class="text-sm text-muted-foreground">
                Entre com seu email para acessar seus dados analíticos
              </p>
            </div>
          </div>

          {/* Error Message */}
          <Show when={auth.error()}>
            <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
              <svg class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div class="flex-1">
                <p class="text-sm text-red-200 font-medium">Erro de Autenticação</p>
                <p class="text-xs text-red-300/80 mt-1">{auth.error()}</p>
              </div>
            </div>
          </Show>

          {/* Form */}
          <form onSubmit={handleSubmit} class="space-y-4" aria-label="Formulário de login">
            {/* Email Field */}
            <div class="space-y-2">
              <label for="email" class="block text-sm font-medium text-foreground">
                Email
              </label>
              <input
                id="email"
                type="text"
                value={email()}
                onInput={(e) => setEmail(e.currentTarget.value)}
                placeholder="Digite seu email ou usuário"
                required
                autocomplete="username"
                aria-label="Email"
                aria-required="true"
                aria-invalid={auth.error() ? 'true' : 'false'}
                class="w-full px-4 py-3 bg-white border-2 border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
            </div>

            {/* Password Field */}
            <div class="space-y-2">
              <label for="password" class="block text-sm font-medium text-foreground">
                Senha
              </label>
              <input
                id="password"
                type="password"
                value={password()}
                onInput={(e) => setPassword(e.currentTarget.value)}
                placeholder="Digite sua senha"
                required
                autocomplete="current-password"
                aria-label="Senha"
                aria-required="true"
                aria-invalid={error() ? 'true' : 'false'}
                class="w-full px-4 py-3 bg-white border-2 border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
              <div class="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowForgotModal(true)}
                  class="text-xs text-primary hover:text-primary/80 hover:underline transition-colors"
                >
                  Esqueci minha senha
                </button>
              </div>
            </div>

            {/* Submit Button - Lojas Caçula */}
            <button
              type="submit"
              disabled={loading()}
              aria-label={loading() ? 'Entrando no sistema' : 'Entrar no sistema'}
              aria-busy={loading()}
              class="w-full py-3 px-4 bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 text-white font-semibold rounded-lg shadow-lg shadow-primary/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Show when={loading()} fallback={<>Entrar</>}>
                <Loader2 size={20} class="animate-spin" />
                <span>Entrando...</span>
              </Show>
            </button>
          </form>
        </div>

        {/* Version Info - Lojas Caçula */}
        <div class="text-center mt-6 space-y-2">
          <div class="flex justify-center">
            <Logo size="sm" className="opacity-60" />
          </div>
          <div class="text-xs text-muted-foreground">
            Caçulinha BI v1.0.0 • Powered by SolidJS
          </div>
        </div>
      </div>

      {/* Forgot Password Modal */}
      <Show when={showForgotModal()}>
        <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div class="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4 animate-in zoom-in-95 duration-200">
            <div class="text-center space-y-2">
              <div class="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
              </div>
              <h3 class="text-lg font-semibold text-gray-900">Recuperar Senha</h3>
              <p class="text-sm text-gray-500">
                Por questões de segurança, a redefinição de senha deve ser solicitada à equipe de TI.
              </p>
            </div>

            <div class="bg-muted/50 p-3 rounded-lg text-sm text-center border space-y-1">
              <p class="font-medium text-foreground">Entre em contato:</p>
              <p class="text-muted-foreground">suporte@cacula.com.br</p>
              <p class="text-muted-foreground text-xs">(21) 9999-9999 (Ramal TI)</p>
            </div>

            <button
              onClick={() => setShowForgotModal(false)}
              class="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors"
            >
              Entendi
            </button>
          </div>
        </div>
      </Show>
    </div>
  );
}
