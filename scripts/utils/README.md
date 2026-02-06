# 🔧 Scripts Utilitários

Scripts de manutenção, diagnóstico e automação do BI Solution.

---

## 🐳 Scripts Docker/WSL

### Inicialização
- **`DOCKER_START_WSL.bat`** - Inicia Docker via WSL2
- **`DOCKER_REBUILD_WSL.bat`** - Rebuild completo dos containers
- **`start-docker.bat`** - Inicia ambiente Docker
- **`start-production.bat`** - Inicia em modo produção
- **`start.sh`** - Script shell de inicialização
- **`run.sh`** - Script shell de execução

### Diagnóstico
- **`check-docker-logs.bat`** - Visualiza logs dos containers
- **`diagnose-wsl-network.bat`** - Diagnostica problemas de rede WSL
- **`test-docker-safe.bat`** - Testa configuração Docker

### Correção
- **`DOCKER_RESTART_FIXED.bat`** - Restart com correções aplicadas
- **`fix-docker-compose-network.bat`** - Corrige problemas de rede
- **`fix-wsl-port-forwarding.bat`** - Corrige port forwarding WSL

### Setup
- **`setup_windows.bat`** - Setup inicial no Windows
- **`build_safe.bat`** - Build seguro dos containers

---

## 📊 Scripts de Análise

- **`deep_analyze.py`** - Análise profunda do projeto
- **`analyze.bat`** - Script de análise rápida
- **`cleanup.bat`** - Limpeza de arquivos temporários

---

## 🗄️ Scripts Legacy

Scripts antigos mantidos em `/scripts/legacy_tests/`:
- `diagnostico_sql_server.bat` - Diagnóstico SQL Server (deprecated)

---

## 📝 Uso Geral

### Para iniciar o projeto:
```bash
# Windows
.\scripts\utils\DOCKER_START_WSL.bat

# Linux/Mac
./scripts/utils/run.sh
```

### Para diagnosticar problemas:
```bash
.\scripts\utils\diagnose-wsl-network.bat
.\scripts\utils\check-docker-logs.bat
```

### Para fazer rebuild:
```bash
.\scripts\utils\DOCKER_REBUILD_WSL.bat
```

---

**Organizado em**: 31 de Dezembro de 2025
