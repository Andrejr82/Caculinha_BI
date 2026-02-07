import os
import sys

BASE_DIR = os.path.abspath(os.getcwd())

EXPECTED_FOLDERS = [
    "backend/domain",
    "backend/application",
    "backend/infrastructure",
    "backend/api",
    "backend/application/agents",
    "backend/application/use_cases",
    "tests",
    "docs"
]

EXPECTED_FILES = [
    "backend/main.py",
    "requirements.txt",
    "docs/diagnostico.md",
    "docs/riscos.md",
    "docs/mapa_modulos.md",
    "backend/application/agents/base_agent.py",
    "backend/application/agents/orchestrator_agent.py",
    "backend/application/agents/sql_agent.py",
    "backend/application/agents/insight_agent.py",
    "backend/application/agents/forecast_agent.py",
    "backend/application/agents/metadata_agent.py",
    "backend/application/agents/tenant_agent.py",
    "backend/application/agents/security_agent.py",
    "backend/application/agents/monitoring_agent.py",
    "backend/application/use_cases/process_chat.py",
]

EXPECTED_TESTS = [
    "tests/test_orchestrator_agent.py",
    "tests/test_sql_agent.py",
    "tests/test_insight_agent.py",
    "tests/test_forecast_agent.py",
    "tests/test_metadata_agent.py",
    "tests/test_tenant_agent.py",
    "tests/test_security_agent.py",
    "tests/test_monitoring_agent.py",
]

EXPECTED_CLASSES = {
    "orchestrator_agent.py": "class OrchestratorAgent",
    "sql_agent.py": "class SQLAgent",
    "insight_agent.py": "class InsightAgent",
    "forecast_agent.py": "class ForecastAgent",
    "metadata_agent.py": "class MetadataAgent",
    "tenant_agent.py": "class TenantAgent",
    "security_agent.py": "class SecurityAgent",
    "monitoring_agent.py": "class MonitoringAgent",
}

def check_exists(path):
    return os.path.exists(os.path.join(BASE_DIR, path))

def check_not_empty(path):
    full = os.path.join(BASE_DIR, path)
    return os.path.isfile(full) and os.path.getsize(full) > 0

def check_class(path, class_name):
    full = os.path.join(BASE_DIR, path)
    if not os.path.isfile(full):
        return False
    with open(full, encoding="utf-8") as f:
        return class_name in f.read()

def print_result(ok, text):
    icon = "✅" if ok else "❌"
    print(f"{icon} {text}")
    return ok

def main():
    print("\n🔍 CACULINHA BI PLATFORM - AUDITORIA AUTOMÁTICA\n")

    total = 0
    passed = 0

    print("📁 PASTAS")
    for folder in EXPECTED_FOLDERS:
        total += 1
        if print_result(check_exists(folder), folder):
            passed += 1

    print("\n📄 ARQUIVOS")
    for file in EXPECTED_FILES:
        total += 1
        if print_result(check_not_empty(file), file):
            passed += 1

    print("\n🧪 TESTES")
    for test in EXPECTED_TESTS:
        total += 1
        if print_result(check_not_empty(test), test):
            passed += 1

    print("\n🧠 CLASSES")
    for file, cls in EXPECTED_CLASSES.items():
        path = f"backend/application/agents/{file}"
        total += 1
        if print_result(check_class(path, cls), f"{file} contém {cls}"):
            passed += 1

    print("\n📊 RESULTADO FINAL")
    print(f"Passou: {passed}/{total}")

    if passed == total:
        print("\n🎉 PLATAFORMA CONFORME COM O PLANO!")
        sys.exit(0)
    else:
        print("\n⚠️ PLATAFORMA INCOMPLETA - VERIFIQUE OS ITENS ACIMA")
        sys.exit(1)

if __name__ == "__main__":
    main()
