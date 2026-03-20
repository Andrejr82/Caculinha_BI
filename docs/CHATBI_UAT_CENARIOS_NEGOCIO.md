# ChatBI UAT - Cenarios de Negocio

## Objetivo
Homologar os fluxos criticos do Caçulinha com linguagem de negocio e aprovacoes rastreaveis.

## Como usar
- Executar cada cenario com usuario autorizado no canary.
- Registrar data, aprovador e observacoes.
- Marcar o checkbox apenas quando o comportamento estiver consistente no frontend e no backend.
- Consolidar o resultado final em `docs/CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md`.
- Para a bateria automatizada local, executar `powershell -ExecutionPolicy Bypass -File scripts/chatbi_uat_local.ps1`.

## Cenarios

### BI e analise
- [ ] Consultar venda por segmento e confirmar citacoes, confianca e `request_id` no resultado final.
- [ ] Pedir grafico de comparacao entre lojas e validar renderizacao sem quebrar o texto explicativo.
- [ ] Pedir dashboard executivo e confirmar que o `dashboard_spec` e exibido com os cards corretos.
- [ ] Fazer uma pergunta ambigua e validar pedido de esclarecimento antes de executar ferramenta errada.

### Mercado e pesquisa externa
- [ ] Solicitar pesquisa de mercado e validar origem, modo e citacoes no evento `final`.
- [ ] Simular consulta degradada e confirmar mensagem segura com `mode=deterministic_degraded_timeout`.

### Memoria e historico
- [ ] Conduzir follow-up em uma mesma sessao e confirmar reaproveitamento do contexto.
- [ ] Reabrir conversa persistida pelo historico e validar que o contexto e restaurado.
- [ ] Excluir uma sessao do historico e confirmar que ela deixa de aparecer na listagem.

### Multimodalidade
- [ ] Anexar documento valido e confirmar indexacao para RAG.
- [ ] Anexar imagem valida e confirmar resumo visual na resposta.
- [ ] Usar entrada por voz e confirmar transcricao no composer.
- [ ] Reproduzir e interromper a leitura por voz de uma resposta.

### Automacao com aprovacao
- [ ] Solicitar geracao de relatorio e confirmar card de aprovacao com status `pending_user_approval`.
- [ ] Aprovar uma automacao de planilha e validar artefato exportavel ao final.
- [ ] Solicitar rascunho de e-mail, revisar o draft e aprovar o envio final.
- [ ] Rejeitar uma automacao e confirmar status final auditado no chat e no historico de automacoes.

## Assinaturas
- [ ] Aprovacao do negocio
- [ ] Aprovacao do produto
- [ ] Aprovacao tecnica
- [ ] Aprovacao operacional
