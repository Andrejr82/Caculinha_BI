---
name: bash-linux
description: Padrões de terminal Bash/Linux. Comandos críticos, piping, tratamento de erros, scripting. Use ao trabalhar em sistemas macOS ou Linux.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Padrões de Bash Linux

> Padrões essenciais para Bash no Linux/macOS.

---

## 1. Sintaxe de Operadores

### Encadeamento de Comandos

| Operador | Significado | Exemplo |
|----------|-------------|---------|
| `;` | Executa sequencialmente | `cmd1; cmd2` |
| `&&` | Executa se o anterior tiver sucesso | `npm install && npm run dev` |
| `||` | Executa se o anterior falhar | `npm test || echo "Testes falharam"` |
| `|` | Redireciona a saída (pipe) | `ls | grep ".js"` |

---

## 2. Operações de Arquivo

### Comandos Essenciais

| Tarefa | Comando |
|--------|---------|
| Listar tudo | `ls -la` |
| Encontrar arquivos | `find . -name "*.js" -type f` |
| Conteúdo do arquivo | `cat arquivo.txt` |
| Primeiras N linhas | `head -n 20 arquivo.txt` |
| Últimas N linhas | `tail -n 20 arquivo.txt` |
| Seguir log | `tail -f log.txt` |
| Buscar em arquivos | `grep -r "padrao" --include="*.js"` |
| Tamanho do arquivo | `du -sh *` |
| Uso do disco | `df -h` |

---

## 3. Gerenciamento de Processos

| Tarefa | Comando |
|--------|---------|
| Listar processos | `ps aux` |
| Buscar por nome | `ps aux | grep node` |
| Matar por PID | `kill -9 <PID>` |
| Buscar usuário da porta | `lsof -i :3000` |
| Matar porta | `kill -9 $(lsof -t -i :3000)` |
| Segundo plano | `npm run dev &` |
| Jobs | `jobs -l` |
| Trazer para frente | `fg %1` |

---

## 4. Processamento de Texto

### Ferramentas Core

| Ferramenta | Propósito | Exemplo |
|------------|-----------|---------|
| `grep` | Busca | `grep -rn "TODO" src/` |
| `sed` | Substituição | `sed -i 's/antigo/novo/g' arquivo.txt` |
| `awk` | Extração de colunas | `awk '{print $1}' arquivo.txt` |
| `cut` | Cortar campos | `cut -d',' -f1 dados.csv` |
| `sort` | Ordenar linhas | `sort -u arquivo.txt` |
| `uniq` | Linhas únicas | `sort arquivo.txt | uniq -c` |
| `wc` | Contagem | `wc -l arquivo.txt` |

---

## 5. Variáveis de Ambiente

| Tarefa | Comando |
|--------|---------|
| Ver todas | `env` ou `printenv` |
| Ver uma | `echo $PATH` |
| Definir temporária | `export VAR="valor"` |
| Definir no script | `VAR="valor" comando` |
| Adicionar ao PATH | `export PATH="$PATH:/novo/caminho"` |

---

## 6. Rede

| Tarefa | Comando |
|--------|---------|
| Download | `curl -O https://exemplo.com/arquivo` |
| Requisição API | `curl -X GET https://api.exemplo.com` |
| POST JSON | `curl -X POST -H "Content-Type: application/json" -d '{"chave":"valor"}' URL` |
| Verificar porta | `nc -zv localhost 3000` |
| Info da rede | `ifconfig` ou `ip addr` |

---

## 7. Template de Script

```bash
#!/bin/bash
set -euo pipefail  # Sai no erro, var indefinida ou erro no pipe

# Cores (opcional)
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Funções
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Principal
main() {
    log_info "Iniciando..."
    # Sua lógica aqui
    log_info "Concluído!"
}

main "$@"
```

---

## 8. Padrões Comuns

### Verificar se o comando existe

```bash
if command -v node &> /dev/null; then
    echo "Node está instalado"
fi
```

### Valor padrão de variável

```bash
NOME=${1:-"valor_padrao"}
```

### Ler arquivo linha por linha

```bash
while IFS= read -r linha; do
    echo "$linha"
done < arquivo.txt
```

### Loop sobre arquivos

```bash
for arquivo in *.js; do
    echo "Processando $arquivo"
done
```

---

## 9. Diferenças para o PowerShell

| Tarefa | PowerShell | Bash |
|--------|------------|------|
| Listar arquivos | `Get-ChildItem` | `ls -la` |
| Buscar arquivos | `Get-ChildItem -Recurse` | `find . -type f` |
| Ambiente | `$env:VAR` | `$VAR` |
| Concat. string | `"$a$b"` | `"$a$b"` (mesmo) |
| Check nulo | `if ($x)` | `if [ -n "$x" ]` |
| Pipeline | Baseado em objetos | Baseado em texto |

---

## 10. Tratamento de Erros

### Definir opções

```bash
set -e          # Sai no erro
set -u          # Sai em variável indefinida
set -o pipefail # Sai em erro no pipe
set -x          # Depuração: imprime os comandos
```

### Trap para limpeza (cleanup)

```bash
cleanup() {
    echo "Limpando..."
    rm -f /tmp/arquivo_temp
}
trap cleanup EXIT
```

---

> **Lembre-se:** O Bash é baseado em texto. Use `&&` para cadeias de sucesso, `set -e` para segurança e coloque suas variáveis entre aspas!
