---
name: powershell-windows
description: Padrões do PowerShell Windows. Armadilhas críticas, sintaxe de operadores, tratamento de erros.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Padrões de PowerShell Windows

> Padrões críticos e armadilhas para o Windows PowerShell.

---

## 1. Regras de Sintaxe de Operadores

### CRÍTICO: Parênteses Obrigatórios

| ❌ Errado | ✅ Correto |
|-----------|------------|
| `if (Test-Path "a" -or Test-Path "b")` | `if ((Test-Path "a") -or (Test-Path "b"))` |
| `if (Get-Item $x -and $y -eq 5)` | `if ((Get-Item $x) -and ($y -eq 5))` |

**Regra:** Cada chamada de cmdlet DEVE estar entre parênteses ao usar operadores lógicos.

---

## 2. Restrição de Unicode/Emoji

### CRÍTICO: Sem Unicode em Scripts

| Propósito | ❌ Não Use | ✅ Use |
|-----------|------------|--------|
| Sucesso | ✅ ✓ | [OK] [+] |
| Erro | ❌ ✗ 🔴 | [!] [X] |
| Aviso (Warning) | ⚠️ 🟡 | [*] [WARN] |
| Info | ℹ️ 🔵 | [i] [INFO] |
| Progresso | ⏳ | [...] |

**Regra:** Use apenas caracteres ASCII em scripts do PowerShell.

---

## 3. Padrões de Verificação de Nulo

### Sempre Verifique Antes de Acessar

| ❌ Errado | ✅ Correto |
|-----------|------------|
| `$array.Count -gt 0` | `$array -and $array.Count -gt 0` |
| `$texto.Length` | `if ($texto) { $texto.Length }` |

---

## 4. Interpolação de Strings

### Expressões Complexas

| ❌ Errado | ✅ Correto |
|-----------|------------|
| `"Valor: $($obj.prop.sub)"` | Armazene na variável primeiro |

**Padrão:**
```powershell
$valor = $obj.prop.sub
Write-Output "Valor: $valor"
```

---

## 5. Tratamento de Erros

### ErrorActionPreference

| Valor | Uso |
|-------|-----|
| Stop | Desenvolvimento (falhe rápido) |
| Continue | Scripts de produção |
| SilentlyContinue | Quando erros são esperados |

### Padrão Try/Catch

- Não use return dentro do bloco try
- Use o bloco finally para limpeza (cleanup)
- Retorne após o try/catch

---

## 6. Caminhos de Arquivo (File Paths)

### Regras de Caminho no Windows

| Padrão | Uso |
|--------|-----|
| Caminho literal | `C:\Users\Usuario\arquivo.txt` |
| Caminho variável | `Join-Path $env:USERPROFILE "arquivo.txt"` |
| Relativo | `Join-Path $ScriptDir "dados"` |

**Regra:** Use Join-Path para segurança entre plataformas.

---

## 7. Operações com Array

### Padrões Corretos

| Operação | Sintaxe |
|----------|---------|
| Array vazio | `$array = @()` |
| Adicionar item | `$array += $item` |
| ArrayList add | `$list.Add($item) | Out-Null` |

---

## 8. Operações JSON

### CRÍTICO: Parâmetro Depth

| ❌ Errado | ✅ Correto |
|-----------|------------|
| `ConvertTo-Json` | `ConvertTo-Json -Depth 10` |

**Regra:** Sempre especifique `-Depth` para objetos aninhados.

### Operações de Arquivo

| Operação | Padrão |
|----------|--------|
| Ler | `Get-Content "arquivo.json" -Raw | ConvertFrom-Json` |
| Escrever | `$dados | ConvertTo-Json -Depth 10 | Out-File "arquivo.json" -Encoding UTF8` |

---

## 9. Erros Comuns

| Mensagem de Erro | Causa | Correção |
|------------------|-------|----------|
| "parameter 'or'" | Falta de parênteses | Envolva os cmdlets em () |
| "Unexpected token"| Caractere Unicode | Use apenas ASCII |
| "Cannot find property" | Objeto nulo | Verifique nulo primeiro |
| "Cannot convert" | Tipo incompatível | Use .ToString() |

---

## 10. Template de Script

```powershell
# Modo estrito
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# Caminhos
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Principal
try {
    # Lógica aqui
    Write-Output "[OK] Concluído"
    exit 0
}
catch {
    Write-Warning "Erro: $_"
    exit 1
}
```

---

> **Lembre-se:** O PowerShell tem regras de sintaxe únicas. Parênteses, caracteres apenas ASCII e verificações de nulo são inegociáveis.
