# 🛒 Agent Solution BI - Lojas Caçula (Executive Edition)

**Inteligência Artificial Generativa e Análise de Alta Performance para a Gestão de Varejo.**

O **Agent Solution BI** é uma plataforma de decisão estratégica desenvolvida especificamente para a rede Lojas Caçula. Combinando o poder do **Google Gemini 3.0 Flash** com a velocidade do motor de dados **Polars**, o sistema transforma milhões de registros de venda e estoque em planos de ação imediatos.

---

## 💎 Diferenciais Estratégicos (Apresentação à Diretoria)

### 🧠 IA Retail Insights (Gemini 3.0 Flash)
Não apenas gráficos, mas diagnósticos. A IA analisa proativamente:
- **Crescimento MoM**: Monitoramento de tração de vendas em tempo real.
- **Eficiência de Cobertura**: Identificação de capital imobilizado (estoque acima de 30 dias).
- **Ruptura de Gôndola**: Alertas imediatos quando há estoque no CD mas falta na Loja.

### 📈 Análise de Pareto 80/20 Real
Foco no que gera faturamento. O sistema utiliza a técnica de **Curva ABC por Receita** para identificar o "Vital Few":
- **Classe A**: Os 20% de produtos que sustentam 80% do faturamento da Caçula.
- **Visualização Dual**: Gráfico de Pareto (Barras + Linha Acumulada) para visão clara de concentração.

### ⚡ Performance Ultra-Rápida
- **Motor DuckDB**: Processamento de mais de 1 milhão de SKUs em milissegundos (3.3x mais rápido).
- **Arquitetura Parquet**: Queries SQL analíticas em arquivos colunares de alta eficiência.
- **76% menos memória**: Otimizado para execução em qualquer ambiente (400 MB vs 1.7 GB).

---

## 🚀 Funcionalidades Principais

### 💬 Chat BI Conversacional
Interação em linguagem natural (ex: *"Quais categorias de Tecidos cresceram mais de 10%?"*). A IA entende o contexto do varejo e gera visualizações sob demanda.

### 📊 Dashboard Estratégico
Painel executivo com KPIs críticos: Valor Total de Estoque, Taxa de Ruptura, Mix de Produtos e Monitoramento de UNEs.

### 🚚 Operacional e Logística
- **Sugestão de Transferência**: Algoritmo inteligente que propõe movimentações CD -> Loja.
- **Rupturas Críticas**: Listagem prioritária baseada em perda de faturamento iminente.

### 🔐 Segurança e Governança
- **Controle por Segmento**: Gestores de "Papelaria" acessam apenas seus dados, enquanto a Diretoria possui "Visão Global".
- **Sistema de Aprendizado**: A IA aprende com o feedback dos gestores para refinar suas recomendações.

---

## 🎨 Identidade Visual (Lojas Caçula - 40 Anos)

| Cor | Hex | Significado |
|-----|-----|-------------|
| Marrom Caçula | `#8B7355` | Solidez e Tradição |
| Dourado/Bronze | `#C9A961` | Excelência e Valor |
| Verde Sucesso | `#166534` | Eficiência de Estoque (Classe A) |
| Vermelho Alerta | `#991B1B` | Risco de Ruptura (Classe C/D) |

---

## 🛠️ Tecnologias Utilizadas

- **Frontend**: SolidJS (Performance reativa superior ao React).
- **Backend**: FastAPI (Python 3.11+).
- **Processamento**: DuckDB 1.1+ (SQL Analítico Ultra-Rápido).
- **IA de Negócio**: Google Gemini 3.0 Flash (Native Function Calling).
- **Armazenamento**: Apache Parquet (Arrow Zero-Copy).

---

## 📁 Guia de Instalação Rápida

```bash
# Instalação simplificada
npm run install
# Execução sincronizada (Frontend + Backend)
npm run dev
```

**Acesse:** [http://localhost:3000](http://localhost:3000)

---

## 👥 Contas de Demonstração

- **Administrador (Global)**: `admin` / `admin`
- **Gestor Segmento**: `hugo.mendes` / `123456`

---

## 📂 Estrutura do Projeto

```
BI_Solution/
├── README.md                  # Este arquivo
├── docker-compose.yml         # Configuração Docker principal
├── docker-compose.light.yml   # Configuração Docker leve
├── start.bat                  # Script de inicialização rápida
│
├── backend/                   # API FastAPI + DuckDB
├── frontend-solid/            # Interface SolidJS
│
├── docs/                      # 📚 Documentação completa
│   ├── INDEX.md              # Índice de toda documentação
│   ├── migration/            # Documentação migração DuckDB
│   ├── guides/               # Guias operacionais
│   ├── archive/              # Documentação histórica
│   └── PRD.md                # Product Requirements Document
│
├── scripts/                   # Scripts utilitários
│   └── utils/                # Scripts Docker/WSL/manutenção
│
├── config/                    # Configurações
│   ├── docker/               # Docker Compose especializados
│   └── prometheus/           # Monitoramento
│
└── data/                      # Dados e cache (não versionado)
    ├── parquet/              # Arquivos .parquet
    └── cache/                # Cache DuckDB
```

**📖 Para começar, leia**: [`docs/INDEX.md`](docs/INDEX.md)

---

*Lojas Caçula © 2025 - Transformando dados em decisões estratégicas.*
*Powered by DuckDB 🦆 - 3.3x mais rápido, 76% menos memória.*