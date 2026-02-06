# Guia de Limpeza Conservadora - BI Solution

## 📋 Visão Geral

Este guia explica como usar o sistema de limpeza seguro do projeto BI_Solution.

**Opção Escolhida:** CONSERVADORA (Opção 2)

### O que será excluído:

✅ **Arquivos de Log** (~4.3 MB)
- `backend/logs/**/*.log`
- `logs/**/*.log`
- `backend/test_login_debug.log`

✅ **Arquivos de Backup** (~12 KB)
- `backend/app/api/v1/endpoints/chat.py.backup`
- `backend/app/core/tools/une_tools_backup_old.py`
- `backend/app/core/utils/error_handler_backup.py`
- `frontend-solid/src/index.tsx.backup`

✅ **Sessões de Teste** (~100 KB)
- `backend/app/data/sessions/test-*.json`
- `backend/app/data/sessions/cache-test-*.json`
- `backend/app/data/sessions/test-cache-*.json`
- `backend/app/data/sessions/test-complex.json`

✅ **CSVs Temporários** (~50 KB)
- `data/input/*_temp_test.csv` (12 arquivos)

**Total Estimado:** ~55 arquivos, ~4.5 MB liberados

---

## 🚀 Como Usar

### Método 1: Usando o .bat (Recomendado - Windows)

```bash
cleanup.bat
```

O script irá:
1. Perguntar se você quer ver um preview primeiro
2. Mostrar todos os arquivos que serão excluídos
3. Pedir confirmação antes de executar
4. Criar backup automático
5. Executar a limpeza
6. Gerar relatório

### Método 2: Usando Python diretamente

**Preview (sem excluir nada):**
```bash
python cleanup_conservative.py --dry-run
```

**Executar limpeza:**
```bash
python cleanup_conservative.py
```

---

## 🔍 Preview Antes de Executar

**SEMPRE** execute o preview primeiro para ver o que será excluído:

```bash
python cleanup_conservative.py --preview
```

Isso mostrará:
- Lista completa de arquivos por categoria
- Tamanho total a ser liberado
- Nenhum arquivo será excluído (modo seguro)

---

## 🛡️ Sistema de Segurança

### 1. Backup Automático

Antes de qualquer exclusão, um backup completo é criado:

```
BACKUP_LIMPEZA_YYYYMMDD_HHMMSS/
├── backend/
│   ├── logs/
│   └── app/
├── logs/
└── BACKUP_REPORT.json
```

### 2. Arquivos Protegidos

O sistema NUNCA tocará em:

❌ Código fonte (Python, TypeScript)
❌ Arquivos .parquet (dados principais)
❌ Configurações (.env, package.json, etc)
❌ Cache semântico ativo
❌ Sessões de usuários reais
❌ Documentação principal (CLAUDE.md, README.md)

### 3. Confirmação Obrigatória

O script pede confirmação antes de executar:

```
Digite 'SIM' para confirmar:
```

Qualquer outra resposta cancela a operação.

---

## ⏮️ Como Reverter (Undo)

Se você quiser desfazer a limpeza:

### Método 1: Usando .bat

```bash
restore.bat
```

O script irá:
1. Listar todos os backups disponíveis
2. Pedir para escolher qual backup restaurar
3. Restaurar todos os arquivos

### Método 2: Usando Python

```bash
python restore_backup.py "BACKUP_LIMPEZA_20251228_150000"
```

**Substitua** `BACKUP_LIMPEZA_20251228_150000` pelo nome da sua pasta de backup.

---

## 📊 Relatórios Gerados

Após a limpeza, 2 relatórios são criados:

### 1. RELATORIO_LIMPEZA_YYYYMMDD_HHMMSS.json

```json
{
  "timestamp": "2025-12-28T15:30:00",
  "backup_location": "BACKUP_LIMPEZA_20251228_153000",
  "files_deleted": ["backend/logs/api/api.log", ...],
  "total_space_freed": 4500000,
  "errors": []
}
```

### 2. RELATORIO_LIMPEZA_YYYYMMDD_HHMMSS.md

Versão em Markdown com:
- Resumo executivo
- Lista completa de arquivos excluídos
- Erros (se houver)
- Instruções de como reverter

---

## ⚠️ Perguntas Frequentes

### Q: É seguro executar a limpeza?

**R:** Sim! O sistema tem múltiplas camadas de segurança:
- Backup automático antes de qualquer exclusão
- Preview obrigatório
- Confirmação manual
- Proteção de arquivos críticos
- Possibilidade de reverter

### Q: Posso perder código importante?

**R:** Não! O sistema NUNCA toca em:
- Arquivos .py (exceto backups)
- Arquivos .ts/.tsx (exceto backups)
- Arquivos de configuração
- Dados principais (.parquet)

### Q: E se eu me arrepender?

**R:** Use o `restore.bat` ou `restore_backup.py` para reverter tudo!

### Q: Quanto espaço vou ganhar?

**R:** Aproximadamente 4.5 MB. Parece pouco, mas limpa arquivos desnecessários e organiza o projeto.

### Q: Os logs serão recriados?

**R:** Sim! Os logs são criados automaticamente pela aplicação quando ela roda.

### Q: Posso executar várias vezes?

**R:** Sim! Após a primeira execução, haverá poucos arquivos para limpar (apenas logs novos).

---

## 🔧 Troubleshooting

### Erro: "Python não encontrado"

**Solução:**
```bash
# Verifique se Python está instalado
python --version

# Se não estiver, instale Python 3.8+
```

### Erro: "Permission denied"

**Solução:**
- Execute como Administrador
- Feche o Visual Studio Code ou editor
- Pare o backend/frontend se estiverem rodando

### Erro: "Falha ao criar backup"

**Solução:**
- Verifique se tem espaço em disco
- Verifique permissões da pasta
- Tente rodar como Administrador

---

## 📝 Checklist Antes de Executar

- [ ] Li este guia completo
- [ ] Executei o preview (`--dry-run`)
- [ ] Verifiquei os arquivos que serão excluídos
- [ ] Tenho certeza que quero prosseguir
- [ ] Fechei editores de código
- [ ] Parei backend/frontend se estiverem rodando

---

## 🎯 Próximos Passos Após Limpeza

1. **Verifique o relatório** gerado
2. **Teste a aplicação** para garantir que tudo funciona
3. **Mantenha o backup** por alguns dias
4. **Execute novamente** quando acumular logs

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique o relatório de erros
2. Reverta usando `restore.bat`
3. Consulte a documentação do projeto

---

**Data:** 2025-12-28
**Versão:** 1.0
**Modo:** Conservador (Opção 2)
