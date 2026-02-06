# Comandos para Docker Limpo - Inicialização do Zero

## 🧹 Sequência Completa

### Passo 1: Limpeza Total
```bash
docker-limpar-tudo.bat
```

**O que faz:**
1. Para todos os containers
2. Remove todos os containers
3. Remove todas as imagens
4. Remove todos os volumes
5. Remove networks customizadas
6. Limpa cache de build
7. Reinicia WSL

**Tempo:** ~2-3 minutos

---

### Passo 2: Reconstruir do Zero
```bash
docker-rebuild.bat
```

**O que faz:**
1. Reconstrói imagens sem cache
2. Inicia containers otimizados (4 workers)
3. Configura para 30 usuários

**Tempo:** ~3-5 minutos

---

## ⚡ Comando Único (Tudo de Uma Vez)

Se preferir executar tudo em sequência:

```bash
docker-limpar-tudo.bat && docker-rebuild.bat
```

---

## 📋 Checklist

Antes de executar:
- [ ] Docker Desktop está rodando?
- [ ] Tem 5GB+ de espaço livre?
- [ ] Salvou dados importantes? (limpeza apaga tudo)

Executar:
```bash
1. docker-limpar-tudo.bat
2. Aguardar conclusão
3. docker-rebuild.bat
4. Aguardar conclusão (~5 min build)
```

Verificar:
```bash
docker ps                    # Ver containers rodando
docker stats                 # Ver uso de recursos
docker-logs.bat              # Ver logs
```

Acessar:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 🔧 Comandos Docker Úteis (Manual)

### Limpeza Manual Completa

```bash
# 1. Parar tudo
docker stop $(docker ps -aq)

# 2. Remover containers
docker rm -f $(docker ps -aq)

# 3. Remover imagens
docker rmi -f $(docker images -aq)

# 4. Remover volumes
docker volume prune -af

# 5. Remover networks
docker network prune -f

# 6. Limpar cache
docker builder prune -af

# 7. Limpeza total final
docker system prune -af --volumes

# 8. Reiniciar WSL
wsl --shutdown
```

---

## 📊 Verificar Espaço Liberado

Antes da limpeza:
```bash
docker system df
```

Depois da limpeza:
```bash
docker system df
```

**Esperado:** Tudo zerado (0B usado)

---

## ⚠️ Avisos

### O que será PERDIDO:
- ✅ Containers antigos (serão recriados)
- ✅ Imagens antigas (serão baixadas/construídas novamente)
- ✅ Volumes Docker (cache temporário)
- ❌ Seus dados em `./backend/app/data` (NÃO são apagados - estão no host)
- ❌ Seus arquivos `.env` (NÃO são apagados)

### O que será MANTIDO:
- ✅ Código fonte (sua pasta do projeto)
- ✅ Configurações `.env`
- ✅ Dados em `./backend/app/data/sessions/`
- ✅ Logs em `./backend/logs/`
- ✅ Cache semântico em `./backend/data/cache/`

---

## 🚀 Resumo Rápido

**Para começar do ZERO absoluto:**

```bash
# Passo 1: Limpar
docker-limpar-tudo.bat

# Passo 2: Reconstruir
docker-rebuild.bat

# Passo 3: Verificar
docker ps
docker stats
```

**Tempo total:** ~5-8 minutos

---

## 🔍 Troubleshooting

### "docker: command not found"
- Docker Desktop não está rodando
- Inicie o Docker Desktop e tente novamente

### "Access denied" ou "Permission denied"
- Execute o CMD como Administrador
- Ou reinicie o Docker Desktop

### Build muito lento
- Primeira vez sempre demora (baixa dependências)
- Próximas builds são mais rápidas (usa cache)

### Container não inicia
```bash
# Ver logs de erro
docker logs agent_bi_backend

# Ver detalhes do container
docker inspect agent_bi_backend
```

---

## 📚 Scripts Disponíveis

| Script | Função |
|--------|--------|
| `docker-limpar-tudo.bat` | Limpeza total do Docker |
| `docker-rebuild.bat` | Reconstrói do zero |
| `docker-start.bat` | Inicia containers (uso diário) |
| `docker-stop.bat` | Para containers |
| `docker-logs.bat` | Ver logs em tempo real |

---

## ✅ Pronto!

Execute agora:
```bash
docker-limpar-tudo.bat
```

Depois:
```bash
docker-rebuild.bat
```

E seu Docker estará completamente limpo e otimizado para 30 usuários!
