"""
Agents Endpoint

Endpoints para gerenciamento e status dos agentes.

Uso:
    GET /api/v2/agents         → Lista agentes
    GET /api/v2/agents/{name}  → Detalhes do agente

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import structlog


logger = structlog.get_logger(__name__)
router = APIRouter()


class AgentInfo(BaseModel):
    """Informações de um agente."""
    name: str
    description: str
    capabilities: List[str]
    status: str = "available"


class AgentListResponse(BaseModel):
    """Lista de agentes."""
    agents: List[AgentInfo]
    total: int


@router.get("", response_model=AgentListResponse)
async def list_agents():
    """
    Lista todos os agentes disponíveis.
    
    Returns:
        Lista de agentes com suas informações
    """
    from backend.application.agents import (
        OrchestratorAgent,
        SQLAgent,
        InsightAgent,
        ForecastAgent,
        MetadataAgent,
        TenantAgent,
        SecurityAgent,
        MonitoringAgent,
    )
    
    # Criar instâncias temporárias para obter informações
    agent_classes = [
        OrchestratorAgent,
        SQLAgent,
        InsightAgent,
        ForecastAgent,
        MetadataAgent,
        TenantAgent,
        SecurityAgent,
        MonitoringAgent,
    ]
    
    agents = []
    for agent_class in agent_classes:
        try:
            instance = agent_class()
            agents.append(AgentInfo(
                name=instance.name,
                description=instance.description,
                capabilities=instance.capabilities,
            ))
        except Exception as e:
            logger.warning(f"Erro ao instanciar {agent_class.__name__}: {e}")
    
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_name}")
async def get_agent_details(agent_name: str):
    """
    Obtém detalhes de um agente específico.
    
    Args:
        agent_name: Nome do agente
    
    Returns:
        Detalhes completos do agente incluindo ferramentas
    """
    from backend.application.agents import (
        OrchestratorAgent,
        SQLAgent,
        InsightAgent,
        ForecastAgent,
        MetadataAgent,
        TenantAgent,
        SecurityAgent,
        MonitoringAgent,
    )
    
    agent_map = {
        "OrchestratorAgent": OrchestratorAgent,
        "SQLAgent": SQLAgent,
        "InsightAgent": InsightAgent,
        "ForecastAgent": ForecastAgent,
        "MetadataAgent": MetadataAgent,
        "TenantAgent": TenantAgent,
        "SecurityAgent": SecurityAgent,
        "MonitoringAgent": MonitoringAgent,
    }
    
    agent_class = agent_map.get(agent_name)
    if not agent_class:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_name}' não encontrado")
    
    try:
        instance = agent_class()
        return {
            "name": instance.name,
            "description": instance.description,
            "capabilities": instance.capabilities,
            "tools": instance.get_tools(),
            "status": "available",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
