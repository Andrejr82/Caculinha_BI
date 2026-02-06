# Comandos Corrigidos - Problemas Resolvidos

## ✅ Problemas Corrigidos

### 1. `.wslconfig` - Removidas configurações não suportadas
- ❌ Removido: `pageReporting=false`
- ❌ Removido: `kernelCommandLine=...`
- ✅ Mantido: memory, processors, swap, localhostForwarding

### 2. Scripts `.sh` - Convertidos para formato Unix
- ✅ Removidos caracteres Windows (CRLF → LF)
- ✅ Permissão de execução aplicada
- ✅ Prontos para usar

---

## 🔄 IMPORTANTE: Reiniciar WSL

Execute no **PowerShell do Windows** (como Administrador):

```powershell
wsl --shutdown
```

Depois reabra o Ubuntu.

---

## 🚀 Comandos Corretos - Ubuntu Terminal

### 1. Abrir Ubuntu
```
Win + R → ubuntu → Enter
```

### 2. Navegar até o projeto
```bash
cd /mnt/c/Agente_BI/BI_Solution
```

### 3. Verificar se está na pasta certa
```bash
pwd
ls -la docker-*.sh
```

**Saída esperada:**
```
/mnt/c/Agente_BI/BI_Solution
-rwxr-xr-x ... docker-limpar-tudo.sh
-rwxr-xr-x ... docker-rebuild.sh
...
```

### 4. Executar limpeza
```bash
./docker-limpar-tudo.sh
```

### 5. Executar rebuild
```bash
./docker-rebuild.sh
```

---

## 📋 Sequência Completa

**No PowerShell (Admin):**
```powershell
wsl --shutdown
```

**Aguarde 5 segundos, depois abra Ubuntu:**
```
Win + R → ubuntu
```

**No Ubuntu:**
```bash
cd /mnt/c/Agente_BI/BI_Solution
./docker-limpar-tudo.sh
./docker-rebuild.sh
```

---

## ⚠️ Se ainda der erro

### Erro: "No such file or directory"
Verifique o caminho exato:
```bash
# Listar drives disponíveis
ls /mnt/

# Verificar se a pasta existe
ls /mnt/c/Agente_BI/

# Ou tente com letra minúscula
cd /mnt/c/agente_bi/BI_Solution
```

### Erro: "Permission denied"
```bash
chmod +x docker-*.sh
```

### Erro: "command not found"
Verifique se está na pasta correta:
```bash
pwd
# Deve mostrar: /mnt/c/Agente_BI/BI_Solution

ls docker-limpar-tudo.sh
# Deve mostrar: docker-limpar-tudo.sh
```

---

## 🎯 Execute Agora

**1. Feche o terminal Ubuntu atual**

**2. No PowerShell do Windows (Admin):**
```powershell
wsl --shutdown
```

**3. Aguarde 5 segundos**

**4. Abra Ubuntu novamente:**
```
Win + R → ubuntu
```

**5. Execute:**
```bash
cd /mnt/c/Agente_BI/BI_Solution
./docker-limpar-tudo.sh
```

---

## ✅ Status

- ✅ `.wslconfig` corrigido
- ✅ Scripts convertidos para formato Unix
- ✅ Permissões de execução aplicadas
- ⏳ **Falta:** Reiniciar WSL

Execute o comando de shutdown e tente novamente!
