# ChatBI - Playbook de Treinamento (Dashboards e Analises)

## Objetivo
Habilitar usuarios de negocio a solicitar dashboards interativos e analises no ChatBI com prompts padronizados e verificaveis.

## Publico-alvo
- Comercial
- Compras
- BI/Controladoria
- Operacoes de loja

## Formato recomendado
- Duracao: 60 minutos
- Turma: ate 12 pessoas
- Modalidade: demo guiada + exercicio pratico

## Agenda
1. Visao geral do ChatBI e limites operacionais (10 min)
2. Como pedir dashboard interativo por segmento/periodo (15 min)
3. Pesquisa de mercado com evidencia e citacoes (10 min)
4. Calculos complexos (EOQ/sensibilidade) e interpretacao (10 min)
5. Boas praticas de prompt e refinamento (10 min)
6. Encerramento com checklist de adocao (5 min)

## Prompts recomendados
- Dashboard:
  - "gere um dashboard interativo do segmento ARTES nos ultimos 30 dias com top lojas e ruptura"
- Mercado:
  - "faca pesquisa de mercado de [produto] em RJ com fontes publicas e links"
- Calculo:
  - "calcule o eoq do item [sku] com demanda mensal [x], custo pedido [y], custo armazenagem [z]"
- Refinamento:
  - "refine o dashboard para UNE 1685 e compare com periodo anterior"

## Checklist de uso correto
- Sempre informar:
  - periodo
  - segmento/UNE
  - produto/SKU (quando aplicavel)
- Sempre verificar:
  - `source`, `confidence`, `citations`
  - filtros aplicados no dashboard

## Escalonamento
- Quando abrir chamado para TI, incluir:
  - pergunta original
  - `request_id`
  - horario aproximado
  - print da resposta

## Criterio de aprovacao do treinamento
- Cada participante conclui:
  - 1 dashboard por segmento
  - 1 consulta de mercado com citacao
  - 1 calculo complexo com resultado interpretado
