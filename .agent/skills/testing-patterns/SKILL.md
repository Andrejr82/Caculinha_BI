---
name: testing-patterns
description: Padrões e princípios de teste. Estratégias de unitário, integração e mock.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Padrões de Teste

> Princípios para suítes de teste confiáveis.

---

## 1. Pirâmide de Testes

```
        /\          E2E (Poucos)
       /  \         Fluxos críticos
      /----\
     /      \       Integração (Alguns)
    /--------\      API, consultas ao BD
   /          \
  /------------\    Unitário (Muitos)
                    Funções, classes
```

---

## 2. Padrão AAA

| Passo | Propósito |
|-------|-----------|
| **Arrange** (Preparar) | Configurar os dados do teste |
| **Act** (Agir) | Executar o código sob teste |
| **Assert** (Verificar) | Verificar o resultado |

---

## 3. Seleção do Tipo de Teste

### Quando Usar Cada Um

| Tipo | Ideal Para | Velocidade |
|------|------------|------------|
| **Unitário** | Funções puras, lógica | Rápido (<50ms) |
| **Integração** | API, BD, serviços | Médio |
| **E2E** | Fluxos críticos do usuário | Lento |

---

## 4. Princípios de Teste Unitário

### Bons Testes Unitários

| Princípio | Significado |
|-----------|-------------|
| Rápido | < 100ms cada |
| Isolado | Sem dependências externas |
| Repetível | Sempre o mesmo resultado |
| Auto-verificável | Sem verificação manual |
| Oportuno | Escrito junto com o código |

### O que Testar Unitariamente

| Testar | Não Testar |
|--------|------------|
| Lógica de negócio | Código do framework |
| Casos de borda | Bibliotecas de terceiros |
| Tratamento de erros | Getters simples |

---

## 5. Princípios de Teste de Integração

### O que Testar

| Área | Foco |
|------|------|
| Endpoints de API | Requisição/Resposta |
| Banco de Dados | Consultas, transações |
| Serviços externos | Contratos |

### Setup/Teardown (Configuração/Limpeza)

| Fase | Ação |
|------|------|
| Before All (Antes de todos) | Conectar recursos |
| Before Each (Antes de cada) | Resetar estado |
| After Each (Depois de cada) | Limpar |
| After All (Depois de todos) | Desconectar |

---

## 6. Princípios de Mocking (Simulação)

### Quando Mockar

| Mockar | Não Mockar |
|--------|------------|
| APIs externas | O código sob teste |
| Banco de dados (unitário) | Dependências simples |
| Tempo/aleatoriedade | Funções puras |
| Rede | Bancos de dados em memória |

### Tipos de Mock

| Tipo | Uso |
|------|-----|
| Stub | Retornar valores fixos |
| Spy | Rastrear chamadas |
| Mock | Definir expectativas |
| Fake | Implementação simplificada |

---

## 7. Organização de Testes

### Nomenclatura

| Padrão | Exemplo |
|--------|---------|
| Comportamento esperado | "deve retornar erro quando..." |
| Condição (When) | "quando usuário não encontrado..." |
| Dado-quando-então | "dado X, quando Y, então Z" |

### Agrupamento

| Nível | Uso |
|-------|-----|
| describe | Agrupar testes relacionados |
| it/test | Caso individual |
| beforeEach | Configuração comum |

---

## 8. Dados de Teste

### Estratégias

| Abordagem | Uso |
|-----------|-----|
| Factories | Gerar dados de teste |
| Fixtures | Conjuntos de dados predefinidos |
| Builders | Criação fluente de objetos |

### Princípios

- Use dados realistas
- Randomize valores não essenciais (faker)
- Compartilhe fixtures comuns
- Mantenha os dados mínimos

---

## 9. Melhores Práticas

| Prática | Por que |
|---------|---------|
| Uma asserção por teste | Razão de falha clara |
| Testes independentes | Sem dependência de ordem |
| Testes rápidos | Executar frequentemente |
| Nomes descritivos | Auto-documentado |
| Limpeza (Clean up) | Evitar efeitos colaterais |

---

## 10. Anti-Padrões

| ❌ Não faça | ✅ Faça |
|-------------|---------|
| Testar implementação | Testar comportamento |
| Duplicar código de teste | Usar factories |
| Setup de teste complexo | Simplificar ou dividir |
| Ignorar testes instáveis | Corrigir a causa raiz |
| Pular a limpeza | Resetar o estado |

---

> **Lembre-se:** Testes são documentação. Se alguém não conseguir entender o que o código faz através dos testes, reescreva-os.
