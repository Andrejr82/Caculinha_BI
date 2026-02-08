import re
import json
import logging
import uuid
from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from backend.app.orchestration.state import AgentState
from backend.app.orchestration.nodes.patterns import HEURISTIC_PATTERNS

logger = logging.getLogger(__name__)

def heuristic_node(state: AgentState) -> Dict[str, Any]:
    """
    Nó determinístico que tenta resolver a query usando Regex.
    Se encontrar um padrão, gera uma 'tool_call' artificialmente.
    Se não, não retorna nada (o grafo seguirá para o LLM).
    """
    messages = state["messages"]
    if not messages:
        return {}
        
    last_message = messages[-1]
    # Só processa mensagens de usuário
    if last_message.type != "human":
        return {}
        
    content = last_message.content.lower()
    
    for pattern, tool_name, arg_extractor in HEURISTIC_PATTERNS:
        try:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                logger.info(f"⚡ [HEURISTIC HIT] Padrão detectado: '{pattern}' -> Tool: {tool_name}")
                
                # Extrair argumentos
                args = arg_extractor(match)
                if args is None:
                    args = {}
                    
                # Gerar ID único para a chamada
                call_id = f"call_heuristic_{str(uuid.uuid4())[:8]}"
                
                # Construir a mensagem do assistente como se fosse o LLM
                ai_message = AIMessage(
                    content="",
                    tool_calls=[{
                        "name": tool_name,
                        "args": args,
                        "id": call_id,
                        "type": "tool_call"
                    }]
                )
                
                return {"messages": [ai_message]}
        except Exception as e:
            logger.error(f"Erro no loop heurístico: {e}")
            continue
            
    # Se nenhum padrão bater, não retornamos nada.
    # O router saberá que deve passar a bola para o LLM.
    return {}
