# 📦 GUIA DE INSTALAÇÃO DE DEPENDÊNCIAS - BI_Solution v2.0

**Data:** 22 de Janeiro de 2026, 22:29  
**Status:** ✅ ATUALIZADO

---

## 🐍 Backend (Python)

### Dependências Principais

```bash
cd backend
pip install -r requirements.txt
```

### Dependências Críticas Adicionais

Se `requirements.txt` não incluir, instalar manualmente:

```bash
pip install langchain langchain-core langchain-community
pip install duckdb polars pyarrow
pip install fastapi uvicorn
pip install google-generativeai
```

### Validação

```bash
python -c "from langchain_core.tools import tool; print('✅ LangChain OK')"
python -c "import duckdb; print('✅ DuckDB OK')"
python -c "import polars; print('✅ Polars OK')"
```

---

## 📦 Frontend (Node.js)

### Dependências Principais

```bash
cd frontend-solid
npm install
```

### Dependências Críticas Adicionais

```bash
npm install chart.js
npm install @solidjs/router
npm install @tanstack/solid-query
```

### Validação

```bash
npm list chart.js
npm list @solidjs/router
```

---

## 🚀 Instalação Completa (Script)

### Windows (PowerShell)

```powershell
# Backend
cd backend
pip install -r requirements.txt
pip install langchain langchain-core langchain-community

# Frontend
cd ../frontend-solid
npm install
npm install chart.js

# Validação
Write-Host "✅ Dependências instaladas!"
```

### Linux/Mac (Bash)

```bash
#!/bin/bash

# Backend
cd backend
pip install -r requirements.txt
pip install langchain langchain-core langchain-community

# Frontend
cd ../frontend-solid
npm install
npm install chart.js

# Validação
echo "✅ Dependências instaladas!"
```

---

## 🔍 Troubleshooting

### Problema: "LangChain dependencies missing"

**Solução:**
```bash
pip install langchain langchain-core langchain-community
```

### Problema: "Cannot find module 'chart.js/auto'"

**Solução:**
```bash
cd frontend-solid
npm install chart.js
```

### Problema: "Module not found: Error: Can't resolve '@solidjs/router'"

**Solução:**
```bash
npm install @solidjs/router
```

---

## ✅ Checklist de Instalação

### Backend
- [ ] Python 3.11+ instalado
- [ ] pip atualizado (`pip install --upgrade pip`)
- [ ] requirements.txt executado
- [ ] LangChain instalado
- [ ] DuckDB instalado
- [ ] Validação OK

### Frontend
- [ ] Node.js 18+ instalado
- [ ] npm atualizado (`npm install -g npm`)
- [ ] package.json executado (`npm install`)
- [ ] chart.js instalado
- [ ] Build OK (`npm run build`)

---

## 📝 Versões Recomendadas

| Dependência | Versão Mínima | Versão Recomendada |
|-------------|---------------|-------------------|
| **Python** | 3.11 | 3.11+ |
| **Node.js** | 18.0 | 20.x LTS |
| **pip** | 23.0 | Latest |
| **npm** | 9.0 | Latest |
| **LangChain** | 0.1.0 | Latest |
| **chart.js** | 4.0 | Latest |
| **DuckDB** | 1.0 | 1.1+ |

---

**Última Atualização:** 22 de Janeiro de 2026  
**Mantido por:** Code Archaeologist
