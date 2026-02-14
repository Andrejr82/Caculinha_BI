# Code Chat Mecânico com Capacidade de Reparos

## Objetivo
Evoluir o Code Chat de assistente de leitura/explicação para um agente de manutenção de código com diagnóstico, geração de patch e aplicação segura com validação automática.

---

## Escopo Funcional

### Nível 1 - Diagnóstico
- Receber erro/sintoma + contexto do usuário.
- Mapear arquivos e módulos prováveis.
- Gerar hipótese de causa raiz com evidências.
- Sugerir plano de correção em passos.

### Nível 2 - Reparo Assistido
- Gerar patch/diff explícito por arquivo.
- Exibir impacto esperado, riscos e testes recomendados.
- Exigir aprovação humana para aplicar.

### Nível 3 - Reparo Automático Seguro
- Aplicar patch em branch isolada.
- Executar validações (lint, testes, smoke).
- Se falhar: rollback automático.
- Produzir relatório final de execução.

---

## Arquitetura Proposta

### Componentes
1. `RepairOrchestrator`
- Coordena todo o fluxo de diagnóstico -> patch -> validação -> rollback.

2. `FailureClassifier`
- Classifica tipo de falha (build, runtime, integração, regressão, segurança).

3. `PatchPlanner`
- Define arquivos-alvo, estratégia de edição e critérios de aceitação.

4. `PatchExecutor`
- Gera e aplica alterações em modo controlado.

5. `ValidationRunner`
- Executa suíte mínima obrigatória por contexto.

6. `SafetyPolicyEngine`
- Aplica regras de permissão, risco e aprovação.

7. `AuditTrail`
- Registra tudo: entrada, decisões, patch, comandos, resultado, rollback.

---

## Fluxo de Execução

1. Entrada
- Usuário envia problema com stacktrace, objetivo e escopo.

2. Triagem
- Classificação da falha e seleção de estratégia.

3. Diagnóstico
- Localização de causas prováveis + evidências no código.

4. Proposta
- Patch em diff + explicação de impacto.

5. Gate de segurança
- Aprovação humana obrigatória para classes de risco alto.

6. Aplicação
- Edição em branch de reparo (`fix/auto-*`).

7. Validação
- Lint + testes + healthchecks.

8. Decisão
- Sucesso: gerar relatório e PR.
- Falha: rollback + relatório de falha.

---

## Guardrails de Segurança

### Política de Escopo
- Permitido: pastas de aplicação previamente autorizadas.
- Bloqueado por padrão: secrets, infra crítica, migrações destrutivas.

### Classes de Risco
- **Baixo**: UI, docs, testes isolados.
- **Médio**: serviços de domínio, roteamento, integração interna.
- **Alto**: autenticação, autorização, pagamentos, dados sensíveis, SQL destrutivo.

### Regras Obrigatórias
- Nunca aplicar alterações de risco alto sem aprovação explícita.
- Nunca executar comandos destrutivos sem confirmação.
- Sempre gerar diff auditável.
- Sempre rodar validação pós-reparo.
- Sempre suportar rollback.

---

## Contratos de API (sugestão)

### `POST /api/v1/code-chat/repair/diagnose`
Entrada:
```json
{
  "issue": "string",
  "context": "string",
  "scope": ["backend/app", "frontend-solid/src"],
  "artifacts": ["traceback", "logs"]
}
```
Saída:
```json
{
  "classification": "runtime_error",
  "suspects": ["backend/app/services/chat_service_v3.py"],
  "root_cause_hypothesis": "...",
  "confidence": 0.78,
  "plan": ["..."]
}
```

### `POST /api/v1/code-chat/repair/propose`
Entrada:
```json
{
  "diagnosis_id": "string",
  "constraints": {
    "no_schema_changes": true,
    "max_files": 5
  }
}
```
Saída:
```json
{
  "patch": "unified diff",
  "files": ["..."],
  "risk": "medium",
  "tests_to_run": ["pytest backend/tests/..."],
  "rollback_plan": "git restore --source ..."
}
```

### `POST /api/v1/code-chat/repair/apply`
Entrada:
```json
{
  "proposal_id": "string",
  "approved": true,
  "validation_profile": "standard"
}
```
Saída:
```json
{
  "applied": true,
  "branch": "fix/auto-2026-...",
  "validation": {
    "lint": "pass",
    "tests": "pass",
    "smoke": "pass"
  },
  "rollback_executed": false,
  "report_path": "artifacts/repair_report_...md"
}
```

---

## Experiência no Frontend (Code Chat)

### Novo Painel: `Repair Mode`
- Campos: problema, escopo, anexos, nível de autonomia.
- Etapas visíveis: Diagnóstico -> Proposta -> Aprovação -> Execução -> Resultado.
- Botões:
  - `Diagnosticar`
  - `Gerar patch`
  - `Aplicar com validação`
  - `Rollback`

### Modos de Operação
- `read_only` (somente diagnóstico)
- `assistive` (gera patch, usuário aplica)
- `auto_safe` (aplica com validação e rollback)

---

## Observabilidade e Auditoria

- Logs estruturados por execução (`repair_id`).
- Métricas:
  - taxa de reparo bem-sucedido
  - tempo médio de reparo
  - taxa de rollback
  - quantidade de reparos por classe de risco
- Artefatos:
  - diff aplicado
  - comandos executados
  - saída dos testes
  - decisão final

---

## Plano de Entrega (Sprints)

### Sprint 1 (base segura)
- Diagnóstico + proposta de patch.
- Guardrails iniciais.
- Modo `assistive`.

### Sprint 2 (execução controlada)
- Aplicação automática em branch isolada.
- Runner de validação padrão.
- Rollback automático.

### Sprint 3 (produção)
- Política de risco completa.
- Telemetria + painel de saúde.
- PR automático com relatório.

---

## Critérios de Pronto

- Nenhuma alteração é aplicada sem rastreabilidade.
- Reparos de risco alto exigem aprovação explícita.
- Cada execução gera relatório completo.
- Rollback funcional e testado.
- Taxa de sucesso operacional monitorada.

---

## Riscos e Mitigações

1. Patch incorreto
- Mitigação: validação automática + rollback + aprovação humana.

2. Escopo excessivo
- Mitigação: limite de arquivos alterados por execução.

3. Falha silenciosa
- Mitigação: logs estruturados + status por etapa + relatório obrigatório.

4. Impacto em segurança
- Mitigação: `SafetyPolicyEngine` com bloqueios por classe de risco.

---

## Decisão Recomendada
Implementar em modo incremental (`assistive` -> `auto_safe`) com segurança como default, mantendo o Code Chat como ferramenta de suporte técnico confiável para analistas e desenvolvedores de BI.
