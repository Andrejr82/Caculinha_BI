---
name: red-team-tactics
description: Princípios de táticas de red team baseados no MITRE ATT&CK. Fases de ataque, evasão de detecção, relatórios.
allowed-tools: Read, Glob, Grep
---

# Táticas de Red Team

> Princípios de simulação de adversário baseados no framework MITRE ATT&CK.

---

## 1. Fases do MITRE ATT&CK

### Ciclo de Vida do Ataque

```
RECONHECIMENTO → ACESSO INICIAL → EXECUÇÃO → PERSISTÊNCIA
       ↓               ↓              ↓             ↓
ESC. PRIVILÉGIO → EVASÃO DE DEFESA → ACESSO CRED → DESCOBERTA
       ↓               ↓              ↓             ↓
MOV. LATERAL → COLETA → C2 (COMANDO) → EXFILTRAÇÃO → IMPACTO
```

### Objetivos das Fases

| Fase | Objetivo |
|------|----------|
| **Reconhecimento** | Mapear a superfície de ataque |
| **Acesso Inicial** | Obter a primeira base (foothold) |
| **Execução** | Rodar código no alvo |
| **Persistência** | Sobreviver a reinicializações |
| **Escalonamento de Privilégio** | Obter acesso admin/root |
| **Evasão de Defesa** | Evitar detecção |
| **Acesso a Credenciais** | Coletar credenciais |
| **Descoberta** | Mapear a rede interna |
| **Movimentação Lateral** | Espalhar-se para outros sistemas |
| **Coleta** | Reunir dados do alvo |
| **C2 (Comando e Controle)** | Manter canal de comando |
| **Exfiltração** | Extrair os dados |

---

## 2. Princípios de Reconhecimento

### Passivo vs Ativo

| Tipo | Trade-off |
|------|-----------|
| **Passivo** | Sem contato com o alvo, informações limitadas |
| **Ativo** | Contato direto, maior risco de detecção |

### Alvos de Informação

| Categoria | Valor |
|-----------|-------|
| Stack tecnológica | Seleção do vetor de ataque |
| Informação de funcionários | Engenharia social |
| Faixas de rede | Escopo de escaneamento |
| Terceiros | Ataque de cadeia de suprimentos |

---

## 3. Vetores de Acesso Inicial

### Critérios de Seleção

| Vetor | Quando Usar |
|-------|-------------|
| **Phishing** | Alvo humano, acesso a e-mail |
| **Exploits públicos** | Serviços vulneráveis expostos |
| **Credenciais válidas** | Vazadas ou quebradas (cracked) |
| **Cadeia de suprimentos**| Acesso via terceiro |

---

## 4. Princípios de Escalonamento de Privilégio

### Alvos Windows

| Verificação | Oportunidade |
|-------------|--------------|
| Unquoted service paths | Escrita no caminho do serviço |
| Permissões de serviço fracas| Modificar o serviço |
| Privilégios de token | Abusar de SeDebug, etc. |
| Credenciais armazenadas | Coleta |

### Alvos Linux

| Verificação | Oportunidade |
|-------------|--------------|
| Binários SUID | Executar como dono (owner) |
| Configuração incorreta de Sudo| Execução de comando |
| Vulnerabilidades de Kernel | Exploits de kernel |
| Tarefas Cron | Scripts com permissão de escrita |

---

## 5. Princípios de Evasão de Defesa

### Técnicas Chave

| Técnica | Propósito |
|---------|-----------|
| LOLBins | Usar ferramentas legítimas do sistema |
| Ofuscação | Esconder código malicioso |
| Timestomping | Esconder modificações de arquivos |
| Limpeza de logs | Remover evidências |

### Segurança Operacional (OpSec)

- Trabalhar durante o horário comercial
- Imitar padrões de tráfego legítimos
- Usar canais criptografados
- Misturar-se com o comportamento normal

---

## 6. Princípios de Movimentação Lateral

### Tipos de Credenciais

| Tipo | Uso |
|------|-----|
| Senha | Autenticação padrão |
| Hash | Pass-the-hash |
| Ticket | Pass-the-ticket |
| Certificado | Autenticação por certificado |

### Caminhos de Movimentação

- Compartilhamentos administrativos
- Serviços remotos (RDP, SSH, WinRM)
- Exploração de serviços internos

---

## 7. Ataques ao Active Directory

### Categorias de Ataque

| Ataque | Alvo |
|--------|------|
| Kerberoasting | Senhas de contas de serviço |
| AS-REP Roasting | Contas sem pré-auth |
| DCSync | Credenciais de domínio |
| Golden Ticket | Acesso persistente ao domínio |

---

## 8. Princípios de Relatório

### Narrativa de Ataque

Documente a cadeia de ataque completa:
1. Como o acesso inicial foi obtido
2. Quais técnicas foram usadas
3. Quais objetivos foram alcançados
4. Onde a detecção falhou

### Lacunas de Detecção

Para cada técnica bem-sucedida:
- O que deveria ter detectado isso?
- Por que a detecção não funcionou?
- Como melhorar a detecção.

---

## 9. Fronteiras Éticas

### Sempre

- Fique dentro do escopo
- Minimize o impacto
- Reporte imediatamente se encontrar uma ameaça real
- Documente todas as ações

### Nunca

- Destrua dados de produção
- Cause negação de serviço (a menos que esteja no escopo)
- Acesse além da prova de conceito
- Retenha dados sensíveis

---

## 10. Anti-Padrões

| ❌ NÃO FAÇA | ✅ FAÇA |
|-------------|---------|
| Apressar a exploração | Siga a metodologia |
| Causar danos | Minimize o impacto |
| Pular o relatório | Documente tudo |
| Ignorar o escopo | Fique dentro dos limites |

---

> **Lembre-se:** O red team simula atacantes para melhorar as defesas, não para causar danos.
