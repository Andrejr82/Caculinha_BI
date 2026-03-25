# Matriz de Modelos LLM por Task

## Objetivo

Definir uma matriz objetiva de escolha de modelos para o `Caculinha_BI`, considerando:

- arquitetura real do projeto
- providers atualmente suportados
- tasks operacionais do sistema
- qualidade de resposta
- latencia
- estabilidade
- compatibilidade com function calling e tool orchestration

Este documento nao propoe providers novos. Ele considera apenas modelos que o projeto consegue usar hoje sem criar um adapter novo.

## Escopo tecnico real do projeto

Hoje o sistema suporta nativamente:

- `Groq`
- `Google/Gemini`
- `mock`

Referencias de codigo:

- [llm_factory.py](c:/Projetos_BI/Caculinha_BI/backend/app/core/llm_factory.py)
- [llm_groq_adapter.py](c:/Projetos_BI/Caculinha_BI/backend/app/core/llm_groq_adapter.py)
- [llm_genai_adapter.py](c:/Projetos_BI/Caculinha_BI/backend/app/core/llm_genai_adapter.py)
- [settings.py](c:/Projetos_BI/Caculinha_BI/backend/app/config/settings.py)

Configuracao atual relevante:

- `LLM_PROVIDER=groq`
- `GROQ_MODEL_NAME=llama-3.3-70b-versatile`
- `INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile`
- `CODE_GENERATION_MODEL=llama-3.3-70b-versatile`

## Requisitos do projeto para escolha de modelo

Os modelos escolhidos precisam atender ao comportamento do sistema como ele existe hoje:

- responder bem em portugues
- sustentar tool use e function calling
- produzir saida executiva relativamente controlada
- nao degradar o roteamento do agente
- trabalhar bem com fluxos de grafico, dashboard e basket
- manter estabilidade para perguntas com e sem anexo
- evitar verbosidade excessiva no chat operacional
- operar com latencia aceitavel em ambiente interno

## Fontes oficiais consideradas

Groq:

- [Supported Models](https://console.groq.com/docs/models)
- [GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b)
- [Deprecations](https://console.groq.com/docs/deprecations)

Google:

- [Gemini Models](https://ai.google.dev/models/gemini)

OpenAI:

- [OpenAI Models](https://platform.openai.com/docs/models)

## Benchmark local ja executado no projeto

Comparacao real feita na API Groq com a chave configurada no projeto:

- `llama-3.3-70b-versatile`
- `openai/gpt-oss-120b`

Prompts usados:

- insight executivo de BI
- interpretacao de intencao de grafico
- guardrail de anexo x base local

Resumo observado:

- `llama-3.3-70b-versatile`
  - media de latencia aproximada: `1.75s`
  - mais estavel
  - menos verboso
  - melhor candidato para default operacional

- `openai/gpt-oss-120b`
  - media de latencia aproximada: `2.00s`
  - melhor estruturacao e reasoning em respostas mais complexas
  - mais verboso
  - maior consumo de tokens
  - bom candidato de canario, nao de troca imediata do default

Conclusao do benchmark:

- manter `llama-3.3-70b-versatile` como baseline
- testar `openai/gpt-oss-120b` apenas em homologacao controlada

## Modelos considerados aptos para o projeto

### Aptos para uso imediato por configuracao

#### Groq

1. `llama-3.3-70b-versatile`
- status: adequado para producao
- papel: baseline principal do sistema
- uso ideal: chat geral, graficos, basket, orchestracao geral

2. `openai/gpt-oss-120b`
- status: candidato forte e atual na Groq
- papel: canario de qualidade
- uso ideal: codigo, respostas mais sofisticadas, raciocinio mais profundo

3. `llama-3.1-8b-instant`
- status: apto tecnicamente
- papel: candidato de baixa latencia
- uso ideal: classificacao curta, prompts simples, alto volume
- observacao: ainda nao validado no projeto para trocar o modelo de intencao

#### Google

4. `gemini-2.5-pro`
- status: apto
- papel: fallback premium e tarefas de pesquisa mais longas
- uso ideal: pesquisa de mercado, contexto longo, sintese mais extensa

5. `gemini-2.5-flash`
- status: apto
- papel: alternativa mais rapida dentro do provider Google
- uso ideal: cargas medias quando houver necessidade de Google com menor latencia

### Excluidos da recomendacao principal

#### Excluidos por preview

- `gemini-3-pro-preview`
- `gemini-3-flash-preview`
- `qwen/qwen3-32b` na Groq

Motivo:

- nao sao a melhor escolha para baseline produtivo do projeto neste momento
- podem ser avaliados em laboratorio, mas nao entram na matriz principal

#### Excluidos por arquitetura atual

- `GPT-5`, `GPT-5 pro`, `GPT-5 mini`, `GPT-5 nano`
- `Claude 4`
- qualquer outro modelo que exija provider novo

Motivo:

- o projeto nao tem adapter nativo para OpenAI Responses API ou Anthropic
- adotar esses modelos exigiria nova camada de provider

#### Excluidos por descontinuacao ou troca de geracao

- modelos Groq oficialmente depreciados

Motivo:

- nao faz sentido planejar sobre base que a Groq esta aposentando

## Matriz por task

## 1. Chat geral

### Caracteristicas da task

- alta frequencia
- precisa de boa qualidade em portugues
- precisa manter tool use
- precisa ser objetiva
- nao pode ficar excessivamente verbosa

### Recomendacao

- baseline: `llama-3.3-70b-versatile`
- canario: `openai/gpt-oss-120b`
- fallback premium: `gemini-2.5-pro`

### Decisao

Use `llama-3.3-70b-versatile` como modelo principal do chat geral.

Motivo:

- passou melhor como default operacional
- equilibrio melhor entre qualidade, latencia e controle
- menos risco de respostas longas demais

## 2. Intencao

### Caracteristicas da task

- classificacao curta
- baixa latencia e previsibilidade importam mais que narrativa
- resposta deve ser consistente

### Recomendacao

- baseline atual aprovado: `llama-3.3-70b-versatile`
- candidato de otimizacao: `llama-3.1-8b-instant`

### Decisao

No estado atual do projeto, manter `INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile`.

Otimizacao futura possivel:

- testar `llama-3.1-8b-instant` em canario tecnico

Motivo:

- o projeto ainda nao validou um classificador separado em producao
- para nao introduzir regressao de roteamento, o baseline atual deve permanecer

## 3. Grafico

### Caracteristicas da task

- exige entendimento correto da intencao
- precisa acionar tools corretas
- precisa manter coerencia de payload visual
- latencia importa, mas estabilidade importa mais

### Recomendacao

- baseline: `llama-3.3-70b-versatile`
- canario: `openai/gpt-oss-120b`
- fallback: `gemini-2.5-pro`

### Decisao

Usar `llama-3.3-70b-versatile` como modelo padrao para fluxos de grafico e dashboard.

Motivo:

- a task depende mais de orchestracao correta do que de reasoning longo
- o modelo atual ja se encaixa melhor no comportamento de producao

## 4. Basket

### Caracteristicas da task

- a parte critica e calculada pelo servico
- o LLM entra principalmente em resumo executivo e explicacao
- precisa ser honesto quando a base estiver `unsupported`

### Recomendacao

- baseline: `llama-3.3-70b-versatile`
- canario: `openai/gpt-oss-120b`

### Decisao

Manter `llama-3.3-70b-versatile`.

Motivo:

- basket aqui nao depende de reasoning livre como nucleo
- a prioridade e resposta executiva clara e controlada
- o ganho do `gpt-oss-120b` nao justifica troca imediata do default

## 5. Codigo

### Caracteristicas da task

- pede melhor reasoning tecnico
- beneficia-se de modelos mais fortes em codigo e estrutura
- tolera um pouco mais de latencia que o chat geral

### Recomendacao

- baseline atual: `llama-3.3-70b-versatile`
- canario recomendado: `openai/gpt-oss-120b`
- fallback premium: `gemini-2.5-pro`

### Decisao

Se houver um unico ponto para testar melhoria real, o melhor candidato e:

- `CODE_GENERATION_MODEL=openai/gpt-oss-120b`

Motivo:

- foi o melhor candidato global para qualidade
- o custo de maior latencia e mais aceitavel em codigo do que no chat geral

## 6. Pesquisa de mercado

### Caracteristicas da task

- precisa sintetizar evidencias
- pode exigir mais contexto
- costuma aceitar latencia um pouco maior
- a fabrica ja prefere Google para `market_research` e `competitive_research`

### Recomendacao

- baseline recomendado por task: `gemini-2.5-pro`
- fallback: `llama-3.3-70b-versatile`
- alternativa rapida: `gemini-2.5-flash`

### Decisao

Para `market_research` e `competitive_research`, a melhor matriz teorica do projeto hoje e:

- primario: `gemini-2.5-pro`
- fallback: `groq`

Motivo:

- o proprio `SmartLLM` ja foi desenhado com preferencia `google -> groq` para essas tasks
- essa task tolera mais latencia e se beneficia de maior folego de sintese

## Matriz resumida

| Task | Baseline recomendado | Canario recomendado | Fallback recomendado | Decisao pratica |
|---|---|---|---|---|
| Chat geral | `llama-3.3-70b-versatile` | `openai/gpt-oss-120b` | `gemini-2.5-pro` | manter baseline atual |
| Intencao | `llama-3.3-70b-versatile` | `llama-3.1-8b-instant` | `gemini-2.5-flash` | manter baseline atual |
| Grafico | `llama-3.3-70b-versatile` | `openai/gpt-oss-120b` | `gemini-2.5-pro` | manter baseline atual |
| Basket | `llama-3.3-70b-versatile` | `openai/gpt-oss-120b` | `gemini-2.5-pro` | manter baseline atual |
| Codigo | `llama-3.3-70b-versatile` | `openai/gpt-oss-120b` | `gemini-2.5-pro` | melhor ponto para canario |
| Pesquisa de mercado | `gemini-2.5-pro` | `gemini-2.5-flash` | `llama-3.3-70b-versatile` | seguir preferencia google->groq |

## Configuracao recomendada agora

### Producao ou baseline estavel

```env
LLM_PROVIDER=groq
GROQ_MODEL_NAME=llama-3.3-70b-versatile
INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile
CODE_GENERATION_MODEL=llama-3.3-70b-versatile
LLM_TASK_PROVIDER_ROUTING=market_research=google,groq;competitive_research=google,groq;visualization=groq,google;dashboard=groq,google;calculation=groq,google;analysis=groq,google;data_query=groq,google
LLM_MODEL_NAME=gemini-2.5-pro
```

### Canario recomendado

```env
LLM_PROVIDER=groq
GROQ_MODEL_NAME=openai/gpt-oss-120b
INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile
CODE_GENERATION_MODEL=openai/gpt-oss-120b
LLM_TASK_PROVIDER_ROUTING=market_research=google,groq;competitive_research=google,groq;visualization=groq,google;dashboard=groq,google;calculation=groq,google;analysis=groq,google;data_query=groq,google
LLM_MODEL_NAME=gemini-2.5-pro
```

## Politica recomendada de adocao

### O que manter

- manter `llama-3.3-70b-versatile` como default do sistema

### O que testar

- testar `openai/gpt-oss-120b` em homologacao
- testar primeiro em codigo
- depois testar em chat geral

### O que nao fazer agora

- nao trocar o modelo de intencao em producao sem canario proprio
- nao adotar preview como baseline
- nao adicionar provider novo antes da homologacao multiusuario

## Decisao final recomendada

### Se a pergunta for "qual modelo deve continuar como padrao do sistema?"

Resposta:

- `llama-3.3-70b-versatile`

### Se a pergunta for "qual modelo vale testar como evolucao real?"

Resposta:

- `openai/gpt-oss-120b`

### Se a pergunta for "qual task mais faz sentido receber canario primeiro?"

Resposta:

- `codigo`

### Se a pergunta for "qual task mais naturalmente combina com Google?"

Resposta:

- `pesquisa de mercado`
