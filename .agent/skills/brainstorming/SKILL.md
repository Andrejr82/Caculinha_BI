---
name: brainstorming
description: Protocolo de questionamento socrático + comunicação com o usuário. OBRIGATÓRIO para pedidos complexos, novas features ou requisitos incertos. Inclui relato de progresso e tratamento de erro.
allowed-tools: Read, Glob, Grep
---

# Protocolo de Brainstorming & Comunicação

> **OBRIGATÓRIO:** Use para pedidos complexos/vagos, novas features, atualizações.

---

## 🛑 SOCRATIC GATE (APLICAÇÃO)

### Quando Ativar

| Padrão | Ação |
|--------|------|
| "Construa/Crie/Faça [coisa]" sem detalhes | 🛑 PERGUNTE 3 questões |
| Feature complexa ou arquitetura | 🛑 Esclareça antes de implementar |
| Pedido de atualização/mudança | 🛑 Confirme o escopo |
| Requisitos vagos | 🛑 Pergunte o propósito, usuários, restrições |

### 🚫 OBRIGATÓRIO: 3 Questões Antes da Implementação

1. **PARE** - NÃO comece a codificar
2. **PERGUNTE** - No mínimo 3 questões:
   - 🎯 Propósito: Qual problema você está resolvendo?
   - 👥 Usuários: Quem vai usar isso?
   - 📦 Escopo: O que é essencial vs desejável?
3. **AGUARDE** - Obtenha resposta antes de prosseguir

---

## 🧠 Geração Dinâmica de Questões

**⛔ NUNCA use templates estáticos.** Leia `dynamic-questioning.md` para os princípios.

### Princípios Core

| Princípio | Significado |
|-----------|-------------|
| **Questões Revelam Consequências** | Cada pergunta se conecta a uma decisão arquitetural |
| **Contexto Antes do Conteúdo** | Entenda o contexto (greenfield/feature/refactor/debug) primeiro |
| **Questões Mínimas Viáveis** | Cada pergunta deve eliminar caminhos de implementação |
| **Gere Dados, Não Suposições** | Não adivinhe—pergunte apresentando trade-offs |

### Processo de Geração de Questões

```
1. Analisar pedido → Extrair domínio, features, indicadores de escala
2. Identificar pontos de decisão → Bloqueantes vs. adiáveis
3. Gerar questões → Prioridade: P0 (bloqueante) > P1 (alto valor) > P2 (desejável)
4. Formatar com trade-offs → O que, Por que, Opções, Padrão
```

### Formato de Questão (OBRIGATÓRIO)

```markdown
### [PRIORIDADE] **[PONTO DE DECISÃO]**

**Pergunta:** [Pergunta clara]

**Por que Isso Importa:**
- [Consequência arquitetural]
- [Afeta: custo/complexidade/cronograma/escala]

**Opções:**
| Opção | Prós | Contras | Melhor Para |
|-------|------|---------|-------------|
| A | [+] | [-] | [Caso de uso] |

**Se Não Especificado:** [Padrão + justificativa]
```

**Para bancos de questões e algoritmos específicos de domínio**, veja: `dynamic-questioning.md`

---

## Relato de Progresso (BASEADO EM PRINCÍPIOS)

**PRINCÍPIO:** Transparência gera confiança. O status deve estar visível e ser acionável.

### Formato do Quadro de Status

| Agente | Status | Tarefa Atual | Progresso |
|--------|--------|--------------|-----------|
| [Nome do Agente] | ✅🔄⏳❌⚠️ | [Descrição da tarefa] | [% ou contagem] |

### Ícones de Status

| Ícone | Significado | Uso |
|-------|-------------|-----|
| ✅ | Concluído | Tarefa finalizada com sucesso |
| 🔄 | Executando | Atualmente processando |
| ⏳ | Aguardando | Bloqueado, esperando dependência |
| ❌ | Erro | Falhou, precisa de atenção |
| ⚠️ | Aviso | Problema potencial, não bloqueante |

---

## Tratamento de Erros (BASEADO EM PRINCÍPIOS)

**PRINCÍPIO:** Erros são oportunidades para comunicação clara.

### Padrão de Resposta de Erro

```
1. Reconheça o erro
2. Explique o que aconteceu (de forma amigável ao usuário)
3. Ofereça soluções específicas com trade-offs
4. Peça ao usuário para escolher ou fornecer alternativa
```

### Categorias de Erro

| Categoria | Estratégia de Resposta |
|-----------|------------------------|
| **Conflito de Porta** | Ofereça porta alternativa ou feche a existente |
| **Dependência Faltando** | Instale automaticamente ou peça permissão |
| **Falha de Build** | Mostre o erro específico + correção sugerida |
| **Erro Obscuro** | Peça detalhes: screenshot, saída do console |

---

## Mensagem de Conclusão (BASEADO EM PRINCÍPIOS)

**PRINCÍPIO:** Celebre o sucesso, guie os próximos passos.

### Estrutura de Conclusão

```
1. Confirmação de sucesso (celebre brevemente)
2. Resumo do que foi feito (concreto)
3. Como verificar/testar (acionável)
4. Sugestão de próximos passos (proativo)
```

---

## Princípios de Comunicação

| Princípio | Implementação |
|-----------|---------------|
| **Conciso** | Sem detalhes desnecessários, vá ao ponto |
| **Visual** | Use emojis (✅🔄⏳❌) para escaneamento rápido |
| **Específico** | "~2 minutos" não "espere um pouco" |
| **Alternativas** | Ofereça múltiplos caminhos quando estiver travado |
| **Proativo** | Sugira o próximo passo após a conclusão |

---

## Anti-Padrões (EVITE)

| Anti-Padrão | Por quê |
|-------------|---------|
| Pular para soluções antes de entender | Desperdiça tempo no problema errado |
| Assumir requisitos sem perguntar | Gera saída errada |
| Excesso de engenharia na primeira versão | Atrasa a entrega de valor |
| Ignorar restrições | Cria soluções inutilizáveis |
| Frases como "Eu acho que" | Incerteza → Pergunte em vez disso |

---
