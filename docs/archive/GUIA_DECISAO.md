# Guia de Decisão: Docker vs Local

## 🎯 Qual Modo Usar?

### Use **MODO LOCAL** se:
- ✅ Está desenvolvendo ativamente
- ✅ Quer hot reload (mudanças instantâneas)
- ✅ Quer economizar RAM (~600MB vs ~1.2GB)
- ✅ Quer startup rápido (~5s vs ~30s)
- ✅ Sua máquina tem 8GB RAM ou menos

**Como iniciar:**
```bash
start-local.bat
```

---

### Use **DOCKER LIGHT** se:
- ✅ Quer ambiente isolado
- ✅ Está testando para produção
- ✅ Quer consistência entre ambientes
- ✅ Não precisa de hot reload
- ✅ Não vai fazer mudanças frequentes no código

**Como iniciar:**
```bash
docker-start.bat
```

**Primeira vez / Rebuild completo:**
```bash
docker-rebuild.bat
```

---

## 📊 Resumo dos Scripts Criados

### Modo Local (SEM Docker)
| Script | Função |
|--------|--------|
| `start-local.bat` | Inicia backend + frontend localmente |
| `testar-ambiente.bat` | Testa todas as dependências |

### Modo Docker Light
| Script | Função |
|--------|--------|
| `docker-start.bat` | Inicia containers (uso diário) |
| `docker-rebuild.bat` | Rebuild completo do zero |
| `docker-logs.bat` | Ver logs em tempo real |
| `docker-stop.bat` | Para todos os containers |

### Utilitários
| Script | Função |
|--------|--------|
| `verificar-docker.bat` | Verifica imagens e containers |
| `limpar-e-reconstruir.bat` | Limpeza total Docker |

---

## 🔧 Arquivo Docker Usado

**SEMPRE usa:** `docker-compose.light.yml`

**Serviços incluídos:**
- Backend (FastAPI) - Porta 8000
- Frontend (SolidJS/Nginx) - Porta 3000

**NÃO inclui** (para economizar RAM):
- ❌ LangFuse (observabilidade)
- ❌ PostgreSQL
- ❌ Prometheus
- ❌ Grafana

Se precisar de observabilidade, use o arquivo completo:
```bash
docker-compose -f docker-compose.yml up -d
```
⚠️ Mas isso usará ~2.5-3.5GB de RAM!

---

## 📝 Configurações Aplicadas

### WSL2 (`.wslconfig`)
```ini
memory=4GB              # 50% da RAM total
processors=2
swap=2GB                # Reduzido para não travar
localhostForwarding=true
pageReporting=false     # Performance
```

### Docker Light (`docker-compose.light.yml`)
```yaml
backend:
  resources:
    limits:
      memory: 1G        # Máximo 1GB
    reservations:
      memory: 512M      # Garantido 512MB

frontend:
  resources:
    limits:
      memory: 256M      # Máximo 256MB
    reservations:
      memory: 128M      # Garantido 128MB
```

---

## 🚀 Fluxo Recomendado

### Primeira Vez com Docker
```bash
1. docker-rebuild.bat    # Constrói tudo do zero
2. docker-start.bat      # Próximas vezes
```

### Desenvolvimento Diário
```bash
start-local.bat          # Mais rápido e leve
```

### Testar Build de Produção
```bash
docker-start.bat         # Testa ambiente containerizado
```

---

## 🔍 Como Verificar o Que Está Rodando

### Docker
```bash
# Ver containers rodando
docker ps

# Ver uso de recursos
docker stats

# Ver logs
docker-logs.bat
```

### Modo Local
```bash
# Verificar portas em uso
netstat -ano | findstr ":8000"
netstat -ano | findstr ":5173"

# Ver processos Python
tasklist | findstr python

# Ver processos Node
tasklist | findstr node
```

---

## 💾 Uso de RAM - Comparação Real

| Cenário | RAM Usada | Recomendado |
|---------|-----------|-------------|
| **Windows Base** | ~2-3GB | - |
| **+ Modo Local** | +600MB = **2.6-3.6GB** | ✅ Ótimo |
| **+ Docker Light** | +1.2GB = **3.2-4.2GB** | ⚠️ OK |
| **+ Docker Completo** | +3GB = **5-6GB** | ❌ Não |
| **Total disponível** | 8GB | - |

**Conclusão:** Para 8GB RAM, prefira **Modo Local** no dia a dia.

---

## ⚠️ Importante

1. **Após alterar `.wslconfig`**, sempre execute:
   ```bash
   wsl --shutdown
   ```

2. **Docker Desktop deve estar rodando** antes de usar os scripts Docker

3. **As portas devem estar livres:**
   - 8000 (Backend)
   - 3000 (Frontend Docker) ou 5173 (Frontend Local)

4. **Não rode os dois modos ao mesmo tempo!**
   - Escolha: OU Docker OU Local

---

## 🎯 Minha Recomendação Final

**Para sua máquina de 8GB:**

1. **Desenvolvimento:** Use `start-local.bat` ⭐
2. **Testes de produção:** Use `docker-start.bat` ocasionalmente
3. **Nunca use:** `docker-compose.yml` (completo)

**Razão:** Economiza ~600MB de RAM, startup 6x mais rápido, hot reload funciona.
