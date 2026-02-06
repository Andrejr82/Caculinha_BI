# Guia Docker - Ubuntu (WSL2)

**Importante:** Todos os comandos Docker devem ser executados no **terminal do Ubuntu**, não no PowerShell/CMD do Windows.

---

## 🐧 Abrindo o Terminal Ubuntu

### Opção 1: Atalho do Windows
```
Pressione: Win + R
Digite: ubuntu
Enter
```

### Opção 2: Windows Terminal
```
Abra o Windows Terminal
Clique na seta ↓ ao lado da aba
Selecione: Ubuntu
```

### Opção 3: Linha de Comando
```powershell
wsl
```

---

## 📂 Navegar até o Projeto

No terminal do Ubuntu, execute:

```bash
cd /mnt/c/Agente_BI/BI_Solution
```

**Dica:** No Ubuntu/WSL2, as pastas do Windows ficam em `/mnt/c/`

---

## 🚀 Comandos Docker - Sequência Completa

### PASSO 1: Limpar TUDO do Docker

```bash
./docker-limpar-tudo.sh
```

**O que faz:**
- Para todos os containers
- Remove todas as imagens
- Remove todos os volumes
- Limpa todo o cache
- **Tempo:** ~2-3 minutos

---

### PASSO 2: Reconstruir Otimizado (30 usuários)

```bash
./docker-rebuild.sh
```

**O que faz:**
- Reconstrói imagens do zero (sem cache)
- Configura 4 workers para backend
- Inicia containers otimizados
- **Tempo:** ~3-5 minutos (primeira vez)

---

### ⚡ Executar Tudo de Uma Vez

```bash
./docker-limpar-tudo.sh && ./docker-rebuild.sh
```

**Tempo total:** ~5-8 minutos

---

## 📋 Comandos Disponíveis

### Uso Diário

| Comando | Função |
|---------|--------|
| `./docker-start.sh` | Inicia os containers (uso diário) |
| `./docker-stop.sh` | Para os containers |
| `./docker-logs.sh` | Ver logs em tempo real |
| `./docker-rebuild.sh` | Rebuild completo |
| `./docker-limpar-tudo.sh` | Limpeza total |

---

## 🔍 Comandos de Verificação

```bash
# Ver containers rodando
docker ps

# Ver uso de recursos (RAM, CPU)
docker stats

# Ver espaço usado pelo Docker
docker system df

# Ver logs de um container específico
docker logs agent_bi_backend
docker logs agent_bi_frontend

# Ver detalhes do container
docker inspect agent_bi_backend
```

---

## 🎯 Passo a Passo Completo

### 1. Abrir Ubuntu
```
Win + R → ubuntu → Enter
```

### 2. Navegar até o projeto
```bash
cd /mnt/c/Agente_BI/BI_Solution
```

### 3. Verificar se Docker está rodando
```bash
docker info
```

Se aparecer erro, inicie o Docker Desktop no Windows.

### 4. Limpar tudo
```bash
./docker-limpar-tudo.sh
```

### 5. Reconstruir
```bash
./docker-rebuild.sh
```

### 6. Verificar
```bash
docker ps
docker stats
```

### 7. Acessar
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## ⚠️ Troubleshooting

### Erro: "Permission denied"
```bash
# Dar permissão aos scripts
chmod +x *.sh
```

### Erro: "docker: command not found"
**Causa:** Docker não está instalado no Ubuntu ou Docker Desktop não está rodando.

**Solução:**
1. Abra o Docker Desktop no Windows
2. Aguarde inicializar completamente
3. No Ubuntu, teste: `docker info`

### Erro: "Cannot connect to Docker daemon"
**Causa:** Docker Desktop não está rodando.

**Solução:**
1. Abra o Docker Desktop
2. Aguarde o ícone ficar verde
3. Tente novamente

### Erro: "No such file or directory"
**Causa:** Você não está na pasta correta.

**Solução:**
```bash
cd /mnt/c/Agente_BI/BI_Solution
pwd  # Verificar pasta atual
ls   # Ver arquivos
```

### Build muito lento
**Normal na primeira vez:**
- Baixa imagens base (~500MB)
- Instala dependências Python (~200MB)
- Compila frontend

**Próximas builds:** ~2-3 minutos (usa cache)

---

## 💡 Dicas Importantes

### 1. Sempre use o Terminal do Ubuntu
❌ **Não funciona:** PowerShell/CMD do Windows
✅ **Funciona:** Terminal do Ubuntu (WSL2)

### 2. Caminho dos arquivos
No Ubuntu, as pastas do Windows ficam em `/mnt/`:
- `C:\Agente_BI` → `/mnt/c/Agente_BI`
- `D:\Projetos` → `/mnt/d/Projetos`

### 3. Docker Desktop precisa estar rodando
O Docker Desktop no Windows gerencia o Docker dentro do WSL2.

### 4. Reiniciar WSL se necessário
Se o Docker ficar lento:
```bash
# No PowerShell do Windows (como Admin)
wsl --shutdown
```

Depois reabra o Ubuntu.

---

## 📊 Monitoramento

### Ver uso em tempo real
```bash
docker stats
```

**Esperado:**
```
CONTAINER           CPU %    MEM USAGE / LIMIT    MEM %
agent_bi_backend    50-80%   1.2GB / 2GB         60%
agent_bi_frontend   5-10%    100MB / 256MB       40%
```

### Ver logs ao vivo
```bash
./docker-logs.sh
```

Ou individual:
```bash
docker logs -f agent_bi_backend    # Backend
docker logs -f agent_bi_frontend   # Frontend
```

---

## 🔄 Workflow Diário

### Primeira vez / Rebuild necessário
```bash
cd /mnt/c/Agente_BI/BI_Solution
./docker-rebuild.sh
```

### Desenvolvimento normal
```bash
cd /mnt/c/Agente_BI/BI_Solution
./docker-start.sh     # Manhã
./docker-stop.sh      # Fim do dia
```

### Ver o que está acontecendo
```bash
./docker-logs.sh
# ou
docker stats
```

---

## 📝 Resumo Rápido

**1. Abrir Ubuntu:**
```
Win + R → ubuntu
```

**2. Ir para o projeto:**
```bash
cd /mnt/c/Agente_BI/BI_Solution
```

**3. Limpar tudo:**
```bash
./docker-limpar-tudo.sh
```

**4. Reconstruir:**
```bash
./docker-rebuild.sh
```

**5. Pronto!**
```
http://localhost:8000  (Backend)
http://localhost:3000  (Frontend)
```

---

## ✅ Checklist

Antes de começar:
- [ ] Docker Desktop está rodando (ícone verde)
- [ ] Abriu o terminal do Ubuntu (não PowerShell)
- [ ] Navegou até `/mnt/c/Agente_BI/BI_Solution`
- [ ] Scripts têm permissão (`chmod +x *.sh`)

Para executar:
- [ ] `./docker-limpar-tudo.sh`
- [ ] `./docker-rebuild.sh`
- [ ] `docker ps` (verificar)
- [ ] Acessar http://localhost:8000/docs

---

## 🎯 Próximos Passos

Execute agora no terminal do Ubuntu:

```bash
# 1. Navegar
cd /mnt/c/Agente_BI/BI_Solution

# 2. Limpar
./docker-limpar-tudo.sh

# 3. Reconstruir
./docker-rebuild.sh
```

**Tempo total:** ~5-8 minutos

Depois acesse: http://localhost:8000/docs
