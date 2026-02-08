# Análise de Scripts de Inicialização (`RUN_NATIVE_ALL`)

**Data:** 2026-02-08
**Solicitante:** Usuário (via Agentes Especialistas)
**Arquivos Analisados:** `RUN_NATIVE_ALL.bat`, `RUN_NATIVE_ALL.ps1`

---

## 1. 🐞 Relatório do Debugger (Análise de Causa Raiz)

> "Causas de instabilidade e 'borked state'."

*   **Sobrescrita Silenciosa de Configuração (CRÍTICO):**
    *   O script define hardcoded `$env:DATABASE_URL = "sqlite:///backend/data/memory.db"`.
    *   **Consequência:** Isso ignora completamente o arquivo `.env`. Se você configurar SQL Server no `.env`, este script **sobrescreve** silenciosamente para SQLite a cada execução.
    *   **Veredito:** Fonte de bugs "funciona no backend, falha no boot completo".

*   **Race Condition (Condição de Corrida):**
    *   O script espera `Start-Sleep -Seconds 5` antes de abrir o navegador.
    *   **Consequência:** Em máquinas mais lentas ou na primeira execução (compilação Vite), o navegador abre antes do servidor estar pronto (Tela "Não foi possível conectar").
    *   **Correção:** Implementar "Wait-For-Port" (polling).

*   **Redundância de Dependências:**
    *   Reexecuta `pip install` a cada boot.
    *   **Consequência:** Lento e desnecessário. Deve delegar para o `bootstrap_backend.ps1` que usa `pip-sync` inteligente.

---

## 2. 🏺 Relatório do Code Archaeologist (Dívida Técnica)

> "Padrões legados e código zumbi."

*   **Artefato Fóssil (SQLite):**
    *   A string `memory.db` é um resquício de protótipos anteriores. O sistema atual (Context7) usa DuckDB (`metrics.duckdb`) e SQL Server.
    *   **Ação:** Remover. O sistema deve respeitar o `.env` ou defaults do `settings.py`.

*   **Inicialização Frontend "Force Brute":**
    *   Executa `npm install` incondicionalmente.
    *   **Consequência:** Desperdiça 10-30s em cada startup.
    *   **Modernização:** Verificar existência de `node_modules` e rodar instalação apenas se necessário.

---

## 3. 🏗 Relatório do Database Architect (Integridade)

> "Consistência de dados e conexão."

*   **Split-Brain de Dados:**
    *   Ao forçar uma URL de banco diferente do `.env`, o script cria dois ambientes de dados: um quando roda via script, outro quando roda via depurador/IDE.
    *   **Risco:** Dados gravados durante teste manual não aparecem quando roda o script oficial.

*   **Violação de Contrato de Serviço:**
    *   O `AuthService` espera conexões persistentes ou Parquet. O override para SQLite em memória pode quebrar a persistência de usuários se o Adapter SQL Server tentar escrever lá.

---

## ✅ Plano de Solução Definitiva ("Solve De Vez")

1.  **Unificação:** Refatorar `RUN_NATIVE_ALL.ps1` para chamar `scripts/bootstrap_backend.ps1`.
2.  **Limpeza:** Remover TODAS as definições de variáveis de ambiente (`$env:...`). O script deve confiar no `.env`.
3.  **Performance:**
    *   Backend: Confiar no `bootstrap` (Check rápido).
    *   Frontend: Pular `npm install` se instalado.
4.  **Robustez:** Adicionar verificação de porta 3000/8000 antes de abrir navegador.
