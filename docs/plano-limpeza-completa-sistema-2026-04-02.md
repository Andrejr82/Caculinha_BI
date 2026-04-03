# Plano: Limpeza Completa do Sistema

**Gerado**: 2026-04-02
**Escopo**: repositório inteiro `Caculinha_BI`
**Objetivo**: auditar pasta por pasta e arquivo por arquivo, separar código vivo de artefato/local legado, e montar uma lista de remoção somente para autorização manual.

## Resumo Executivo

O repositório mistura quatro categorias no mesmo espaço:

1. código-fonte ativo
2. artefatos gerados localmente
3. dados/runtime/cache
4. documentação histórica e evidências temporárias

Pelos levantamentos iniciais:

- `backend/` concentra volume alto de dados locais e runtime
- `frontend-solid/` carrega `node_modules`, `dist`, relatórios e logs locais
- `data/`, `app/data/` e `backend/data/` contêm caches e sessões locais
- `docs/` mistura documentação ativa, histórico e mockups versionados

O plano abaixo não remove nada automaticamente. Ele organiza a revisão e traz uma primeira lista de candidatos com confiança.

## Inventário Inicial

- Total aproximado de arquivos rastreáveis fora de `node_modules/.git/.venv/dist/build`: `718`
- Pastas com maior volume bruto:
  - `backend/`: `990` arquivos, `~866.77 MB`
  - `frontend-solid/`: `34901` arquivos, `~407.44 MB`
  - `data/`: `112` arquivos, `~13.57 MB`
  - `docs/`: `78` arquivos, `~2.63 MB`
  - `.agent/`: `201` arquivos, `~1.52 MB`

## Critérios de Classificação

### Manter

- código referenciado em runtime, testes, build ou documentação operacional viva
- configurações canônicas do stack atual
- datasets canônicos necessários para rodar localmente ou validar regressão

### Revisar

- arquivos com nomes de histórico, plano, v2/v3/v4, draft, smoke, backup, old, legacy
- cópias de dados em múltiplos caminhos
- lockfiles conflitantes
- documentação redundante com o mesmo assunto

### Candidato à limpeza

- cache, log, build, relatório, screenshot, vídeo, sessão local, artefato de teste
- diretórios já cobertos pelo `.gitignore`
- arquivos sem referência no código e com característica de evidência temporária

## Ordem de Auditoria Pasta por Pasta

### Fase 1. Artefatos gerados e caches

**Objetivo**: reduzir ruído sem risco funcional.

Pastas/arquivos:

- `/.mypy_cache/`
- `/.pytest_cache/`
- `/.vite/`
- `/.venv/`
- `/logs/`
- `/backend/logs/`
- `/backend/**/__pycache__/`
- `/frontend-solid/node_modules/`
- `/frontend-solid/dist/`
- `/frontend-solid/playwright-report/`
- `/frontend-solid/test-results/`
- `/test-results/`
- `/frontend-solid/vite-smoke.out.log`
- `/frontend-solid/vite-smoke.err.log`

Validação:

- confirmar que estão ignorados no `.gitignore`
- confirmar que podem ser recriados por `pytest`, `vite`, `bun install`, `playwright`, `python -m venv`

### Fase 2. Runtime e dados locais

**Objetivo**: separar dado operacional local de ativo do sistema.

Pastas/arquivos:

- `/app/data/sessions/*.json`
- `/backend/data/runtime/**`
- `/data/cache/**`
- `/backend/data/sessions_test_tmp/**`
- `/backend/data/sessions_test_tmp2/**`
- `/backend/data/whoosh_index/**`
- `/backend/data/learning/examples_*.jsonl`
- `/backend/data/learning/embeddings_cache.json`

Perguntas por arquivo:

- é regenerável?
- é fixture de teste ou sujeira de execução?
- é dado canônico ou snapshot local?
- existe cópia equivalente em outro caminho?

### Fase 3. Duplicações e restos legados

**Objetivo**: identificar estruturas duplicadas e resíduos de arquitetura antiga.

Pastas/arquivos:

- `/backend/api/` residual
- `/backend/scripts/backend/data/parquet/admmat.parquet`
- `/backend/scripts/data/parquet/admmat.parquet`
- lockfiles concorrentes em `frontend-solid/`
- root files sem referência operacional

Checagens:

- busca por referências com `rg`
- comparação com runtime real documentado
- confirmação se o arquivo é insumo de script ou somente sobra de manutenção

### Fase 4. Documentação e histórico

**Objetivo**: manter docs operacionais e arquivar excesso.

Pastas/arquivos:

- `/docs/historico/**`
- `/docs/mockups/**`
- múltiplos runbooks/checklists sobre o mesmo tema
- markdowns soltos na raiz

Heurística:

- documentação ativa: arquitetura, onboarding, runbook vigente, overview, changelog
- documentação arquivável: auditorias antigas, planos já executados, mockups intermediários, versões `v2+`, demo notes

### Fase 5. Scripts de manutenção

**Objetivo**: reduzir scripts one-off espalhados.

Pastas/arquivos:

- `/backend/scripts/maintenance/**`
- `/scripts/**`
- `START_*.bat`

Perguntas por script:

- é usado no fluxo atual?
- há duplicata funcional?
- deveria virar comando documentado em `README`?
- é diagnóstico pontual que pode ir para `docs/historico/` ou sair do repo?

## Método de Revisão Arquivo por Arquivo

Para cada pasta da fase ativa:

1. listar arquivos
2. marcar categoria: `codigo`, `config`, `dado canonico`, `runtime`, `cache`, `doc ativa`, `doc historica`, `artefato`
3. buscar referência com `rg`
4. verificar se já está coberto por `.gitignore`
5. classificar risco:
   - `baixo`: regenerável, ignorado, sem impacto funcional
   - `medio`: não é código, mas pode apoiar operação local
   - `alto`: pode quebrar build, testes, runtime ou onboarding
6. adicionar à lista de autorização

## Candidatos Iniciais à Limpeza

### Alta confiança

- `/.mypy_cache/`
- `/.pytest_cache/`
- `/.vite/`
- `/.venv/`
- `/logs/`
- `/backend/logs/`
- `/backend/**/__pycache__/`
- `/frontend-solid/node_modules/`
- `/frontend-solid/dist/`
- `/frontend-solid/playwright-report/`
- `/frontend-solid/test-results/`
- `/test-results/`
- `/frontend-solid/vite-smoke.out.log`
- `/frontend-solid/vite-smoke.err.log`
- `/app/data/sessions/*.json`
- `/backend/data/runtime/**`
- `/data/cache/**`
- `/backend/data/sessions_test_tmp/**`
- `/backend/data/sessions_test_tmp2/**`
- `/backend/data/whoosh_index/**`

### Média confiança

- `/frontend-solid/package-lock.json`
  - motivo: `README.md` e docs apontam `bun.lock` como lock oficial
- `/backend/api/`
  - motivo: hoje aparenta conter apenas resíduos e `__pycache__`
- `/backend/scripts/backend/data/parquet/admmat.parquet`
- `/backend/scripts/data/parquet/admmat.parquet`
  - motivo: cópias duplicadas dentro de `scripts`
- `/docs/historico/**`
  - motivo: histórico útil, mas provavelmente arquivável fora da raiz principal
- `/docs/mockups/**`
  - motivo: múltiplas versões intermediárias de mockups e smoke captures
- `/chatbi-55a787a8-7457-4e62-8348-2e04529c722c.md`
  - motivo: markdown solto na raiz, sem referência encontrada
- `/csv_basket_realista_baseado_no_parquet_12000_linhas.csv`
  - motivo: dataset avulso grande na raiz, sem referência encontrada
- `/START_BACKEND_DEV.bat`
- `/START_SYSTEM_V2026.bat`
  - motivo: launchers locais; manter apenas se forem parte explícita do onboarding atual

### Baixa confiança

- consolidação de runbooks e checklists em `docs/`
- consolidação de scripts `backend/scripts/maintenance/`
- consolidação de datasets em `backend/data/learning/`

Esses itens exigem leitura contextual antes de qualquer limpeza.

## Entregáveis da Auditoria

### Entregável 1. Inventário mestre

Tabela com colunas:

- `caminho`
- `categoria`
- `referenciado_por`
- `status_gitignore`
- `risco`
- `acao_sugerida`

### Entregável 2. Lista para autorização

Duas listas separadas:

- limpeza local imediata
- limpeza estrutural/versionamento

### Entregável 3. PR de saneamento

Somente após autorização:

- remover artefatos aprovados
- ajustar `.gitignore` se necessário
- consolidar docs/scripts aprovados
- validar build/testes

## Estratégia de Execução

### Sprint 1. Limpeza sem risco

Escopo:

- caches
- logs
- builds
- relatórios
- sessões locais

Validação:

- `python -m pytest` focal
- `tsc --noEmit`
- `vitest` focal

### Sprint 2. Consolidação de dados e runtime

Escopo:

- runtime local
- caches de embedding
- índices de busca
- diretórios de sessão temporários

Validação:

- subida local backend
- smoke básico de chat/playground

### Sprint 3. Limpeza estrutural

Escopo:

- lockfiles conflitantes
- scripts duplicados
- diretórios legados residuais
- markdowns soltos e docs históricas

Validação:

- README atualizado
- fluxo de onboarding reproduzível

## Riscos e Cuidados

- `backend/data/parquet/*.parquet` e `backend/data/*.duckdb` não devem ser removidos sem confirmar se são base canônica de desenvolvimento.
- `docs/historico/` e `docs/mockups/` podem ser arquivados, mas não eliminados sem decisão de governança.
- `frontend-solid/package-lock.json` só deve sair após confirmar que nenhum pipeline usa `npm ci`.
- `backend/scripts/maintenance/` mistura utilitários úteis e one-offs; precisa de triagem manual antes de reduzir.

## Próximo Passo Recomendado

Executar a auditoria em duas ondas:

1. autorizar limpeza dos itens de **alta confiança**
2. revisar comigo a lista de **média confiança** antes de qualquer remoção estrutural
