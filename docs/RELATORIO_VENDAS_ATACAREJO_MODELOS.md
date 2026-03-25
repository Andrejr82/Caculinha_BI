# Modelos de Relatório de Vendas para Segmentos da Caçula

## Objetivo

Evoluir o relatório atual do chat de um formato muito sintético para um formato gerencial, acionável e compatível com o contexto de uma operação de atacarejo como a Caçula, para qualquer segmento da rede.

## Problema do formato atual

O formato atual:

- resume demais a análise
- não mostra a leitura de concentração do faturamento
- não diferencia liderança, cauda e dispersão entre lojas
- não conecta venda com mix, preço, estoque e ação comercial
- entrega uma tabela curta, mas pouca interpretação gerencial

Para um atacarejo, isso é insuficiente. O gestor precisa entender:

- onde está o faturamento
- onde está a perda de oportunidade
- se o problema é cobertura, mix, preço, execução ou demanda
- qual ação tomar por loja, faixa ou cluster

## Referências pesquisadas

### 1. Microsoft Learn: Retail Analysis Sample

A referência da Microsoft para varejo multi-loja usa como base:

- vendas do ano atual vs. ano anterior
- unidades
- margem bruta
- variância
- análise de novas lojas
- leitura por distrito/loja
- sales per square foot

Aplicação no projeto:

- comparar venda atual vs. período anterior por UNE
- destacar variância por loja
- separar líderes, medianas e cauda
- suportar drill-down por segmento, grupo e produto

### 2. Shopify: Sell-through, inventory turnover e inventory aging

As referências da Shopify reforçam que retail reporting não deve parar em faturamento. Para gestão comercial e de estoque, o relatório precisa considerar:

- sell-through
- turnover
- aging
- margem bruta

Aplicação no projeto:

- se o dataset suportar estoque/custo, o relatório de vendas deve evoluir para leitura conjunta de:
  - venda
  - margem
  - giro
  - cobertura
  - risco de estoque lento

### 3. Site da Lojas Caçula: categoria Tecidos

Na categoria `Tecidos` da Caçula aparecem sinais claros de operação que importam para o relatório:

- múltiplas marcas
- ampla faixa de preço
- atributo `Venda Metro`
- subcategorias específicas como TNT e Tricoline

Aplicação no projeto:

- relatório de Tecidos precisa olhar:
  - venda por loja
  - venda por marca
  - venda por faixa de preço
  - venda por subgrupo
  - itens vendidos por metro vs. unitários, quando houver dado

## Escopo

Este documento não vale só para `Tecidos`.

Ele foi pensado para qualquer segmento relevante da Caçula, por exemplo:

- Papelaria
- Tecidos
- Festas
- Artes
- Armarinho e Confecção
- Embalagens e Descartáveis
- Casa e Decoração
- Sazonais
- Higiene e Beleza

## Leitura recomendada para atacarejo

Para a Caçula, o melhor relatório de vendas no chat não deve ser apenas “top lojas”.

Ele deve combinar 4 blocos.

### 1. Performance

Responde:

- quanto vendeu
- em quantas lojas
- quem lidera
- quem está na cauda
- qual a concentração do faturamento

### 2. Mix e preço

Responde:

- quais marcas puxam o segmento
- quais subgrupos sustentam a venda
- onde o ticket/preço médio foge do padrão
- onde há potencial de ajuste comercial

### 3. Eficiência comercial

Responde:

- lojas fortes
- lojas frágeis
- lojas com oportunidade
- cluster de lojas com comportamento parecido

### 4. Ação operacional

Responde:

- o que fazer nos próximos 7 dias
- em quais lojas agir primeiro
- qual hipótese operacional validar

## Modelo recomendado para o projeto

## Catálogo de modelos

## Modelo 1: Relatório Gerencial de Vendas por Segmento e Loja

Usar como modelo padrão para consultas como:

- `relatório de vendas do segmento tecidos de todas as lojas`
- `analise vendas de papelaria em todas as unes`
- `me dê um relatório de vendas do grupo festas por loja`
- `quero um relatório de vendas do segmento artes em toda a rede`

### Estrutura recomendada

#### 1. Resumo executivo

Deve responder em 4 linhas:

- total vendido no segmento
- quantidade de lojas com venda
- loja líder e participação
- leitura principal da distribuição

Exemplo de forma:

`O segmento Tecidos vendeu R$ X no período, distribuído em Y UNEs. A UNE líder respondeu por Z% do faturamento, indicando concentração alta/moderada/baixa. A cauda de lojas sugere oportunidade comercial relevante em N unidades.`

#### 2. KPIs de abertura

Exibir sempre:

- venda total
- lojas com venda
- média por loja
- mediana por loja
- participação da Top 5
- participação da cauda
- amplitude entre líder e última loja

Se houver base suficiente:

- variação vs. período anterior
- ticket médio
- unidades vendidas
- preço médio

#### 3. Tabela operacional enriquecida

Trocar a tabela curta por uma tabela com mais valor.

Colunas recomendadas:

- UNE
- venda
- participação %
- ranking
- diferença para a média
- cluster
- sinal gerencial

Exemplo de sinal:

- `acima da média`
- `na média`
- `abaixo da média`
- `prioridade comercial`

#### 4. Leitura gerencial

Adicionar uma seção textual nova, entre tabela e ações:

- concentração do faturamento
- leitura da dispersão
- lojas com maior oportunidade
- hipótese dominante

Exemplo:

`A venda está concentrada em poucas UNEs, com forte diferença entre a líder e a base da cauda. Isso sugere que o segmento não está igualmente desenvolvido na rede. A leitura inicial aponta oportunidade de sortimento e execução comercial nas lojas de menor venda.`

#### 5. Próximas ações

As ações precisam ser específicas, não genéricas.

Modelo:

- revisar mix de Tecidos nas 5 menores UNEs
- comparar preço e profundidade de sortimento entre Top 5 e Bottom 5
- validar ruptura/exposição nas lojas com venda muito abaixo da mediana
- acompanhar D+7 após ação

## Modelo 2: Relatório de Mix e Marca

Usar quando a pergunta envolver:

- marcas
- preço
- linha
- subgrupo
- tecido por metro

Estrutura:

- resumo executivo
- marcas líderes
- subgrupos líderes
- faixas de preço
- oportunidades de sortimento

Esse modelo é especialmente importante quando o segmento tem muita variedade de portfólio, marcas ou faixas de preço. Em `Tecidos`, por exemplo, o site mostra:

- marcas diferentes
- subgrupos específicos
- atributo `Venda Metro`

## Modelo 3: Relatório de Execução por Loja

Usar quando a pergunta exigir decisão operacional.

Estrutura:

- lojas líderes
- lojas abaixo da mediana
- gap para média da rede
- lojas críticas
- plano de ação de 7 dias

## Modelo 4: Relatório Evolutivo

Usar quando houver período comparável.

Estrutura:

- venda atual
- venda período anterior
- variação %
- lojas que cresceram
- lojas que recuaram
- leitura do movimento

Esse é o modelo mais gerencial para diretoria/comercial.

## Modelo 5: Relatório de Participação na Rede

Usar quando a pergunta exigir leitura de peso relativo do segmento entre lojas.

Estrutura:

- participação da loja no total do segmento
- participação acumulada da Top 5
- concentração do faturamento
- lojas com share abaixo do esperado
- interpretação comercial

Exemplo de perguntas:

- `quais lojas concentram mais vendas do segmento papelaria`
- `me mostre a participação das unes no segmento festas`

## Modelo 6: Relatório de Cauda e Oportunidade

Usar quando a pergunta estiver orientada a ação comercial.

Estrutura:

- Bottom 5 lojas
- gap para mediana
- gap para média
- hipótese operacional
- ação prioritária por cluster

Exemplo de perguntas:

- `quais lojas têm pior desempenho no segmento artes`
- `onde estão as oportunidades no segmento casa e decoração`

## O que cabe no projeto hoje

Com alta confiança, o projeto já sustenta:

- venda por UNE
- ranking por loja
- análise por segmento/grupo/produto
- gráfico + tabela
- resumo executivo

Com dependência de campos adicionais, ele pode sustentar depois:

- margem bruta
- ticket médio
- unidades
- preço médio
- giro
- cobertura
- sell-through
- aging

## Proposta objetiva de melhoria do relatório do chat

Substituir o formato atual:

- resumo curto
- tabela curta
- ações genéricas

Pelo formato:

### Resumo executivo

- total vendido
- capilaridade
- concentração
- insight principal

### KPIs-chave

- venda total
- média por loja
- mediana por loja
- Top 5 share
- Bottom 5 share

### Tabela operacional

- UNE
- venda
- participação %
- ranking
- gap vs. média
- classificação

### Leitura gerencial

- o que o número significa
- se a rede está concentrada ou equilibrada
- onde está a oportunidade

### Próximas ações

- ação comercial
- ação de abastecimento
- ação de sortimento
- prazo de revisão

## Modelo-padrão recomendado para qualquer segmento

Se o usuário pedir simplesmente:

- `relatório de vendas do segmento X`
- `análise de vendas do segmento X em todas as lojas`

O padrão recomendado é:

1. Resumo executivo
2. KPIs-chave
3. Tabela operacional enriquecida
4. Leitura gerencial
5. Próximas ações

## Exemplo de saída-alvo para a Caçula

Pergunta:

`preciso de um relatório de vendas do segmento tecidos de todas as lojas`

Saída-alvo:

### Resumo executivo

- O segmento `Tecidos` apresenta desempenho distribuído em toda a rede, porém com concentração relevante nas lojas líderes. A diferença entre topo e cauda indica espaço para ganho comercial nas UNEs com menor penetração do segmento.

### KPIs-chave

- Venda total: `R$ X`
- Lojas com venda: `Y`
- Média por loja: `R$ Z`
- Mediana por loja: `R$ W`
- Participação Top 5: `A%`
- Participação Bottom 5: `B%`

### Tabela operacional

| UNE | Venda (R$) | Part. % | Ranking | Gap vs média | Classificação |
|---|---:|---:|---:|---:|---|
| 1685 | ... | ... | 1 | ... | liderança |
| 2365 | ... | ... | 2 | ... | acima da média |
| ... | ... | ... | ... | ... | ... |

### Leitura gerencial

- A liderança está concentrada em poucas UNEs.
- A mediana abaixo da média sugere assimetria de performance.
- As lojas da cauda podem estar com problema de mix, exposição ou baixa profundidade de sortimento.
- Em Tecidos, vale investigar também marcas, subgrupos e itens com venda por metro.

### Próximas ações

- Revisar mix de Tecidos nas 5 UNEs abaixo da mediana.
- Comparar marcas e subgrupos entre Top 5 e Bottom 5.
- Validar ruptura e cobertura dos itens líderes em Tecidos.
- Reavaliar após 7 dias com novo corte por loja.

## Recomendação final

Para a Caçula, o melhor padrão de relatório de vendas no chat, para qualquer segmento, é:

- `modelo gerencial por loja` como default
- `modelo de mix/marca` como aprofundamento
- `modelo evolutivo` quando houver comparação temporal

O relatório atual precisa evoluir para:

- mais KPI
- mais leitura gerencial
- mais contexto de atacarejo
- ações menos genéricas

Esse é o modelo mais aderente ao projeto e ao contexto comercial da empresa.
