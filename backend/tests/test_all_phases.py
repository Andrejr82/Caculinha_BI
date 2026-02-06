"""
Testes Robustos - Todas as 5 Fases de Implementação
Executa testes completos de cada módulo implementado
"""

import sys
import os
import json
from pathlib import Path

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)

def print_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"   {status}: {name}")
    if details:
        print(f"      → {details}")


class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, phase: str, test: str, passed: bool, details: str = ""):
        self.results.append({
            "phase": phase,
            "test": test,
            "passed": passed,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print_result(test, passed, details)
    
    def test_fase1_thinking_mode(self):
        """Testa Fase 1: Gemini Thinking Mode"""
        print_header("FASE 1: Gemini Thinking Mode")
        
        try:
            from app.config.settings import settings
            
            # Teste 1: Verificar modelo configurado
            model = settings.LLM_MODEL_NAME
            passed = "gemini" in model.lower()
            self.add_result("Fase 1", "Modelo Gemini configurado", passed, f"Modelo: {model}")
            
            # Teste 2: Verificar import do adapter
            from app.core.llm_gemini_adapter import GeminiLLMAdapter
            self.add_result("Fase 1", "Import GeminiLLMAdapter", True, "Import OK")
            
            # Teste 3: Verificar GenerationConfig
            import google.generativeai as genai
            config = genai.GenerationConfig(temperature=0.7, max_output_tokens=8192)
            self.add_result("Fase 1", "GenerationConfig criado", True, f"temp={config.temperature}")
            
        except Exception as e:
            self.add_result("Fase 1", "Erro geral", False, str(e))
    
    def test_fase2_semantic_cache(self):
        """Testa Fase 2: Semantic Caching"""
        print_header("FASE 2: Semantic Caching")
        
        try:
            from app.core.utils.semantic_cache import SemanticCache, cache_get, cache_set, cache_stats
            
            # Teste 1: Criar instância
            cache = SemanticCache(cache_dir="data/cache/test_semantic", ttl_minutes=60)
            self.add_result("Fase 2", "SemanticCache criado", True, f"Dir: {cache.cache_dir}")
            
            # Teste 2: Set e Get
            test_query = "Qual o estoque total?"
            test_response = {"type": "text", "result": "Estoque: 1000 unidades"}
            
            cache.set(test_query, test_response)
            cached = cache.get(test_query)
            
            passed = cached is not None and cached.get("result") == test_response["result"]
            self.add_result("Fase 2", "Cache SET e GET", passed, "Resposta cacheada corretamente")
            
            # Teste 3: Normalização de query
            normalized = cache._normalize_query("  QUAL O ESTOQUE TOTAL?  ")
            passed = normalized == "qual o estoque total"
            self.add_result("Fase 2", "Normalização de query", passed, f"'{normalized}'")
            
            # Teste 4: Estatísticas
            stats = cache.get_stats()
            passed = "hits" in stats and "misses" in stats
            self.add_result("Fase 2", "Estatísticas funcionam", passed, f"Hits: {stats['hits']}")
            
            # Limpar teste
            cache.clear()
            
        except Exception as e:
            self.add_result("Fase 2", "Erro geral", False, str(e))
    
    def test_fase3_response_validator(self):
        """Testa Fase 3: Response Validator"""
        print_header("FASE 3: Response Validator")
        
        try:
            from app.core.utils.response_validator import (
                ResponseValidator, validate_response, validator_stats, ValidationResult
            )
            
            # Teste 1: Criar instância
            validator = ResponseValidator()
            self.add_result("Fase 3", "ResponseValidator criado", True, f"Colunas: {len(validator.VALID_COLUMNS)}")
            
            # Teste 2: Validar resposta válida
            good_response = {"result": "O estoque total da UNE 261 é de 5.000 unidades."}
            result = validator.validate(good_response, "Qual o estoque?")
            passed = result.confidence >= 0.7
            self.add_result("Fase 3", "Resposta válida aceita", passed, f"Confiança: {result.confidence:.2f}")
            
            # Teste 3: Detectar resposta vazia
            empty_response = {"result": ""}
            result = validator.validate(empty_response, "teste")
            passed = result.confidence < 1.0 and len(result.issues) > 0
            self.add_result("Fase 3", "Resposta vazia detectada", passed, f"Issues: {result.issues}")
            
            # Teste 4: Detectar alucinação
            uncertain_response = {"result": "Provavelmente o estoque é de 100 unidades, talvez mais."}
            result = validator.validate(uncertain_response, "estoque")
            passed = result.confidence < 1.0  # Deve ter menor confiança
            self.add_result("Fase 3", "Alucinação detectada", passed, f"Confiança: {result.confidence:.2f}")
            
            # Teste 5: Estatísticas
            stats = validator.get_stats()
            passed = stats["total_validations"] >= 3
            self.add_result("Fase 3", "Estatísticas funcionam", passed, f"Validações: {stats['total_validations']}")
            
        except Exception as e:
            self.add_result("Fase 3", "Erro geral", False, str(e))
    
    def test_fase4_multi_step_agent(self):
        """Testa Fase 4: LangGraph Multi-Step"""
        print_header("FASE 4: LangGraph Multi-Step Agent")
        
        try:
            from app.core.agents.multi_step_agent import (
                MultiStepAgent, AgentState, LANGGRAPH_AVAILABLE
            )
            
            # Teste 1: Import bem-sucedido
            self.add_result("Fase 4", "Import MultiStepAgent", True, f"LangGraph: {LANGGRAPH_AVAILABLE}")
            
            # Teste 2: Verificar AgentState
            state_keys = list(AgentState.__annotations__.keys())
            expected_keys = ["query", "plan", "tool_calls", "results", "response"]
            passed = all(k in state_keys for k in expected_keys)
            self.add_result("Fase 4", "AgentState estruturado", passed, f"Keys: {len(state_keys)}")
            
            # Teste 3: Criar instância (mock agent)
            class MockAgent:
                def run(self, query, history=None):
                    return {"type": "text", "result": f"Mock: {query}"}
            
            multi_agent = MultiStepAgent(agent=MockAgent())
            self.add_result("Fase 4", "MultiStepAgent criado", True, f"Max iter: {multi_agent.MAX_ITERATIONS}")
            
            # Teste 4: Executar (fallback simples)
            result = multi_agent._run_simple("teste query")
            passed = "result" in result or "type" in result
            self.add_result("Fase 4", "Execução simplificada", passed, f"Result type: {type(result)}")
            
            # Teste 5: Estatísticas
            stats = multi_agent.get_stats()
            passed = "execution_count" in stats
            self.add_result("Fase 4", "Estatísticas funcionam", passed, f"Execuções: {stats['execution_count']}")
            
        except Exception as e:
            self.add_result("Fase 4", "Erro geral", False, str(e))
    
    def test_fase5_code_interpreter(self):
        """Testa Fase 5: Code Interpreter"""
        print_header("FASE 5: Code Interpreter")
        
        try:
            from app.core.tools.code_interpreter import (
                CodeInterpreter, get_interpreter, ALLOWED_MODULES, BLOCKED_FUNCTIONS
            )
            
            # Teste 1: Criar instância
            interpreter = CodeInterpreter()
            self.add_result("Fase 5", "CodeInterpreter criado", True, f"Timeout: {interpreter.timeout}s")
            
            # Teste 2: Executar código simples
            result = interpreter.execute("result = 2 + 2")
            passed = result["success"] and result["result"] == 4
            self.add_result("Fase 5", "Código simples executado", passed, f"2+2={result.get('result')}")
            
            # Teste 3: Bloquear código perigoso
            result = interpreter.execute("import os; os.system('ls')")
            passed = not result["success"]
            self.add_result("Fase 5", "Código perigoso bloqueado", passed, f"Erro: {result.get('error', 'N/A')[:50]}")
            
            # Teste 4: Usar pandas
            result = interpreter.execute("""
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
result = df['a'].sum()
""")
            passed = result["success"] and result["result"] == 6
            self.add_result("Fase 5", "Pandas funciona", passed, f"Sum: {result.get('result')}")
            
            # Teste 5: Estatísticas
            stats = interpreter.get_stats()
            passed = stats["execution_count"] >= 3
            self.add_result("Fase 5", "Estatísticas funcionam", passed, f"Execuções: {stats['execution_count']}")
            
        except Exception as e:
            self.add_result("Fase 5", "Erro geral", False, str(e))
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "=" * 70)
        print("🚀 TESTES ROBUSTOS - TODAS AS 5 FASES")
        print("=" * 70)
        
        self.test_fase1_thinking_mode()
        self.test_fase2_semantic_cache()
        self.test_fase3_response_validator()
        self.test_fase4_multi_step_agent()
        self.test_fase5_code_interpreter()
        
        # Resumo final
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES")
        print("=" * 70)
        
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n   Total de testes: {total}")
        print(f"   ✅ Passaram: {self.passed}")
        print(f"   ❌ Falharam: {self.failed}")
        print(f"   📈 Taxa de sucesso: {percentage:.1f}%")
        
        # Por fase
        print("\n   Por fase:")
        phases = {}
        for r in self.results:
            phase = r["phase"]
            if phase not in phases:
                phases[phase] = {"passed": 0, "failed": 0}
            if r["passed"]:
                phases[phase]["passed"] += 1
            else:
                phases[phase]["failed"] += 1
        
        for phase, counts in phases.items():
            total_phase = counts["passed"] + counts["failed"]
            status = "✅" if counts["failed"] == 0 else "⚠️"
            print(f"      {status} {phase}: {counts['passed']}/{total_phase}")
        
        print("\n" + "=" * 70)
        if percentage >= 80:
            print("✅ TESTES CONCLUÍDOS COM SUCESSO!")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM - VERIFICAR")
        print("=" * 70)
        
        return percentage >= 80


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
