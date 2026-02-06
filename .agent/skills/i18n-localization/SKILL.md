---
name: i18n-localization
description: Padrões de internacionalização e localização. Detecção de strings estáticas (hardcoded), gerenciamento de traduções, arquivos de locale, suporte a RTL.
allowed-tools: Read, Glob, Grep
---

# i18n & Localização

> Melhores práticas de Internacionalização (i18n) e Localização (L10n).

---

## 1. Conceitos Core

| Termo | Significado |
|-------|-------------|
| **i18n** | Internacionalização - tornar o app traduzível |
| **L10n** | Localização - as traduções reais |
| **Locale** | Idioma + Região (en-US, pt-BR) |
| **RTL** | Idiomas da direita para a esquerda (Árabe, Hebraico) |

---

## 2. Quando Usar i18n

| Tipo de Projeto | i18n Necessário? |
|-----------------|-------------------|
| Web app público | ✅ Sim |
| Produto SaaS | ✅ Sim |
| Ferramenta interna | ⚠️ Talvez |
| App de região única | ⚠️ Considere o futuro |
| Projeto pessoal | ❌ Opcional |

---

## 3. Padrões de Implementação

### React (react-i18next)

```tsx
import { useTranslation } from 'react-i18next';

function BoasVindas() {
  const { t } = useTranslation();
  return <h1>{t('boas_vindas.titulo')}</h1>;
}
```

### Next.js (next-intl)

```tsx
import { useTranslations } from 'next-intl';

export default function Pagina() {
  const t = useTranslations('Home');
  return <h1>{t('titulo')}</h1>;
}
```

### Python (gettext)

```python
from gettext import gettext as _

print(_("Bem-vindo ao nosso aplicativo"))
```

---

## 4. Estrutura de Arquivos

```
locales/
├── en/
│   ├── common.json
│   ├── auth.json
│   └── errors.json
├── pt/
│   ├── common.json
│   ├── auth.json
│   └── errors.json
└── ar/          # RTL
    └── ...
```

---

## 5. Melhores Práticas

### FAÇA ✅

- Use chaves de tradução, não texto bruto (hardcoded)
- Use namespaces para traduções por funcionalidade
- Suporte a pluralização
- Lide com formatos de data/número por localidade
- Planeje suporte para RTL desde o início
- Use o formato de mensagem ICU para strings complexas

### NÃO FAÇA ❌

- Escrever strings estáticas nos componentes
- Concatenar strings traduzidas
- Assumir o comprimento do texto (o Alemão é 30% mais longo que o Inglês)
- Esquecer o layout RTL
- Misturar idiomas no mesmo arquivo

---

## 6. Problemas Comuns

| Problema | Solução |
|----------|---------|
| Tradução ausente | Use o idioma padrão como fallback |
| Strings estáticas (hardcoded) | Use um script de verificação/linter |
| Formato de data | Use Intl.DateTimeFormat |
| Formato de número | Use Intl.NumberFormat |
| Pluralização | Use o formato de mensagem ICU |

---

## 7. Suporte a RTL

```css
/* Propriedades Lógicas de CSS */
.container {
  margin-inline-start: 1rem;  /* Em vez de margin-left */
  padding-inline-end: 1rem;   /* Em vez de padding-right */
}

[dir="rtl"] .icon {
  transform: scaleX(-1);
}
```

---

## 8. Checklist

Antes de entregar:

- [ ] Todas as strings voltadas ao usuário usam chaves de tradução
- [ ] Os arquivos de localidade existem para todos os idiomas suportados
- [ ] A formatação de data/número usa a API Intl
- [ ] Layout RTL testado (se aplicável)
- [ ] Idioma de fallback configurado
- [ ] Sem strings estáticas nos componentes

---

## Script

| Script | Propósito | Comando |
|--------|-----------|---------|
| `scripts/i18n_checker.py` | Detecta strings estáticas e traduções ausentes | `python scripts/i18n_checker.py <caminho_projeto>` |
