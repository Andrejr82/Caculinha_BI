# Guia de Observabilidade (Custo Zero)
# Agent Solution BI

Este guia explica como subir a stack completa de monitoramento e observabilidade localmente, sem custos de licença.

---

## 🛠️ Stack Tecnológica

| Ferramenta | Porta | Função | Login Padrão |
|---|---|---|---|
| **LangFuse** | `:3000` | Tracing de LLM, Custos, Debug de Agentes | Criação no 1º acesso |
| **Grafana** | `:3001` | Dashboards Visuais (CPU, RAM, Erros) | `admin` / `admin` |
| **Prometheus** | `:9090` | Coletor de Métricas (Backend) | (Sem login) |

---

## 🚀 Como Iniciar

1. **Certifique-se de ter o Docker instalado** e rodando.
2. Execute o comando na raiz do projeto:

```powershell
docker-compose -f docker-compose.observability.yml up -d
```

3. Aguarde cerca de 1-2 minutos para os bancos de dados inicializarem.

---

## 🔌 Configurando o Projeto (Conexão)

### 1. Conectar LangFuse (Rastreio de IA)

1. Acesse `http://localhost:3000` e crie sua conta (local).
2. Crie um novo projeto (ex: "Agent BI").
3. Vá em **Settings > API Keys** e gere um novo par de chaves.
4. Adicione ao seu `.env` do backend (`backend/.env`):

```env
# LangFuse (Observabilidade IA)
LANGFUSE_SECRET_KEY=sk-lf-... (sua chave secreta)
LANGFUSE_PUBLIC_KEY=pk-lf-... (sua chave pública)
LANGFUSE_HOST=http://localhost:3000
```

### 2. Conectar Prometheus (Métricas de Servidor)

O backend já possui a biblioteca `prometheus-client` instalada.
Certifique-se de que o middleware de métricas esteja ativo no FastAPI (arquivo `main.py`).

O Prometheus tentará acessar `http://localhost:8000/metrics`.

---

## 📊 O Que Você Ganha?

### No LangFuse:
- **Tracing Visual:** Veja o fluxo exato: Usuário -> Agente -> Tool -> Gemini -> Resposta.
- **Custos:** Veja quanto custou cada interação em dólares (baseado nos tokens).
- **Latência:** Identifique gargalos (ex: "A query SQL demorou 5s, mas a LLM só 1s").

### No Grafana:
- Crie dashboards conectando ao **Prometheus** (DataSource).
- Monitore: Uso de CPU, Memória RAM, Quantidade de Requests/segundo.

---

## 🛑 Como Parar

```powershell
docker-compose -f docker-compose.observability.yml down
```
