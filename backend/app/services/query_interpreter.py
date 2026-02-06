"""
Query Interpreter - Componente de interpretação de queries com estratégia heurística-first.

Arquitetura Metrics-First - Fase 4
Responsável por extrair intenção e entidades da query do usuário.

Estratégia:
- 80% heurística (rápido, determinístico)
- 20% LLM fallback (casos complexos)
- Confidence gate (< 0.6 → pedir esclarecimento)
"""

import re
import logging
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Tipos de intenção suportados"""
    VENDAS = "vendas"
    ESTOQUE = "estoque"
    RUPTURA = "ruptura"
    COMPARACAO = "comparacao"
    GRAFICO = "grafico"
    CHAT = "chat"


@dataclass
class QueryIntent:
    """
    Representa a intenção extraída de uma query do usuário.
    
    Attributes:
        intent_type: Tipo de intenção (vendas, estoque, etc)
        entities: Entidades extraídas (une, segmento, produto, etc)
        aggregations: Agregações solicitadas (sum, avg, count)
        visualization: Tipo de visualização (bar, line, table, None)
        confidence: Confiança na classificação (0.0 - 1.0)
        raw_query: Query original do usuário
    """
    intent_type: IntentType
    entities: Dict[str, Any]
    aggregations: List[str]
    visualization: Optional[str]
    confidence: float
    raw_query: str


class NeedsClarificationError(Exception):
    """Levantado quando a query é ambígua e precisa de esclarecimento"""
    pass


class QueryInterpreter:
    """
    Interpretador de queries com estratégia heurística-first.
    
    Fluxo:
    1. Tentar classificação heurística (80% dos casos)
    2. Se falhar ou baixa confiança, usar LLM fallback
    3. Se ainda baixa confiança (< 0.6), pedir esclarecimento
    """
    
    def __init__(self, llm_adapter=None):
        """
        Args:
            llm_adapter: Adapter LLM para fallback (opcional)
        """
        self.llm_adapter = llm_adapter
        
        # Padrões heurísticos
        self._vendas_patterns = [
            r'\bvenda[s]?\b', r'\bfaturamento\b', r'\breceita\b',
            r'\bvendeu\b', r'\bvendendo\b', r'\bvenderam\b'
        ]
        
        self._estoque_patterns = [
            r'\bestoque\b', r'\bquantidade\b', r'\bdispon[ií]vel\b',
            r'\btem\b.*\bestoque\b', r'\bquanto.*\btem\b'
        ]
        
        self._ruptura_patterns = [
            r'\bruptura[s]?\b', r'\bfalta[m]?\b', r'\bacabou\b',
            r'\bzerado[s]?\b', r'\bsem\s+estoque\b'
        ]
        
        self._grafico_patterns = [
            r'\bgr[áa]fico\b', r'\bgerar\b', r'\bmostrar\b',
            r'\bvisualizar\b', r'\bexibir\b', r'\bplottar\b',
            r'\bver\b', r'\bpainel\b', r'\bdashboard\b', r'\bplot\b',
            r'\branking\b', r'\btop\s*\d+\b', r'\bpizza\b', r'\bbarras?\b',
            r'\blinha\b', r'\bhistograma\b', r'\bchart\b'
        ]
        
        self._comparacao_patterns = [
            r'\bcomparar\b', r'\bcompara[çc][ãa]o\b', r'\bversus\b',
            r'\bvs\b', r'\bentre\b.*\be\b'
        ]
    
    def interpret(self, query: str, user_context: Optional[Dict] = None, chat_history: Optional[List[Dict]] = None) -> QueryIntent:
        """
        Interpreta a query do usuário e retorna a intenção.
        
        Args:
            query: Query do usuário
            user_context: Contexto adicional (user_id, histórico, etc)
            chat_history: Histórico de chat para Entity Carry-Over (Stateful)
        
        Returns:
            QueryIntent com intenção e entidades extraídas
        
        Raises:
            NeedsClarificationError: Se a query for muito ambígua
        """
        logger.info(f"Interpretando query: '{query[:100]}...'")
        
        # 1. Tentar classificação heurística primeiro
        intent = self._heuristic_classify(query)
        
        # 2. Se falhou ou baixa confiança, usar LLM fallback
        if not intent or intent.confidence < 0.7:
            if self.llm_adapter:
                logger.info("Heurística falhou ou baixa confiança. Usando LLM fallback...")
                intent = self._llm_classify(query, user_context)
            else:
                # Sem LLM disponível, usar intent heurístico mesmo com baixa confiança
                if not intent:
                    # Fallback final: classificar como chat
                    intent = QueryIntent(
                        intent_type=IntentType.CHAT,
                        entities={},
                        aggregations=[],
                        visualization=None,
                        confidence=0.5,
                        raw_query=query
                    )
        
        # 2.5 Entity Carry-Over (Stateful Context) - FIX 2026-01-17
        if chat_history and intent:
            self._apply_entity_carry_over(intent, chat_history)
        
        # 3. Confidence gate: se ainda muito baixo, pedir esclarecimento
        if intent.confidence < 0.6:
            logger.warning(f"Confiança muito baixa ({intent.confidence}). Pedindo esclarecimento.")
            raise NeedsClarificationError(
                "Não entendi sua pergunta. Pode reformular de forma mais específica? "
                "Por exemplo: 'Quais as vendas da loja 1685?' ou 'Mostre o estoque de tecidos'"
            )
        
        # 4. Validar completude da query (FIX 2026-01-16)
        self._validate_query_completeness(query, intent)
        
        logger.info(f"Intent classificado: {intent.intent_type} (confiança: {intent.confidence:.2f})")
        return intent
    
    def _validate_query_completeness(self, query: str, intent: QueryIntent) -> None:
        """
        Valida se a query tem informações suficientes para ser processada.
        
        Args:
            query: Query original do usuário
            intent: Intent classificado
        
        Raises:
            NeedsClarificationError: Se a query estiver incompleta
        """
        query_lower = query.lower()
        
        # Caso 1: "produto em todas as lojas" sem especificar qual produto
        if ("produto" in query_lower and 
            ("todas" in query_lower or "cada" in query_lower) and 
            "loja" in query_lower):
            if not intent.entities.get("produto"):
                raise NeedsClarificationError(
                    "Para gerar relatório de produto em todas as lojas, "
                    "preciso saber QUAL produto. "
                    "Exemplo: 'vendas do produto 59294 em todas as lojas' ou "
                    "'relatório do produto 369947 em todas as lojas'"
                )
        
        # Caso 2: "loja" sem especificar qual (e não é "todas as lojas")
        if ("loja" in query_lower and 
            not intent.entities.get("une") and 
            "todas" not in query_lower):
            raise NeedsClarificationError(
                "Qual loja você quer analisar? "
                "Exemplo: 'vendas da loja 1685' ou 'todas as lojas'"
            )
        
        # Caso 3: Comparação sem especificar o que comparar
        if intent.intent_type == IntentType.COMPARACAO:
            if not intent.entities.get("unes") and not intent.entities.get("segmento"):
                raise NeedsClarificationError(
                    "Para comparar, preciso saber o que você quer comparar. "
                    "Exemplo: 'comparar vendas das lojas 1685 e 2365' ou "
                    "'comparar segmentos TECIDOS e AVIAMENTOS'"
                )
        
        logger.info(f"Intent classificado: {intent.intent_type} (confiança: {intent.confidence:.2f})")
        return intent
    
    def _heuristic_classify(self, query: str) -> Optional[QueryIntent]:
        """
        Classificação heurística baseada em padrões regex.
        Rápido e determinístico (80% dos casos).
        
        Args:
            query: Query do usuário
        
        Returns:
            QueryIntent ou None se não conseguir classificar
        """
        query_lower = query.lower()
        entities = self._extract_entities(query)
        
        # 1. Padrões de gráfico (PRIORIDADE MÁXIMA)
        # Se usuário pediu gráfico explicitamente, a intenção primária deve refletir isso
        # ou o visualization deve ser forçado.
        visualization = None
        is_explicit_chart = self._match_patterns(query_lower, self._grafico_patterns)
        if is_explicit_chart:
            # FORCE visualization to 'bar' (not 'auto') to ensure chart is generated
            visualization = "bar"
            logger.info(f"[Heuristic] Gráfico explícito detectado - forçando visualization='bar'")

        # 2. Padrões de vendas (mais comum)
        if self._match_patterns(query_lower, self._vendas_patterns):
            return QueryIntent(
                intent_type=IntentType.VENDAS,
                entities=entities,
                aggregations=["sum", "count"],
                visualization=visualization,
                confidence=0.9,
                raw_query=query
            )
        
        # 3. Padrões de estoque
        if self._match_patterns(query_lower, self._estoque_patterns):
            return QueryIntent(
                intent_type=IntentType.ESTOQUE,
                entities=entities,
                aggregations=["sum"],
                visualization=visualization,
                confidence=0.85,
                raw_query=query
            )
        
        # 4. Padrões de ruptura
        if self._match_patterns(query_lower, self._ruptura_patterns):
            return QueryIntent(
                intent_type=IntentType.RUPTURA,
                entities=entities,
                aggregations=["count"],
                visualization=visualization,
                confidence=0.9,
                raw_query=query
            )
        
        # 5. Padrões de comparação
        if self._match_patterns(query_lower, self._comparacao_patterns):
            return QueryIntent(
                intent_type=IntentType.COMPARACAO,
                entities=entities,
                aggregations=["sum", "avg"],
                visualization=visualization or "bar",  # Comparação geralmente usa gráfico
                confidence=0.85,
                raw_query=query
            )
        
        # 6. Apenas gráfico (sem intenção específica de negócio detectada)
        if is_explicit_chart:
            return QueryIntent(
                intent_type=IntentType.GRAFICO,
                entities=entities,
                aggregations=["sum"],
                visualization=visualization,
                confidence=0.95,
                raw_query=query
            )
        
        # Não conseguiu classificar com heurística
        return None
    
    def _llm_classify(self, query: str, user_context: Optional[Dict] = None) -> QueryIntent:
        """
        Classificação usando LLM (fallback para casos complexos).
        Apenas 20% dos casos.
        
        Args:
            query: Query do usuário
            user_context: Contexto adicional
        
        Returns:
            QueryIntent classificado pela LLM
        """
        # Prompt avançado com Chain-of-Thought e Few-Shot Learning (2026-01-16)
        prompt = """Você é um especialista em classificação de queries de Business Intelligence.

# 🧠 CHAIN-OF-THOUGHT (Raciocínio Passo a Passo)

Antes de classificar, analise:
1. **Intenção Principal:** O que o usuário quer? (vendas, estoque, ruptura, comparação, gráfico)
2. **Entidades Específicas:** Há loja, produto, segmento ou período mencionados?
3. **Visualização:** O usuário quer ver um gráfico, tabela ou apenas dados?
4. **Confiança:** Quão certo estou da classificação? (0.0 = incerto, 1.0 = certeza total)

---

# [TIP] EXEMPLOS (FEW-SHOT LEARNING)

**Exemplo 1:**
Query: "Como estão as vendas da loja 1685?"
Raciocínio:
- Intenção: VENDAS (palavra-chave clara)
- Entidades: UNE=1685 (loja específica)
- Visualização: Não solicitada explicitamente
- Confiança: 0.95 (muito claro)
Resposta: {"intent_type": "vendas", "confidence": 0.95, "visualization": null}

**Exemplo 2:**
Query: "Mostre um gráfico de rupturas"
Raciocínio:
- Intenção: RUPTURA (palavra-chave "rupturas")
- Entidades: Nenhuma específica (análise geral)
- Visualização: "gráfico" solicitado explicitamente
- Confiança: 0.90 (claro, mas sem entidades)
Resposta: {"intent_type": "ruptura", "confidence": 0.90, "visualization": "auto"}

**Exemplo 3:**
Query: "Compare vendas das lojas 1685 e 2365"
Raciocínio:
- Intenção: COMPARACAO (palavra-chave "compare")
- Entidades: UNEs=1685,2365 (múltiplas lojas)
- Visualização: Implícita (comparação geralmente usa gráfico)
- Confiança: 0.92 (muito claro)
Resposta: {"intent_type": "comparacao", "confidence": 0.92, "visualization": "bar"}

**Exemplo 4:**
Query: "Quanto tem em estoque de tecidos?"
Raciocínio:
- Intenção: ESTOQUE (palavra-chave "estoque")
- Entidades: Segmento=TECIDOS
- Visualização: Não solicitada
- Confiança: 0.88 (claro)
Resposta: {"intent_type": "estoque", "confidence": 0.88, "visualization": null}

**Exemplo 5:**
Query: "Gere um gráfico de vendas por categoria"
Raciocínio:
- Intenção: GRAFICO (foco principal é visualização)
- Entidades: Agrupamento por categoria
- Visualização: "gráfico" explícito
- Confiança: 0.95 (muito claro)
Resposta: {"intent_type": "grafico", "confidence": 0.95, "visualization": "auto"}

**Exemplo 6:**
Query: "Quais colunas você tem no banco?"
Raciocínio:
- Intenção: CHAT (pergunta sobre o sistema/conhecimento, não busca de dados)
- Entidades: Nenhuma direta
- Visualização: Null
- Confiança: 0.98
Resposta: {"intent_type": "chat", "confidence": 0.98, "visualization": null}

---

# [INFO] TAREFA

Query do usuário: "{query}"

**Seu raciocínio (pense em voz alta):**
1. Intenção:
2. Entidades:
3. Visualização:
4. Confiança:

**Resposta (APENAS JSON válido):**
{{
  "intent_type": "vendas|estoque|ruptura|comparacao|grafico|chat",
  "entities": {{ "une": 1234, "segmento": "TEXTO", "produto": 123, "periodo": "30d" }},
  "confidence": 0.0-1.0,
  "visualization": "bar|line|table|auto|null"
}}

JSON:"""
        
        try:
            # Usar get_completion (sync) compatível com SmartLLM
            messages = [{"role": "user", "content": prompt}]
            # SmartLLM.get_completion espera messages e tools (opcional)
            llm_result = self.llm_adapter.get_completion(messages)
            
            if "error" in llm_result:
                raise Exception(llm_result["error"])
                
            response = llm_result.get("content", "")
            result = self._parse_llm_response(response)
            
            # Extrair entidades (priorizando LLM para flexibilidade)
            llm_entities = result.get("entities", {})
            heuristic_entities = self._extract_entities(query)
            
            # Merge: Heurística tem prioridade para UNE/Códigos (mais preciso com regex), 
            # LLM tem prioridade para Texto (Segmento, Categoria) que regex não pega.
            entities = heuristic_entities.copy()
            for k, v in llm_entities.items():
                if k not in entities and v:
                    entities[k] = v
            
            # Normalizar chaves para lowercase
            entities = {k.lower(): v for k, v in entities.items()}
            
            return QueryIntent(
                intent_type=IntentType(result["intent_type"]),
                entities=entities,
                aggregations=["sum"],  # Default
                visualization=result.get("visualization"),
                confidence=result["confidence"],
                raw_query=query
            )
        
        except Exception as e:
            logger.error(f"Erro na classificação LLM: {e}")
            # Fallback: retornar como chat com baixa confiança
            return QueryIntent(
                intent_type=IntentType.CHAT,
                entities={},
                aggregations=[],
                visualization=None,
                confidence=0.4,
                raw_query=query
            )
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extrai entidades da query usando regex.
        
        Entidades suportadas:
        - UNE (loja): números de 4 dígitos
        - Segmento: TECIDOS, AVIAMENTOS, etc
        - Produto: código numérico
        - Período: 30d, 7d, hoje, ontem, etc
        
        Args:
            query: Query do usuário
        
        Returns:
            Dicionário com entidades extraídas
        """
        entities = {}
        query_lower = query.lower()
        
        # UNE (loja) - padrões: "loja 35", "une 520", "loja 1685" (1-4 dígitos)
        une_match = re.search(r'\b(?:loja|une|unidade)\s+(\d{1,4})\b', query_lower)
        if une_match:
            entities["une"] = int(une_match.group(1))
        
        # Múltiplas UNEs para comparação (ex: "lojas 35 e 520")
        unes_match = re.findall(r'\b(?:loja|une|unidade)\s+(\d{1,4})\b', query_lower)
        if len(unes_match) > 1:
            entities["unes"] = [int(u) for u in unes_match]
        
        # Segmento
        segmentos = ["tecidos", "aviamentos", "armarinho", "papelaria"]
        for seg in segmentos:
            if seg in query_lower:
                entities["segmento"] = seg.upper()
                break
        
        # Produto (código)
        produto_match = re.search(r'\bproduto\s*(\d+)\b', query_lower)
        if produto_match:
            entities["produto"] = int(produto_match.group(1))
        
        # Período
        if "30" in query and ("dia" in query_lower or "d" in query_lower):
            entities["periodo"] = "30d"
        elif "7" in query and ("dia" in query_lower or "d" in query_lower):
            entities["periodo"] = "7d"
        elif "hoje" in query_lower:
            entities["periodo"] = "hoje"
        elif "ontem" in query_lower:
            entities["periodo"] = "ontem"
        
        return entities
    
    def _match_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Verifica se algum dos padrões regex corresponde ao texto.
        
        Args:
            text: Texto para verificar
            patterns: Lista de padrões regex
        
        Returns:
            True se algum padrão corresponder
        """
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse da resposta JSON da LLM.
        
        Args:
            response: Resposta da LLM
        
        Returns:
            Dicionário com intent_type e confidence
        """
        import json
        
        # Tentar extrair JSON da resposta (Robustez: 1. Markdown, 2. Raw JSON)
        try:
            # Estratégia 1: Extrair de bloco de código Markdown ```json ... ```
            code_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response)
            if code_match:
                return json.loads(code_match.group(1))

            # Estratégia 2: Busca direta por chaves (fallback)
            # Encontra primeiro '{' e último '}'
            start = response.find('{')
            end = response.rfind('}')
            
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Erro ao decodificar JSON da LLM: {e}. Raw: {response}")
        
        # Fallback
        return {"intent_type": "chat", "confidence": 0.5}

    def _apply_entity_carry_over(self, intent: QueryIntent, chat_history: List[Dict]) -> None:
        """
        Aplica lógica de Entity Carry-Over: Herdar entidades do contexto anterior se a query atual for vaga.
        
        Exemplo:
        Usuario: "Vendas da loja 1685" -> Intent(VENDAS, entities={une: 1685})
        Usuario: "E o estoque?" -> Intent(ESTOQUE, entities={}) -> Carry-Over -> entities={une: 1685}
        """
        # Não aplicar para CHAT ou se intent for nulo
        if not intent or intent.intent_type == IntentType.CHAT:
            return

        # Verificar se a query atual JÁ TEM entidades fortes
        strong_keys = ["une", "segmento", "produto"]
        has_strong_entity = any(intent.entities.get(k) for k in strong_keys)
        
        if has_strong_entity:
            return # Query já é específica, não herdar contexto antigo
            
        logger.info("[CONTEXT] Tentando Entity Carry-Over (Query atual sem entidades específicas)")

        # Percorrer histórico de trás para frente
        # Ignorar a última mensagem se for a própria query atual (depende de como o histórico é passado)
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                last_content = msg.get("content", "")
                
                # Evitar loop com a própria query
                if last_content.strip() == intent.raw_query.strip():
                    continue
                
                # Extrair entidades da query anterior (re-parsing rápido por regex)
                prev_entities = self._extract_entities(last_content)
                
                # Se encontrou entidade forte na anterior
                if any(prev_entities.get(k) for k in strong_keys):
                    logger.info(f"[CONTEXT] Carry-Over Aplicado! Herdando de: '{last_content[:30]}...' -> {prev_entities}")
                    
                    # Merge (Entidades atuais têm prioridade se existirem, mas sabemos que são vazias/fracas)
                    for k, v in prev_entities.items():
                        if k not in intent.entities:
                            intent.entities[k] = v
                    
                    # Parar na primeira "âncora" de contexto encontrada
                    break
