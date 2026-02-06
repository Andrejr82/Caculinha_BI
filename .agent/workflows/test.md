---
description: Comando de geração e execução de testes. Cria e executa testes para o código.
---

# /test - Geração e Execução de Testes

$ARGUMENTS

---

## Propósito

Este comando gera testes, executa testes existentes ou verifica a cobertura de testes.

---

## Sub-comandos

```
/test                - Executar todos os testes
/test [arquivo/feature] - Gerar testes para um alvo específico
/test coverage       - Mostrar relatório de cobertura de testes
/test watch          - Executar testes no modo watch
```

---

## Comportamento

### Gerar Testes

Ao solicitar o teste de um arquivo ou feature:

1. **Analisar o código**
   - Identificar funções e métodos
   - Encontrar casos de borda
   - Detectar dependências para mock (simulação)

2. **Gerar casos de teste**
   - Testes de "caminho feliz" (happy path)
   - Casos de erro
   - Casos de borda
   - Testes de integração (se necessário)

3. **Escrever os testes**
   - Usar o framework de teste do projeto (Jest, Vitest, etc.)
   - Seguir padrões de teste existentes
   - Mockar dependências externas

---

## Formato de Saída

### Para Geração de Testes

```markdown
## 🧪 Testes: [Alvo]

### Plano de Teste
| Caso de Teste | Tipo | Cobertura |
|---------------|------|-----------|
| Deve criar usuário | Unitário | Happy path |
| Deve rejeitar e-mail inválido | Unitário | Validação |
| Deve lidar com erro de BD | Unitário | Caso de erro |

### Testes Gerados

`tests/[arquivo].test.ts`

[Bloco de código com os testes]

---

Execute com: `npm test`
```

### Para Execução de Testes

```
🧪 Executando testes...

✅ auth.test.ts (5 passaram)
✅ user.test.ts (8 passaram)
❌ order.test.ts (2 passaram, 1 falhou)

Falhou:
  ✗ deve calcular o total com desconto
    Esperado: 90
    Recebido: 100

Total: 15 testes (14 passaram, 1 falhou)
```

---

## Exemplos

```
/test src/services/auth.service.ts
/test fluxo de registro de usuário
/test coverage
/test corrigir testes que falharam
```

---

## Padrões de Teste

### Estrutura do Teste Unitário

```typescript
describe('AuthService', () => {
  describe('login', () => {
    it('deve retornar token para credenciais válidas', async () => {
      // Arrange (Preparar)
      const credentials = { email: 'test@test.com', password: 'pass123' };
      
      // Act (Agir)
      const result = await authService.login(credentials);
      
      // Assert (Verificar)
      expect(result.token).toBeDefined();
    });

    it('deve lançar erro para senha inválida', async () => {
      // Arrange (Preparar)
      const credentials = { email: 'test@test.com', password: 'wrong' };
      
      // Act & Assert (Agir & Verificar)
      await expect(authService.login(credentials)).rejects.toThrow('Credenciais inválidas');
    });
  });
});
```

---

## Princípios Chave

- **Teste o comportamento, não a implementação**
- **Uma asserção por teste** (quando prático)
- **Nomes de teste descritivos**
- **Padrão Arrange-Act-Assert**
- **Mockar dependências externas**
