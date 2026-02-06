# Plano de Implementação Infalível - Sistema BI_Solution

## 📋 Resumo Executivo

Este plano detalha a estratégia completa para unificar o prompt do sistema BI_Solution, tornando-o production-ready sem falhas ou erros. O plano integra os insights do "Relatório de Análise Estratégica" com o novo "Prompt Mestre Unificado v2.1", garantindo robustez, especificidade e tratamento de erros em todos os níveis.

---

## 🔍 Análise da Arquitetura Atual

### Localização dos Prompts

| Arquivo | Linha | Status | Função |
|---------|-------|--------|--------|
| `backend/app/services/chat_service_v3.py` | 308-670 | **ATIVO** | Prompt principal do sistema (usado em produção) |
| `backend/app/core/agents/caculinha_bi_agent.py` | 73-74 | **DEPRECATED** | Fallback temporário (não usado) |

### Arquitetura de Fluxo Atual

```
Usuário → ChatServiceV3 → QueryInterpreter → MetricsCalculator → ContextBuilder → LLM (Narrative) → Resposta
                                                                                      ↓
                                                                              [SYSTEM_PROMPT]
```

**Conclusão:** O prompt está centralizado em `chat_service_v3.py` dentro do método `_generate_narrative()`.

---

## 🎯 Mudanças Propostas

### 1. Unificação do Prompt (CRÍTICO)

**Objetivo:** Substituir o prompt atual por uma versão unificada que incorpora:
- ✅ Protocolo Context7 Ultimate
- ✅ Análise de Sazonalidade obrigatória
- ✅ Fallback inteligente para ferramentas
- ✅ Estrutura de resposta universal (simples → complexa)

**Arquivo Alvo:** `backend/app/services/chat_service_v3.py`

**Mudança:**
- **Substituir:** Linhas 308-670 (prompt atual)
- **Por:** Novo prompt unificado (baseado em `Relatorio_Avaliacao_e_Prompt_Unificado.md`)

### 2. Criação de Módulo de Prompt Centralizado (ALTA PRIORIDADE)

**Problema:** Prompt hardcoded dentro do método dificulta manutenção.

**Solução:** Criar arquivo dedicado para gerenciamento de prompts.

**Novo Arquivo:** `backend/app/core/prompts/master_prompt.py`

**Estrutura:**
```python
"""
Master System Prompt - Context7 Ultimate v2.1
Centraliza todos os prompts do sistema para fácil manutenção.
"""

MASTER_PROMPT_V2_1 = """
# SYSTEM PROMPT: AGENTE ESTRATÉGICO DE BI (Context7 Ultimate v2.1)
...
"""

def get_system_prompt(mode: str = "default", has_chart: bool = False) -> str:
    """
    Retorna o prompt apropriado baseado no contexto.
    
    Args:
        mode: "default", "visual", "seasonal"
        has_chart: Se há gráfico na resposta
    
    Returns:
        System prompt formatado
    """
    prompt = MASTER_PROMPT_V2_1
    
    if has_chart:
        # Injetar instruções de modo visual
        prompt = f"[MODO VISUAL ATIVO]...\n{prompt}"
    
    return prompt
```

### 3. Integração de Sazonalidade (NOVO)

**Objetivo:** Adicionar detecção automática de períodos sazonais.

**Novo Arquivo:** `backend/app/core/utils/seasonality_detector.py`

**Funcionalidade:**
```python
from datetime import datetime
from typing import Dict, Optional

SEASONAL_PERIODS = {
    "volta_as_aulas": {
        "months": [1, 2],  # Janeiro-Fevereiro
        "coverage_days": 60,
        "urgency": "ALTA"
    },
    "natal": {
        "months": [11, 12],
        "coverage_days": 90,
        "urgency": "CRÍTICA"
    },
    "pascoa": {
        "months": [3, 4],
        "coverage_days": 45,
        "urgency": "MÉDIA"
    }
}

def detect_seasonal_context() -> Optional[Dict]:
    """Detecta se estamos em período sazonal."""
    current_month = datetime.now().month
    
    for season, config in SEASONAL_PERIODS.items():
        if current_month in config["months"]:
            return {
                "season": season,
                "coverage_days": config["coverage_days"],
                "urgency": config["urgency"],
                "message": f"MODO {season.upper().replace('_', ' ')} ATIVADO"
            }
    
    return None
```

### 4. Sistema de Fallback Robusto (CRÍTICO)

**Problema:** Se ferramentas falharem, o sistema não tem estratégia de degradação.

**Solução:** Implementar circuit breaker e fallback hierárquico.

**Arquivo:** `backend/app/core/utils/tool_fallback.py`

**Funcionalidade:**
```python
class ToolFallbackManager:
    """Gerencia fallbacks quando ferramentas falham."""
    
    def __init__(self):
        self.failure_count = {}
        self.circuit_open = {}
    
    async def execute_with_fallback(self, tool_name: str, tool_func, *args, **kwargs):
        """
        Executa ferramenta com fallback automático.
        
        Returns:
            Resultado da ferramenta ou fallback
        """
        try:
            # Verificar circuit breaker
            if self.circuit_open.get(tool_name, False):
                return self._get_fallback_response(tool_name)
            
            # Executar ferramenta
            result = await tool_func(*args, **kwargs)
            
            # Reset failure count on success
            self.failure_count[tool_name] = 0
            return result
            
        except Exception as e:
            # Incrementar contador de falhas
            self.failure_count[tool_name] = self.failure_count.get(tool_name, 0) + 1
            
            # Abrir circuit breaker após 3 falhas
            if self.failure_count[tool_name] >= 3:
                self.circuit_open[tool_name] = True
                logger.error(f"Circuit breaker OPEN para {tool_name}")
            
            # Retornar fallback
            return self._get_fallback_response(tool_name, error=str(e))
```

### 5. Validação de Resposta Aprimorada

**Objetivo:** Garantir que respostas sempre contenham dados específicos (não genéricos).

**Arquivo:** `backend/app/core/validators/response_validator.py`

**Funcionalidade:**
```python
def validate_response_specificity(response: str, context: str) -> Dict:
    """
    Valida se a resposta contém dados específicos do contexto.
    
    Returns:
        {
            "is_valid": bool,
            "errors": List[str],
            "suggestions": List[str]
        }
    """
    errors = []
    
    # Verificar se contém números do contexto
    context_numbers = re.findall(r'\d+[.,]?\d*', context)
    response_numbers = re.findall(r'\d+[.,]?\d*', response)
    
    if len(context_numbers) > 0 and len(response_numbers) == 0:
        errors.append("Resposta não contém dados numéricos específicos")
    
    # Verificar palavras genéricas proibidas
    generic_phrases = [
        "produtos em ruptura",
        "investigar problemas",
        "revisar itens críticos"
    ]
    
    for phrase in generic_phrases:
        if phrase.lower() in response.lower():
            errors.append(f"Frase genérica detectada: '{phrase}'")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "suggestions": ["Adicione nomes de produtos, SKUs ou valores específicos"]
    }
```

---

## 🚀 Plano de Implementação (Sequencial)

### Fase 1: Preparação (30 min)

- [ ] **1.1** Criar backup do arquivo `chat_service_v3.py`
  - Comando: `cp backend/app/services/chat_service_v3.py backend/app/services/chat_service_v3.py.backup`

- [ ] **1.2** Criar estrutura de diretórios
  ```bash
  mkdir -p backend/app/core/prompts
  mkdir -p backend/app/core/validators
  ```

- [ ] **1.3** Documentar prompt atual
  - Extrair linhas 308-670 de `chat_service_v3.py`
  - Salvar em `docs/archive/old_system_prompt.md`

### Fase 2: Implementação Core (1-2 horas)

- [ ] **2.1** Criar `backend/app/core/prompts/master_prompt.py`
  - Implementar `MASTER_PROMPT_V2_1` (baseado no relatório de avaliação)
  - Implementar função `get_system_prompt()`

- [ ] **2.2** Criar `backend/app/core/utils/seasonality_detector.py`
  - Implementar detecção de períodos sazonais
  - Adicionar testes unitários

- [ ] **2.3** Criar `backend/app/core/utils/tool_fallback.py`
  - Implementar `ToolFallbackManager`
  - Adicionar circuit breaker logic

- [ ] **2.4** Criar `backend/app/core/validators/response_validator.py`
  - Implementar `validate_response_specificity()`

### Fase 3: Integração (1 hora)

- [ ] **3.1** Modificar `chat_service_v3.py`
  - Importar `from app.core.prompts.master_prompt import get_system_prompt`
  - Substituir prompt hardcoded por chamada à função
  - Integrar `seasonality_detector` no início do método `_generate_narrative()`

- [ ] **3.2** Adicionar validação de resposta
  - Chamar `validate_response_specificity()` antes de retornar resposta
  - Implementar retry se validação falhar

### Fase 4: Testes e Validação (2-3 horas)

- [ ] **4.1** Testes Unitários
  - Testar `get_system_prompt()` com diferentes modos
  - Testar `seasonality_detector` para cada mês
  - Testar `ToolFallbackManager` com falhas simuladas

- [ ] **4.2** Testes de Integração
  - Testar fluxo completo com query simples
  - Testar fluxo com query complexa (sazonalidade)
  - Testar fallback quando ferramenta falha

- [ ] **4.3** Testes de Regressão
  - Executar suite de testes existente
  - Verificar se nenhuma funcionalidade quebrou

---

## ✅ Plano de Verificação

### Testes Automatizados

#### 1. Teste de Unidade - Prompt System

**Arquivo:** `backend/tests/test_master_prompt.py`

```python
def test_get_system_prompt_default():
    """Testa prompt padrão."""
    prompt = get_system_prompt()
    assert "Context7 Ultimate v2.1" in prompt
    assert "REGRAS DE OURO" in prompt

def test_get_system_prompt_visual_mode():
    """Testa modo visual."""
    prompt = get_system_prompt(has_chart=True)
    assert "MODO VISUAL ATIVO" in prompt

def test_seasonality_detection_january():
    """Testa detecção de Volta às Aulas."""
    # Mock datetime to January
    with patch('datetime.datetime') as mock_date:
        mock_date.now.return_value = datetime(2026, 1, 15)
        context = detect_seasonal_context()
        assert context["season"] == "volta_as_aulas"
        assert context["urgency"] == "ALTA"
```

**Como executar:**
```bash
cd backend
pytest tests/test_master_prompt.py -v
```

#### 2. Teste de Integração - Fluxo Completo

**Arquivo:** `backend/tests/integration/test_chat_flow.py`

```python
@pytest.mark.asyncio
async def test_simple_query_flow():
    """Testa query simples end-to-end."""
    service = ChatServiceV3(session_manager, parquet_path)
    
    response = await service.process_message(
        query="Quanto vendeu a loja 1685?",
        session_id="test_session",
        user_id="test_user"
    )
    
    assert response["type"] == "text"
    assert "loja" in response["result"]["mensagem"].lower()
    assert "1685" in response["result"]["mensagem"]

@pytest.mark.asyncio
async def test_seasonal_query_january():
    """Testa query em período sazonal."""
    with patch('datetime.datetime') as mock_date:
        mock_date.now.return_value = datetime(2026, 1, 15)
        
        response = await service.process_message(
            query="Devo comprar cadernos agora?",
            session_id="test_session",
            user_id="test_user"
        )
        
        # Deve mencionar Volta às Aulas
        assert "volta às aulas" in response["result"]["mensagem"].lower() or \
               "sazonal" in response["result"]["mensagem"].lower()
```

**Como executar:**
```bash
cd backend
pytest tests/integration/test_chat_flow.py -v
```

### Testes Manuais

#### Teste Manual 1: Verificação de Especificidade

**Objetivo:** Garantir que respostas não sejam genéricas.

**Passos:**
1. Iniciar backend: `cd backend && python main.py`
2. Iniciar frontend: `cd frontend-solid && npm run dev`
3. Fazer login no sistema
4. No chat, perguntar: "Quais produtos estão em ruptura?"
5. **Verificar:** A resposta deve conter:
   - ✅ Nomes específicos de produtos (ex: "PAPEL CHAMEX A4")
   - ✅ Códigos SKU (ex: "SKU 59294")
   - ✅ Valores numéricos (ex: "estoque: 0 unidades")
   - ❌ NÃO deve conter frases genéricas como "produtos em ruptura" sem especificar

#### Teste Manual 2: Sazonalidade (Janeiro/Fevereiro)

**Objetivo:** Verificar se o sistema detecta período de Volta às Aulas.

**Passos:**
1. Garantir que a data do sistema está em Janeiro ou Fevereiro
2. No chat, perguntar: "Devo comprar cadernos agora?"
3. **Verificar:** A resposta deve mencionar:
   - ✅ "Volta às Aulas" ou "período sazonal"
   - ✅ Recomendação de estoque para 60-90 dias
   - ✅ Urgência elevada

#### Teste Manual 3: Fallback de Ferramentas

**Objetivo:** Verificar comportamento quando ferramenta falha.

**Passos:**
1. Simular falha de ferramenta (desconectar banco de dados temporariamente)
2. No chat, fazer uma pergunta que exija consulta ao banco
3. **Verificar:** O sistema deve:
   - ✅ Retornar mensagem de erro clara (não crash)
   - ✅ Sugerir alternativa ao usuário
   - ❌ NÃO deve retornar stack trace ou erro técnico

---

## 📊 Critérios de Sucesso

### Obrigatórios (Must-Have)

- [ ] ✅ Prompt unificado implementado em `master_prompt.py`
- [ ] ✅ Todos os testes unitários passando (100%)
- [ ] ✅ Testes de integração passando (100%)
- [ ] ✅ Respostas sempre contêm dados específicos (validação automática)
- [ ] ✅ Sistema detecta sazonalidade corretamente
- [ ] ✅ Fallback funciona quando ferramentas falham
- [ ] ✅ Nenhuma regressão em funcionalidades existentes

### Desejáveis (Nice-to-Have)

- [ ] 🎯 Tempo de resposta < 2 segundos (95% das queries)
- [ ] 🎯 Logs estruturados para debugging
- [ ] 🎯 Métricas de qualidade de resposta (dashboard)

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Prompt muito longo (>4000 tokens) | Média | Alto | Dividir em seções condicionais (carregar apenas o necessário) |
| Quebra de compatibilidade com frontend | Baixa | Alto | Manter estrutura de resposta JSON idêntica |
| Degradação de performance | Média | Médio | Implementar cache de prompt, lazy loading |
| Falha em produção | Baixa | Crítico | Feature flag para rollback instantâneo |

---

## 📝 Checklist Final de Deploy

Antes de considerar o sistema production-ready:

- [ ] Todos os testes automatizados passando
- [ ] Testes manuais executados e documentados
- [ ] Backup do sistema atual criado
- [ ] Feature flag implementada para rollback
- [ ] Documentação atualizada (`README.md`, `GEMINI.md`)
- [ ] Logs de monitoramento configurados
- [ ] Revisão de código por outro desenvolvedor
- [ ] Teste em ambiente de staging
- [ ] Plano de rollback documentado

---

## 🎯 Próximos Passos Após Aprovação

1. **Executar Fase 1** (Preparação) - 30 min
2. **Executar Fase 2** (Implementação Core) - 2 horas
3. **Executar Fase 3** (Integração) - 1 hora
4. **Executar Fase 4** (Testes) - 3 horas
5. **Revisão Final** - 1 hora
6. **Deploy em Staging** - 30 min
7. **Deploy em Produção** (após validação) - 30 min

**Tempo Total Estimado:** 8 horas de trabalho focado

---

## 📚 Referências

- [Relatório de Análise Estratégica](file:///D:/Dev/Agente_BI/BI_Solution/Relatório%20de%20Análise%20Estratégica%20e%20Prontidão%20Tecnológica_%20BI_Solution%20para%20Lojas%20Caçula.md)
- [Prompt Mestre Unificado v2.1](file:///D:/Dev/Agente_BI/BI_Solution/Relatorio_Avaliacao_e_Prompt_Unificado.md)
- [Chat Service V3 (Atual)](file:///D:/Dev/Agente_BI/BI_Solution/backend/app/services/chat_service_v3.py)
