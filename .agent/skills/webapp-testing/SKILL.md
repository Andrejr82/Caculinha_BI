---
name: webapp-testing
description: Princípios de teste de aplicações web. E2E, Playwright, estratégias de auditoria profunda.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Teste de Web App

> Descubra e teste tudo. Não deixe nenhuma rota sem teste.

---

## 🔧 Scripts de Execução

**Execute estes para testes de navegador automatizados:**

| Script | Propósito | Uso |
|--------|-----------|-----|
| `scripts/playwright_runner.py` | Teste de navegador básico | `python scripts/playwright_runner.py https://exemplo.com` |
| | Com screenshot | `python scripts/playwright_runner.py <url> --screenshot` |
| | Verificação de acessibilidade | `python scripts/playwright_runner.py <url> --a11y` |

**Requer:** `pip install playwright && playwright install chromium`

---

## 1. Abordagem de Auditoria Profunda

### Descoberta Primeiro

| Alvo | Como encontrar |
|------|----------------|
| Rotas | Escanear arquivos em app/, pages/, router |
| Endpoints de API | Buscar (grep) por métodos HTTP |
| Componentes | Encontrar diretórios de componentes |
| Recursos (Features) | Ler a documentação |

### Teste Sistemático

1. **Mapear** - Listar todas as rotas/APIs
2. **Escanear** - Verificar se elas respondem
3. **Testar** - Cobrir caminhos críticos

---

## 2. Pirâmide de Testes para Web

```
        /\          E2E (Poucos)
       /  \         Fluxos críticos do usuário
      /----\
     /      \       Integração (Alguns)
    /--------\      API, fluxo de dados
   /          \
  /------------\    Componente (Muitos)
                    Peças de UI individuais
```

---

## 3. Princípios de Teste E2E

### O que Testar

| Prioridade | Testes |
|------------|--------|
| 1 | Fluxos de usuário do caminho feliz |
| 2 | Fluxos de autenticação |
| 3 | Ações críticas de negócio |
| 4 | Tratamento de erros |

### Melhores Práticas de E2E

| Prática | Por que |
|---------|---------|
| Usar data-testid | Seletores estáveis |
| Esperar por elementos | Evitar testes instáveis (flaky) |
| Estado limpo | Testes independentes |
| Evitar detalhes de implementação | Testar o comportamento do usuário |

---

## 4. Princípios de Playwright

### Conceitos Core

| Conceito | Uso |
|----------|-----|
| Page Object Model | Encapsular lógica da página |
| Fixtures | Configuração de teste reutilizável |
| Assertions | Auto-espera (auto-wait) integrada |
| Trace Viewer | Depurar falhas |

### Configuração

| Configuração | Recomendação |
|--------------|--------------|
| Retentativas (Retries) | 2 no CI |
| Trace | on-first-retry |
| Screenshots | on-failure |
| Vídeo | retain-on-failure |

---

## 5. Testes Visuais

### Quando Usar

| Cenário | Valor |
|---------|-------|
| Sistema de design | Alto |
| Páginas de marketing | Alto |
| Biblioteca de componentes | Médio |
| Conteúdo dinâmico | Baixo |

### Estratégia

- Screenshots de linha de base (baseline)
- Comparar nas mudanças
- Revisar diferenças visuais
- Atualizar mudanças intencionais

---

## 6. Princípios de Teste de API

### Áreas de Cobertura

| Área | Testes |
|------|--------|
| Códigos de status | 200, 400, 404, 500 |
| Formato da resposta | Corresponde ao schema |
| Mensagens de erro | Amigáveis ao usuário |
| Casos de borda | Vazio, grande, caracteres especiais |

---

## 7. Organização de Testes

### Estrutura de Arquivos

```
tests/
├── e2e/           # Fluxos de usuário completos
├── integration/   # API, dados
├── component/     # Unidades de UI
└── fixtures/      # Dados compartilhados
```

### Convenção de Nomenclatura

| Padrão | Exemplo |
|--------|---------|
| Baseado em feature | `login.spec.ts` |
| Descritivo | `user-can-checkout.spec.ts` |

---

## 8. Integração com CI

### Passos do Pipeline

1. Instalar dependências
2. Instalar navegadores
3. Executar testes
4. Fazer upload de artefatos (traces, screenshots)

### Paralelização

| Estratégia | Uso |
|------------|-----|
| Por arquivo | Playwright default |
| Fragmentação (Sharding)| Suítes grandes |
| Workers | Múltiplos navegadores |

---

## 9. Anti-Padrões

| ❌ Não faça | ✅ Faça |
|-------------|---------|
| Testar implementação | Testar comportamento |
| Esperas fixas (hardcode) | Use auto-espera |
| Pular a limpeza | Isole os testes |
| Ignorar testes instáveis | Corrigir a causa raiz |

---

> **Lembre-se:** Testes E2E são caros. Use-os apenas para caminhos críticos.
