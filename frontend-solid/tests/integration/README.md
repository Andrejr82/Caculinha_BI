# Testes de Integração E2E - Agent BI

Este diretório contém os testes de integração end-to-end usando Playwright.

## 📋 Estrutura

```
tests/integration/
├── setup.ts              # Fixtures e configuração
├── auth.spec.ts          # Testes de autenticação
├── pages.spec.ts         # Testes de páginas
├── performance.spec.ts   # Testes de performance
└── README.md            # Este arquivo
```

## 🚀 Executar Testes

### Pré-requisitos
```bash
# Instalar Playwright
bun install
bunx playwright install
```

### Comandos

```bash
# Executar todos os testes
bunx playwright test

# Executar com UI interativa
bunx playwright test --ui

# Executar testes específicos
bunx playwright test auth.spec.ts

# Executar em modo debug
bunx playwright test --debug

# Ver relatório
bunx playwright show-report
```

## 📊 Cobertura de Testes

### Autenticação (4 testes)
- ✅ Login com credenciais válidas
- ✅ Login com credenciais inválidas
- ✅ Logout
- ✅ Redirecionamento quando não autenticado

### Páginas Usuário (7 testes)
- ✅ Dashboard
- ✅ Chat
- ✅ Rupturas
- ✅ Transfers
- ✅ Profile
- ✅ Help
- ✅ About

### Páginas Admin (4 testes)
- ✅ Metrics (Analytics)
- ✅ Reports
- ✅ Admin
- ✅ Diagnostics

### Performance (3 testes)
- ✅ Tempo de carregamento Dashboard
- ✅ Tempo de carregamento Chat
- ✅ Erros de console

**Total:** 18 testes

## 📸 Screenshots

Screenshots são salvos em `test-results/screenshots/` para cada página testada.

## 📄 Relatórios

Relatórios HTML são gerados em `test-results/html-report/`.

## ⚙️ Configuração

A configuração está em `playwright.config.ts` na raiz do projeto frontend.

## 🔐 Credenciais de Teste

**IMPORTANTE:** Use apenas credenciais de teste, nunca produção!

- Usuário: `teste@cacularetail.com.br` / `Teste@123`
- Admin: `admin@cacularetail.com.br` / `Admin@123`

## 🐛 Troubleshooting

### Testes falhando
1. Verificar se o servidor está rodando (`bun run dev`)
2. Verificar credenciais de teste
3. Reinstalar navegadores do Playwright: `bunx playwright install --force`

### Timeout
- Aumentar timeout em `playwright.config.ts`
- Verificar performance do servidor

---

**Última Atualização:** 2026-01-17
