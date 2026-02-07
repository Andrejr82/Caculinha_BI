import os
from pathlib import Path
import json

BASE_PATH = Path(r"C:\Projetos_BI\BI_Solution")

REPORT = {
    "fase1_diagnostico": [],
    "fase2_arquitetura": [],
    "fase3_agentes": [],
    "fase4_codigo_base": [],
    "fase5_mvp": [],
    "fase6_saas": []
}


def exists(path):
    return path.exists()


def check(path, description, bucket):
    REPORT[bucket].append({
        "item": description,
        "path": str(path),
        "status": "OK" if exists(path) else "MISSING"
    })


def run():
    # ---------- FASE 1 ----------
    docs = BASE_PATH / "docs"
    check(docs / "diagnostico.md", "Diagnóstico", "fase1_diagnostico")
    check(docs / "riscos.md", "Riscos", "fase1_diagnostico")
    check(docs / "mapa_modulos.md", "Mapa de módulos", "fase1_diagnostico")

    # ---------- FASE 2 ----------
    backend = BASE_PATH / "backend"
    for d in ["domain", "application", "infrastructure", "api"]:
        check(backend / d, f"Camada {d}", "fase2_arquitetura")

    check(BASE_PATH / "Dockerfile", "Dockerfile", "fase2_arquitetura")
    check(BASE_PATH / "docker-compose.yml", "Docker Compose", "fase2_arquitetura")

    # ---------- FASE 3 ----------
    agents = backend / "application" / "agents"
    expected_agents = [
        "orchestrator_agent.py",
        "sql_agent.py",
        "insight_agent.py",
        "forecast_agent.py",
        "metadata_agent.py",
        "tenant_agent.py",
        "security_agent.py",
        "monitoring_agent.py"
    ]

    for a in expected_agents:
        check(agents / a, f"Agente {a}", "fase3_agentes")

    # ---------- FASE 4 ----------
    check(agents / "base_agent.py", "BaseAgent", "fase4_codigo_base")
    check(backend / "main.py", "FastAPI App", "fase4_codigo_base")
    check(BASE_PATH / "requirements.txt", "requirements.txt", "fase4_codigo_base")

    # ---------- FASE 5 ----------
    api = backend / "api"
    check(api, "API Layer", "fase5_mvp")

    # ---------- FASE 6 ----------
    infra_auth = backend / "infrastructure" / "adapters" / "auth"
    check(infra_auth, "Auth Adapter", "fase6_saas")

    output = BASE_PATH / "platform_audit_report.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=2)

    print(f"Relatório gerado em: {output}")


if __name__ == "__main__":
    run()
