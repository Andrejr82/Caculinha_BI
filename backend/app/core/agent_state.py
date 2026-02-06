from __future__ import annotations

import operator
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    TypedDict,
)

from langchain_core.messages import BaseMessage
from plotly.graph_objects import Figure as PlotlyFigure


# RouteDecision será definido como string para evitar import circular
# from app.core.agents.supervisor import RouteDecision

# O bloco TYPE_CHECKING anterior para RouteDecision não é mais estritamente necessário
# para esta anotação específica, pois RouteDecision é importado diretamente.
# Mantendo o bloco TYPE_CHECKING caso seja usado para outras importações condicionais.
if TYPE_CHECKING:
    pass  # Pode ser usado para outras importações apenas de checagem de tipo


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    retrieved_data: Optional[List[Dict[str, Any]]]
    chart_code: Optional[str]
    plotly_fig: Optional[PlotlyFigure]
    route_decision: Optional["RouteDecision"]  # Usar string para anotação de tipo
