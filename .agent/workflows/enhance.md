---
description: Adicionar ou atualizar recursos em aplicação existente. Usado para desenvolvimento iterativo.
---

# /enhance - Atualizar Aplicação

$ARGUMENTS

---

## Tarefa

Este comando adiciona recursos ou faz atualizações em uma aplicação existente.

### Passos:

1. **Entender o Estado Atual**
   - Carregar o estado do projeto com `session_manager.py`
   - Entender os recursos existentes e a tech stack

2. **Planejar Mudanças**
   - Determinar o que será adicionado/alterado
   - Detectar arquivos afetados
   - Verificar dependências

3. **Apresentar Plano ao Usuário** (para mudanças grandes)
   ```
   "Para adicionar o painel administrativo:
   - Vou criar 15 novos arquivos
   - Atualizar 8 arquivos
   - Levará ~10 minutos
   
   Devo começar?"
   ```

4. **Aplicar**
   - Chamar os agentes relevantes
   - Fazer as alterações
   - Testar

5. **Atualizar Preview**
   - Hot reload ou reiniciar

---

## Exemplos de Uso

```
/enhance adicionar modo escuro
/enhance construir painel administrativo
/enhance integrar sistema de pagamento
/enhance adicionar recurso de busca
/enhance editar página de perfil
/enhance tornar responsivo
```

---

## Atenção

- Obtenha aprovação para mudanças grandes
- Avise sobre pedidos conflitantes (ex: "use Firebase" quando o projeto usa PostgreSQL)
- Commit de cada mudança com git
