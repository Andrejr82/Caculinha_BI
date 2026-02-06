import { createSignal, createResource, For, Show } from 'solid-js';
import auth from '@/store/auth';

interface PreferenceKey {
  key: string;
  description: string;
  options?: string[];
  type?: string;
  default?: string;
}

export function UserPreferences() {
  const [saving, setSaving] = createSignal(false);
  const [message, setMessage] = createSignal('');
  const [preferences, setPreferences] = createSignal<Record<string, string>>({});

  // Fetch common keys
  const [commonKeys] = createResource(async () => {
    const response = await fetch('/api/v1/preferences/common/keys');
    const data = await response.json();
    return data.keys as PreferenceKey[];
  });

  // Fetch user preferences
  const [userPrefs, { refetch }] = createResource(async () => {
    const token = auth.token();
    if (!token) return { preferences: {} };

    const response = await fetch('/api/v1/preferences', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setPreferences(data.preferences || {});
    return data;
  });

  const savePreferences = async () => {
    const token = auth.token();
    if (!token) return;

    setSaving(true);
    setMessage('');

    try {
      const response = await fetch('/api/v1/preferences/batch', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(preferences())
      });

      if (!response.ok) {
        throw new Error('Falha ao salvar preferências');
      }

      setMessage('✓ Preferências salvas com sucesso!');
      setTimeout(() => setMessage(''), 3000);
      refetch();
    } catch (err) {
      console.error('Error saving preferences:', err);
      setMessage('✗ Erro ao salvar preferências');
    } finally {
      setSaving(false);
    }
  };

  const updatePreference = (key: string, value: string) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div class="space-y-6">
      <div>
        <h3 class="text-lg font-semibold mb-2">Preferências do Usuário</h3>
        <p class="text-sm text-muted-foreground">
          Configure suas preferências para personalizar sua experiência no Chat BI.
        </p>
      </div>

      <Show when={!commonKeys.loading} fallback={<div>Carregando...</div>}>
        <div class="space-y-4">
          <For each={commonKeys()}>
            {(prefKey) => (
              <div class="space-y-2">
                <label class="block text-sm font-medium">
                  {prefKey.description}
                </label>
                <Show
                  when={prefKey.options}
                  fallback={
                    <input
                      type="text"
                      class="input w-full"
                      value={preferences()[prefKey.key] || ''}
                      onInput={(e) => updatePreference(prefKey.key, e.currentTarget.value)}
                      placeholder={`Digite ${prefKey.description.toLowerCase()}`}
                    />
                  }
                >
                  <select
                    class="input w-full"
                    value={preferences()[prefKey.key] || prefKey.default || ''}
                    onChange={(e) => updatePreference(prefKey.key, e.currentTarget.value)}
                  >
                    <option value="">Selecione...</option>
                    <For each={prefKey.options}>
                      {(option) => <option value={option}>{option}</option>}
                    </For>
                  </select>
                </Show>
              </div>
            )}
          </For>
        </div>

        <div class="flex items-center gap-4 pt-4">
          <button
            onClick={savePreferences}
            disabled={saving()}
            class="btn btn-primary"
          >
            {saving() ? 'Salvando...' : 'Salvar Preferências'}
          </button>

          <Show when={message()}>
            <span class={`text-sm ${message().startsWith('✓') ? 'text-green-500' : 'text-red-500'}`}>
              {message()}
            </span>
          </Show>
        </div>
      </Show>
    </div>
  );
}
