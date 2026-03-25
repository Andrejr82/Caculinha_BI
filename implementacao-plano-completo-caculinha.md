# Implementacao Completa do Plano do Assistente Caçulinha

## Goal
Implementar integralmente o plano de evolucao do Caçulinha sobre a stack ativa do produto, com foco em entrega vertical, baixo retrabalho e validacao continua.

## Direcao Tecnica
- [x] Implementar primeiro na stack ativa: `frontend-solid/src/pages/Chat.tsx` + `backend/app/api/v1/endpoints/chat.py` + `backend/app/services/chat_service_v3.py` + `backend/app/core/agents/caculinha_bi_agent.py` -> Verificar: o fluxo principal do chat continua funcional sem migracao arquitetural paralela.
- [x] Tratar `backend/app/api/v2/endpoints/chat.py` como rota secundaria ate haver paridade real com o fluxo principal -> Verificar: nenhuma feature critica depende do endpoint v2 isolado.
- [x] Preservar contratos existentes de `text`, `chart`, `table`, `dashboard`, `error`, `final` durante toda a evolucao -> Verificar: suites de regressao do chat continuam passando.

## Task Board

### Fase 0 - Fundacao do Contrato do Chat
- [x] Unificar `request_id` e `response_id` de ponta a ponta no SSE, no frontend e no feedback -> Verificar: o `FeedbackButtons` envia o ID real retornado pelo backend.
- [x] Incluir `source`, `confidence`, `citations` e `mode` no evento `final` do stream normal, nao so nos fast paths -> Verificar: uma resposta analitica comum entrega esses campos no SSE.
- [x] Renderizar fontes, citacoes e confianca no `Chat.tsx` com UI legivel e acessivel -> Verificar: consultas de mercado e RAG mostram citacoes clicaveis.
- [x] Formalizar o contrato SSE com testes para `tool_progress`, `text`, `chart`, `table`, `dashboard`, `keepalive`, `error` e `final` -> Verificar: testes de contrato falham quando o payload quebra.
- [x] Remover lacunas entre feedback do frontend e persistencia do backend -> Verificar: um feedback positivo/negativo/partial fica rastreavel por resposta real.

### Fase 1 - Raciocinio e Orquestracao de Ferramentas
- [x] Reforcar o planejamento de execucao do agente sem expor chain-of-thought bruto, mantendo apenas passos resumidos para `ThinkingProcess` -> Verificar: o frontend mostra etapas consistentes e nao vaza raciocinio sensivel.
- [x] Melhorar selecao dinamica de ferramentas com fallback semantico e recuperacao automatica de erro -> Verificar: falha de ferramenta primaria aciona fallback sem erro generico ao usuario.
- [x] Implementar execucao paralela onde houver independencia real entre ferramentas -> Verificar: cenarios de pesquisa/recuperacao apresentam menor latencia.
- [x] Completar o conjunto de analytics/ML previsto no plano com sandbox seguro -> Verificar: clustering, classificacao, forecast e otimizacao simples possuem testes unitarios.
- [x] Implementar fluxo robusto de esclarecimento para perguntas ambiguas -> Verificar: consultas vagas pedem confirmacao antes de acionar ferramentas erradas.

### Fase 2 - Memoria de Longo Prazo e RAG Avancado
- [x] Trocar o historico baseado apenas em arquivo por persistencia conversacional real no fluxo ativo do chat -> Verificar: conversas persistem entre recargas e podem ser reabertas.
- [x] Inicializar e conectar `MemoryAgent` no startup da aplicacao -> Verificar: `/api/v1/memory` deixa de responder com `503` e funciona ponta a ponta.
- [x] Integrar embeddings de conversa e fatos de negocio ao fluxo ativo de resposta -> Verificar: follow-ups recuperam contexto relevante de sessoes anteriores.
- [x] Implementar perfil de usuario e memoria de preferencias -> Verificar: preferencias salvas influenciam respostas futuras.
- [x] Expandir RAG para documentos internos, uploads e base de conhecimento com recuperacao hibrida -> Verificar: respostas fundamentadas citam a origem do documento recuperado.
- [x] Adicionar UI de historico de conversa no frontend com listar, abrir e excluir -> Verificar: o usuario pode retomar uma conversa real da memoria persistida.

### Fase 3 - Entrada Multimodal
- [x] Implementar upload real de anexos no chat com fluxo completo frontend/backend -> Verificar: o usuario consegue anexar arquivo a partir do `Chat.tsx`.
- [x] Adicionar processamento de imagem no fluxo do chat -> Verificar: uma imagem enviada pode ser analisada pelo assistente.
- [x] Adicionar ingestao segura de documentos para uso em RAG -> Verificar: arquivos validos entram na base consultavel e arquivos invalidos sao bloqueados.
- [x] Implementar entrada por voz com permissao de microfone e fallback adequado -> Verificar: o usuario fala, o texto e transcrito e enviado ao chat.
- [x] Garantir que multimodalidade respeite limite de tamanho, tipo de arquivo e politicas de seguranca -> Verificar: testes de upload rejeitam payloads indevidos.

### Fase 4 - Saida Multimodal
- [x] Implementar leitura por voz das respostas com controle por mensagem -> Verificar: cada resposta do assistente pode ser reproduzida e interrompida.
- [x] Adicionar suporte a retorno de imagem gerada quando o provider estiver disponivel -> Verificar: prompts de geracao retornam asset e metadados.
- [x] Integrar respostas multimodais ao contrato de mensagens do frontend -> Verificar: o chat renderiza texto, dashboard, tabela, grafico, audio e imagem sem colidir estados.
- [x] Garantir auditoria e telemetria de uso por tipo de midia -> Verificar: metrics/logs discriminam uso de voz, imagem e anexo.

### Fase 5 - Computer Use e Automacoes com Aprovacao
- [x] Definir modelo de aprovacao explicita para acao de navegador, planilha, exportacao, email e mensagens -> Verificar: nenhuma acao sensivel executa sem aprovacao do usuario.
- [x] Implementar executor de automacoes com registry restrito de capacidades -> Verificar: acoes nao autorizadas sao bloqueadas antes da execucao.
- [x] Integrar automacao web para navegacao controlada em sistemas e dashboards -> Verificar: um fluxo aprovado executa navegacao guiada em ambiente de teste.
- [x] Integrar automacoes de planilha e geracao de relatorios -> Verificar: o assistente cria ou preenche artefatos exportaveis mediante aprovacao.
- [x] Integrar redacao e envio de email/mensagem com etapa de revisao obrigatoria -> Verificar: o usuario aprova o rascunho antes do envio final.
- [x] Expor no `Chat.tsx` uma UX de aprovacao, rejeicao e status da automacao -> Verificar: a conversa mostra o passo pendente e o estado final auditado.

### Fase 6 - Feedback Loop, Observabilidade e Aprendizado Continuo
- [x] Conectar o `ContinuousLearner` ao fluxo ativo do chat e nao apenas a endpoints isolados -> Verificar: feedback alimenta golden dataset, fila de review e estatisticas reais.
- [x] Correlacionar feedback com ferramenta usada, confianca, latencia e citacoes -> Verificar: cada feedback fica associado a metadados operacionais da resposta.
- [x] Expandir o dashboard administrativo para SLOs de chat, citacao, no-data false positive e acuracia de tool selection -> Verificar: endpoints admin exibem os indicadores com testes.
- [x] Implementar logging estruturado com trace de request SSE, tool calls e jobs assincornos -> Verificar: uma requisicao pode ser rastreada ponta a ponta.
- [x] Implementar hooks de A/B testing para prompts, estrategias de tool routing e UX -> Verificar: requests podem ser bucketizados e comparados por resultado.

### Fase 7 - Seguranca, Hardening e Governanca
- [x] Endurecer sanitizacao de Markdown, HTML, citacoes, anexos e comandos de automacao -> Verificar: testes de XSS, upload malicioso e comando indevido falham com bloqueio.
- [x] Aplicar controles de permissao por role/capability para memoria, multimodalidade e computer use -> Verificar: features sensiveis podem ser habilitadas por perfil.
- [x] Criar testes de carga, streaming prolongado, timeouts e recuperacao de falha -> Verificar: SLOs de latencia e resiliencia sao medidos em ambiente de homologacao.
- [x] Definir feature flags e canary rollout por capacidade -> Verificar: memoria, voz, anexos e computer use podem ser ativados seletivamente.
- [x] Produzir runbooks operacionais, rollback e troubleshooting -> Verificar: suporte/admin consegue habilitar, desabilitar e diagnosticar cada capacidade.

### Fase 8 - Fechamento e Go-Live
- [x] Executar validacao integrada de frontend, backend, observabilidade, seguranca e automacoes -> Verificar: checklist de pre-producao completo sem bloqueios abertos.
- [ ] Executar UAT com cenarios de negocio reais de BI, mercado, memoria, multimodalidade e automacao -> Verificar: cenarios criticos sao aprovados.
- [x] Congelar contrato final do chat e documentar suporte -> Verificar: API, UX e operacao ficam documentadas na raiz/docs.
- [ ] Realizar go-live controlado com monitoramento reforcado -> Verificar: rollout concluido com acompanhamento de metricas e plano de rollback ativo.

## Definition of Done
- [x] O chat suporta respostas fundamentadas com texto, grafico, tabela, dashboard, memoria persistente e citacoes visiveis.
- [x] O chat suporta anexos, imagem, voz e saida de voz com fluxo operacional real.
- [x] O chat suporta automacoes aprovadas com auditoria e controles de permissao.
- [x] Feedback, continuous learning, metrics e admin dashboard estao conectados ao fluxo real de producao.
- [x] Testes de contrato, integracao, seguranca e carga cobrem as capacidades adicionadas.
- [x] O rollout pode ser feito por feature flag com observabilidade e rollback.

## Pendencias Operacionais
- [ ] Executar e assinar o UAT em ambiente de homologacao usando `docs/CHATBI_UAT_CENARIOS_NEGOCIO.md`.
- [ ] Conduzir o go-live real com monitoramento reforcado seguindo `docs/CHATBI_SPRINT6_GO_LIVE_RUNBOOK.md`.

## Ordem Recomendada de Execucao
- [x] Executar primeiro as Fases 0, 1 e 2 para estabilizar contrato, contexto e confiabilidade.
- [x] Executar depois as Fases 6 e 7 para fechar telemetria, governanca e seguranca antes de expandir poder operacional.
- [x] Executar em seguida as Fases 3 e 4 para multimodalidade completa.
- [x] Executar a Fase 5 somente com aprovacao, auditoria e feature flags prontas.
- [ ] Encerrar com a Fase 8 e checklist de go-live.
