# 🚀 Setup Local para Desenvolvimento - 8GB RAM

**Situação**: Máquina com 8GB RAM → Docker consome toda memória disponível
**Solução**: Rodar Backend + Frontend **diretamente no host** (SEM containers)

---

## ✅ VANTAGENS DO SETUP LOCAL

| Aspecto | Docker | Local (SEM Docker) |
|---------|--------|-------------------|
| **Memória** | ~6GB (todos os containers) | ~1.5GB (só backend+frontend) |
| **Startup** | 90+ segundos | 10-15 segundos |
| **Hot Reload** | Lento (rebuild) | Instantâneo |
| **Debug** | Complexo (logs container) | Direto (IDE/console) |
| **Dependências** | Isoladas (container) | Locais (pip/npm) |

**Recomendação**: Para desenvolvimento individual em máquina com 8GB, **SEMPRE use local**.

---

## 📋 PRÉ-REQUISITOS

### 1. Python 3.11+
```bash
python --version
# Esperado: Python 3.11.x ou superior
```

**Se não tiver**: https://www.python.org/downloads/

### 2. Node.js 18+
```bash
node --version
# Esperado: v18.x.x ou superior
```

**Se não tiver**: https://nodejs.org/

### 3. Git (Opcional - para versionamento)
```bash
git --version
```

---

## 🚀 INSTALAÇÃO RÁPIDA (5 MINUTOS)

### Passo 1: Configurar Backend

```bash
cd C:\Agente_BI\BI_Solution\backend

# Instalar dependências Python (primeira vez: ~3-5 min)
pip install -r requirements.txt

# Configurar .env
copy .env.example .env
notepad .env
```

**Editar `.env`** - Configurar API Key:
```env
# Escolha UM dos dois:
GROQ_API_KEY=gsk_sua_chave_aqui  # Grátis: https://console.groq.com/
# OU
GEMINI_API_KEY=AIza...          # https://aistudio.google.com/

LLM_PROVIDER=groq  # ou "google"
SECRET_KEY="WX9-C-irMEjSON0iTV4yUM0imUir7B3QigYSMuBdgVFycJri27ht-DF49Siw4GHc"
USE_SQL_SERVER=false
FALLBACK_TO_PARQUET=true
```

### Passo 2: Configurar Frontend

```bash
cd C:\Agente_BI\BI_Solution\frontend-solid

# Instalar dependências Node (primeira vez: ~2-3 min)
npm install
```

---

## ▶️ INICIAR DESENVOLVIMENTO

### Opção 1: Script Automático (RECOMENDADO)

```bat
START_LOCAL_DEV.bat
```

**O script abre 2 janelas**:
1. Backend (porta 8000)
2. Frontend (porta 3000)

### Opção 2: Manual (2 terminais separados)

**Terminal 1 - Backend**:
```bash
cd C:\Agente_BI\BI_Solution\backend
python main.py
```

**Terminal 2 - Frontend**:
```bash
cd C:\Agente_BI\BI_Solution\frontend-solid
npm run dev
```

### Aguardar Inicialização

**Backend** (~10s):
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Frontend** (~5s):
```
VITE ready in 500 ms
➜  Local:   http://localhost:3000/
```

---

## 🎯 ACESSAR APLICAÇÃO

1. **Frontend**: http://localhost:3000
2. **Backend API Docs**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/health

**Credenciais**:
- Usuário: `admin`
- Senha: `admin`

---

## 🔧 DESENVOLVIMENTO DIÁRIO

### Iniciar Trabalho
```bat
START_LOCAL_DEV.bat
```

### Hot Reload Automático

- **Backend**: Mude qualquer arquivo `.py` → Uvicorn recarrega automaticamente
- **Frontend**: Mude qualquer arquivo `.tsx/.ts` → Vite atualiza o browser instantaneamente

### Debug

**Backend**:
- Adicione `print()` ou `logger.info()` no código
- Veja logs na janela do terminal backend

**Frontend**:
- Use `console.log()` no código
- Abra DevTools do browser (F12)

### Parar Serviços

- **Fechar janelas** do Backend e Frontend
- **OU** pressionar `Ctrl+C` em cada terminal

---

## 📊 MONITORAMENTO DE MEMÓRIA

### Verificar Uso de RAM

**Windows Task Manager** (Ctrl+Shift+Esc):
- `python.exe` - Backend (~800MB-1.2GB)
- `node.exe` - Frontend (~300-500MB)
- **Total**: ~1.5GB (vs 6GB do Docker)

### Se Memória Ainda Alta

**Reduzir workers do backend** - Editar `backend/main.py`:
```python
# Trocar de:
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=4)

# Para:
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
```

**Fechar aplicações desnecessárias**:
- Chrome/Edge (manter só 2-3 abas)
- VS Code extensions pesadas
- Docker Desktop (se ainda estiver rodando!)

---

## 🐛 TROUBLESHOOTING

### Erro: `ModuleNotFoundError: No module named 'X'`

**Causa**: Dependências não instaladas

**Solução**:
```bash
cd backend
pip install -r requirements.txt
```

### Erro: `Address already in use: port 8000`

**Causa**: Outra aplicação usando porta 8000

**Solução**:
```bash
# Windows - Matar processo na porta 8000
netstat -ano | findstr :8000
taskkill /PID <numero_do_pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Erro: `GROQ_API_KEY is required`

**Causa**: API key não configurada no `.env`

**Solução**:
1. Obter chave grátis em https://console.groq.com/
2. Adicionar em `backend/.env`:
   ```env
   GROQ_API_KEY=gsk_sua_chave_aqui
   LLM_PROVIDER=groq
   ```

### Erro: `npm ERR! code ELIFECYCLE`

**Causa**: Dependências do Node desatualizadas

**Solução**:
```bash
cd frontend-solid
rm -rf node_modules package-lock.json
npm install
```

### Frontend não conecta ao Backend

**Verificar**:
1. Backend está rodando? → Acesse http://localhost:8000/health
2. CORS configurado? → Deve estar em `backend/.env`:
   ```env
   BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

---

## 🔄 QUANDO USAR DOCKER vs LOCAL

### Use Docker Quando:
- ✅ Deploy em produção (servidor com 16GB+ RAM)
- ✅ Testar configuração de produção
- ✅ Precisa de LangFuse/Prometheus/Grafana
- ✅ Servidor dedicado (não desenvolvimento)

### Use Local Quando:
- ✅ Desenvolvimento individual (8GB RAM)
- ✅ Precisa de hot reload rápido
- ✅ Debug frequente
- ✅ Iteração rápida de código
- ✅ **SUA SITUAÇÃO ATUAL** ✅

---

## 📈 ROADMAP PARA PRODUÇÃO (30 USUÁRIOS)

### Opção 1: VPS Cloud (Recomendado)

**Specs Mínimas**:
- **RAM**: 16GB (para Docker stack completo)
- **CPU**: 4 vCPUs
- **Disco**: 50GB SSD
- **Custo**: ~R$ 100-200/mês

**Providers**:
- DigitalOcean Droplet (16GB) - $84/mês
- AWS Lightsail (16GB) - ~$80/mês
- Azure VM B2ms (8GB) - ~R$ 150/mês
- Contabo VPS (16GB) - €10/mês (~R$ 60)

### Opção 2: Servidor On-Premise

**Specs Recomendadas**:
- **RAM**: 32GB
- **CPU**: Intel i5/i7 (8+ threads)
- **Disco**: 256GB SSD
- **Custo**: ~R$ 3.000-5.000 (one-time)

**Vantagens**:
- Sem mensalidade
- Controle total
- Dados locais

**Desvantagens**:
- Energia + Internet dedicada
- Manutenção manual
- Backup manual

---

## 🎓 DICAS DE PERFORMANCE (8GB RAM)

### Windows

1. **Desabilitar serviços desnecessários**:
   - Windows Search
   - Superfetch/Prefetch
   - Print Spooler (se não usa impressora)

2. **Gerenciador de Tarefas**:
   - Desabilitar programas de inicialização desnecessários
   - Fechar aplicações em background (OneDrive, Dropbox, etc)

3. **Configuração de Memória Virtual**:
   - Aumentar Paging File para 8GB-12GB

### Durante Desenvolvimento

- ✅ Fechar Chrome/Edge (manter só 2-3 abas)
- ✅ Usar VS Code Insiders (mais leve) ou Sublime Text
- ✅ Desabilitar extensions pesadas do VS Code
- ✅ **NUNCA rodar Docker + Local simultaneamente**
- ✅ Usar `npm run build` só quando necessário (build consome 2-3GB)

---

## 📝 CHECKLIST DIÁRIO

### Ao Iniciar Trabalho

- [ ] Fechar Docker Desktop (se estiver rodando)
- [ ] Fechar aplicações pesadas (Chrome com 20 abas, etc)
- [ ] Executar `START_LOCAL_DEV.bat`
- [ ] Aguardar 15s até backend e frontend iniciarem
- [ ] Acessar http://localhost:3000

### Durante Desenvolvimento

- [ ] Salvar arquivos frequentemente (Ctrl+S)
- [ ] Verificar logs do backend para erros
- [ ] Testar mudanças incrementalmente

### Ao Finalizar

- [ ] Fazer commit das mudanças (git)
- [ ] Fechar janelas do Backend e Frontend
- [ ] Documentar o que foi feito (se necessário)

---

## 🚀 QUICK START (RESUMO)

```bash
# 1. Instalar dependências (APENAS PRIMEIRA VEZ)
cd backend
pip install -r requirements.txt

cd ../frontend-solid
npm install

# 2. Configurar .env (APENAS PRIMEIRA VEZ)
copy backend\.env.example backend\.env
notepad backend\.env  # Adicionar GROQ_API_KEY

# 3. Iniciar desenvolvimento (TODO DIA)
START_LOCAL_DEV.bat

# 4. Acessar
http://localhost:3000
```

**Tempo total**: 5 min primeira vez, 15s próximas vezes

---

## 📞 SUPORTE

### Problemas Comuns

1. **Backend não inicia** → Verificar logs: falta API key ou SECRET_KEY
2. **Frontend erro 404** → Backend não está rodando
3. **Memória alta** → Reduzir workers do backend para 1
4. **Lento** → Fechar aplicações desnecessárias

### Logs Úteis

**Backend**:
```bash
cd backend
python main.py 2>&1 | tee logs/debug.log
```

**Frontend**:
```bash
cd frontend-solid
npm run dev > logs/vite.log 2>&1
```

---

**✅ SETUP LOCAL COMPLETO PARA 8GB RAM**
**🚀 EXECUTE `START_LOCAL_DEV.bat` AGORA**

**Economia**: 6GB RAM → 1.5GB RAM (75% menos!)
