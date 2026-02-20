# Checklist ChatBI Pronto para Produção Enterprise

## Objetivo
Garantir que o ChatBI esteja apto para operação corporativa com segurança, confiabilidade, governança e valor de negócio para áreas comerciais e compras.

## 1. Cobertura funcional mínima
- Consultas essenciais disponíveis: vendas, margem, estoque, ruptura, giro, fornecedores, transferências.
- Cálculos essenciais disponíveis: EOQ, previsão, alocação, outliers, comparativos por período/UNE/segmento.
- Saídas suportadas: texto, tabela, gráfico e geração de SQL/Python quando solicitado.
- Critério de aceite: bateria de perguntas reais do negócio com aproveitamento mínimo de 90%.

## 2. Precisão e confiabilidade
- Respostas auditadas contra dados reais (amostra controlada).
- Bloqueio de resposta quando faltarem filtros críticos ou dados mínimos.
- Toda resposta analítica deve informar filtros e evidências utilizadas.
- Critério de aceite: taxa de erro factual abaixo de 5%.

## 3. Governança de acesso
- Role dinâmica por usuário no chat (admin, compras, BI, viewer).
- RLS aplicado em todas as ferramentas e consultas.
- Trilha de auditoria com: usuário, pergunta, ferramentas acionadas, data/hora, escopo de dados.
- Critério de aceite: testes de permissão sem vazamento entre perfis.

## 4. Segurança
- Não expor JWT em query string.
- Segredos em política de rotação (LLM, Supabase e integrações).
- Sanitização de entrada/saída e proteção contra prompt injection básica.
- Rate limit por usuário/IP e proteção contra abuso.
- Critério de aceite: revisão de segurança sem vulnerabilidade crítica.

## 5. Robustez operacional
- Timeouts, retries e fallback de provedores LLM.
- Degradação graciosa com mensagens claras para o usuário.
- Circuit breaker para falhas repetidas de provedores externos.
- Critério de aceite: erro 5xx abaixo de 1% em operação normal.

## 6. Observabilidade
- Métricas obrigatórias: latência, erro, custo/tokens, cache hit, uso de ferramentas, feedback útil.
- Logs estruturados com `request_id` e rastreabilidade ponta a ponta.
- Painel operacional de saúde do ChatBI.
- Critério de aceite: detecção de incidente em menos de 5 minutos.

## 7. Performance
- SLO recomendado:
- P95 até 3s para consultas simples.
- P95 até 8s para consultas complexas.
- Streaming contínuo sem travamento de interface.
- Warm-up de componentes críticos no startup.
- Critério de aceite: SLO cumprido por 7 dias consecutivos.

## 8. Qualidade de UX
- Estados claros: processando, ferramenta em execução, erro, resposta final.
- Ação de refinamento quando pergunta estiver ambígua.
- Exportação robusta (JSON/CSV/Markdown/TXT) e cópia confiável.
- Critério de aceite: avaliação interna positiva definida pelo negócio.

## 9. Relatórios robustos no chat
- Templates oficiais por processo de negócio.
- Saída padrão em: Resumo, Tabela operacional, SQL/Python, Ação recomendada.
- Integração com fluxo operacional (aprovação, tarefa, encaminhamento).
- Critério de aceite: 100% dos relatórios críticos geráveis sem retrabalho manual relevante.

## 10. LLMOps contínuo
- Base versionada de perguntas reais para regressão.
- Testes automáticos por release (funcional, factual e segurança).
- Coleta e uso sistemático de feedback (`positivo`, `negativo`, `parcial`).
- Critério de aceite: melhoria contínua documentada por release.

## 11. Conformidade de dados
- Política de retenção, mascaramento e exportação por perfil.
- Controle de acesso a dados sensíveis e rastreabilidade.
- Critério de aceite: validação da política interna de dados.

## 12. Go-live controlado
- Liberação gradual (canary) por grupos de usuários.
- Plano de rollback testado.
- Runbook de incidente publicado e conhecido pelo time.
- Critério de aceite: checklist final aprovado antes da abertura geral.

## 13. Arquitetura multi-LLM (agnóstica de provedor)
- Orquestração central via `SmartLLM` (sem acoplamento do fluxo de negócio ao provider).
- Adapters específicos por provider (ex.: Google/GenAI, Groq) plugados no mesmo contrato.
- Cadeia de fallback configurável por ambiente (`LLM_PROVIDER`, `LLM_FALLBACK_PROVIDERS`).
- Endpoint técnico de status dos providers em `GET /api/v1/chat/llm/status`.
- Critério de aceite: troca de provider sem alterar rota de chat, agente ou payload frontend.

## Matriz de status recomendada
- `Nao iniciado`
- `Em andamento`
- `Validado`
- `Bloqueado`

## Evidências mínimas por item
- Link para PR/commit.
- Resultado de teste (print/log/relatório).
- Data de validação.
- Responsável técnico e responsável de negócio.


## Documentos de apoio
- Matriz de go-live: `docs/CHATBI_GO_LIVE_MATRIZ.md`
- Plano por fases: `docs/CHATBI_IMPLEMENTACAO_FASES.md`
- Roteiro da demo: `docs/CHATBI_DEMO_2026-02-20.md`
- Checklist técnico pré-demo: `docs/CHATBI_CHECKLIST_PRE_DEMO_2026-02-20.md`


