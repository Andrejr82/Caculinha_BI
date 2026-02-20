# ChatBI - Plano de Execução e Go-Live (Visão Clara)

## Objetivo
Conduzir o ChatBI para operação enterprise com controle de risco, dono definido e execução diária.

## Como ler este documento
- `Status`: situação atual do item.
- `Evidência`: prova objetiva do que já foi implementado.
- `Próxima entrega`: ação imediata para avançar o item.

## Status permitidos
- `Nao iniciado`
- `Em andamento`
- `Validado`
- `Bloqueado`

## Responsáveis oficiais
- TI: João Silva
- BI: Fausto Neto
- Compras: Rodrigo Dias e Neilor Santos
- Operações: Christiana Gouvea

## Resumo executivo (hoje)
- Itens totais: 20
- Validado: 1
- Em andamento: 10
- Nao iniciado: 9
- Bloqueado: 0

---

## P1 - Crítico (Go-Live)
| ID | Tema | Status | Responsável técnico | Responsável negócio | Evidência atual | Próxima entrega |
|---|---|---|---|---|---|---|
| 1 | Cobertura de consultas essenciais | Em andamento | João Silva (TI) | Fausto Neto (BI) | Chat já responde com texto/tabela/gráfico | Rodar bateria de 50 perguntas reais e medir taxa de sucesso |
| 2 | Cálculos críticos (EOQ, previsão, alocação, outliers) | Em andamento | João Silva (TI) | Rodrigo Dias e Neilor Santos (Compras) | Ferramentas de cálculo disponíveis no agente | Validar 10 cenários com planilha de referência |
| 3 | Evidência e filtros nas respostas | Em andamento | João Silva (TI) | Fausto Neto (BI) | Parte das respostas já inclui evidência | Padronizar resposta final para sempre incluir filtros/evidência |
| 4 | Erro factual < 5% | Nao iniciado | João Silva (TI) | Fausto Neto (BI) | Sem auditoria formal consolidada | Executar auditoria de 100 respostas reais |
| 5 | Role dinâmica por usuário no chat | Nao iniciado | João Silva (TI) | Fausto Neto (BI) | Serviço ainda com papel fixo no core do chat | Remover hardcode e aplicar role real do usuário |
| 6 | RLS em todas as ferramentas | Em andamento | João Silva (TI) | Fausto Neto (BI) | RLS ativo em rotas-chave | Executar teste de vazamento cruzado por perfil |
| 7 | Segurança de stream (sem JWT na URL) | Validado | João Silva (TI) | Christiana Gouvea (Operações) | Token efêmero obrigatório no `/api/v1/chat/stream` | Monitorar logs por 7 dias e encerrar item |
| 8 | Rate limit e proteção de abuso | Em andamento | João Silva (TI) | Christiana Gouvea (Operações) | Middleware de rate limit ativo | Rodar teste de carga por usuário/IP |
| 9 | Timeout/retry/fallback LLM | Em andamento | João Silva (TI) | Fausto Neto (BI) | Timeout e fallback implementados | Testar cenários de falha Gemini/Groq |
| 10 | Erro 5xx < 1% | Nao iniciado | João Silva (TI) | Christiana Gouvea (Operações) | Falta baseline semanal consolidada | Instrumentar painel semanal de 5xx |
| 11 | Métricas operacionais (latência/erro/custo/cache/tools) | Em andamento | João Silva (TI) | Christiana Gouvea (Operações) | Métricas e logs já disponíveis no backend | Consolidar dashboard único de SLO ChatBI |
| 12 | Logs com request_id ponta a ponta | Em andamento | João Silva (TI) | Christiana Gouvea (Operações) | request_id presente no pipeline HTTP | Garantir propagação completa no fluxo SSE |
| 20 | Canary + rollback + runbook | Nao iniciado | João Silva (TI) | Christiana Gouvea (Operações) | Estrutura parcial de operação | Publicar runbook final e simular rollback |

---

## P2 - Importante (Escala e qualidade)
| ID | Tema | Status | Responsável técnico | Responsável negócio | Evidência atual | Próxima entrega |
|---|---|---|---|---|---|---|
| 13 | P95 consultas simples <= 3s | Nao iniciado | João Silva (TI) | Fausto Neto (BI) | Sem medição oficial fechada | Medir baseline e otimizar hot paths |
| 14 | P95 consultas complexas <= 8s | Nao iniciado | João Silva (TI) | Fausto Neto (BI) | Sem medição oficial fechada | Perfilar por tipo de pergunta e ferramenta |
| 15 | UX com estados claros | Em andamento | João Silva (TI) | Fausto Neto (BI) | Thinking process e estados já ativos | Revisão final com usuários-chave |
| 16 | Exportação robusta (JSON/CSV/MD/TXT) | Em andamento | João Silva (TI) | Fausto Neto (BI) | Export menu funcional no chat | Testar sessões longas e caracteres especiais |
| 17 | Templates oficiais de relatório | Nao iniciado | João Silva (TI) | Rodrigo Dias e Neilor Santos (Compras) | Sem catálogo oficial consolidado | Definir 6 templates oficiais por processo |
| 18 | Saída padrão (Resumo/Tabela/SQL-Python/Ação) | Nao iniciado | João Silva (TI) | Rodrigo Dias e Neilor Santos (Compras) | Sem validador final obrigatório | Implementar pós-processador de formato |

---

## P3 - Evolução contínua
| ID | Tema | Status | Responsável técnico | Responsável negócio | Evidência atual | Próxima entrega |
|---|---|---|---|---|---|---|
| 19 | Regressão automática por release (LLMOps) | Nao iniciado | João Silva (TI) | Fausto Neto (BI) | Base de testes ainda não versionada | Criar dataset versionado + job de regressão |

---

## Fechamento de hoje (check rápido)
| Item | Meta de hoje | Resultado |
|---|---|---|
| Documento organizado | Formato claro e acionável | Concluído |
| Responsáveis aplicados | TI/BI/Compras/Operações | Concluído |
| Priorização | P1/P2/P3 definida | Concluído |
| Próximas ações | Definidas por item | Concluído |

## Assinaturas de aprovação
- Responsável técnico (TI): João Silva
- Responsável negócio (BI): Fausto Neto
- Responsáveis negócio (Compras): Rodrigo Dias e Neilor Santos
- Responsável negócio (Operações): Christiana Gouvea
- Data de aprovação final:
