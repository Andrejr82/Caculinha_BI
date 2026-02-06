from typing import Annotated, List, Any, Dict, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Estado do Agente BI.
    Herda de TypedDict para garantir tipagem.
    """
    # Histórico de mensagens (User, AI, Tool)
    # add_messages garante que novas mensagens sejam anexadas à lista existente
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Contexto de dados (opcional, para passar dataframes ou metadados entre nós)
    data_context: Optional[Dict[str, Any]]
    
    # Contadores para controle de loops/retries
    loop_count: int
