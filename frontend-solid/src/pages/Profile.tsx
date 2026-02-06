import { createSignal, createMemo, Show } from 'solid-js';
import { Lock, CheckCircle, AlertCircle, Shield, Info } from 'lucide-solid';
import auth from '@/store/auth';
import { UserPreferences } from '@/components/UserPreferences';

interface PasswordStrength {
  score: number; // 0-4
  label: string;
  color: string;
  barColor: string;
}

export default function Profile() {
  const [currentPass, setCurrentPass] = createSignal('');
  const [newPass, setNewPass] = createSignal('');
  const [confirmPass, setConfirmPass] = createSignal('');
  const [message, setMessage] = createSignal<{ type: 'success' | 'error', text: string } | null>(null);

  // Validação de requisitos de senha
  const passwordRequirements = createMemo(() => {
    const pass = newPass();
    return {
      length: pass.length >= 8,
      uppercase: /[A-Z]/.test(pass),
      lowercase: /[a-z]/.test(pass),
      number: /\d/.test(pass),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(pass),
    };
  });

  // Calcular força da senha
  const passwordStrength = createMemo((): PasswordStrength => {
    const reqs = passwordRequirements();
    const pass = newPass();

    if (!pass) {
      return { score: 0, label: 'Nenhuma', color: 'text-gray-500', barColor: 'bg-gray-500' };
    }

    const score = [reqs.length, reqs.uppercase, reqs.lowercase, reqs.number, reqs.special].filter(Boolean).length;

    if (score === 5) {
      return { score: 4, label: 'Muito Forte', color: 'text-green-500', barColor: 'bg-green-500' };
    }
    if (score === 4) {
      return { score: 3, label: 'Forte', color: 'text-blue-500', barColor: 'bg-blue-500' };
    }
    if (score === 3) {
      return { score: 2, label: 'Média', color: 'text-yellow-500', barColor: 'bg-yellow-500' };
    }
    if (score >= 1) {
      return { score: 1, label: 'Fraca', color: 'text-orange-500', barColor: 'bg-orange-500' };
    }

    return { score: 0, label: 'Muito Fraca', color: 'text-red-500', barColor: 'bg-red-500' };
  });

  const isPasswordValid = createMemo(() => {
    const reqs = passwordRequirements();
    return reqs.length && reqs.uppercase && reqs.lowercase && reqs.number && reqs.special;
  });

  const handleChangePassword = async (e: Event) => {
    e.preventDefault();

    if (newPass() !== confirmPass()) {
      setMessage({ type: 'error', text: 'As senhas não coincidem.' });
      return;
    }

    if (!isPasswordValid()) {
      setMessage({ type: 'error', text: 'A senha não atende aos requisitos mínimos de segurança.' });
      return;
    }

    try {
      const token = auth.token();
      if (!token) {
        setMessage({ type: 'error', text: 'Você precisa estar logado.' });
        return;
      }

      const formData = new FormData();
      formData.append('old_password', currentPass());
      formData.append('new_password', newPass());
      
      const response = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao alterar senha');
      }
      
      setMessage({ type: 'success', text: 'Senha alterada com sucesso! Você será deslogado em 3 segundos...' });
      setCurrentPass('');
      setNewPass('');
      setConfirmPass('');

      // Logout automático após 3 segundos
      setTimeout(() => {
        auth.logout();
        window.location.href = '/login';
      }, 3000);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Erro ao alterar senha' });
    }
  };

  return (
    <div class="p-6 max-w-3xl mx-auto">
      <h2 class="text-2xl font-bold mb-6 flex items-center gap-2">
        <Lock /> Perfil e Segurança
      </h2>

      <div class="card border p-6 space-y-6">
        <div>
          <h3 class="text-lg font-medium">Dados do Usuário</h3>
          <div class="mt-4 grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs text-muted">Nome de Usuário</label>
              <div class="font-medium">{auth.user()?.username}</div>
            </div>
            <div>
              <label class="text-xs text-muted">Função (Role)</label>
              <div class="font-medium capitalize">{auth.user()?.role}</div>
            </div>
            <div class="col-span-2">
              <label class="text-xs text-muted">Segmentos Permitidos</label>
              <div class="font-mono text-xs bg-secondary p-2 rounded mt-1">
                {JSON.stringify(auth.user()?.allowed_segments || [], null, 2)}
              </div>
            </div>
          </div>
        </div>

        <hr class="border-border" />

        <form onSubmit={handleChangePassword} class="space-y-4">
          <h3 class="text-lg font-medium">Alterar Senha</h3>

          {message() && (
            <div class={`p-3 rounded text-sm flex items-center gap-2 ${
              message()?.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
            }`}>
              {message()?.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              {message()?.text}
            </div>
          )}

          <div>
            <label class="label">Senha Atual</label>
            <input type="password" class="input" value={currentPass()} onInput={(e) => setCurrentPass(e.currentTarget.value)} required />
          </div>

          <div>
            <label class="label">Nova Senha</label>
            <input type="password" class="input" value={newPass()} onInput={(e) => setNewPass(e.currentTarget.value)} required />

            {/* Indicador de Força da Senha */}
            <Show when={newPass()}>
              <div class="mt-2">
                <div class="flex justify-between items-center mb-1">
                  <span class="text-xs text-muted-foreground">Força da senha:</span>
                  <span class={`text-xs font-medium ${passwordStrength().color}`}>
                    {passwordStrength().label}
                  </span>
                </div>
                <div class="w-full bg-gray-700 rounded-full h-2">
                  <div
                    class={`h-2 rounded-full transition-all ${passwordStrength().barColor}`}
                    style={`width: ${(passwordStrength().score / 4) * 100}%`}
                  />
                </div>
              </div>
            </Show>

            {/* Requisitos de Senha */}
            <Show when={newPass()}>
              <div class="mt-3 space-y-1">
                <p class="text-xs text-muted-foreground font-medium mb-2">Requisitos:</p>
                <div class={`text-xs flex items-center gap-2 ${passwordRequirements().length ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {passwordRequirements().length ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  Mínimo de 8 caracteres
                </div>
                <div class={`text-xs flex items-center gap-2 ${passwordRequirements().uppercase ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {passwordRequirements().uppercase ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  Letra maiúscula (A-Z)
                </div>
                <div class={`text-xs flex items-center gap-2 ${passwordRequirements().lowercase ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {passwordRequirements().lowercase ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  Letra minúscula (a-z)
                </div>
                <div class={`text-xs flex items-center gap-2 ${passwordRequirements().number ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {passwordRequirements().number ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  Número (0-9)
                </div>
                <div class={`text-xs flex items-center gap-2 ${passwordRequirements().special ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {passwordRequirements().special ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  Caractere especial (!@#$%^&*...)
                </div>
              </div>
            </Show>
          </div>

          <div>
            <label class="label">Confirmar Nova Senha</label>
            <input type="password" class="input" value={confirmPass()} onInput={(e) => setConfirmPass(e.currentTarget.value)} required />
            <Show when={confirmPass() && newPass() !== confirmPass()}>
              <p class="text-xs text-red-500 mt-1 flex items-center gap-1">
                <AlertCircle size={12} />
                As senhas não coincidem
              </p>
            </Show>
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            disabled={!isPasswordValid() || newPass() !== confirmPass()}
          >
            Salvar Nova Senha
          </button>
        </form>

        {/* Dicas de Segurança */}
        <div class="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
          <h4 class="font-semibold text-blue-500 mb-2 flex items-center gap-2">
            <Shield size={18} />
            Dicas de Segurança
          </h4>
          <ul class="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>Nunca compartilhe sua senha com outras pessoas</li>
            <li>Use senhas diferentes para cada sistema</li>
            <li>Evite senhas óbvias como datas de nascimento</li>
            <li>Considere usar um gerenciador de senhas</li>
            <li>Troque sua senha regularmente (a cada 3-6 meses)</li>
          </ul>
        </div>
      </div>

      {/* User Preferences Section */}
      <div class="card border p-6 mt-6">
        <UserPreferences />
      </div>
    </div>
  );
}
