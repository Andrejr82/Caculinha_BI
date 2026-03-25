# Plano Completo de Homologacao Multiusuario

## Objetivo

Preparar o `Caculinha_BI` para homologacao e operacao multiusuario com:

- `SQL Server` para estado transacional do chat
- `Parquet/DuckDB` como fonte analitica principal de negocio
- `Redis` como etapa posterior, fora da primeira homologacao
- `Prometheus + Grafana` para monitoramento
- `Sentry` para erros
- `Locust` para testes de carga

## Estado Atual

- [x] Arquitetura alvo definida: `SQL Server = transacional do chat`, `Parquet/DuckDB = analytics`, `Redis = posterior`
- [x] Configuracoes de runtime adicionadas para `SQL Server`, `Redis` e paths de runtime
- [x] `SessionManager` preparado para backend `sqlserver`
- [x] `MemoryAdapter` preparado para `SQL Server`
- [x] Redis integrado a cache, rate limit e locks de ingestao
- [x] Runtime local do chat validado com `SQL Server` via `mssql+pytds`
- [x] Endpoint principal do chat validado localmente com persistencia em `SQL Server`
- [x] `health` e `diagnostics` ajustados para reconhecer `sqlserver_pytds`
- [x] `health` e `diagnostics` ajustados para expor `analytics_source=parquet`
- [x] Guardrails semanticos de resposta ampliados para `grafico`, `table`, `export` e `dashboard`
- [x] Smoke tests locais cobrindo consulta simples, grafico e basket
- [ ] Homologacao real com infraestrutura da empresa ainda nao executada
- [ ] Observabilidade de producao ainda nao concluida
- [ ] Teste de carga multiusuario real ainda nao concluido

## Arquitetura Alvo

- `Frontend` publicado com URL estavel
- `Reverse proxy` com HTTPS
- `FastAPI` como backend principal
- `SQL Server` para `chat_conversations`, `chat_messages`, `chat_feedbacks`
- `Parquet/DuckDB` para consultas analiticas e leitura principal da base de negocio
- `Redis` para hot path operacional em fase posterior
- `Prometheus` para metricas
- `Grafana` para dashboards e alertas
- `Sentry` para erros e excecoes
- `Locust` para testes multiusuario

## Fase 1 - Fechar Runtime de Homologacao

### Configuracao de ambiente

- [x] Criar template `.env` de homologacao com `ENVIRONMENT=staging`
- [x] Definir `CHAT_STATE_BACKEND=sqlserver` no template de homologacao
- [x] Definir `CHAT_STATE_SQLITE_FALLBACK_ENABLED=false` no template de homologacao
- [x] Definir `DATABASE_URL` e/ou `PYODBC_CONNECTION_STRING` apenas para o estado transacional do chat no template
- [ ] Definir `PARQUET_DATA_PATH` real do ambiente corporativo
- [ ] Definir `PARQUET_FILE_PATH` real do ambiente corporativo
- [x] Definir `USE_SQL_SERVER=false` se a homologacao usar `mssql+pytds` local controlado
- [x] Manter `REDIS_ENABLED=false` e `REDIS_REQUIRED=false` na primeira homologacao
- [ ] Definir `BACKEND_CORS_ORIGINS` real do frontend de homologacao
- [ ] Definir `SECRET_KEY` e `JWT_SECRET` de homologacao
- [ ] Definir chaves LLM reais de homologacao
- [x] Definir baseline de modelo Groq para homologacao
- [x] Se houver canario, registrar `openai/gpt-oss-120b` como experimento controlado

### Infraestrutura local do servidor

- [ ] Validar instalacao do `ODBC Driver 17` ou `18 for SQL Server`
- [ ] Validar conectividade entre app e `SQL Server`
- [ ] Confirmar que `Redis` fica desabilitado nesta primeira homologacao
- [ ] Validar permissao de escrita nos paths de runtime
- [ ] Validar existencia do `PARQUET_DATA_PATH`

### Criterio de aceite

- [ ] Backend sobe em modo de homologacao sem depender de `SQLite`
- [ ] `SQL Server` passa a ser dependencia do chat state
- [ ] `.parquet` passa a ser dependencia obrigatoria da base analitica

## Fase 2 - Consolidar Persistencia no SQL Server

### Schema e tabelas

- [x] Validar criacao de `chat_conversations`
- [x] Validar criacao de `chat_messages`
- [x] Validar criacao de `chat_feedbacks`
- [ ] Validar indices por `tenant_id`, `user_id`, `conversation_id`, `updated_at`
- [ ] Validar permissao do usuario do banco para `CREATE TABLE`
- [ ] Validar permissao do usuario do banco para `CREATE INDEX`
- [ ] Validar permissao do usuario do banco para `SELECT`, `INSERT`, `UPDATE`, `DELETE`

### Fluxo transacional do chat

- [x] Validar gravacao de conversa nova no `SQL Server`
- [x] Validar gravacao de mensagem do usuario
- [x] Validar gravacao de mensagem do assistente
- [x] Validar recuperacao de historico recente
- [x] Validar recuperacao de historico completo
- [x] Validar exclusao de sessao
- [x] Validar atualizacao de metadata por `request_id`
- [x] Validar gravacao de feedback

### Isolamento e ownership

- [x] Validar que usuario A nao enxerga sessao de usuario B
- [x] Validar que sessao A nao mistura mensagens de sessao B
- [ ] Validar que tenant A nao enxerga tenant B, se aplicavel

### Criterio de aceite

- [x] Fluxo principal do chat persiste em `SQL Server`
- [ ] `SQLite` deixa de ser necessario no runtime produtivo

## Fase 3 - Redis Posterior ao Go-Live Inicial

### Componentes Redis

- [x] Planejar a ativacao de Redis apos a primeira homologacao funcional
- [ ] Validar conexao Redis no startup da aplicacao
- [ ] Validar `response cache` em Redis
- [ ] Validar `semantic cache` em Redis
- [ ] Validar `rate limit` global em Redis
- [ ] Validar `rate limit` interno do chat em Redis
- [ ] Validar `runtime lock` de ingestao em Redis

### Comportamento em falha

- [ ] Validar comportamento quando Redis fica indisponivel em ambiente de homologacao
- [ ] Validar se a aplicacao falha corretamente quando `REDIS_REQUIRED=true`
- [ ] Validar fallback controlado apenas em ambiente local/dev

### Criterio de aceite

- [ ] Redis controla cache, rate limit e locks em homologacao
- [ ] Concorrencia de ingestao nao corrompe estado

## Fase 4 - Publicacao e Acesso Multiusuario

### Backend

- [ ] Publicar backend como servico no servidor da empresa
- [ ] Configurar restart automatico
- [ ] Configurar variaveis de ambiente de homologacao
- [x] Validar endpoint `/health` localmente
- [x] Validar endpoints de diagnostico localmente

### Frontend

- [ ] Publicar frontend apontando para o backend de homologacao
- [ ] Validar URL base da API no frontend
- [ ] Validar CORS com o dominio final

### Reverse proxy e rede

- [ ] Configurar proxy reverso
- [ ] Configurar HTTPS
- [ ] Validar acesso interno
- [ ] Validar acesso externo, se aplicavel

### Criterio de aceite

- [ ] Sistema acessivel por varios usuarios no ambiente de homologacao
- [ ] Reinicio do backend nao perde estado transacional do chat

## Fase 5 - Observabilidade

### Prometheus

- [ ] Expor metricas do backend para `Prometheus`
- [ ] Expor metricas de latencia por endpoint
- [ ] Expor metricas de erro `4xx/5xx`
- [ ] Expor metricas de uso de cache
- [ ] Expor metricas de ingestao
- [ ] Expor metricas de falha de lock

### Grafana

- [ ] Criar dashboard `Visao Geral`
- [ ] Criar dashboard `Chat`
- [ ] Criar dashboard `Infra`
- [ ] Criar dashboard `Dados`

### Sentry

- [ ] Integrar `Sentry` ao backend
- [ ] Capturar excecoes do FastAPI
- [ ] Capturar erros de `SQL Server`
- [ ] Capturar erros de `Redis`
- [ ] Capturar erros de LLM
- [ ] Enriquecer eventos com `request_id`
- [ ] Enriquecer eventos com `session_id`
- [ ] Enriquecer eventos com `user_id`
- [ ] Enriquecer eventos com `tenant_id`

### Alertas minimos

- [ ] Alerta para backend fora do ar
- [ ] Alerta para `/health` degradado
- [ ] Alerta para taxa de erro alta
- [ ] Alerta para p95 alto do chat
- [ ] Alerta para `Redis` indisponivel
- [ ] Alerta para `SQL Server` indisponivel
- [ ] Alerta para disco quase cheio
- [ ] Alerta para memoria alta

### Criterio de aceite

- [ ] Grafana mostra backend, `Redis` e `SQL Server`
- [ ] Sentry captura erros acionaveis do sistema

## Fase 6 - Homologacao Funcional

### Fluxos principais

- [ ] Validar login
- [ ] Validar autenticacao por token
- [x] Validar chat simples
- [x] Validar historico persistido
- [x] Validar persistencia de feedback no arquivo de learning
- [x] Validar persistencia de feedback em `chat_feedbacks`
- [x] Validar consulta de grafico
- [x] Validar consulta analitica por produto
- [x] Validar market basket
- [x] Validar anexos
- [x] Validar ingestao manual

### Validacao de modelo em homologacao

- [ ] Validar baseline com `llama-3.3-70b-versatile`
- [ ] Validar canario com `openai/gpt-oss-120b`
- [ ] Manter `INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile`
- [ ] Opcionalmente validar `CODE_GENERATION_MODEL=openai/gpt-oss-120b`
- [ ] Comparar qualidade, latencia e estabilidade antes de trocar o default

### Regras de comportamento do agente

- [x] Validar que anexos nao substituem a base local por padrao
- [x] Validar que pergunta sobre cesta usa anexo apenas quando pedido explicitamente
- [x] Validar que perguntas de grafico usam a base local mesmo com anexo presente
- [x] Validar que tabela/exportacao/dashboard bloqueiam respostas incoerentes sem payload minimo
- [x] Validar que o agente responde corretamente a assuntos diferentes no mesmo chat
- [x] Validar que historico do chat nao contamina outra sessao

### Erros e fallback

- [ ] Validar resposta quando `SQL Server` falha
- [ ] Validar resposta quando `Redis` falha, quando o Redis for ativado
- [ ] Validar resposta quando LLM falha
- [x] Validar erro controlado em ingestao concorrente

### Criterio de aceite

- [x] Todas as capabilities principais funcionam em homologacao local controlada
- [x] O agente responde corretamente com e sem anexos

## Fase 7 - Teste Multiusuario

### Preparacao

- [x] Criar cenarios `Locust` para chat leve
- [ ] Criar cenarios `Locust` para analytics/graficos
- [ ] Criar cenarios `Locust` para basket
- [ ] Criar cenarios `Locust` para anexos e ingestao
- [ ] Criar mistura realista de perfis de uso

### Execucao

- [ ] Rodar teste com `5` usuarios simultaneos
- [ ] Rodar teste com `10` usuarios simultaneos
- [ ] Rodar teste com `20` usuarios simultaneos
- [ ] Rodar teste com `30` usuarios simultaneos
- [ ] Rodar teste prolongado de estabilidade

### Validacoes

- [ ] Validar erro abaixo do limite aceitavel
- [ ] Validar p95 e p99 aceitaveis
- [ ] Validar ausencia de mistura de sessoes
- [ ] Validar ausencia de corrupcao de historico
- [ ] Validar ausencia de deadlock recorrente
- [ ] Validar ausencia de timeout sistemico

### Criterio de aceite

- [ ] Sistema suporta a carga alvo de homologacao com estabilidade

## Fase 8 - Operacao

### Runbooks

- [x] Criar runbook de subida
- [x] Criar runbook de rollback
- [x] Criar runbook de incidente
- [x] Criar runbook de validacao pos-deploy

### Rotinas

- [ ] Definir rotina de backup
- [ ] Definir rotina de limpeza de runtime
- [ ] Definir rotina de revisao de alertas
- [ ] Definir rotina de revisao de capacidade

### Criterio de aceite

- [ ] Equipe consegue operar o sistema com procedimento documentado

## Checklist Final de Aceite

- [ ] `SQL Server` ativo e usado pelo chat
- [ ] `Redis` ativo e usado por cache, rate limit e locks
- [ ] `SQLite` fora do fluxo produtivo
- [ ] `Parquet/DuckDB` usados apenas para analytics
- [ ] Backend publicado com acesso multiusuario
- [ ] Frontend publicado e apontando para o backend correto
- [ ] Prometheus coletando metricas
- [ ] Grafana com dashboards uteis
- [ ] Sentry capturando erros reais
- [ ] Testes funcionais aprovados
- [ ] Testes multiusuario aprovados
- [ ] Sistema pronto para uso interno controlado

## Observacoes

- `SQLite` pode continuar existindo apenas para desenvolvimento local e fallback controlado.
- `.parquet` nao deve armazenar sessao, mensagem, feedback ou estado concorrente do chat.
- Para a primeira homologacao corporativa, a combinacao recomendada e `SQL Server + Parquet`, com `Redis` como etapa posterior.
- O template de ambiente para esta estrategia esta em `backend/.env.homologacao.example`.
