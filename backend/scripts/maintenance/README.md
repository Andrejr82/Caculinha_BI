# Scripts de Manutenção

Esta pasta concentra utilitários operacionais que não fazem parte do runtime do produto.

## Regras

- execute esses scripts a partir do diretório `backend/`
- trate-os como ferramentas de manutenção, migração, diagnóstico ou recuperação
- nenhum arquivo desta pasta deve ser importado pelo runtime principal
- scripts de benchmark, auditoria, validação ad hoc e testes manuais também ficam aqui

## Convenção de pastas

- `backend/scripts/`: apenas bootstrap, carga, seed, sync e execuções operacionais recorrentes
- `backend/scripts/maintenance/`: diagnóstico, benchmark, validação, recuperação e utilitários ad hoc

## Exemplos

Do diretório raiz do projeto:

```powershell
cd backend
python scripts/maintenance/promote_to_admin.py
python scripts/maintenance/verify_gemini_env.py
python scripts/maintenance/backfill_chat_examples_from_sessions.py
python scripts/maintenance/build_unified_learning_dataset.py
python scripts/maintenance/benchmark_quick.py
python scripts/maintenance/check_config.py
python scripts/maintenance/preload_embedding_model.py --allow-download
```

## Observação

Se um script desta pasta passar a ser necessário no fluxo normal do sistema, ele deve ser promovido para um módulo estruturado do backend em vez de permanecer como utilitário avulso.

Os scripts Python de manutenção ligados a aprendizado/dataset também ficam aqui. A pasta `scripts/` da raiz deve ficar reservada a bootstrap local, quality gates e runbooks operacionais do repositório.

Parte do acervo histórico e one-off desta pasta pode ser movida para `legacy_quarantine/cleanup-2026-04-02/` durante saneamentos estruturais do repositório. O objetivo é manter aqui apenas o subconjunto de utilitários ainda claramente úteis para manutenção recorrente.
