# Onboarding de 7 Dias - De visitante a copiloto

Atualizado em: 2026-03-07

Este plano assume 4 pessoas no projeto:

- voce;
- integrante 1;
- integrante 2;
- integrante 3.

O objetivo real da semana nao e "ler documentacao".
E este:

> no fim de 7 dias, ninguem do time deve dizer "eu so entendo minha parte".

Todo mundo precisa entender o caminho principal do produto.

## O que significa estar onboarded de verdade

Ao final da primeira semana, cada integrante precisa conseguir:

1. explicar o sistema em 3 a 5 minutos;
2. seguir o fluxo de login sem ajuda;
3. seguir o fluxo do chat SSE ponta a ponta;
4. apontar de onde o dado vem;
5. dizer quais partes sao sensiveis ou legadas;
6. abrir uma PR pequena com seguranca.

Se a pessoa leu tudo, mas ainda nao consegue explicar isso, o onboarding nao terminou.

Traduzindo:

- entender nao e repetir sigla;
- entender e conseguir contar a historia do sistema de um jeito que outra pessoa acompanhe.

## O material base da semana

Leitura obrigatoria:

- `README.md`
- `docs/SYSTEM_OVERVIEW.md`
- `docs/CHATBI_TOOL_CONTRACTS.md`
- `docs/adr/ADR-004-rbac-capability-scoping.md`
- `docs/adr/ADR-005-dashboard-chat-first.md`

Leitura de apoio:

- `backend/tests/README_TESTS.md`
- `docs/CHATBI_TEST_CASES.md`

Observacao importante:

- se algum termo tecnico travar a leitura, volte no "Minidicionario do projeto" dentro de `docs/SYSTEM_OVERVIEW.md`;
- aqui vale uma regra simples: ninguem precisa fingir que entendeu uma palavra so porque ela parece tecnica.

## Como dividir o ownership sem fragmentar o entendimento

A distribuicao abaixo nao serve para isolar pessoas.
Serve para garantir que cada uma mergulhe fundo em um fluxo, mas continue entendendo o todo.

### Voce - Arquitetura e integracao

Responsabilidade inicial:

- visao do produto;
- backlog e prioridades;
- criterios de qualidade;
- coerencia entre frontend, backend e negocio;
- decisao final de rollout.

### Integrante 1 - Portaria do sistema

Missao:

- dominar login, JWT, tenant, rate limit e contexto de requisicao.

Arquivos foco:

- `backend/main.py`
- `backend/app/api/middleware/auth.py`
- `backend/app/api/middleware/tenant.py`
- `backend/app/api/middleware/rate_limit.py`
- `backend/app/api/v1/endpoints/auth.py`

### Integrante 2 - Cerebro do chat

Missao:

- dominar stream SSE, roteamento, tools e recorte de dados.

Arquivos foco:

- `backend/app/api/v1/endpoints/chat.py`
- `backend/app/services/chat_service_v3.py`
- `backend/app/core/utils/query_router.py`
- `backend/app/core/tools/`
- `docs/CHATBI_TOOL_CONTRACTS.md`

### Integrante 3 - Cockpit do produto

Missao:

- dominar rotas protegidas, UX do chat, renderizacao de eventos e comportamento de erro.

Arquivos foco:

- `frontend-solid/src/index.tsx`
- `frontend-solid/src/Layout.tsx`
- `frontend-solid/src/pages/Chat.tsx`
- `frontend-solid/src/components/`
- `frontend-solid/tests/integration/`

## Regra da semana

Cada dia precisa terminar com uma micro-apresentacao de 10 minutos.

Nao precisa ser formal.
Precisa apenas responder:

1. o que eu entendi hoje;
2. o que ainda esta confuso;
3. qual risco tecnico eu encontrei.

Esse ritual acelera o entendimento e revela cedo onde a documentacao ainda falha.

## Dia 1 - Ligar o motor

**Meta do dia:** todo mundo com ambiente local funcionando.

Atividades:

1. ler `README.md` e `docs/SYSTEM_OVERVIEW.md`;
2. executar `START_SYSTEM_V2026.bat`;
3. validar `http://localhost:8000/health`;
4. abrir o frontend;
5. fazer login;
6. registrar qualquer obstaculo de setup.

Entrega do dia:

- ambiente local funcionando;
- lista unica de problemas de setup encontrada por quem entrou agora.

Pergunta que cada pessoa deve responder no fim do dia:

> "Se outro dev chegasse hoje, eu saberia colocar o sistema de pe com ele?"

## Dia 2 - Entender a portaria

**Meta do dia:** saber o que acontece antes da logica de negocio rodar.

Atividades:

1. seguir `POST /api/v1/auth/login`;
2. seguir `GET /api/v1/auth/me`;
3. ler `backend/main.py`;
4. ler os middlewares na ordem real de entrada;
5. entender o efeito de `AUTH_DISABLED=true` e `RATE_LIMIT_DISABLED=true`.

Entrega do dia:

- diagrama simples de request -> middleware -> endpoint.

Pergunta do fim do dia:

> "Onde eu olharia primeiro se um usuario dissesse que o sistema esta negando acesso errado?"

## Dia 3 - Ver a pergunta atravessar o sistema

**Meta do dia:** entender o fluxo principal do produto sem pular etapas.

Atividades:

1. abrir `frontend-solid/src/pages/Chat.tsx`;
2. localizar o pedido de `stream-token`;
3. localizar a abertura do `EventSource`;
4. abrir `backend/app/api/v1/endpoints/chat.py`;
5. localizar `/stream-token` e `/stream`;
6. executar 3 perguntas reais no chat:
   - uma saudacao;
   - uma consulta de dados;
   - um pedido de grafico ou dashboard.

Entrega do dia:

- explicacao clara de como a resposta chega em streaming.

Pergunta do fim do dia:

> "Se o chat ficar preso em carregamento, em quais 3 pontos eu investigaria primeiro?"

## Dia 4 - Entender de onde a resposta vem

**Meta do dia:** parar de tratar a IA como caixa preta.

Atividades:

1. ler `docs/CHATBI_TOOL_CONTRACTS.md`;
2. mapear quais tools consultam dados internos;
3. mapear quais tools montam visualizacao;
4. mapear quais tools fazem pesquisa externa;
5. revisar como `allowed_segments` e role afetam a resposta.

Entrega do dia:

- mapa simples de pergunta -> roteamento -> tool -> tipo de resposta.

Pergunta do fim do dia:

> "Quando uma resposta vem errada, como eu separo erro de prompt, erro de tool e erro de dado?"

## Dia 5 - Entender o cockpit

**Meta do dia:** dominar a experiencia que o usuario realmente enxerga.

Atividades:

1. abrir `frontend-solid/src/index.tsx`;
2. mapear rotas protegidas e rotas por role;
3. revisar comportamento de erro e fallback no chat;
4. rodar testes de frontend mais relevantes;
5. identificar os pontos de regressao mais provaveis na UX.

Entrega do dia:

- lista das telas criticas e do que pode quebrar cada uma.

Pergunta do fim do dia:

> "Qual bug no frontend parece visual, mas na verdade denuncia problema de backend?"

## Dia 6 - Testar, observar, operar

**Meta do dia:** aprender a validar mudanca sem supersticao.

Atividades:

1. ler `backend/tests/README_TESTS.md`;
2. rodar ao menos uma suite backend;
3. rodar ao menos uma suite frontend;
4. revisar healthcheck, logs e runbooks;
5. ler:
   - `docs/CHATBI_TEST_CASES.md`
   - `docs/PLAYGROUND_BI_RUNBOOK.md`
   - `docs/CHATBI_SPRINT6_GO_LIVE_RUNBOOK.md`

Entrega do dia:

- mini-checklist de validacao para PR de fluxo critico.

Pergunta do fim do dia:

> "O que eu preciso rodar antes de mexer em auth, chat ou tool selection?"

## Dia 7 - Apresentacao reversa

**Meta do dia:** transformar leitura em entendimento compartilhado.

Formato:

1. integrante 1 apresenta auth, tenant e rate limit;
2. integrante 2 apresenta chat backend, roteamento e tools;
3. integrante 3 apresenta frontend, rotas e experiencia do chat;
4. voce fecha com prioridades, backlog e pontos de risco.

Regra:

- a apresentacao precisa mostrar codigo;
- quem apresenta precisa mostrar um fluxo real, nao so uma lista de arquivos.

Se alguem nao conseguir explicar sua parte conectando com o resto, vale repetir o circuito na semana seguinte.

## Como saber se a semana funcionou

O onboarding deu certo quando:

- o time sobe o sistema sem depender de voce;
- cada pessoa sabe onde comecar um debug;
- ninguem trata o chat como uma caixa preta;
- o grupo entende pelo menos um risco legado real;
- ja existe ownership inicial sem virar silo.

## O formato de repasse que mais combina com este projeto

Para este sistema, o melhor formato e:

1. uma sessao de arquitetura no inicio da semana;
2. leitura guiada por fluxo, nao por pasta;
3. pratica real no ambiente local;
4. ownership inicial por area critica;
5. apresentacao reversa no fim.

Evite estes 3 erros:

- jogar o repositorio na mao do time e dizer "explorem";
- dividir apenas "frontend", "backend" e "docs" sem contexto;
- fazer todo o onboarding oral e deixar o conhecimento preso nas pessoas.

## Frase-guia da semana

Se o time entender esta frase, o onboarding foi bem desenhado:

> "No Caculinha BI, uma pergunta entra pelo frontend, passa pela portaria do backend, vira execucao no chat, consulta dados reais e volta em stream como insight."
