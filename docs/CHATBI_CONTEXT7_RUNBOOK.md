# ChatBI Context7 Runbook

## 1. Premissa importante
No ChatBI, **Context7 é framework externo de bibliotecas/contexto** (via integração), não um "módulo interno de limpeza de resposta".

## 2. Estado atual do projeto
- O sanitizador textual interno foi neutralizado para `response_sanitizer`.
- O módulo `context7.py` permanece apenas como alias legado para compatibilidade de imports.

## 3. Checklist de integração Context7
1. Confirmar servidor/contexto Context7 configurado no runtime (MCP/server target).
2. Validar credenciais e permissões de leitura.
3. Garantir timeout e fallback para não bloquear o fluxo principal do chat.
4. Logar disponibilidade do Context7 na inicialização.

## 4. Estratégia de fallback
- Se Context7 externo estiver indisponível:
  - seguir com pipeline local normal de tool routing;
  - não quebrar resposta final ao usuário;
  - registrar evento de observabilidade (`context7_unavailable`).

## 5. Testes recomendados para Context7
1. Health check de disponibilidade na inicialização.
2. Teste de timeout controlado.
3. Teste de fallback com resposta funcional sem Context7.
4. Teste de regressão garantindo que rotas de chat continuam estáveis.

## 6. Procedimento de incidente
1. Detectar indisponibilidade/context timeout do Context7.
2. Ativar modo fallback local automaticamente.
3. Preservar SLA da resposta do ChatBI.
4. Abrir incidente com evidência de logs e janela de impacto.

## 7. Governança
- Toda nova dependência de Context7 deve:
  - ser opcional (degradação graciosa),
  - ter contrato claro de entrada/saída,
  - possuir teste automatizado de fallback.

