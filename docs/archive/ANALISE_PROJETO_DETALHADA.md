# Análise Detalhada do Projeto BI_Solution

**Data da Análise:** 28/12/2025 15:18:29

---

## Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Backend (FastAPI + Python)](#backend-fastapi--python)
3. [Frontend (SolidJS + TypeScript)](#frontend-solidjs--typescript)
4. [Arquivos de Configuração](#arquivos-de-configuração)
5. [Documentação](#documentação)
6. [Scripts e Utilitários](#scripts-e-utilitários)
7. [Testes](#testes)
8. [Dados](#dados)
9. [Arquivos para Limpeza](#arquivos-para-limpeza)
10. [Todos os Arquivos (Detalhado)](#todos-os-arquivos-detalhado)

---

## Visão Geral da Arquitetura

- **Backend:** 319 arquivos Python
- **Frontend:** 111 arquivos TypeScript/JavaScript
- **Configuração:** 4 arquivos
- **Documentação:** 47 arquivos
- **Scripts:** 31 arquivos
- **Testes:** 32 arquivos
- **Dados:** 39 arquivos

---

## Backend (FastAPI + Python)

### Ponto de Entrada

**`backend\main.py`**

- **Propósito:** Ponto de entrada da aplicação FastAPI

### API Endpoints

#### `backend\app\api\v1\endpoints\__init__.py`

- **Propósito:** Inicializador de pacote Python

#### `backend\app\api\v1\endpoints\admin.py`

- **Propósito:** Admin Endpoints

#### `backend\app\api\v1\endpoints\analytics.py`

- **Propósito:** Analytics Endpoints
- **Endpoints:** 1 rotas
  - `_initialize_metrics_dashboard()` - N/A

#### `backend\app\api\v1\endpoints\auth.py`

- **Propósito:** Authentication Endpoints

#### `backend\app\api\v1\endpoints\auth_alt.py`

- **Propósito:** ENDPOINT DE LOGIN ALTERNATIVO - USA PYODBC DIRETO (SÍNCRONO)
- **Endpoints:** 1 rotas
  - `login_alt()` - Login alternativo usando pyodbc síncrono

#### `backend\app\api\v1\endpoints\chat.py`

- **Propósito:** Chat Endpoints
- **Endpoints:** 2 rotas
  - `safe_json_dumps()` - Safely serialize any Python object to JSON string.
Handles MapComposite, numpy types, pandas types, 
  - `_initialize_agents_and_llm()` - Lazy initialization: Executado apenas no primeiro request ao invés de no startup.
Reduz tempo de ini

#### `backend\app\api\v1\endpoints\chat.py.backup`

- **Propósito:** Não identificado

#### `backend\app\api\v1\endpoints\code_chat.py`

- **Propósito:** Code Chat API Endpoints

#### `backend\app\api\v1\endpoints\diagnostics.py`

- **Propósito:** Define classes: DBConfig, ConnectionTestResult

#### `backend\app\api\v1\endpoints\frontend_logs.py`

- **Propósito:** Endpoint para receber logs do frontend
- **Endpoints:** 1 rotas
  - `map_frontend_log_level()` - Mapeia níveis de log do frontend para níveis do Python logging
Frontend: DEBUG=0, INFO=1, WARN=2, ER

#### `backend\app\api\v1\endpoints\health.py`

- **Propósito:** Health Check Endpoint with Timeout
- **Endpoints:** 1 rotas
  - `check_environment()` - Check critical environment variables

Returns:
    Status dictionary for environment configuration

#### `backend\app\api\v1\endpoints\insights.py`

- **Propósito:** AI Insights Endpoints

#### `backend\app\api\v1\endpoints\learning.py`

- **Propósito:** Define classes: FeedbackSubmission, RetrievalQuery

#### `backend\app\api\v1\endpoints\metrics.py`

- **Propósito:** Metrics Endpoints

#### `backend\app\api\v1\endpoints\playground.py`

- **Propósito:** Define classes: QueryRequest, ChatMessage, PlaygroundChatRequest

#### `backend\app\api\v1\endpoints\preferences.py`

- **Propósito:** User Preferences Endpoints

#### `backend\app\api\v1\endpoints\reports.py`

- **Propósito:** Reports Endpoints

#### `backend\app\api\v1\endpoints\rupturas.py`

- **Propósito:** Não identificado

#### `backend\app\api\v1\endpoints\shared.py`

- **Propósito:** Shared Conversations Endpoints

#### `backend\app\api\v1\endpoints\test.py`

- **Propósito:** Testes unitários (0 testes)

#### `backend\app\api\v1\endpoints\transfers.py`

- **Propósito:** Define classes: TransferRequestPayload, TransferReportQuery, ProductSearchRequest

---

## Frontend (SolidJS + TypeScript)

### Páginas

#### `frontend-solid\src\pages\About.tsx`

- **Propósito:** Página: Não identificado
- **Dependências:** 1 imports

#### `frontend-solid\src\pages\Admin.tsx`

- **Propósito:** Página: Componentes React/Solid: openCreateUserModal, openEditUserModal, closeUserModal
- **Componentes:** openCreateUserModal, openEditUserModal, closeUserModal
- **Dependências:** 3 imports

#### `frontend-solid\src\pages\Analytics.tsx`

- **Propósito:** Página: Componentes React/Solid: downloadABCCSV, generateCharts
- **Componentes:** downloadABCCSV, generateCharts
- **Dependências:** 5 imports

#### `frontend-solid\src\pages\Chat.tsx`

- **Propósito:** Página: Componentes React/Solid: stopGeneration, clearConversation, regenerateLastResponse
- **Componentes:** stopGeneration, clearConversation, regenerateLastResponse, startEditMessage, cancelEditMessage
- **Dependências:** 13 imports

#### `frontend-solid\src\pages\CodeChat.tsx`

- **Propósito:** Página: Componentes React/Solid: clearHistory, loadExample
- **Componentes:** clearHistory, loadExample
- **Dependências:** 4 imports

#### `frontend-solid\src\pages\Dashboard.tsx`

- **Propósito:** Página: Componentes React/Solid: handleProductClick
- **Componentes:** handleProductClick
- **Dependências:** 8 imports

#### `frontend-solid\src\pages\Diagnostics.tsx`

- **Propósito:** Página: Componentes React/Solid: getStatusColor, getStatusIcon, getStatusLabel
- **Componentes:** getStatusColor, getStatusIcon, getStatusLabel
- **Dependências:** 2 imports

#### `frontend-solid\src\pages\Examples.tsx`

- **Propósito:** Página: Componentes React/Solid: perguntasFiltradas, handleTestarPergunta
- **Componentes:** perguntasFiltradas, handleTestarPergunta
- **Dependências:** 3 imports

#### `frontend-solid\src\pages\Help.tsx`

- **Propósito:** Página: Componentes React/Solid: isAdmin, filteredFAQ
- **Componentes:** isAdmin, filteredFAQ
- **Dependências:** 3 imports

#### `frontend-solid\src\pages\Learning.tsx`

- **Propósito:** Página: Componentes React/Solid: getSuccessRateColor
- **Componentes:** getSuccessRateColor
- **Dependências:** 4 imports

#### `frontend-solid\src\pages\Login.tsx`

- **Propósito:** Página: Exporta: Login
- **Dependências:** 5 imports

#### `frontend-solid\src\pages\Playground.tsx`

- **Propósito:** Página: Componentes React/Solid: clearHistory, loadExample, generateCodeSnippet
- **Componentes:** clearHistory, loadExample, generateCodeSnippet
- **Dependências:** 4 imports

#### `frontend-solid\src\pages\Profile.tsx`

- **Propósito:** Página: Exporta: Profile
- **Dependências:** 4 imports

#### `frontend-solid\src\pages\Reports.tsx`

- **Propósito:** Página: Componentes React/Solid: downloadReport, downloadAllAsCSV, filteredReports
- **Componentes:** downloadReport, downloadAllAsCSV, filteredReports, setQuickFilter
- **Dependências:** 3 imports

#### `frontend-solid\src\pages\Rupturas.tsx`

- **Propósito:** Página: Componentes React/Solid: generateCharts, handleChartClick, handleGroupClick
- **Componentes:** generateCharts, handleChartClick, handleGroupClick, getProductsByGroup, clearFilters
- **Dependências:** 5 imports

#### `frontend-solid\src\pages\SharedConversation.tsx`

- **Propósito:** Página: Exporta: SharedConversation
- **Dependências:** 3 imports

#### `frontend-solid\src\pages\Transfers.tsx`

- **Propósito:** Página: Componentes React/Solid: toggleProductSelection, removeFromCart, clearCart
- **Componentes:** toggleProductSelection, removeFromCart, clearCart, getUrgencyColor, isSelectedInMode
- **Dependências:** 4 imports

#### `frontend-solid\src\pages\chat-markdown.css`

- **Propósito:** Não identificado

### Componentes

#### `frontend-solid\src\components\AIInsightsPanel.tsx`

- **Propósito:** Componente: Componentes React/Solid: getCategoryIcon, getCategoryColor, getSeverityBadge
- **Componentes:** getCategoryIcon, getCategoryColor, getSeverityBadge

#### `frontend-solid\src\migrated-components\components\ui\Alert.tsx`

- **Propósito:** Componente: * Alert component - notification container
 * Migrated from React to SolidJS

#### `frontend-solid\src\migrated-components\components\ui\Avatar.tsx`

- **Propósito:** Componente: * Avatar component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation)

#### `frontend-solid\src\migrated-components\components\ui\Badge.test.tsx`

- **Propósito:** Componente: Não identificado

#### `frontend-solid\src\migrated-components\components\ui\Badge.tsx`

- **Propósito:** Componente: * Badge component for status indicators and labels
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Badge variant="default">New</Badge>
 * <Badge variant="destructive">Error</Badge>
 * 

#### `frontend-solid\src\migrated-components\components\ui\Button.test.tsx`

- **Propósito:** Componente: Não identificado

#### `frontend-solid\src\migrated-components\components\ui\Button.tsx`

- **Propósito:** Componente: * Button component with multiple variants and sizes
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Button variant="default">Click me</Button>
 * <Button variant="destructive" size="sm

#### `frontend-solid\src\migrated-components\components\ui\Card.tsx`

- **Propósito:** Componente: * Card component - main container

#### `frontend-solid\src\components\ChartDownloadButton.tsx`

- **Propósito:** Componente: Exporta: ChartDownloadButton, MultiFormatDownload

#### `frontend-solid\src\components\__tests__\Chat.test.tsx`

- **Propósito:** Componente: Não identificado

#### `frontend-solid\src\components\DataTable.tsx`

- **Propósito:** Componente: Componentes React/Solid: DataTable, tableData, headers
- **Componentes:** DataTable, tableData, headers, paginatedData, totalPages, goToPage, canGoPrev, canGoNext

#### `frontend-solid\src\migrated-components\components\ui\Dialog.tsx`

- **Propósito:** Componente: * Dialog component - modal dialog
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
- **Componentes:** open, setOpen

#### `frontend-solid\src\components\DownloadButton.tsx`

- **Propósito:** Componente: Componentes React/Solid: handleDownload
- **Componentes:** handleDownload

#### `frontend-solid\src\migrated-components\components\ui\DropdownMenu.tsx`

- **Propósito:** Componente: * DropdownMenu component - dropdown menu
 * Migrated from React to SolidJS (simplified native implementation)
- **Componentes:** open, setOpen

#### `frontend-solid\src\components\ErrorBoundary.tsx`

- **Propósito:** Componente: Exporta: ErrorBoundary

#### `frontend-solid\src\components\ExportMenu.tsx`

- **Propósito:** Componente: Componentes React/Solid: downloadFile, exportAsJSON, exportAsMarkdown
- **Componentes:** downloadFile, exportAsJSON, exportAsMarkdown, exportAsText

#### `frontend-solid\src\components\FeedbackButtons.tsx`

- **Propósito:** Componente: Componentes React/Solid: handleFeedbackClick
- **Componentes:** handleFeedbackClick

#### `frontend-solid\src\migrated-components\components\ui\Input.tsx`

- **Propósito:** Componente: * Input component for form fields
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Input type="text" placeholder="Enter text..." />
 * <Input type="email" />
 * ```

#### `frontend-solid\src\migrated-components\components\ui\Label.tsx`

- **Propósito:** Componente: * Label component for form fields
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Label for="email">Email</Label>
 * ```

#### `frontend-solid\src\migrated-components\components\ui\LazyImage.tsx`

- **Propósito:** Componente: * LazyImage component - optimized image loading
 * Migrated from React to SolidJS (Next.js Image removed, native img)
 * 
 * @example
 * ```tsx
 * <LazyImage src="/image.jpg" alt="Description" />
 * `
- **Componentes:** fallbackSrc, imageSrc

#### `frontend-solid\src\components\Logo.tsx`

- **Propósito:** Componente: Exporta: Logo

#### `frontend-solid\src\components\MessageActions.tsx`

- **Propósito:** Componente: Componentes React/Solid: copyToClipboard
- **Componentes:** copyToClipboard

#### `frontend-solid\src\components\PlotlyChart.tsx`

- **Propósito:** Componente: Componentes React/Solid: PlotlyChart, toggleExpand, handleEsc
- **Componentes:** PlotlyChart, toggleExpand, handleEsc, renderPlot

#### `frontend-solid\src\migrated-components\README.md`

- **Propósito:** Documentação: Componentes UI Migrados - React → SolidJS

#### `frontend-solid\src\migrated-components\utils\README.md`

- **Propósito:** Documentação: Utilitários Migrados

#### `frontend-solid\src\migrated-components\components\ui\Select.tsx`

- **Propósito:** Componente: * Select component - native select dropdown
 * Migrated from React to SolidJS (simplified, native select)

#### `frontend-solid\src\migrated-components\components\ui\Separator.tsx`

- **Propósito:** Componente: * Separator component for visual division
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Separator />
 * <Separator orientation="vertical" />
- **Componentes:** orientation, decorative

#### `frontend-solid\src\components\ShareButton.tsx`

- **Propósito:** Componente: Componentes React/Solid: openModal, closeModal
- **Componentes:** openModal, closeModal

#### `frontend-solid\src\migrated-components\components\ui\Sheet.tsx`

- **Propósito:** Componente: * Sheet component - side panel/drawer
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
- **Componentes:** side, open, setOpen, sideClasses

#### `frontend-solid\src\migrated-components\components\ui\Skeleton.test.tsx`

- **Propósito:** Componente: Não identificado

#### `frontend-solid\src\migrated-components\components\ui\Skeleton.tsx`

- **Propósito:** Componente: * Skeleton component for loading states
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Skeleton class="w-full h-20" />
 * ```

#### `frontend-solid\src\migrated-components\components\ui\SkipLink.tsx`

- **Propósito:** Componente: * SkipLink Component
 * Link de pular navegação para acessibilidade
 * Migrated from React to SolidJS (Next.js Link removed, native anchor)

#### `frontend-solid\src\migrated-components\components\ui\Sonner.tsx`

- **Propósito:** Componente: * Toast notification system (Sonner alternative)
 * Migrated from React to SolidJS (native implementation)
- **Componentes:** getToastClasses

#### `frontend-solid\src\migrated-components\components\ui\Table.tsx`

- **Propósito:** Componente: * Table component - table container with scroll
 * Migrated from React to SolidJS

#### `frontend-solid\src\migrated-components\components\ui\Tabs.tsx`

- **Propósito:** Componente: * Tabs component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation with createSignal)
- **Componentes:** value, setValue, isActive, isActive

#### `frontend-solid\src\components\Typewriter.tsx`

- **Propósito:** Componente: * Componente Typewriter - Efeito de digitação ChatGPT-like
 *
 * Renderiza texto com efeito de digitação suave, caractere por caractere.
 * Perfeito para respostas de chat/IA que chegam via streaming.

#### `frontend-solid\src\components\TypingIndicator.css`

- **Propósito:** Não identificado

#### `frontend-solid\src\components\TypingIndicator.tsx`

- **Propósito:** Componente: Exporta: TypingIndicator

#### `frontend-solid\src\migrated-components\USAGE_GUIDE.md`

- **Propósito:** Documentação: Guia de Uso - Componentes UI Migrados para SolidJS

#### `frontend-solid\src\components\UserPreferences.tsx`

- **Propósito:** Componente: Componentes React/Solid: updatePreference
- **Componentes:** updatePreference

#### `frontend-solid\src\migrated-components\utils\a11y.ts`

- **Propósito:** Componente: * Accessibility Utilities for SolidJS
 * Funções utilitárias para acessibilidade
- **Componentes:** handleTabKey

#### `frontend-solid\src\migrated-components\utils\cn.ts`

- **Propósito:** Componente: * Combina classes CSS com suporte a Tailwind
 * Útil para mesclar classes condicionais

#### `frontend-solid\src\migrated-components\globals.css`

- **Propósito:** Não identificado

#### `frontend-solid\src\components\index.ts`

- **Propósito:** Componente: * Components Index
 * Central export for all reusable components

#### `frontend-solid\src\migrated-components\components\ui\index.ts`

- **Propósito:** Componente: * UI Components - Migrated from React to SolidJS
 * 
 * This barrel file exports all UI components for easy importing
 * 
 * Total: 18 components migrated (100%)

---

## Arquivos de Configuração

### `.gitignore`

- **Propósito:** Arquivos ignorados pelo Git

### `analyze.bat`

- **Propósito:** Script de análise do projeto

### `package.json`

- **Propósito:** Configuração de dependências Node.js

### `start.bat`

- **Propósito:** Script de inicialização Windows

---

## Documentação

### `docs\troubleshooting\AGENT_JSON_OUTPUT.md`

- **Propósito:** Documentação: Troubleshooting: Agent Returning Raw JSON (Context7 Violation)
- **Seções:** 🚨 Problema Relatado, 🔍 Causa Raiz, 🛠️ Solução Aplicada (24/12/2025), ✅ Validação

### `ANALISE_PROJETO_DETALHADA.md`

- **Propósito:** Documentação: Análise Detalhada do Projeto BI_Solution
- **Seções:** Índice, Visão Geral da Arquitetura, Backend (FastAPI + Python), Frontend (SolidJS + TypeScript), Arquivos de Configuração, Documentação, Scripts e Utilitários, Testes

### `docs\API_DOCUMENTATION.md`

- **Propósito:** Documentação: Documentação da API - Agent Solution BI
- **Seções:** Visão Geral, 🔐 Autenticação, 💬 Chat BI (Agente), 📊 Analytics, 📦 Transferências (UNE), ⚠️ Rupturas

### `docs\ARQUITETURA.md`

- **Propósito:** Documentação: Arquitetura do Sistema Agent Solution BI
- **Seções:** 1. Visão Geral, 2. Componentes do Backend, 3. Componentes do Frontend, 4. Fluxos de Dados Principais, 5. Considerações de Segurança

### `docs\ARQUITETURA_VISUAL.md`

- **Propósito:** Documentação: Diagrama Visual da Arquitetura do Sistema
- **Seções:** Visão Geral (C4 Container Diagram), Legenda Técnica

### `CLAUDE.md`

- **Propósito:** Documentação: CLAUDE.md
- **Seções:** Project Overview, Quick Start Commands, Architecture Overview, Important Architectural Decisions, Authentication & Security, Environment Variables, Database Schema, Code Style & Conventions

### `docs\CODE_CHAT_GUIDE.md`

- **Propósito:** Documentação: Code Chat - Agente Fullstack Completo
- **Seções:** Visão Geral, ✨ Funcionalidades, 📦 Instalação, 🚀 Uso, 📊 Arquitetura, 💰 Custos, 🔧 Manutenção, 🐛 Troubleshooting

### `docs\CORRECAO_DEFINITIVA_UNE.md`

- **Propósito:** Documentação: ✅ CORREÇÃO DEFINITIVAVA: Seleção UNE em Transferências
- **Seções:** 📋 O Que Foi Consertado, 🧪 Como Testar, 🔧 Mudanças Técnicas, ✨ Por Que Isso Funciona Agora, 📊 Checklist de Implantação, 📌 Próximos Passos (User), 🎯 Resolução da Solicitação Original

### `docs\archive\CORRECOES_CRITICAS_IMPLEMENTADAS.md`

- **Propósito:** Documentação: RELATÓRIO DE CORREÇÕES CRÍTICAS IMPLEMENTADAS
- **Seções:** 📋 RESUMO EXECUTIVO, 🔧 CORREÇÃO 1: Validação de Query Vazia, 🔧 CORREÇÃO 2: Maximum Conversation Turns Exceeded, 🔧 CORREÇÃO 3: Cache Semântico, 📊 RESULTADO CONSOLIDADO DOS TESTES, 🎯 IMPACTO NO SISTEMA, 🚀 DEPLOYMENT, 📝 NOTAS ADICIONAIS

### `docs\CREDENTIALS.md`

- **Propósito:** Documentação: Credenciais de Acesso - Agent Solution BI
- **Seções:** Credenciais Padrão, Como Fazer Login, Troubleshooting, Verificação do Sistema, Alterando a Senha, Suporte

### `docs\archive\DIAGNOSTICO_COMPLETO.md`

- **Propósito:** Documentação: Diagnóstico Completo - SQL Server e Sincronização Parquet
- **Seções:** 📋 Resumo Executivo, ✅ Problemas Resolvidos (Código), ⚠️ Problema Pendente (Configuração SQL Server), 🔧 Ação Necessária, 📊 Configuração do Sistema, 🚀 Próximos Passos, 📁 Arquivos Modificados/Criados, 🎯 Resultado Esperado

### `docs\archive\DIAGNOSTICO_MAX_TURNS_FIX.md`

- **Propósito:** Documentação: DIAGNÓSTICO E CORREÇÃO: Maximum Conversation Turns Exceeded
- **Seções:** CAUSA RAIZ IDENTIFICADA, CORREÇÕES IMPLEMENTADAS, VALIDAÇÃO, ARQUIVOS ADICIONAIS COM EMOJIS (NÃO CRÍTICOS), PRÓXIMOS PASSOS, IMPACTO ESPERADO, CONCLUSÃO

### `docs\FEATURE_CONTEXT7_ACCESS_CONTROL.md`

- **Propósito:** Documentação: Implementation Plan: User Segmentation & Dashboard Storytelling
- **Seções:** Objective, Phase 1: Backend Authentication Updates, Phase 2: Frontend Authentication & Access Control, Phase 3: Dashboard Storytelling ("Context7"), Execution Strategy

### `docs\GAP_ANALYSIS_100_PERCENT.md`

- **Propósito:** Documentação: Gap Analysis: Caminho para 100% de Paridade Funcional
- **Seções:** 📊 Estado Atual: 85% de Paridade, ❌ O Que Falta para 100% (15%), 🎯 Roadmap para 100%, 💡 Decisão Estratégica

### `docs\GRAPH_GENERATION_FIX.md`

- **Propósito:** Documentação: Correção de Geração de Gráficos - Context7 Best Practices 2025
- **Seções:** Problemas Identificados, Soluções Aplicadas, Arquivos Modificados, Como Testar, Logs de Sucesso, Performance, Compatibilidade, Próximos Passos (Opcional)

### `docs\GUIA_GERENCIAMENTO_USUARIOS.md`

- **Propósito:** Documentação: Guia de Gerenciamento de Usuários - Agent Solution BI
- **Seções:** 🎉 Sistema Implementado com Sucesso!, 🚀 Como Usar, 🔧 Detalhes Técnicos, 🔐 Segurança, 📋 Estrutura de Dados, 🐛 Resolução de Problemas, 🎯 Próximos Passos (Opcional), 📞 Suporte

### `docs\GUIA_INICIALIZACAO.md`

- **Propósito:** Documentação: 🚀 Guia de Inicialização - AgentBI
- **Seções:** 🎯 Melhorias Implementadas, 📋 Opções de Inicialização, 🔧 Scripts NPM Disponíveis, 🎨 Cores dos Logs, 🛠️ Tecnologia Utilizada, 📁 Estrutura de Arquivos, 🚨 Troubleshooting, 💡 Dicas de Uso

### `GUIA_LIMPEZA.md`

- **Propósito:** Documentação: Guia de Limpeza Conservadora - BI Solution
- **Seções:** 📋 Visão Geral, 🚀 Como Usar, 🔍 Preview Antes de Executar, 🛡️ Sistema de Segurança, ⏮️ Como Reverter (Undo), 📊 Relatórios Gerados, ⚠️ Perguntas Frequentes, 🔧 Troubleshooting

### `docs\troubleshooting\GUIA_RAPIDO.md`

- **Propósito:** Documentação: 🔧 GUIA RÁPIDO DE RECUPERAÇÃO
- **Seções:** ⚠️ PROBLEMA ATUAL, ✅ CAUSA & SOLUÇÃO, 🚀 3 PASSOS PARA RESOLVER, 🎯 APÓS RESOLVER, 📋 CHECKLIST, ❓ DÚVIDAS?

### `docs\GUIA_TESTES.md`

- **Propósito:** Documentação: 🧪 Guia de Testes - Agent BI
- **Seções:** 📋 Testes Disponíveis, 🐛 Solucionando Tela Branca, 🚀 Teste Rápido, 📊 Interpretando Resultados, 🔍 Debug Avançado, 📞 Ainda com problemas?

### `docs\guides\HABILITAR_TCP_IP_SQL_SERVER.md`

- **Propósito:** Documentação: Como Habilitar TCP/IP no SQL Server
- **Seções:** Problema Identificado, Solução Passo a Passo, Verificações Rápidas, Troubleshooting, Configuração Atual do Sistema, Próximos Passos Após Habilitar TCP/IP

### `docs\LOGGING_QUICK_START.md`

- **Propósito:** Documentação: 🚀 Logging - Guia Rápido
- **Seções:** Backend (FastAPI), Frontend (SolidJS), Estrutura de Logs, Visualizar Logs, Níveis de Log, ⚠️ Importante, 📚 Documentação Completa

### `docs\MANUAL_TEST_CHECKLIST.md`

- **Propósito:** Documentação: MANUAL TEST CHECKLIST - Agent Solution BI (SolidJS + FastAPI)
- **Seções:** 🎯 OBJETIVO, 📝 INSTRUÇÕES, ✅ CHECKLIST DE TESTES, 🏁 CONCLUSÃO DO TESTE MANUAL

### `docs\MIGRATION_GUIDE.md`

- **Propósito:** Documentação: Guia de Migração - Agent BI Solution
- **Seções:** 📋 Resumo das Mudanças, 🎯 Principais Melhorias, 🚀 Como Usar, 📦 Scripts npm Disponíveis, 🔧 Taskfile (Opcional - Requer Instalação), 🏥 Endpoints de Saúde, ⚙️ Variáveis de Ambiente (.env), 🐛 Troubleshooting

### `docs\PARQUET_SCHEMA_REFERENCE.md`

- **Propósito:** Documentação: Referência de Esquema do Parquet - admmat.parquet
- **Seções:** INSTRUÇÕES PARA EDIÇÃO:, COLUNAS DE IDENTIFICAÇÃO, COLUNAS DE CLASSIFICAÇÃO, COLUNAS DE ESTOQUE, COLUNAS DE PONTO DE PEDIDO E PARÂMETROS, COLUNAS DE VENDAS - MENSAL, COLUNAS DE VENDAS - SEMANAL, COLUNAS DE VENDAS - PERÍODO

### `docs\PERFORMANCE_OPTIMIZATION.md`

- **Propósito:** Documentação: Performance Optimization Guide - Agent BI
- **Seções:** 📊 Executive Summary, 🎯 Problem Identification, ✅ Solutions Implemented, 📈 Performance Metrics, 🔧 Configuration, 🎨 Architecture Patterns, 📝 Future Optimizations, 🚨 Troubleshooting

### `docs\PIC_MAPPING.md`

- **Propósito:** Documentação: Mapeamento: Próximos Passos ↔ PIC (Plano de Implementação Cirúrgica)
- **Seções:** ✅ Resposta Direta, 📊 Mapeamento Detalhado, 📝 Detalhamento das Seções Pendentes, 🎯 Resumo da Correspondência, 📋 Próximos Passos Detalhados (Seguindo o PIC), ✅ Conclusão

### `docs\PLANO_HIBRIDO_IMPLEMENTADO.md`

- **Propósito:** Documentação: 🎉 Plano Híbrido - IMPLEMENTAÇÃO COMPLETA
- **Seções:** ✅ **Status: 100% Concluído**, 📊 **O Que Foi Implementado**, 🏗️ **Arquitetura Implementada**, 📈 **Progresso de Paridade**, 🎯 **Diferenciais Competitivos**, 🚀 **Como Usar as Novas Features**, 🗄️ **Migração de Banco de Dados**, 🧪 **Como Testar**

### `docs\PRD.md`

- **Propósito:** Documentação: Product Requirements Document (PRD)
- **Seções:** 1. Visão do Produto, 2. Objetivos do Negócio, 3. Usuários-Alvo e Personas, 4. Requisitos Funcionais, 5. Requisitos Não-Funcionais, 6. Casos de Uso Principais, 7. Stack Tecnológica, 8. Roadmap de Produto

### `docs\QUICK_START.md`

- **Propósito:** Documentação: Guia Rápido de Inicialização - Agent Solution BI
- **Seções:** ✅ Status Atual do Sistema, 🚀 Como Iniciar o Frontend, 🔐 Credenciais de Login, 📋 Checklist de Inicialização, 🔧 Comandos Úteis, ⚡ Próximo Passo, 💡 Dicas, ❓ Problemas Comuns

### `README.md`

- **Propósito:** Documentação: 🛒 Agent Solution BI - Lojas Caçula (Executive Edition)
- **Seções:** 💎 Diferenciais Estratégicos (Apresentação à Diretoria), 🚀 Funcionalidades Principais, 🎨 Identidade Visual (Lojas Caçula - 40 Anos), 🛠️ Tecnologias Utilizadas, 📁 Guia de Instalação Rápida, 👥 Contas de Demonstração

### `docs\archive\README_NEW_SYSTEM.md`

- **Propósito:** Documentação: 🚀 Agent BI Solution - Quick Start
- **Seções:** Início Rápido, 📦 Comandos Principais, ⚙️ Configuração Inicial, 🏥 Health Checks, 🛠️ Troubleshooting, 📚 Documentação Completa, 🎯 Stack Tecnológica, ✅ Checklist Pré-Desenvolvimento

### `docs\RELATORIO_COMPARATIVO_CHATGPT_vs_CHATBI.md`

- **Propósito:** Documentação: Relatório Comparativo: ChatGPT vs ChatBI
- **Seções:** 📊 Sumário Executivo, 🔍 Metodologia de Análise, 📋 Análise Comparativa Detalhada, 🚀 Implementações Realizadas, 📈 Métricas de Melhoria, 🎯 Funcionalidades Exclusivas do ChatBI, ⚠️ Gaps Remanescentes (Não-Críticos), 🧪 Testes Realizados

### `docs\archive\RELATORIO_DIAGNOSTICO_COMPLETO.md`

- **Propósito:** Documentação: 🔍 Relatório de Diagnóstico Completo - Agent BI Solution
- **Seções:** 📋 Resumo Executivo, 🔎 Páginas Analisadas, 🛠️ Problemas Identificados, ✅ Correções Aplicadas, 🚀 Solução Imediata, 📊 Resultados Esperados Após Restart, 📝 Recomendações de Longo Prazo, 🎯 Checklist de Verificação Pós-Restart

### `docs\RELATORIO_FINAL_IMPLEMENTACAO.md`

- **Propósito:** Documentação: 📊 SUMÁRIO EXECUTIVO: Agent BI Solution - Lojas Caçula
- **Seções:** 🚀 1. Visão Geral, 💡 2. Diferenciais Competitivos (O Valor da IA), ⚡ 3. Engenharia de Alta Performance, 🔐 4. Governança e Segurança, 📈 5. Métricas de Impacto Estimadas, 🎯 6. Conclusão e Próximos Passos

### `docs\RELATORIO_PERFORMANCE_CHAT_CONTEXT7.md`

- **Propósito:** Documentação: Relatório Context7: Análise de Performance do Chat
- **Seções:** 1. Sumário Executivo, 2. Diagnóstico Técnico, 3. Recomendações (Plano de Ação), 4. Conclusão

### `docs\RELATORIO_VERIFICACAO.md`

- **Propósito:** Documentação: 📊 Relatório de Verificação - Agent BI
- **Seções:** ✅ Testes Realizados, 🔍 Diagnóstico da Tela Branca, 🛠️ Ferramentas de Diagnóstico Criadas, 📋 Checklist para Resolver Tela Branca, 🎯 Conclusão, 📞 Suporte Adicional

### `Relatório de Infraestrutura, Custos e Viabilidade_ Projeto BI_Solution.md`

- **Propósito:** Documentação: Relatório de Infraestrutura, Custos e Viabilidade: Projeto BI_Solution
- **Seções:** 1. Viabilidade de Servidor Local, 2. Análise da LLM (Gemini 3 Flash Preview), 3. Comparativo: Local vs. Nuvem (Cloud), 4. Conclusão e Recomendações

### `docs\SISTEMA_LOGGING.md`

- **Propósito:** Documentação: Sistema de Logging - AgentBI
- **Seções:** 📋 Índice, Visão Geral, Backend - Configuração, Backend - Uso, Frontend - Configuração, Frontend - Uso, Estrutura de Logs, Visualização e Análise

### `docs\SOLUCAO_FILTROS_ANALYTICS.md`

- **Propósito:** Documentação: Solução: Filtros da Página Analytics
- **Seções:** 🎯 Problema Identificado, ✅ Solução Implementada, 📚 Melhores Práticas Aplicadas, 🧪 Como Testar, 🎨 Melhorias de UX Implementadas, 🔄 Fluxo Completo, 📦 Arquivos Modificados, 🚀 Próximos Passos (Opcionais)

### `docs\archive\SOLUCAO_FINAL.md`

- **Propósito:** Documentação: ✅ SOLUÇÃO FINAL - Dados Visíveis em Todas as Páginas
- **Seções:** PROBLEMA RESOLVIDO, ⚡ O QUE FOI CORRIGIDO, 📊 RESULTADOS (TESTADOS), 🚀 BACKEND RODANDO, 📝 ARQUIVOS MODIFICADOS, ⚠️ IMPORTANTE

### `docs\troubleshooting\SOLUCAO_NODE_JS.md`

- **Propósito:** Documentação: 🚀 SOLUCIONANDO ERRO DE NODE.JS
- **Seções:** ❌ Erro Encontrado, 🤔 O Que Significa?, 💡 ESCOLHA UMA OPÇÃO, 🎯 RECOMENDAÇÃO, 🔧 Verificação Rápida (Sem Instalar Nada), ❓ Dúvidas?, 📋 Resumo das Ações, 🚀 Próximos Passos

### `docs\guides\SQL_SERVER_SETUP.md`

- **Propósito:** Documentação: Configuração do SQL Server - Agent Solution BI
- **Seções:** Problema Identificado, Solução, Modo Híbrido (Recomendado), Troubleshooting, Alternativas

### `docs\archive\SQL_SERVER_STATUS_REPORT.md`

- **Propósito:** Documentação: SQL Server Diagnostics - Status Report
- **Seções:** Summary of Work Completed, Current System Status, Recommended Next Steps, Testing Performed, Files Modified, Conclusion

### `docs\archive\SYSTEM_STATUS.md`

- **Propósito:** Documentação: Relatório de Status do Sistema - Agent BI Solution
- **Seções:** ✅ Resumo Executivo para a Diretoria, ✅ Status dos Componentes Core, ✅ Funcionalidades Certificadas, ✅ Dados e Governança, ✅ Credenciais de Demonstração (Seguras), 📄 CERTIFICAÇÃO FINAL

### `docs\regras_negocio_une.md`

- **Propósito:** Documentação: Regras de Negócio UNE (Unidade de Negócio)
- **Seções:** 1. Glossário, 2. Cálculos e Métricas, 3. Classificação de Criticidade, 4. Regras de Transferência entre UNEs, 5. Implementação Técnica

### `docs\sql-queries-top-vendas.md`

- **Propósito:** Documentação: Consultas SQL - Top 10 Vendas por Categoria
- **Seções:** 📊 Consulta 1: Top 10 Categorias por Valor Total, 📊 Consulta 2: Top 10 Produtos por Categoria, 📊 Consulta 3: Top 10 Produtos Globais, 📊 Consulta 4: Top 10 com Percentual do Total, 📊 Consulta 5: Top 10 por Período, 🔧 Adaptação para Parquet (Polars), 💡 Dicas de Performance, 📝 Notas

---

## Scripts e Utilitários

### `scripts\utils\HARD_RESET_LOGIN.bat`

- **Propósito:** Não identificado

### `scripts\utils\RESET_LOGIN.ps1`

- **Propósito:** Não identificado

### `scripts\utils\add_nodejs_to_path.ps1`

- **Propósito:** Não identificado

### `scripts\clean-port.js`

- **Propósito:** * Cross-platform script to kill processes on specific ports
 * Works on Windows, Linux, and macOS
 * Ports: 8000 (Backend), 3000 (Frontend)

### `scripts\create_supabase_test_user.py`

- **Propósito:** Testes unitários (0 testes)

### `scripts\create_supabase_users.sql`

- **Propósito:** Não identificado

### `scripts\create_test_user.py`

- **Propósito:** Testes unitários (1 testes)

### `scripts\create_user_profiles.sql`

- **Propósito:** Não identificado

### `scripts\create_users_parquet.py`

- **Propósito:** Create users.parquet file with test admin user for authentication fallback

### `scripts\debug_transfers.js`

- **Propósito:** * DIAGNÓSTICO DE CLIQUES - Cole no Console do Navegador
 * 
 * Abre DevTools (F12), vai em Console, e cola este script.
 * Ele vai monitorar EXATAMENTE o que está acontecendo nos cliques.

### `scripts\legacy_tests\diagnostico_sql_server.bat`

- **Propósito:** Não identificado

### `scripts\index_codebase.py`

- **Propósito:** Code Indexer - Generate RAG Index for Entire Codebase

### `scripts\insert_user_profiles.sql`

- **Propósito:** Não identificado

### `scripts\kill_port.py`

- **Propósito:** Não identificado

### `scripts\kill_ports.py`

- **Propósito:** Script para liberar portas 8000 e 3000

### `scripts\utils\kill_python.bat`

- **Propósito:** Não identificado

### `scripts\legacy_tests\reproduce_gemini_error.py`

- **Propósito:** Não identificado

### `scripts\utils\run-with-logs.bat`

- **Propósito:** Não identificado

### `scripts\utils\run.ps1`

- **Propósito:** Não identificado

### `scripts\utils\run_backend_only.ps1`

- **Propósito:** Não identificado

### `scripts\show-logs.js`

- **Propósito:** * Script para visualizar logs agregados em tempo real
 * Monitora múltiplos arquivos de log e exibe com cores

### `scripts\signup_test_user.py`

- **Propósito:** Testes unitários (1 testes)

### `scripts\utils\start_system.ps1`

- **Propósito:** Não identificado

### `scripts\legacy_tests\test_chat_robust.py`

- **Propósito:** Testes unitários (3 testes)

### `scripts\legacy_tests\test_code_chat.py`

- **Propósito:** Testes unitários (0 testes)

### `scripts\legacy_tests\test_critical_fixes.py`

- **Propósito:** Testes unitários (4 testes)

### `scripts\legacy_tests\test_diagnostics.py`

- **Propósito:** Testes unitários (0 testes)

### `scripts\legacy_tests\test_kpis.py`

- **Propósito:** Testes unitários (0 testes)

### `scripts\test_llm_v3.py`

- **Propósito:** Testes unitários (1 testes)

### `scripts\legacy_tests\test_sql_connection.py`

- **Propósito:** Testes unitários (1 testes)

### `scripts\utils\validate_changes.ps1`

- **Propósito:** Não identificado

---

## Testes

### `data\input\118d1957b67043aeb872acd9ed5f8714_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\29c3896b8bd445269e784dc4221cbaae_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\621843dbdc0c43dd967d4ffb225839f4_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\696b783d90e14857982c7988ba674038_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\8362ccd7951c4f06aa1d3528e2810b23_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\aaa0fde96a1443848a390e05804c6ff6_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\b60c04e3270d44d5b405fad69d57e920_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\c1ef0fb29a8c40ed91cfe29518eabfe1_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\c89d14f7b08747da973468ef2dda5ea9_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\d94b48625a8c4b93add4f933624cdcb7_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\f374bfb5f23549b79f3de5d38ae774ff_temp_test.csv`

- **Propósito:** Não identificado

### `data\input\fbce5c3727a848c2a96459b8948763ea_temp_test.csv`

- **Propósito:** Não identificado

### `tests\playwright.config.ts`

- **Propósito:** * Playwright configuration for TestSprite-generated E2E tests
 * See https://playwright.dev/docs/test-configuration

### `tests\test_agent_comprehensive.py`

- **Propósito:** Agente BI: Testes unitários (0 testes)

### `test_agent_http.py`

- **Propósito:** Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (3 testes)

### `test_agent_intelligence.py`

- **Propósito:** Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

### `tests\test_agent_quick.py`

- **Propósito:** Agente BI: Testes unitários (0 testes)

### `tests\test_chat_interactions.py`

- **Propósito:** Testes unitários (3 testes)

### `tests\test_duckdb_performance.py`

- **Propósito:** Testes unitários (0 testes)

### `tests\test_extreme_performance.py`

- **Propósito:** Testes unitários (0 testes)

### `test_final_fix.py`

- **Propósito:** [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

### `tests\test_graph_vs_text.py`

- **Propósito:** Testes unitários (0 testes)

### `test_oxford_direct.py`

- **Propósito:** [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

### `tests\test_performance_v2.py`

- **Propósito:** Testes unitários (0 testes)

### `tests\test_products_selection.ts`

- **Propósito:** * Teste de seleção de Produtos para Transferências (Multi-Seleção)

### `test_query_oxford.py`

- **Propósito:** [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

### `test_query_oxford_simple.py`

- **Propósito:** [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

### `docs\archive\test_results.txt`

- **Propósito:** Não identificado

### `tests\test_rls_data_manager.py`

- **Propósito:** Testes unitários (0 testes)

### `tests\test_textual_analysis.py`

- **Propósito:** Testes unitários (0 testes)

### `tests\test_transfers_selection.ts`

- **Propósito:** * Teste de seleção UNE para Transferências
 * Valida comportamento de 1→1, 1→N, N→N

### `tests\verify_run_bat.ps1`

- **Propósito:** Não identificado

---

## Dados

### `data\input\ADMAT.csv`

- **Propósito:** Não identificado
- **Tamanho:** 131.61 KB

### `data\input\SEMVENDAS.csv`

- **Propósito:** Não identificado
- **Tamanho:** 48.62 KB

### `data\parquet\admmat.parquet`

- **Propósito:** Dataset Parquet (análise rápida com Polars)
- **Tamanho:** 60.21 MB

### `analise_projeto.json`

- **Propósito:** Não identificado
- **Tamanho:** 1.41 MB

### `analise_projeto_detalhada.json`

- **Propósito:** Não identificado
- **Tamanho:** 1.23 MB

### `data\catalog_focused.json`

- **Propósito:** Não identificado
- **Tamanho:** 10.03 KB

### `storage\default__vector_store.json`

- **Propósito:** Não identificado
- **Tamanho:** 4.96 MB

### `storage\docstore.json`

- **Propósito:** Não identificado
- **Tamanho:** 2.17 MB

### `data\learning\error_counts_20251108.json`

- **Propósito:** Não identificado
- **Tamanho:** 34.00 B

### `data\learning\error_counts_20251109.json`

- **Propósito:** Não identificado
- **Tamanho:** 23.00 B

### `data\learning\error_log_20251108.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 4.72 KB

### `data\learning\error_log_20251109.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 24.96 KB

### `data\learning\error_log_20251207.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 6.12 KB

### `storage\graph_store.json`

- **Propósito:** Não identificado
- **Tamanho:** 18.00 B

### `data\query_history\history_20251108.json`

- **Propósito:** Não identificado
- **Tamanho:** 10.01 KB

### `data\query_history\history_20251109.json`

- **Propósito:** Não identificado
- **Tamanho:** 4.52 KB

### `data\query_history\history_20251111.json`

- **Propósito:** Não identificado
- **Tamanho:** 2.76 KB

### `data\query_history\history_20251116.json`

- **Propósito:** Não identificado
- **Tamanho:** 763.00 B

### `data\query_history\history_20251119.json`

- **Propósito:** Não identificado
- **Tamanho:** 5.89 KB

### `data\query_history\history_20251120.json`

- **Propósito:** Não identificado
- **Tamanho:** 8.22 KB

### `data\query_history\history_20251121.json`

- **Propósito:** Não identificado
- **Tamanho:** 1.59 KB

### `data\query_history\history_20251122.json`

- **Propósito:** Não identificado
- **Tamanho:** 3.40 KB

### `storage\image__vector_store.json`

- **Propósito:** Não identificado
- **Tamanho:** 72.00 B

### `storage\index_stats.json`

- **Propósito:** Não identificado
- **Tamanho:** 241.00 B

### `storage\index_store.json`

- **Propósito:** Não identificado
- **Tamanho:** 39.86 KB

### `package-lock.json`

- **Propósito:** Não identificado
- **Tamanho:** 12.38 KB

### `data\query_examples.json`

- **Propósito:** Não identificado
- **Tamanho:** 586.84 KB

### `data\query_patterns.json`

- **Propósito:** Não identificado
- **Tamanho:** 2.33 KB

### `.claude\settings.local.json`

- **Propósito:** Não identificado
- **Tamanho:** 857.00 B

### `data\learning\successful_queries_20251108.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 33.52 KB

### `data\learning\successful_queries_20251109.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 86.84 KB

### `data\learning\successful_queries_20251111.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 8.90 KB

### `data\learning\successful_queries_20251116.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 5.05 KB

### `data\learning\successful_queries_20251120.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 23.40 KB

### `data\learning\successful_queries_20251122.jsonl`

- **Propósito:** Não identificado
- **Tamanho:** 5.81 KB

### `data\transferencias\transferencia_20251108_102233.json`

- **Propósito:** Não identificado
- **Tamanho:** 2.14 KB

### `data\transferencias\transferencia_20251108_163027.json`

- **Propósito:** Não identificado
- **Tamanho:** 4.41 KB

### `data\transferencias\transferencia_20251109_153242.json`

- **Propósito:** Não identificado
- **Tamanho:** 1.70 KB

### `data\parquet\users.parquet`

- **Propósito:** Dataset Parquet (análise rápida com Polars)
- **Tamanho:** 4.84 KB

---

## Arquivos para Limpeza

**TOTAL IDENTIFICADO: 42 arquivos (5.26 MB)**

### Arquivos Temporários (.log, cache)

- `backend\logs\api\api.log` (2.93 MB)
- `backend\logs\app\app.log` (649.37 KB)
- `backend\logs\errors\errors.log` (484.39 KB)
- `backend\logs\errors\critical.log` (399.91 KB)
- `logs\backend.log` (363.90 KB)
- `backend\logs\audit\audit.log` (148.16 KB)
- `backend\logs\security\security.log` (111.91 KB)
- `logs\app\app.log` (8.11 KB)
- `logs\errors\critical.log` (1.42 KB)
- `logs\api\api.log` (941.00 B)
- `backend\test_login_debug.log` (570.00 B)
- `backend\logs\chat\chat.log` (0.00 B)
- `logs\audit\audit.log` (0.00 B)
- `logs\chat\chat.log` (0.00 B)
- `logs\errors\errors.log` (0.00 B)
- `logs\security\security.log` (0.00 B)

**Subtotal:** 16 arquivos, 5.05 MB

### Documentação Obsoleta/Temporária (na raiz e docs/)

- `AGENT_FIX_REPORT_2025-12-28.md` - [OBSOLETO] Documentação: Relatorio de Correcao do Agente BI - 2025-12-28
- `ASYNC_RAG_IMPLEMENTATION.md` - [OBSOLETO] Documentação: Async RAG Implementation - Modern Python 3.11+
- `FIX_MAX_TURNS_2025-12-28.md` - [OBSOLETO] Documentação: Correção Definitiva: "Maximum conversation turns exceeded"
- `IMPLEMENTATION_SUMMARY.md` - [OBSOLETO] Documentação: Implementação Completa - Modernização de Tools LLM
- `IMPROVEMENTS_SUMMARY_2025-12-28.md` - [OBSOLETO] Documentação: Resumo de Melhorias Implementadas - 2025-12-28
- `MODERNIZATION_SUMMARY.md` - [OBSOLETO] Documentação: Modernização Agent BI - Sumário Executivo
- `PERFORMANCE_FIX_2025-12-27.md` - [OBSOLETO] Documentação: Performance Fix - 4+ Minute Hang Issue
- `QUICK_START_MODERNIZATION.md` - [OBSOLETO] Documentação: Quick Start - Melhorias de Modernização 2025
- `backend\CONTINUOUS_LEARNING_GUIDE.md` - Documentação: Guia de Continuous Learning - Agent BI (2025)
- `backend\PRODUCT_ANALYSIS_FIX.md` - Documentação: Correção: Análise de Produto Individual
- `docs\CODE_CHAT_GUIDE.md` - Documentação: Code Chat - Agente Fullstack Completo
- `docs\GRAPH_GENERATION_FIX.md` - Documentação: Correção de Geração de Gráficos - Context7 Best Practices 2025
- `docs\MIGRATION_GUIDE.md` - Documentação: Guia de Migração - Agent BI Solution
- `docs\archive\DIAGNOSTICO_MAX_TURNS_FIX.md` - Documentação: DIAGNÓSTICO E CORREÇÃO: Maximum Conversation Turns Exceeded
- `frontend-solid\TESTING_GUIDE.md` - Documentação: Guia de Testes - Componentes Migrados SolidJS
- `frontend-solid\src\migrated-components\USAGE_GUIDE.md` - Documentação: Guia de Uso - Componentes UI Migrados para SolidJS

**Subtotal:** 16 arquivos, 121.74 KB

### Scripts de Teste na Raiz (devem estar em tests/)

- `test_agent_http.py` - Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (3 testes)
- `test_agent_intelligence.py` - Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- `test_final_fix.py` - [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- `test_oxford_direct.py` - [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- `test_query_oxford.py` - [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- `test_query_oxford_simple.py` - [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)

**Subtotal:** 6 arquivos, 21.14 KB

### Scripts Temporários de Análise (gerados para limpeza/análise)

- `analyze_project.py` - [SCRIPT TEMPORÁRIO] Não identificado
- `analyze_project_detailed.py` - [SCRIPT TEMPORÁRIO] Não identificado
- `cleanup_conservative.py` - [SCRIPT TEMPORÁRIO] Não identificado
- `restore_backup.py` - [SCRIPT TEMPORÁRIO] Não identificado

**Subtotal:** 4 arquivos, 73.56 KB

---

## Todos os Arquivos (Detalhado)

### Categoria: config

**`.gitignore`**
- Propósito: Arquivos ignorados pelo Git
- Tamanho: 1.39 KB

**`analyze.bat`**
- Propósito: Script de análise do projeto
- Tamanho: 1.05 KB

**`backend\.env`**
- Propósito: Variáveis de ambiente
- Tamanho: 2.78 KB

**`backend\.gitignore`**
- Propósito: Arquivos ignorados pelo Git
- Tamanho: 555.00 B

**`backend\main.py`**
- Propósito: Ponto de entrada da aplicação FastAPI
- Tamanho: 5.57 KB

**`backend\pyproject.toml`**
- Propósito: Configuração do projeto Python
- Tamanho: 2.04 KB

**`backend\requirements.txt`**
- Propósito: Dependências Python
- Tamanho: 11.25 KB

**`frontend-solid\package.json`**
- Propósito: Configuração de dependências Node.js
- Tamanho: 1.45 KB

**`frontend-solid\tsconfig.json`**
- Propósito: Configuração do compilador TypeScript
- Tamanho: 422.00 B

**`frontend-solid\vite.config.ts`**
- Propósito: Configuração do bundler Vite
- Tamanho: 1.02 KB

**`package.json`**
- Propósito: Configuração de dependências Node.js
- Tamanho: 1.32 KB

**`start.bat`**
- Propósito: Script de inicialização Windows
- Tamanho: 3.77 KB

### Categoria: data

**`.claude\settings.local.json`**
- Propósito: Não identificado
- Tamanho: 857.00 B

**`analise_projeto.json`**
- Propósito: Não identificado
- Tamanho: 1.41 MB

**`analise_projeto_detalhada.json`**
- Propósito: Não identificado
- Tamanho: 1.23 MB

**`backend\app\data\parquet\admmat.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 60.21 MB

**`backend\app\data\sessions\04abba9a-06bc-4fbd-b12d-463a267d1c22.json`**
- Propósito: Não identificado
- Tamanho: 8.12 KB

**`backend\app\data\sessions\25637002-59ea-4fb9-a38e-d4d7abc2dff0.json`**
- Propósito: Não identificado
- Tamanho: 3.61 KB

**`backend\app\data\sessions\2c1e4ece-046e-4323-9635-671e95379242.json`**
- Propósito: Não identificado
- Tamanho: 2.74 KB

**`backend\app\data\sessions\355bc17d-fba5-4d95-9729-ad3390b370ed.json`**
- Propósito: Não identificado
- Tamanho: 448.00 B

**`backend\app\data\sessions\3f26e098-f20b-4a08-929e-58d31fc39b68.json`**
- Propósito: Não identificado
- Tamanho: 70.95 KB

**`backend\app\data\sessions\46d1c1c0-d075-44f5-9164-0f9bd612ae62.json`**
- Propósito: Não identificado
- Tamanho: 2.45 KB

**`backend\app\data\sessions\5177828c-eebb-465c-9272-580df78842b1.json`**
- Propósito: Não identificado
- Tamanho: 13.69 KB

**`backend\app\data\sessions\537b72b4-ff3e-47b9-a3d9-3c3d6c7b878b.json`**
- Propósito: Não identificado
- Tamanho: 1.02 KB

**`backend\app\data\sessions\569e94f3-0699-4f7f-9653-538e567b5af2.json`**
- Propósito: Não identificado
- Tamanho: 317.00 B

**`backend\app\data\sessions\71fda5a5-46a9-4dd2-97e9-57eaa46956a7.json`**
- Propósito: Não identificado
- Tamanho: 3.57 KB

**`backend\app\data\sessions\7d4cd5bf-9cc7-41be-b400-44bf76f0c5cf.json`**
- Propósito: Não identificado
- Tamanho: 2.38 KB

**`backend\app\data\sessions\7ee2d4ea-ce23-4495-85f2-1dcc09f05b55.json`**
- Propósito: Não identificado
- Tamanho: 463.00 B

**`backend\app\data\sessions\82bee385-699c-4f04-a1e3-499031a954d4.json`**
- Propósito: Não identificado
- Tamanho: 604.00 B

**`backend\app\data\sessions\85411dd2-0692-4186-acf2-8b489e863367.json`**
- Propósito: Não identificado
- Tamanho: 4.31 KB

**`backend\app\data\sessions\a9e60fe1-59cd-436d-b6fa-a66d143975ba.json`**
- Propósito: Não identificado
- Tamanho: 1.70 KB

**`backend\app\data\sessions\b2b0e38a-3cfc-4261-b125-7f98677a6218.json`**
- Propósito: Não identificado
- Tamanho: 718.00 B

**`backend\app\data\sessions\c322cc58-a7b7-41b5-be95-089d3c90609e.json`**
- Propósito: Não identificado
- Tamanho: 10.16 KB

**`backend\app\data\sessions\cache-test-1766325258.json`**
- Propósito: Cache de dados
- Tamanho: 899.00 B

**`backend\app\data\sessions\cache-test-1766325969.json`**
- Propósito: Cache de dados
- Tamanho: 746.00 B

**`backend\app\data\sessions\d94af482-5693-46ff-8fe5-8e67b75e3437.json`**
- Propósito: Não identificado
- Tamanho: 319.00 B

**`backend\app\data\sessions\d9a6bc3d-82cf-4ba5-9d93-1ba93f54ecee.json`**
- Propósito: Não identificado
- Tamanho: 1.37 KB

**`backend\app\data\sessions\test-cache-1.json`**
- Propósito: Cache de dados
- Tamanho: 805.00 B

**`backend\app\data\sessions\test-cache-2.json`**
- Propósito: Cache de dados
- Tamanho: 218.00 B

**`backend\app\data\sessions\test-complex.json`**
- Propósito: Não identificado
- Tamanho: 326.00 B

**`backend\app\data\sessions\test-session-001.json`**
- Propósito: Dados de sessão de chat
- Tamanho: 1.92 KB

**`backend\app\data\sessions\test-session-002.json`**
- Propósito: Dados de sessão de chat
- Tamanho: 138.00 B

**`backend\app\data\sessions\test-session-1766324899.json`**
- Propósito: Dados de sessão de chat
- Tamanho: 1.49 KB

**`backend\app\data\sessions\test-session-1766324987.json`**
- Propósito: Dados de sessão de chat
- Tamanho: 4.84 KB

**`backend\app\data\sessions\test-session-1766325867.json`**
- Propósito: Dados de sessão de chat
- Tamanho: 3.75 KB

**`backend\data\cache\semantic\1af96ff6522dab74ed93ee0bc381f2bc.json`**
- Propósito: Cache de dados
- Tamanho: 1.70 KB

**`backend\data\cache\semantic\22153012b73bcb1f40c70dd5fcd466bd.json`**
- Propósito: Cache de dados
- Tamanho: 39.00 B

**`backend\data\cache\semantic\24758a433ecd09604de2b51b7f880c40.json`**
- Propósito: Cache de dados
- Tamanho: 224.00 B

**`backend\data\cache\semantic\25767916627907e8f7d274ae0afc0fc8.json`**
- Propósito: Cache de dados
- Tamanho: 9.28 KB

**`backend\data\cache\semantic\2e3c9a63fffb52f97299883eeddcaa1e.json`**
- Propósito: Cache de dados
- Tamanho: 144.00 B

**`backend\data\cache\semantic\3070057a28f8ee68d1fdf381a97341aa.json`**
- Propósito: Cache de dados
- Tamanho: 331.00 B

**`backend\data\cache\semantic\30b85e0c920ef58a145e421522e1d320.json`**
- Propósito: Cache de dados
- Tamanho: 1.28 KB

**`backend\data\cache\semantic\34e9d20e2057865814feb72f09871385.json`**
- Propósito: Cache de dados
- Tamanho: 1.87 KB

**`backend\data\cache\semantic\38a9f8390c4525a049f90e66b77853af.json`**
- Propósito: Cache de dados
- Tamanho: 507.00 B

**`backend\data\cache\semantic\40df51f64b3e2d39580faf89c7d54be0.json`**
- Propósito: Cache de dados
- Tamanho: 1.74 KB

**`backend\data\cache\semantic\42855106065dc471b5a91887187f1bac.json`**
- Propósito: Cache de dados
- Tamanho: 1.76 KB

**`backend\data\cache\semantic\43fa78def25e84fac067b8fb288e9e2e.json`**
- Propósito: Cache de dados
- Tamanho: 39.00 B

**`backend\data\cache\semantic\49b65803b8bd245937e20d6e97be37f2.json`**
- Propósito: Cache de dados
- Tamanho: 557.00 B

**`backend\data\cache\semantic\4ae3b266361e3b75ba3db6bbdb23502d.json`**
- Propósito: Cache de dados
- Tamanho: 460.00 B

**`backend\data\cache\semantic\50f970ddb739f3bccf489574d5e9f52c.json`**
- Propósito: Cache de dados
- Tamanho: 441.00 B

**`backend\data\cache\semantic\5348653381fa50634b2ee8dd001954bc.json`**
- Propósito: Cache de dados
- Tamanho: 434.00 B

**`backend\data\cache\semantic\5a74b6b99cd2592d468c14cc2bc97985.json`**
- Propósito: Cache de dados
- Tamanho: 298.00 B

**`backend\data\cache\semantic\66d11dacffcc933c743c2ae1f15f5a6c.json`**
- Propósito: Cache de dados
- Tamanho: 2.14 KB

**`backend\data\cache\semantic\6c8b56b3fed46216805ed78f30cf704d.json`**
- Propósito: Cache de dados
- Tamanho: 174.00 B

**`backend\data\cache\semantic\6dcba9a072715735fde48bac4d242334.json`**
- Propósito: Cache de dados
- Tamanho: 2.30 KB

**`backend\data\cache\semantic\6fdf9cc4149f5eb2d96671b101fcc68e.json`**
- Propósito: Cache de dados
- Tamanho: 135.00 B

**`backend\data\cache\semantic\7c7a36596e4c53fe03a7a105c0c4b7f6.json`**
- Propósito: Cache de dados
- Tamanho: 205.00 B

**`backend\data\cache\semantic\7df39b2e37a393c80f5747b55483e204.json`**
- Propósito: Cache de dados
- Tamanho: 471.00 B

**`backend\data\cache\semantic\810199084a94a86aa58b3a4b781154f2.json`**
- Propósito: Cache de dados
- Tamanho: 441.00 B

**`backend\data\cache\semantic\8a03571643a8c08a45b0cca61485d720.json`**
- Propósito: Cache de dados
- Tamanho: 5.47 KB

**`backend\data\cache\semantic\8bab08c1b014ec512c97e71311829c37.json`**
- Propósito: Cache de dados
- Tamanho: 1.85 KB

**`backend\data\cache\semantic\8e5c349b3e270b3704520127be33fa65.json`**
- Propósito: Cache de dados
- Tamanho: 1.23 KB

**`backend\data\cache\semantic\95ec80d9464c5051aec255043444bb57.json`**
- Propósito: Cache de dados
- Tamanho: 520.00 B

**`backend\data\cache\semantic\96828792686798e29666234032ded85d.json`**
- Propósito: Cache de dados
- Tamanho: 1.88 KB

**`backend\data\cache\semantic\987e4691d1096173ce5fa33386242e60.json`**
- Propósito: Cache de dados
- Tamanho: 39.00 B

**`backend\data\cache\semantic\9e49cb43bdc537a363dcaea074917292.json`**
- Propósito: Cache de dados
- Tamanho: 5.47 KB

**`backend\data\cache\semantic\a8373de016f153ce0c67f037e080b642.json`**
- Propósito: Cache de dados
- Tamanho: 943.00 B

**`backend\data\cache\semantic\ab20561f0e7cf8533c3a5962bdd8010f.json`**
- Propósito: Cache de dados
- Tamanho: 39.00 B

**`backend\data\cache\semantic\b7bb7c15be6d0d34f747db4ca1a18381.json`**
- Propósito: Cache de dados
- Tamanho: 2.23 KB

**`backend\data\cache\semantic\ba6dd1e8424534cc960b62ce9cb6ad95.json`**
- Propósito: Cache de dados
- Tamanho: 360.00 B

**`backend\data\cache\semantic\c0d8285d1c57552e23e3bfddf40716a0.json`**
- Propósito: Cache de dados
- Tamanho: 280.00 B

**`backend\data\cache\semantic\cc57f8346af46448819d7e2fa325154e.json`**
- Propósito: Cache de dados
- Tamanho: 1.35 KB

**`backend\data\cache\semantic\d3fad6791c9660e38a2f45cd008d4a34.json`**
- Propósito: Cache de dados
- Tamanho: 2.09 KB

**`backend\data\cache\semantic\d9b7294e98179dc8e496ac32f933006a.json`**
- Propósito: Cache de dados
- Tamanho: 9.75 KB

**`backend\data\cache\semantic\dfb55e042df58956f554a0e8f36d467a.json`**
- Propósito: Cache de dados
- Tamanho: 572.00 B

**`backend\data\cache\semantic\e1d62205f6ca070d6a8cf5af653bccc2.json`**
- Propósito: Cache de dados
- Tamanho: 591.00 B

**`backend\data\cache\semantic\e499cc4d23451f05c823b77cc22f91bf.json`**
- Propósito: Cache de dados
- Tamanho: 477.00 B

**`backend\data\cache\semantic\eff06dfeca50cc20a09ec8dcc2a3061c.json`**
- Propósito: Cache de dados
- Tamanho: 1.81 KB

**`backend\data\cache\semantic\ffe54fd058c60c46606515b6ff81d2f3.json`**
- Propósito: Cache de dados
- Tamanho: 1.57 KB

**`backend\data\cache\semantic\index.json`**
- Propósito: Cache de dados
- Tamanho: 13.68 KB

**`backend\data\cache\test_semantic\index.json`**
- Propósito: Cache de dados
- Tamanho: 2.00 B

**`backend\data\learning\golden_dataset\positive\golden_20251227_152604_013930.json`**
- Propósito: Não identificado
- Tamanho: 297.00 B

**`backend\data\learning\golden_dataset\review\review_20251227_152604_013930.json`**
- Propósito: Não identificado
- Tamanho: 327.00 B

**`backend\data\learning\golden_dataset\review\review_20251227_152604_018362.json`**
- Propósito: Não identificado
- Tamanho: 316.00 B

**`backend\data\parquet\admmat.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 60.21 MB

**`backend\data\parquet\users.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 4.91 KB

**`backend\data\transferencias\batch_20251208221533042604.json`**
- Propósito: Não identificado
- Tamanho: 1.34 KB

**`backend\data\transferencias\batch_20251214134747282728.json`**
- Propósito: Não identificado
- Tamanho: 796.00 B

**`backend\data\transferencias\transfer_20251207223105055653.json`**
- Propósito: Não identificado
- Tamanho: 180.00 B

**`backend\data\transferencias\transfer_past.json`**
- Propósito: Não identificado
- Tamanho: 146.00 B

**`backend\scripts\backend\data\parquet\admmat.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 12.63 KB

**`backend\scripts\data\parquet\admmat.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 12.63 KB

**`data\catalog_focused.json`**
- Propósito: Não identificado
- Tamanho: 10.03 KB

**`data\input\118d1957b67043aeb872acd9ed5f8714_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\29c3896b8bd445269e784dc4221cbaae_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\621843dbdc0c43dd967d4ffb225839f4_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\696b783d90e14857982c7988ba674038_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\8362ccd7951c4f06aa1d3528e2810b23_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\ADMAT.csv`**
- Propósito: Não identificado
- Tamanho: 131.61 KB

**`data\input\SEMVENDAS.csv`**
- Propósito: Não identificado
- Tamanho: 48.62 KB

**`data\input\aaa0fde96a1443848a390e05804c6ff6_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\b60c04e3270d44d5b405fad69d57e920_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\c1ef0fb29a8c40ed91cfe29518eabfe1_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\c89d14f7b08747da973468ef2dda5ea9_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\d94b48625a8c4b93add4f933624cdcb7_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\f374bfb5f23549b79f3de5d38ae774ff_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\input\fbce5c3727a848c2a96459b8948763ea_temp_test.csv`**
- Propósito: Não identificado
- Tamanho: 19.00 B

**`data\learning\error_counts_20251108.json`**
- Propósito: Não identificado
- Tamanho: 34.00 B

**`data\learning\error_counts_20251109.json`**
- Propósito: Não identificado
- Tamanho: 23.00 B

**`data\parquet\admmat.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 60.21 MB

**`data\parquet\users.parquet`**
- Propósito: Dataset Parquet (análise rápida com Polars)
- Tamanho: 4.84 KB

**`data\query_examples.json`**
- Propósito: Não identificado
- Tamanho: 586.84 KB

**`data\query_history\history_20251108.json`**
- Propósito: Não identificado
- Tamanho: 10.01 KB

**`data\query_history\history_20251109.json`**
- Propósito: Não identificado
- Tamanho: 4.52 KB

**`data\query_history\history_20251111.json`**
- Propósito: Não identificado
- Tamanho: 2.76 KB

**`data\query_history\history_20251116.json`**
- Propósito: Não identificado
- Tamanho: 763.00 B

**`data\query_history\history_20251119.json`**
- Propósito: Não identificado
- Tamanho: 5.89 KB

**`data\query_history\history_20251120.json`**
- Propósito: Não identificado
- Tamanho: 8.22 KB

**`data\query_history\history_20251121.json`**
- Propósito: Não identificado
- Tamanho: 1.59 KB

**`data\query_history\history_20251122.json`**
- Propósito: Não identificado
- Tamanho: 3.40 KB

**`data\query_patterns.json`**
- Propósito: Não identificado
- Tamanho: 2.33 KB

**`data\transferencias\transferencia_20251108_102233.json`**
- Propósito: Não identificado
- Tamanho: 2.14 KB

**`data\transferencias\transferencia_20251108_163027.json`**
- Propósito: Não identificado
- Tamanho: 4.41 KB

**`data\transferencias\transferencia_20251109_153242.json`**
- Propósito: Não identificado
- Tamanho: 1.70 KB

**`frontend-solid\package-lock.json`**
- Propósito: Não identificado
- Tamanho: 71.33 KB

**`package-lock.json`**
- Propósito: Não identificado
- Tamanho: 12.38 KB

**`storage\default__vector_store.json`**
- Propósito: Não identificado
- Tamanho: 4.96 MB

**`storage\docstore.json`**
- Propósito: Não identificado
- Tamanho: 2.17 MB

**`storage\graph_store.json`**
- Propósito: Não identificado
- Tamanho: 18.00 B

**`storage\image__vector_store.json`**
- Propósito: Não identificado
- Tamanho: 72.00 B

**`storage\index_stats.json`**
- Propósito: Não identificado
- Tamanho: 241.00 B

**`storage\index_store.json`**
- Propósito: Não identificado
- Tamanho: 39.86 KB

### Categoria: docs

**`ANALISE_PROJETO_DETALHADA.md`**
- Propósito: Documentação: Análise Detalhada do Projeto BI_Solution
- Tamanho: 133.32 KB

**`CLAUDE.md`**
- Propósito: Documentação: CLAUDE.md
- Tamanho: 10.55 KB

**`GUIA_LIMPEZA.md`**
- Propósito: Documentação: Guia de Limpeza Conservadora - BI Solution
- Tamanho: 5.82 KB

**`README.md`**
- Propósito: Documentação: 🛒 Agent Solution BI - Lojas Caçula (Executive Edition)
- Tamanho: 3.39 KB

**`Relatório de Infraestrutura, Custos e Viabilidade_ Projeto BI_Solution.md`**
- Propósito: Documentação: Relatório de Infraestrutura, Custos e Viabilidade: Projeto BI_Solution
- Tamanho: 4.57 KB

**`backend\CONTINUOUS_LEARNING_GUIDE.md`**
- Propósito: Documentação: Guia de Continuous Learning - Agent BI (2025)
- Tamanho: 14.56 KB

**`backend\DEPENDENCY_ANALYSIS_REPORT.md`**
- Propósito: Documentação: Relatório de Análise de Dependências - Agent Solution BI Backend
- Tamanho: 14.94 KB

**`backend\MODERNIZATION_COMPLETE.md`**
- Propósito: Documentação: Modernização do Agent BI - Implementação Completa
- Tamanho: 13.39 KB

**`backend\PRODUCT_ANALYSIS_FIX.md`**
- Propósito: Documentação: Correção: Análise de Produto Individual
- Tamanho: 11.47 KB

**`backend\QUICKSTART.md`**
- Propósito: Documentação: 🚀 Quick Start - Backend FastAPI
- Tamanho: 1.66 KB

**`backend\README.md`**
- Propósito: Documentação: Agent BI Backend
- Tamanho: 2.33 KB

**`backend\TOOL_MODERNIZATION_ANALYSIS.md`**
- Propósito: Documentação: Análise de Modernização de Tools LLM - 2025
- Tamanho: 17.84 KB

**`backend\app\core\prompts\code_generation_system_prompt.md`**
- Propósito: Não identificado
- Tamanho: 1.48 KB

**`backend\app\core\prompts\json_filter_generation_prompt.md`**
- Propósito: Não identificado
- Tamanho: 799.00 B

**`backend\app\core\prompts\prompt_analise.md`**
- Propósito: Documentação: PROMPT PRINCIPAL DE ANÁLISE - Agent_BI (CO-STAR)
- Tamanho: 3.38 KB

**`backend\app\core\prompts\prompt_desambiguacao.md`**
- Propósito: Documentação: PROMPT DE DESAMBIGUAÇÃO - Agent_BI
- Tamanho: 2.24 KB

**`backend\app\core\prompts\prompt_gerar_manifesto.md`**
- Propósito: Documentação: Chaves de API e Configurações (substitua com seus valores)
- Tamanho: 117.88 KB

**`backend\app\core\prompts\prompt_integracao_avancada.md`**
- Propósito: Documentação: Relatório Completo de Arquivos do Projeto Agent_BI
- Tamanho: 83.35 KB

**`backend\app\core\prompts\prompt_refatoracao_completa.md`**
- Propósito: Documentação: PROMPT MESTRE: PLANO DE REFATORAÇÃO EXECUTÁVEL E SEGURO
- Tamanho: 1.04 MB

**`backend\app\core\prompts\tool_routing_prompt.md`**
- Propósito: Não identificado
- Tamanho: 891.00 B

**`docs\API_DOCUMENTATION.md`**
- Propósito: Documentação: Documentação da API - Agent Solution BI
- Tamanho: 3.11 KB

**`docs\ARQUITETURA.md`**
- Propósito: Documentação: Arquitetura do Sistema Agent Solution BI
- Tamanho: 5.21 KB

**`docs\ARQUITETURA_VISUAL.md`**
- Propósito: Documentação: Diagrama Visual da Arquitetura do Sistema
- Tamanho: 5.08 KB

**`docs\CODE_CHAT_GUIDE.md`**
- Propósito: Documentação: Code Chat - Agente Fullstack Completo
- Tamanho: 7.01 KB

**`docs\CORRECAO_DEFINITIVA_UNE.md`**
- Propósito: Documentação: ✅ CORREÇÃO DEFINITIVAVA: Seleção UNE em Transferências
- Tamanho: 6.67 KB

**`docs\CREDENTIALS.md`**
- Propósito: Documentação: Credenciais de Acesso - Agent Solution BI
- Tamanho: 2.97 KB

**`docs\FEATURE_CONTEXT7_ACCESS_CONTROL.md`**
- Propósito: Documentação: Implementation Plan: User Segmentation & Dashboard Storytelling
- Tamanho: 2.89 KB

**`docs\GAP_ANALYSIS_100_PERCENT.md`**
- Propósito: Documentação: Gap Analysis: Caminho para 100% de Paridade Funcional
- Tamanho: 4.70 KB

**`docs\GRAPH_GENERATION_FIX.md`**
- Propósito: Documentação: Correção de Geração de Gráficos - Context7 Best Practices 2025
- Tamanho: 5.16 KB

**`docs\GUIA_GERENCIAMENTO_USUARIOS.md`**
- Propósito: Documentação: Guia de Gerenciamento de Usuários - Agent Solution BI
- Tamanho: 5.91 KB

**`docs\GUIA_INICIALIZACAO.md`**
- Propósito: Documentação: 🚀 Guia de Inicialização - AgentBI
- Tamanho: 8.00 KB

**`docs\GUIA_TESTES.md`**
- Propósito: Documentação: 🧪 Guia de Testes - Agent BI
- Tamanho: 4.62 KB

**`docs\LOGGING_QUICK_START.md`**
- Propósito: Documentação: 🚀 Logging - Guia Rápido
- Tamanho: 2.49 KB

**`docs\MANUAL_TEST_CHECKLIST.md`**
- Propósito: Documentação: MANUAL TEST CHECKLIST - Agent Solution BI (SolidJS + FastAPI)
- Tamanho: 13.38 KB

**`docs\MIGRATION_GUIDE.md`**
- Propósito: Documentação: Guia de Migração - Agent BI Solution
- Tamanho: 9.84 KB

**`docs\PARQUET_SCHEMA_REFERENCE.md`**
- Propósito: Documentação: Referência de Esquema do Parquet - admmat.parquet
- Tamanho: 10.50 KB

**`docs\PERFORMANCE_OPTIMIZATION.md`**
- Propósito: Documentação: Performance Optimization Guide - Agent BI
- Tamanho: 8.29 KB

**`docs\PIC_MAPPING.md`**
- Propósito: Documentação: Mapeamento: Próximos Passos ↔ PIC (Plano de Implementação Cirúrgica)
- Tamanho: 5.77 KB

**`docs\PLANO_HIBRIDO_IMPLEMENTADO.md`**
- Propósito: Documentação: 🎉 Plano Híbrido - IMPLEMENTAÇÃO COMPLETA
- Tamanho: 11.29 KB

**`docs\PRD.md`**
- Propósito: Documentação: Product Requirements Document (PRD)
- Tamanho: 31.33 KB

**`docs\QUICK_START.md`**
- Propósito: Documentação: Guia Rápido de Inicialização - Agent Solution BI
- Tamanho: 2.65 KB

**`docs\README.md`**
- Propósito: Documentação: 🤖 Agent Solution BI
- Tamanho: 8.50 KB

**`docs\RELATORIO_COMPARATIVO_CHATGPT_vs_CHATBI.md`**
- Propósito: Documentação: Relatório Comparativo: ChatGPT vs ChatBI
- Tamanho: 15.01 KB

**`docs\RELATORIO_FINAL_IMPLEMENTACAO.md`**
- Propósito: Documentação: 📊 SUMÁRIO EXECUTIVO: Agent BI Solution - Lojas Caçula
- Tamanho: 3.07 KB

**`docs\RELATORIO_PERFORMANCE_CHAT_CONTEXT7.md`**
- Propósito: Documentação: Relatório Context7: Análise de Performance do Chat
- Tamanho: 3.39 KB

**`docs\RELATORIO_VERIFICACAO.md`**
- Propósito: Documentação: 📊 Relatório de Verificação - Agent BI
- Tamanho: 6.98 KB

**`docs\SISTEMA_LOGGING.md`**
- Propósito: Documentação: Sistema de Logging - AgentBI
- Tamanho: 15.68 KB

**`docs\SOLUCAO_FILTROS_ANALYTICS.md`**
- Propósito: Documentação: Solução: Filtros da Página Analytics
- Tamanho: 10.56 KB

**`docs\archive\CORRECOES_CRITICAS_IMPLEMENTADAS.md`**
- Propósito: Documentação: RELATÓRIO DE CORREÇÕES CRÍTICAS IMPLEMENTADAS
- Tamanho: 12.22 KB

**`docs\archive\DIAGNOSTICO_COMPLETO.md`**
- Propósito: Documentação: Diagnóstico Completo - SQL Server e Sincronização Parquet
- Tamanho: 5.72 KB

**`docs\archive\DIAGNOSTICO_MAX_TURNS_FIX.md`**
- Propósito: Documentação: DIAGNÓSTICO E CORREÇÃO: Maximum Conversation Turns Exceeded
- Tamanho: 7.56 KB

**`docs\archive\README_NEW_SYSTEM.md`**
- Propósito: Documentação: 🚀 Agent BI Solution - Quick Start
- Tamanho: 2.30 KB

**`docs\archive\RELATORIO_DIAGNOSTICO_COMPLETO.md`**
- Propósito: Documentação: 🔍 Relatório de Diagnóstico Completo - Agent BI Solution
- Tamanho: 8.79 KB

**`docs\archive\SOLUCAO_FINAL.md`**
- Propósito: Documentação: ✅ SOLUÇÃO FINAL - Dados Visíveis em Todas as Páginas
- Tamanho: 2.35 KB

**`docs\archive\SQL_SERVER_STATUS_REPORT.md`**
- Propósito: Documentação: SQL Server Diagnostics - Status Report
- Tamanho: 4.53 KB

**`docs\archive\SYSTEM_STATUS.md`**
- Propósito: Documentação: Relatório de Status do Sistema - Agent BI Solution
- Tamanho: 2.90 KB

**`docs\guides\HABILITAR_TCP_IP_SQL_SERVER.md`**
- Propósito: Documentação: Como Habilitar TCP/IP no SQL Server
- Tamanho: 4.73 KB

**`docs\guides\SQL_SERVER_SETUP.md`**
- Propósito: Documentação: Configuração do SQL Server - Agent Solution BI
- Tamanho: 4.21 KB

**`docs\regras_negocio_une.md`**
- Propósito: Documentação: Regras de Negócio UNE (Unidade de Negócio)
- Tamanho: 4.14 KB

**`docs\sql-queries-top-vendas.md`**
- Propósito: Documentação: Consultas SQL - Top 10 Vendas por Categoria
- Tamanho: 5.14 KB

**`docs\troubleshooting\AGENT_JSON_OUTPUT.md`**
- Propósito: Documentação: Troubleshooting: Agent Returning Raw JSON (Context7 Violation)
- Tamanho: 2.23 KB

**`docs\troubleshooting\GUIA_RAPIDO.md`**
- Propósito: Documentação: 🔧 GUIA RÁPIDO DE RECUPERAÇÃO
- Tamanho: 1.57 KB

**`docs\troubleshooting\SOLUCAO_NODE_JS.md`**
- Propósito: Documentação: 🚀 SOLUCIONANDO ERRO DE NODE.JS
- Tamanho: 2.89 KB

**`frontend-solid\DASHBOARDS_INTERATIVOS_IMPLEMENTACAO.md`**
- Propósito: Documentação: 🎯 Dashboards Interativos - Implementação Completa
- Tamanho: 10.04 KB

**`frontend-solid\INTEGRATION_TESTS.md`**
- Propósito: Documentação: Plano de Testes de Integração - Aplicação SolidJS
- Tamanho: 3.33 KB

**`frontend-solid\TESTING_GUIDE.md`**
- Propósito: Documentação: Guia de Testes - Componentes Migrados SolidJS
- Tamanho: 7.64 KB

**`frontend-solid\src\examples\README.md`**
- Propósito: Documentação: Exemplos e Demonstrações
- Tamanho: 1.56 KB

**`frontend-solid\src\migrated-components\README.md`**
- Propósito: Documentação: Componentes UI Migrados - React → SolidJS
- Tamanho: 3.58 KB

**`frontend-solid\src\migrated-components\USAGE_GUIDE.md`**
- Propósito: Documentação: Guia de Uso - Componentes UI Migrados para SolidJS
- Tamanho: 4.13 KB

**`frontend-solid\src\migrated-components\utils\README.md`**
- Propósito: Documentação: Utilitários Migrados
- Tamanho: 1.13 KB

### Categoria: docs_obsolete

**`AGENT_FIX_REPORT_2025-12-28.md`**
- Propósito: [OBSOLETO] Documentação: Relatorio de Correcao do Agente BI - 2025-12-28
- Tamanho: 8.04 KB

**`ASYNC_RAG_IMPLEMENTATION.md`**
- Propósito: [OBSOLETO] Documentação: Async RAG Implementation - Modern Python 3.11+
- Tamanho: 11.48 KB

**`FIX_MAX_TURNS_2025-12-28.md`**
- Propósito: [OBSOLETO] Documentação: Correção Definitiva: "Maximum conversation turns exceeded"
- Tamanho: 5.29 KB

**`IMPLEMENTATION_SUMMARY.md`**
- Propósito: [OBSOLETO] Documentação: Implementação Completa - Modernização de Tools LLM
- Tamanho: 8.27 KB

**`IMPROVEMENTS_SUMMARY_2025-12-28.md`**
- Propósito: [OBSOLETO] Documentação: Resumo de Melhorias Implementadas - 2025-12-28
- Tamanho: 6.20 KB

**`MODERNIZATION_SUMMARY.md`**
- Propósito: [OBSOLETO] Documentação: Modernização Agent BI - Sumário Executivo
- Tamanho: 4.30 KB

**`PERFORMANCE_FIX_2025-12-27.md`**
- Propósito: [OBSOLETO] Documentação: Performance Fix - 4+ Minute Hang Issue
- Tamanho: 6.52 KB

**`QUICK_START_MODERNIZATION.md`**
- Propósito: [OBSOLETO] Documentação: Quick Start - Melhorias de Modernização 2025
- Tamanho: 4.28 KB

### Categoria: script_temp

**`analyze_project.py`**
- Propósito: [SCRIPT TEMPORÁRIO] Não identificado
- Tamanho: 15.86 KB
- Classes: ProjectAnalyzer

**`analyze_project_detailed.py`**
- Propósito: [SCRIPT TEMPORÁRIO] Não identificado
- Tamanho: 35.32 KB
- Classes: DetailedProjectAnalyzer

**`cleanup_conservative.py`**
- Propósito: [SCRIPT TEMPORÁRIO] Não identificado
- Tamanho: 15.42 KB
- Classes: SafeCleanup

**`restore_backup.py`**
- Propósito: [SCRIPT TEMPORÁRIO] Não identificado
- Tamanho: 6.96 KB
- Classes: BackupRestorer

### Categoria: source_javascript

**`frontend-solid\postcss.config.js`**
- Propósito: Não identificado
- Tamanho: 86.00 B

**`frontend-solid\src\Layout.tsx`**
- Propósito: Componentes React/Solid: userRole, NavItem
- Tamanho: 5.59 KB

**`frontend-solid\src\__tests__\App.test.tsx`**
- Propósito: Não identificado
- Tamanho: 808.00 B

**`frontend-solid\src\__tests__\ErrorBoundary.test.tsx`**
- Propósito: Componentes React/Solid: ThrowError
- Tamanho: 816.00 B

**`frontend-solid\src\__tests__\Layout.test.tsx`**
- Propósito: Não identificado
- Tamanho: 841.00 B

**`frontend-solid\src\components\AIInsightsPanel.tsx`**
- Propósito: Componente: Componentes React/Solid: getCategoryIcon, getCategoryColor, getSeverityBadge
- Tamanho: 8.05 KB

**`frontend-solid\src\components\ChartDownloadButton.tsx`**
- Propósito: Componente: Exporta: ChartDownloadButton, MultiFormatDownload
- Tamanho: 3.38 KB

**`frontend-solid\src\components\DataTable.tsx`**
- Propósito: Componente: Componentes React/Solid: DataTable, tableData, headers
- Tamanho: 4.59 KB

**`frontend-solid\src\components\DownloadButton.tsx`**
- Propósito: Componente: Componentes React/Solid: handleDownload
- Tamanho: 1.29 KB

**`frontend-solid\src\components\ErrorBoundary.tsx`**
- Propósito: Componente: Exporta: ErrorBoundary
- Tamanho: 1.38 KB

**`frontend-solid\src\components\ExportMenu.tsx`**
- Propósito: Componente: Componentes React/Solid: downloadFile, exportAsJSON, exportAsMarkdown
- Tamanho: 4.18 KB

**`frontend-solid\src\components\FeedbackButtons.tsx`**
- Propósito: Componente: Componentes React/Solid: handleFeedbackClick
- Tamanho: 1.17 KB

**`frontend-solid\src\components\Logo.tsx`**
- Propósito: Componente: Exporta: Logo
- Tamanho: 686.00 B

**`frontend-solid\src\components\MessageActions.tsx`**
- Propósito: Componente: Componentes React/Solid: copyToClipboard
- Tamanho: 1.50 KB

**`frontend-solid\src\components\PlotlyChart.tsx`**
- Propósito: Componente: Componentes React/Solid: PlotlyChart, toggleExpand, handleEsc
- Tamanho: 5.52 KB

**`frontend-solid\src\components\ShareButton.tsx`**
- Propósito: Componente: Componentes React/Solid: openModal, closeModal
- Tamanho: 6.08 KB

**`frontend-solid\src\components\Typewriter.tsx`**
- Propósito: Componente: * Componente Typewriter - Efeito de digitação ChatGPT-like
 *
 * Renderiza texto com efeito de digitação suave, caractere por caractere.
 * Perfeito para respostas de chat/IA que chegam via streaming.
- Tamanho: 3.40 KB

**`frontend-solid\src\components\TypingIndicator.tsx`**
- Propósito: Componente: Exporta: TypingIndicator
- Tamanho: 294.00 B

**`frontend-solid\src\components\UserPreferences.tsx`**
- Propósito: Componente: Componentes React/Solid: updatePreference
- Tamanho: 4.28 KB

**`frontend-solid\src\components\__tests__\Chat.test.tsx`**
- Propósito: Componente: Não identificado
- Tamanho: 9.06 KB

**`frontend-solid\src\components\index.ts`**
- Propósito: Componente: * Components Index
 * Central export for all reusable components
- Tamanho: 370.00 B

**`frontend-solid\src\examples\ComponentsDemo.tsx`**
- Propósito: * Demo page for migrated UI components
 * Showcases Skeleton, Badge, and Button components
- Tamanho: 6.67 KB

**`frontend-solid\src\examples\MinimalLogin.tsx`**
- Propósito: Exporta: MinimalLogin
- Tamanho: 853.00 B

**`frontend-solid\src\examples\SkeletonDemo.tsx`**
- Propósito: * Demo page for Skeleton component
 * Tests visual rendering and different use cases
- Tamanho: 3.02 KB

**`frontend-solid\src\hooks\useAdmin.ts`**
- Propósito: * useAdmin Hook - SolidJS
 * Hook para gerenciar operações administrativas
- Tamanho: 2.90 KB

**`frontend-solid\src\hooks\useAnalytics.ts`**
- Propósito: * useAnalytics Hook - SolidJS
 * Hook customizado para gerenciar estado e operações de analytics
- Tamanho: 2.17 KB

**`frontend-solid\src\hooks\useMediaQuery.ts`**
- Propósito: * useMediaQuery Hook - SolidJS
 * Hook para detectar breakpoints responsivos
- Tamanho: 970.00 B

**`frontend-solid\src\hooks\useReports.ts`**
- Propósito: * useReports Hook - SolidJS
 * Hook para gerenciar estado e operações de relatórios
- Tamanho: 2.82 KB

**`frontend-solid\src\index.tsx`**
- Propósito: Não identificado
- Tamanho: 5.82 KB

**`frontend-solid\src\index_minimal_test.tsx`**
- Propósito: Não identificado
- Tamanho: 401.00 B

**`frontend-solid\src\lib\api.ts`**
- Propósito: Exporta: KpiMetrics, ErrorTrendItem, TopQueryItem
- Tamanho: 6.71 KB

**`frontend-solid\src\lib\api\client.ts`**
- Propósito: Exporta: apiClient
- Tamanho: 1.88 KB

**`frontend-solid\src\lib\export.ts`**
- Propósito: * Exports an array of objects to a CSV file.
 * @param data The array of objects to export.
 * @param filename The name of the CSV file.
- Tamanho: 926.00 B

**`frontend-solid\src\lib\formatters.ts`**
- Propósito: Exporta: formatTimestamp, formatCurrency, formatNumber
- Tamanho: 688.00 B

**`frontend-solid\src\lib\supabase.ts`**
- Propósito: * Supabase Client Configuration for Frontend
- Tamanho: 485.00 B

**`frontend-solid\src\migrated-components\components\ui\Alert.tsx`**
- Propósito: Componente: * Alert component - notification container
 * Migrated from React to SolidJS
- Tamanho: 1.96 KB

**`frontend-solid\src\migrated-components\components\ui\Avatar.tsx`**
- Propósito: Componente: * Avatar component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
- Tamanho: 1.29 KB

**`frontend-solid\src\migrated-components\components\ui\Badge.test.tsx`**
- Propósito: Componente: Não identificado
- Tamanho: 1.94 KB

**`frontend-solid\src\migrated-components\components\ui\Badge.tsx`**
- Propósito: Componente: * Badge component for status indicators and labels
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Badge variant="default">New</Badge>
 * <Badge variant="destructive">Error</Badge>
 * 
- Tamanho: 1.89 KB

**`frontend-solid\src\migrated-components\components\ui\Button.test.tsx`**
- Propósito: Componente: Não identificado
- Tamanho: 2.67 KB

**`frontend-solid\src\migrated-components\components\ui\Button.tsx`**
- Propósito: Componente: * Button component with multiple variants and sizes
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Button variant="default">Click me</Button>
 * <Button variant="destructive" size="sm
- Tamanho: 2.44 KB

**`frontend-solid\src\migrated-components\components\ui\Card.tsx`**
- Propósito: Componente: * Card component - main container
- Tamanho: 2.56 KB

**`frontend-solid\src\migrated-components\components\ui\Dialog.tsx`**
- Propósito: Componente: * Dialog component - modal dialog
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
- Tamanho: 2.31 KB

**`frontend-solid\src\migrated-components\components\ui\DropdownMenu.tsx`**
- Propósito: Componente: * DropdownMenu component - dropdown menu
 * Migrated from React to SolidJS (simplified native implementation)
- Tamanho: 1.85 KB

**`frontend-solid\src\migrated-components\components\ui\Input.tsx`**
- Propósito: Componente: * Input component for form fields
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Input type="text" placeholder="Enter text..." />
 * <Input type="email" />
 * ```
- Tamanho: 1.22 KB

**`frontend-solid\src\migrated-components\components\ui\Label.tsx`**
- Propósito: Componente: * Label component for form fields
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Label for="email">Email</Label>
 * ```
- Tamanho: 852.00 B

**`frontend-solid\src\migrated-components\components\ui\LazyImage.tsx`**
- Propósito: Componente: * LazyImage component - optimized image loading
 * Migrated from React to SolidJS (Next.js Image removed, native img)
 * 
 * @example
 * ```tsx
 * <LazyImage src="/image.jpg" alt="Description" />
 * `
- Tamanho: 1.22 KB

**`frontend-solid\src\migrated-components\components\ui\Select.tsx`**
- Propósito: Componente: * Select component - native select dropdown
 * Migrated from React to SolidJS (simplified, native select)
- Tamanho: 960.00 B

**`frontend-solid\src\migrated-components\components\ui\Separator.tsx`**
- Propósito: Componente: * Separator component for visual division
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Separator />
 * <Separator orientation="vertical" />
- Tamanho: 1.03 KB

**`frontend-solid\src\migrated-components\components\ui\Sheet.tsx`**
- Propósito: Componente: * Sheet component - side panel/drawer
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
- Tamanho: 2.14 KB

**`frontend-solid\src\migrated-components\components\ui\Skeleton.test.tsx`**
- Propósito: Componente: Não identificado
- Tamanho: 1.57 KB

**`frontend-solid\src\migrated-components\components\ui\Skeleton.tsx`**
- Propósito: Componente: * Skeleton component for loading states
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Skeleton class="w-full h-20" />
 * ```
- Tamanho: 516.00 B

**`frontend-solid\src\migrated-components\components\ui\SkipLink.tsx`**
- Propósito: Componente: * SkipLink Component
 * Link de pular navegação para acessibilidade
 * Migrated from React to SolidJS (Next.js Link removed, native anchor)
- Tamanho: 548.00 B

**`frontend-solid\src\migrated-components\components\ui\Sonner.tsx`**
- Propósito: Componente: * Toast notification system (Sonner alternative)
 * Migrated from React to SolidJS (native implementation)
- Tamanho: 1.96 KB

**`frontend-solid\src\migrated-components\components\ui\Table.tsx`**
- Propósito: Componente: * Table component - table container with scroll
 * Migrated from React to SolidJS
- Tamanho: 3.34 KB

**`frontend-solid\src\migrated-components\components\ui\Tabs.tsx`**
- Propósito: Componente: * Tabs component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation with createSignal)
- Tamanho: 3.84 KB

**`frontend-solid\src\migrated-components\components\ui\index.ts`**
- Propósito: Componente: * UI Components - Migrated from React to SolidJS
 * 
 * This barrel file exports all UI components for easy importing
 * 
 * Total: 18 components migrated (100%)
- Tamanho: 1.34 KB

**`frontend-solid\src\migrated-components\utils\a11y.ts`**
- Propósito: Componente: * Accessibility Utilities for SolidJS
 * Funções utilitárias para acessibilidade
- Tamanho: 2.03 KB

**`frontend-solid\src\migrated-components\utils\cn.ts`**
- Propósito: Componente: * Combina classes CSS com suporte a Tailwind
 * Útil para mesclar classes condicionais
- Tamanho: 276.00 B

**`frontend-solid\src\pages\About.tsx`**
- Propósito: Página: Não identificado
- Tamanho: 6.22 KB

**`frontend-solid\src\pages\Admin.tsx`**
- Propósito: Página: Componentes React/Solid: openCreateUserModal, openEditUserModal, closeUserModal
- Tamanho: 18.57 KB

**`frontend-solid\src\pages\Analytics.tsx`**
- Propósito: Página: Componentes React/Solid: downloadABCCSV, generateCharts
- Tamanho: 31.35 KB

**`frontend-solid\src\pages\Chat.tsx`**
- Propósito: Página: Componentes React/Solid: stopGeneration, clearConversation, regenerateLastResponse
- Tamanho: 22.27 KB

**`frontend-solid\src\pages\CodeChat.tsx`**
- Propósito: Página: Componentes React/Solid: clearHistory, loadExample
- Tamanho: 15.43 KB

**`frontend-solid\src\pages\Dashboard.tsx`**
- Propósito: Página: Componentes React/Solid: handleProductClick
- Tamanho: 19.45 KB

**`frontend-solid\src\pages\Diagnostics.tsx`**
- Propósito: Página: Componentes React/Solid: getStatusColor, getStatusIcon, getStatusLabel
- Tamanho: 14.50 KB

**`frontend-solid\src\pages\Examples.tsx`**
- Propósito: Página: Componentes React/Solid: perguntasFiltradas, handleTestarPergunta
- Tamanho: 7.31 KB

**`frontend-solid\src\pages\Help.tsx`**
- Propósito: Página: Componentes React/Solid: isAdmin, filteredFAQ
- Tamanho: 17.32 KB

**`frontend-solid\src\pages\Learning.tsx`**
- Propósito: Página: Componentes React/Solid: getSuccessRateColor
- Tamanho: 18.81 KB

**`frontend-solid\src\pages\Login.tsx`**
- Propósito: Página: Exporta: Login
- Tamanho: 6.12 KB

**`frontend-solid\src\pages\Playground.tsx`**
- Propósito: Página: Componentes React/Solid: clearHistory, loadExample, generateCodeSnippet
- Tamanho: 20.58 KB

**`frontend-solid\src\pages\Profile.tsx`**
- Propósito: Página: Exporta: Profile
- Tamanho: 9.94 KB

**`frontend-solid\src\pages\Reports.tsx`**
- Propósito: Página: Componentes React/Solid: downloadReport, downloadAllAsCSV, filteredReports
- Tamanho: 11.42 KB

**`frontend-solid\src\pages\Rupturas.tsx`**
- Propósito: Página: Componentes React/Solid: generateCharts, handleChartClick, handleGroupClick
- Tamanho: 40.19 KB

**`frontend-solid\src\pages\SharedConversation.tsx`**
- Propósito: Página: Exporta: SharedConversation
- Tamanho: 5.33 KB

**`frontend-solid\src\pages\Transfers.tsx`**
- Propósito: Página: Componentes React/Solid: toggleProductSelection, removeFromCart, clearCart
- Tamanho: 30.78 KB

**`frontend-solid\src\services\admin.service.ts`**
- Propósito: Exporta: adminService
- Tamanho: 2.01 KB

**`frontend-solid\src\services\analytics.service.ts`**
- Propósito: * Analytics Service
 * Serviço para comunicação com API de analytics
- Tamanho: 1.89 KB

**`frontend-solid\src\services\auth.service.ts`**
- Propósito: Exporta: LoginCredentials, AuthResponse, authService
- Tamanho: 1.07 KB

**`frontend-solid\src\services\logger.service.ts`**
- Propósito: * Sistema de Logging para Frontend
 * Gerencia logs no browser e envia logs importantes para o backend
- Tamanho: 12.35 KB

**`frontend-solid\src\services\reports.service.ts`**
- Propósito: Exporta: reportsService
- Tamanho: 2.07 KB

**`frontend-solid\src\store\auth.ts`**
- Propósito: Componentes React/Solid: initializeAuth, logout
- Tamanho: 5.51 KB

**`frontend-solid\src\store\dashboard.ts`**
- Propósito: Componentes React/Solid: startPolling, stopPolling, togglePolling
- Tamanho: 2.43 KB

**`frontend-solid\tailwind.config.js`**
- Propósito: Não identificado
- Tamanho: 1.50 KB

**`frontend-solid\vitest.setup.ts`**
- Propósito: Não identificado
- Tamanho: 37.00 B

**`scripts\clean-port.js`**
- Propósito: * Cross-platform script to kill processes on specific ports
 * Works on Windows, Linux, and macOS
 * Ports: 8000 (Backend), 3000 (Frontend)
- Tamanho: 3.29 KB

**`scripts\debug_transfers.js`**
- Propósito: * DIAGNÓSTICO DE CLIQUES - Cole no Console do Navegador
 * 
 * Abre DevTools (F12), vai em Console, e cola este script.
 * Ele vai monitorar EXATAMENTE o que está acontecendo nos cliques.
- Tamanho: 2.07 KB

**`scripts\show-logs.js`**
- Propósito: * Script para visualizar logs agregados em tempo real
 * Monitora múltiplos arquivos de log e exibe com cores
- Tamanho: 5.23 KB

**`tests\playwright.config.ts`**
- Propósito: * Playwright configuration for TestSprite-generated E2E tests
 * See https://playwright.dev/docs/test-configuration
- Tamanho: 2.22 KB

**`tests\test_products_selection.ts`**
- Propósito: * Teste de seleção de Produtos para Transferências (Multi-Seleção)
- Tamanho: 1.45 KB

**`tests\test_transfers_selection.ts`**
- Propósito: * Teste de seleção UNE para Transferências
 * Valida comportamento de 1→1, 1→N, N→N
- Tamanho: 4.62 KB

### Categoria: source_python

**`backend\app\api\dependencies.py`**
- Propósito: API Dependencies
- Tamanho: 16.55 KB
- Funções: require_role, require_permission

**`backend\app\api\v1\endpoints\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 148.00 B

**`backend\app\api\v1\endpoints\admin.py`**
- Propósito: Admin Endpoints
- Tamanho: 15.15 KB
- Classes: AdminStats

**`backend\app\api\v1\endpoints\analytics.py`**
- Propósito: Analytics Endpoints
- Tamanho: 19.85 KB
- Classes: MetricsSummary, ErrorTrendItem, TopQueryItem, ABCDetailItem
- Funções: _initialize_metrics_dashboard

**`backend\app\api\v1\endpoints\auth.py`**
- Propósito: Authentication Endpoints
- Tamanho: 10.13 KB

**`backend\app\api\v1\endpoints\auth_alt.py`**
- Propósito: ENDPOINT DE LOGIN ALTERNATIVO - USA PYODBC DIRETO (SÍNCRONO)
- Tamanho: 3.48 KB
- Classes: LoginRequest, UserData, Token
- Funções: login_alt

**`backend\app\api\v1\endpoints\chat.py`**
- Propósito: Chat Endpoints
- Tamanho: 25.39 KB
- Classes: ChatRequest, FeedbackRequest, ChatResponse
- Funções: safe_json_dumps, _initialize_agents_and_llm

**`backend\app\api\v1\endpoints\code_chat.py`**
- Propósito: Code Chat API Endpoints
- Tamanho: 4.35 KB
- Classes: ChatMessage, CodeChatRequest, CodeReference, CodeChatResponse, IndexStats

**`backend\app\api\v1\endpoints\diagnostics.py`**
- Propósito: Define classes: DBConfig, ConnectionTestResult
- Tamanho: 6.88 KB
- Classes: DBConfig, ConnectionTestResult

**`backend\app\api\v1\endpoints\frontend_logs.py`**
- Propósito: Endpoint para receber logs do frontend
- Tamanho: 4.96 KB
- Classes: FrontendLogEntry, FrontendLogsRequest, Config
- Funções: map_frontend_log_level

**`backend\app\api\v1\endpoints\health.py`**
- Propósito: Health Check Endpoint with Timeout
- Tamanho: 7.55 KB
- Funções: check_environment

**`backend\app\api\v1\endpoints\insights.py`**
- Propósito: AI Insights Endpoints
- Tamanho: 11.19 KB
- Classes: InsightResponse, InsightsListResponse

**`backend\app\api\v1\endpoints\learning.py`**
- Propósito: Define classes: FeedbackSubmission, RetrievalQuery
- Tamanho: 17.15 KB
- Classes: FeedbackSubmission, RetrievalQuery

**`backend\app\api\v1\endpoints\metrics.py`**
- Propósito: Metrics Endpoints
- Tamanho: 13.97 KB
- Classes: MetricsSummary, SaleItem, TopProduct, BusinessKPIs

**`backend\app\api\v1\endpoints\playground.py`**
- Propósito: Define classes: QueryRequest, ChatMessage, PlaygroundChatRequest
- Tamanho: 5.54 KB
- Classes: QueryRequest, ChatMessage, PlaygroundChatRequest

**`backend\app\api\v1\endpoints\preferences.py`**
- Propósito: User Preferences Endpoints
- Tamanho: 8.04 KB
- Classes: PreferenceCreate, PreferenceResponse, PreferenceListResponse

**`backend\app\api\v1\endpoints\reports.py`**
- Propósito: Reports Endpoints
- Tamanho: 6.58 KB

**`backend\app\api\v1\endpoints\rupturas.py`**
- Propósito: Não identificado
- Tamanho: 7.83 KB

**`backend\app\api\v1\endpoints\shared.py`**
- Propósito: Shared Conversations Endpoints
- Tamanho: 5.64 KB
- Classes: ShareConversationRequest, ShareConversationResponse, SharedConversationView

**`backend\app\api\v1\endpoints\transfers.py`**
- Propósito: Define classes: TransferRequestPayload, TransferReportQuery, ProductSearchRequest
- Tamanho: 15.80 KB
- Classes: TransferRequestPayload, TransferReportQuery, ProductSearchRequest, BulkTransferRequestPayload

**`backend\app\api\v1\router.py`**
- Propósito: Endpoints API: API V1 Router
- Tamanho: 1.42 KB

**`backend\app\config\database.py`**
- Propósito: Database Configuration
- Tamanho: 2.24 KB
- Classes: Base

**`backend\app\config\logging_config.py`**
- Propósito: Logging Configuration for Agent Solution BI
- Tamanho: 2.68 KB
- Funções: setup_logging, get_logger

**`backend\app\config\security.py`**
- Propósito: Security Configuration
- Tamanho: 2.80 KB
- Funções: verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token

**`backend\app\config\settings.py`**
- Propósito: Settings Configuration
- Tamanho: 7.10 KB
- Classes: Settings
- Funções: get_settings

**`backend\app\core\agent_state.py`**
- Propósito: Agente BI: Define classes: AgentState
- Tamanho: 1.08 KB
- Classes: AgentState

**`backend\app\core\agent_wrapper.py`**
- Propósito: Agente BI: Wrapper simplificado para integração do sistema de agentes com FastAPI
- Tamanho: 2.21 KB
- Classes: AgentWrapper
- Funções: get_agent_wrapper

**`backend\app\core\agents\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 142.00 B

**`backend\app\core\agents\base_agent.py`**
- Propósito: Agente BI: Define classes: BaseAgent
- Tamanho: 3.77 KB
- Classes: BaseAgent

**`backend\app\core\agents\caculinha_bi_agent.py`**
- Propósito: Agente BI: Define classes: CaculinhaBIAgent
- Tamanho: 84.36 KB
- Classes: CaculinhaBIAgent

**`backend\app\core\agents\code_gen_agent.py`**
- Propósito: Agente BI: Define classes: CodeGenAgent
- Tamanho: 15.24 KB
- Classes: CodeGenAgent
- Funções: _load_prompt_template

**`backend\app\core\agents\developer_agent.py`**
- Propósito: Agente BI: Define classes: DeveloperAgent
- Tamanho: 4.67 KB
- Classes: DeveloperAgent

**`backend\app\core\agents\multi_step_agent.py`**
- Propósito: Agente BI: LangGraph Multi-Step Agent - Workflow cíclico para raciocínio avançado
- Tamanho: 9.86 KB
- Classes: AgentState, MultiStepAgent
- Funções: create_multi_step_agent

**`backend\app\core\agents\product_agent.py`**
- Propósito: Agente BI: Define classes: ProductAgent
- Tamanho: 14.21 KB
- Classes: ProductAgent

**`backend\app\core\agents\prompt_loader.py`**
- Propósito: Define classes: PromptLoader
- Tamanho: 4.65 KB
- Classes: PromptLoader

**`backend\app\core\agents\supervisor_agent.py`**
- Propósito: Agente BI: Define classes: SupervisorAgent
- Tamanho: 4.03 KB
- Classes: SupervisorAgent

**`backend\app\core\agents\tool_agent.py`**
- Propósito: Agente BI: Define classes: ToolAgent
- Tamanho: 8.96 KB
- Classes: ToolAgent
- Funções: initialize_agent_for_session

**`backend\app\core\auth_service.py`**
- Propósito: Define classes: AuthService
- Tamanho: 14.26 KB
- Classes: AuthService

**`backend\app\core\cache.py`**
- Propósito: Agent Graph Cache
- Tamanho: 8.30 KB
- Classes: AgentGraphCache

**`backend\app\core\code_rag_service.py`**
- Propósito: Code RAG Service - Semantic Code Search with LlamaIndex + Gemini
- Tamanho: 10.73 KB
- Classes: CodeRAGService
- Funções: get_code_rag_service

**`backend\app\core\context.py`**
- Propósito: Funções: set_current_user_context, get_current_user_context, get_current_user_segments
- Tamanho: 904.00 B
- Funções: set_current_user_context, get_current_user_context, get_current_user_segments

**`backend\app\core\data_scope_service.py`**
- Propósito: Define classes: DataScopeService
- Tamanho: 7.26 KB
- Classes: DataScopeService

**`backend\app\core\data_source_manager.py`**
- Propósito: Data Source Manager - Acesso centralizado aos dados Parquet
- Tamanho: 8.28 KB
- Classes: ParquetDataSource, DataSourceManager
- Funções: get_data_manager

**`backend\app\core\factory\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 18.00 B

**`backend\app\core\factory\component_factory.py`**
- Propósito: Fábrica de Componentes
- Tamanho: 1.86 KB
- Classes: ComponentFactory

**`backend\app\core\graph\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 446.00 B

**`backend\app\core\graph\agent.py`**
- Propósito: Agente BI: Define classes: GraphAgent
- Tamanho: 3.39 KB
- Classes: GraphAgent

**`backend\app\core\intelligent_chatbi.py`**
- Propósito: Chat BI - Sistema Inteligente com Gemini
- Tamanho: 6.94 KB
- Classes: IntelligentChatBI

**`backend\app\core\learning\continuous_learner.py`**
- Propósito: Sistema de Aprendizado Contínuo para LLM
- Tamanho: 19.34 KB
- Classes: ContinuousLearner
- Funções: get_continuous_learner

**`backend\app\core\learning\feedback_system.py`**
- Propósito: Sistema de coleta e análise de feedback do usuário.
- Tamanho: 8.84 KB
- Classes: FeedbackSystem

**`backend\app\core\learning\pattern_matcher.py`**
- Propósito: Define classes: PatternMatcher
- Tamanho: 3.19 KB
- Classes: PatternMatcher

**`backend\app\core\llm_base.py`**
- Propósito: Define classes: BaseLLMAdapter
- Tamanho: 155.00 B
- Classes: BaseLLMAdapter

**`backend\app\core\llm_factory.py`**
- Propósito: Factory para seleção automática de adaptadores LLM.
- Tamanho: 3.05 KB
- Classes: LLMFactory

**`backend\app\core\llm_gemini_adapter.py`**
- Propósito: Adaptador de dados: Define classes: GeminiLLMAdapter
- Tamanho: 29.32 KB
- Classes: GeminiLLMAdapter

**`backend\app\core\llm_gemini_adapter_v2.py`**
- Propósito: Adaptador de dados: GeminiLLMAdapter V2 - Usando objetos nativos do SDK
- Tamanho: 12.06 KB
- Classes: GeminiLLMAdapterV2
- Funções: _convert_to_serializable

**`backend\app\core\llm_gemini_adapter_v3.py`**
- Propósito: Adaptador de dados: GeminiLLMAdapter V3 - Usando o NOVO SDK google-genai (Oficial 2025)
- Tamanho: 7.81 KB
- Classes: GeminiLLMAdapterV3

**`backend\app\core\llm_langchain_adapter.py`**
- Propósito: Adaptador de dados: Define classes: CustomLangChainLLM
- Tamanho: 12.18 KB
- Classes: CustomLangChainLLM
- Funções: _clean_json_schema

**`backend\app\core\logging_config.py`**
- Propósito: Sistema de Logging Centralizado
- Tamanho: 13.60 KB
- Classes: LogConfig, JSONFormatter, ColoredConsoleFormatter
- Funções: get_file_handler, get_timed_file_handler, get_console_handler, setup_logger, configure_structlog

**`backend\app\core\logging_middleware.py`**
- Propósito: Middleware de Logging para FastAPI
- Tamanho: 10.41 KB
- Classes: RequestLoggingMiddleware, PerformanceLoggingMiddleware, SecurityLoggingMiddleware, AuditLoggingMiddleware, ErrorLoggingMiddleware

**`backend\app\core\monitoring\metrics_dashboard.py`**
- Propósito: Define classes: MetricsDashboard
- Tamanho: 8.60 KB
- Classes: MetricsDashboard

**`backend\app\core\parquet_cache.py`**
- Propósito: Parquet Cache System with LRU eviction policy
- Tamanho: 4.39 KB
- Classes: ParquetCache

**`backend\app\core\query_processor.py`**
- Propósito: Define classes: QueryProcessor
- Tamanho: 6.01 KB
- Classes: QueryProcessor

**`backend\app\core\rag\example_collector.py`**
- Propósito: Define classes: ExampleCollector
- Tamanho: 5.64 KB
- Classes: ExampleCollector

**`backend\app\core\rag\hybrid_retriever.py`**
- Propósito: Hybrid Retriever - BM25 + Dense Embeddings (2025)
- Tamanho: 20.53 KB
- Classes: HybridRetriever
- Funções: get_hybrid_retriever

**`backend\app\core\rag\query_retriever.py`**
- Propósito: Define classes: QueryRetriever
- Tamanho: 7.80 KB
- Classes: QueryRetriever

**`backend\app\core\robust_chatbi.py`**
- Propósito: Chat BI - Sistema ROBUSTO com Regex (SEM dependência de API)
- Tamanho: 12.78 KB
- Classes: RobustChatBI

**`backend\app\core\security\data_masking.py`**
- Propósito: Funções: mask_pii, get_pii_summary
- Tamanho: 3.28 KB
- Funções: mask_pii, get_pii_summary

**`backend\app\core\security\input_validator.py`**
- Propósito: Funções: sanitize_username, validate_password_strength, sanitize_sql_input
- Tamanho: 3.38 KB
- Funções: sanitize_username, validate_password_strength, sanitize_sql_input

**`backend\app\core\supabase_client.py`**
- Propósito: Supabase Client Configuration
- Tamanho: 2.23 KB
- Funções: get_supabase_client, get_supabase_admin_client

**`backend\app\core\supabase_user_service.py`**
- Propósito: Supabase User Management Service
- Tamanho: 11.56 KB
- Classes: SupabaseUserService

**`backend\app\core\sync_service.py`**
- Propósito: Define classes: SyncService
- Tamanho: 3.63 KB
- Classes: SyncService

**`backend\app\core\tools\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 0.00 B

**`backend\app\core\tools\chart_tools.py`**
- Propósito: Ferramentas: Ferramentas para geração de gráficos e visualizações.
- Tamanho: 61.76 KB
- Funções: _get_theme_template, _apply_chart_customization, _export_chart_to_json, gerar_grafico_vendas_por_categoria, gerar_grafico_estoque_por_produto

**`backend\app\core\tools\check_gui_dependencies.py`**
- Propósito: Funções: check_dependency, main
- Tamanho: 1.65 KB
- Funções: check_dependency, main

**`backend\app\core\tools\check_integration.py`**
- Propósito: Não identificado
- Tamanho: 0.00 B

**`backend\app\core\tools\code_interpreter.py`**
- Propósito: Code Interpreter - Sandbox seguro para execução de código Python
- Tamanho: 8.89 KB
- Classes: CodeInterpreter
- Funções: get_interpreter, executar_codigo_python

**`backend\app\core\tools\date_time_tools.py`**
- Propósito: Ferramentas: Funções: get_current_datetime
- Tamanho: 388.00 B
- Funções: get_current_datetime

**`backend\app\core\tools\debug_server.py`**
- Propósito: Não identificado
- Tamanho: 1.24 KB

**`backend\app\core\tools\flexible_query_tool.py`**
- Propósito: Ferramentas: Ferramenta genérica e flexível para consultas ao Parquet
- Tamanho: 9.83 KB
- Funções: _safe_serialize, _find_column, consultar_dados_flexivel

**`backend\app\core\tools\graph_integration.py`**
- Propósito: Funções: processar_resposta_com_grafico
- Tamanho: 6.13 KB
- Funções: processar_resposta_com_grafico

**`backend\app\core\tools\mcp_parquet_tools.py`**
- Propósito: Ferramentas: Funções: get_product_data, get_product_stock, list_product_categories
- Tamanho: 4.18 KB
- Funções: get_product_data, get_product_stock, list_product_categories

**`backend\app\core\tools\mcp_sql_server_tools.py`**
- Propósito: Ferramentas: Funções: get_product_data, get_product_stock, list_product_categories
- Tamanho: 4.00 KB
- Funções: get_product_data, get_product_stock, list_product_categories

**`backend\app\core\tools\quick_response.py`**
- Propósito: Sistema de Resposta Rápida (Quick Response)
- Tamanho: 5.98 KB
- Classes: QuickResponseSystem
- Funções: create_quick_response_system

**`backend\app\core\tools\semantic_search_tool.py`**
- Propósito: Ferramentas: Ferramenta de busca semântica para produtos usando RAG (Retrieval-Augmented Generation).
- Tamanho: 10.58 KB
- Funções: _get_embeddings_model, _initialize_vector_store, _reciprocal_rank_fusion, buscar_produtos_inteligente, reinicializar_vector_store

**`backend\app\core\tools\sql_server_tools.py`**
- Propósito: Ferramentas: Ferramentas para executar consultas SQL Server através do agente.
- Tamanho: 10.50 KB
- Funções: query_database, get_product_by_code, search_products_by_name, get_products_by_category, get_top_selling_products

**`backend\app\core\tools\une_tools.py`**
- Propósito: Ferramentas: Ferramentas LangChain para operações UNE.
- Tamanho: 65.84 KB
- Funções: _get_data_adapter, _normalize_dataframe, _load_data, calcular_abastecimento_une, calcular_mc_produto

**`backend\app\core\tools\une_tools_backup_old.py`**
- Propósito: Ferramentas: Define classes: HybridAdapter
- Tamanho: 16.47 KB
- Classes: HybridAdapter
- Funções: tool, _get_data_adapter, _normalize_dataframe, _load_data, calcular_abastecimento_une

**`backend\app\core\tools\unified_data_tools.py`**
- Propósito: Ferramentas: Ferramentas unificadas para acessar dados de Filial_Madureira.parquet
- Tamanho: 12.12 KB
- Funções: _truncate_df_for_llm, listar_colunas_disponiveis, consultar_dados, buscar_produto, obter_estoque

**`backend\app\core\tools\universal_chart_generator.py`**
- Propósito: Ferramenta Universal de Geração de Gráficos - Context7 2025
- Tamanho: 10.25 KB
- Funções: _export_chart_to_json, gerar_grafico_universal_v2

**`backend\app\core\tools\verify_imports.py`**
- Propósito: Funções: check_import
- Tamanho: 1.19 KB
- Funções: check_import

**`backend\app\core\utils\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 16.00 B

**`backend\app\core\utils\agent_cache.py`**
- Propósito: Agente BI: Agent Cache - Cache em memória para resultados de ferramentas
- Tamanho: 5.97 KB
- Classes: AgentCache
- Funções: get_agent_cache, cached_tool

**`backend\app\core\utils\cache_cleaner.py`**
- Propósito: Sistema Automático de Limpeza de Cache
- Tamanho: 12.13 KB
- Classes: CacheCleaner
- Funções: run_cache_cleanup

**`backend\app\core\utils\chart_saver.py`**
- Propósito: Funções: save_chart
- Tamanho: 1.92 KB
- Funções: save_chart

**`backend\app\core\utils\confidence_scorer.py`**
- Propósito: Confidence Scoring para Respostas LLM
- Tamanho: 7.67 KB
- Classes: ConfidenceScorer
- Funções: get_confidence_scorer

**`backend\app\core\utils\error_handler.py`**
- Propósito: Error Handler - Gerenciamento centralizado de erros.
- Tamanho: 12.48 KB
- Classes: APIError, ErrorContext, ErrorHandler, ParquetErrorHandler
- Funções: handle_error, get_error_stats, error_handler_decorator, create_error_response

**`backend\app\core\utils\error_handler_backup.py`**
- Propósito: Define classes: APIError
- Tamanho: 4.49 KB
- Classes: APIError
- Funções: error_handler_decorator

**`backend\app\core\utils\fast_path_detector.py`**
- Propósito: Funções: detect_fast_path_query
- Tamanho: 3.55 KB
- Funções: detect_fast_path_query

**`backend\app\core\utils\field_mapper.py`**
- Propósito: Define classes: FieldMapper
- Tamanho: 7.05 KB
- Classes: FieldMapper

**`backend\app\core\utils\query_history.py`**
- Propósito: Define classes: QueryHistory
- Tamanho: 8.66 KB
- Classes: QueryHistory

**`backend\app\core\utils\query_validator.py`**
- Propósito: Query Validator - Validador de queries Parquet.
- Tamanho: 11.72 KB
- Classes: QueryTimeout, QueryValidator
- Funções: safe_convert_types, validate_columns, handle_nulls, safe_filter, get_friendly_error

**`backend\app\core\utils\response_cache.py`**
- Propósito: Define classes: ResponseCache
- Tamanho: 6.86 KB
- Classes: ResponseCache

**`backend\app\core\utils\response_parser.py`**
- Propósito: Utilitários para parsear e processar respostas do agente.
- Tamanho: 4.38 KB
- Funções: parse_agent_response, _extract_chart_from_response, detect_dataframe_response

**`backend\app\core\utils\response_validator.py`**
- Propósito: Response Validator - Valida respostas do agente para detectar erros e alucinações
- Tamanho: 8.11 KB
- Classes: ValidationResult, ResponseValidator
- Funções: get_validator, validate_response, validator_stats

**`backend\app\core\utils\semantic_cache.py`**
- Propósito: Semantic Cache - Cache inteligente baseado em similaridade semântica
- Tamanho: 9.86 KB
- Classes: SemanticCache
- Funções: get_semantic_cache, cache_get, cache_set, cache_stats

**`backend\app\core\utils\serializers.py`**
- Propósito: Utilitários de serialização para tipos complexos Python/SQLAlchemy.
- Tamanho: 5.55 KB
- Classes: TypeConverter
- Funções: safe_json_dumps, convert_mapcomposite

**`backend\app\core\utils\session_manager.py`**
- Propósito: Define classes: SessionManager
- Tamanho: 3.08 KB
- Classes: SessionManager

**`backend\app\core\utils\tool_scoping.py`**
- Propósito: Ferramentas: Tool Scoping - Controle de acesso a ferramentas baseado em role do usuário.
- Tamanho: 7.60 KB
- Classes: ToolPermissionManager, DummyTool
- Funções: get_scoped_tools

**`backend\app\core\validators\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 2.00 B

**`backend\app\core\validators\schema_validator.py`**
- Propósito: SchemaValidator - Validador de schemas Parquet.
- Tamanho: 14.19 KB
- Classes: SchemaValidator
- Funções: validate_parquet_schema

**`backend\app\core\visualization\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 24.00 B

**`backend\app\core\visualization\advanced_charts.py`**
- Propósito: Módulo de Gráficos Avançados para Business Intelligence
- Tamanho: 2.95 KB
- Classes: AdvancedChartGenerator

**`backend\app\infrastructure\data\base.py`**
- Propósito: Database Adapter Interface
- Tamanho: 904.00 B
- Classes: DatabaseAdapter

**`backend\app\infrastructure\data\config\column_mapping.py`**
- Propósito: Mapeamento Oficial de Colunas do Parquet
- Tamanho: 9.32 KB
- Funções: normalize_column_name, get_column_info, validate_columns, get_essential_columns, list_all_columns

**`backend\app\infrastructure\data\dependency.py`**
- Propósito: Data Adapter Dependency
- Tamanho: 845.00 B
- Funções: get_data_adapter

**`backend\app\infrastructure\data\duckdb_adapter.py`**
- Propósito: Adaptador de dados: Define classes: DuckDBAdapter
- Tamanho: 11.24 KB
- Classes: DuckDBAdapter

**`backend\app\infrastructure\data\hybrid_adapter.py`**
- Propósito: Adaptador de dados: HybridDataAdapter: Adaptador híbrido com fallback automático e inteligente.
- Tamanho: 5.02 KB
- Classes: HybridDataAdapter

**`backend\app\infrastructure\data\parquet_adapter.py`**
- Propósito: Adaptador de dados: ParquetAdapter: Adaptador para arquivos Parquet.
- Tamanho: 1.18 KB
- Classes: ParquetAdapter

**`backend\app\infrastructure\data\polars_dask_adapter.py`**
- Propósito: Adaptador de dados: PolarsDaskAdapter: Adaptador inteligente que escolhe automaticamente entre Polars e Dask.
- Tamanho: 13.82 KB
- Classes: PolarsDaskAdapter

**`backend\app\infrastructure\data\sql_server_adapter.py`**
- Propósito: Adaptador de dados: SQLServerAdapter: Adaptador para Microsoft SQL Server usando aioodbc (Async).
- Tamanho: 5.30 KB
- Classes: SQLServerAdapter

**`backend\app\infrastructure\data\utils\column_validator.py`**
- Propósito: Sistema Robusto de Validação e Auto-Correção de Colunas
- Tamanho: 11.05 KB
- Classes: ColumnValidationError
- Funções: get_available_columns_cached, validate_column, validate_columns, safe_select_columns, extract_columns_from_query

**`backend\app\infrastructure\data\utils\query_optimizer.py`**
- Propósito: Query Optimizer: Otimizador cirúrgico de queries para evitar saturação de buffer.
- Tamanho: 9.12 KB
- Funções: detect_query_intent, get_optimized_columns, should_use_column_optimization, get_streamlit_height_param, optimize_query_result

**`backend\app\infrastructure\database\migrations\env.py`**
- Propósito: Funções: run_migrations_offline, run_migrations_online
- Tamanho: 1.84 KB
- Funções: run_migrations_offline, run_migrations_online

**`backend\app\infrastructure\database\migrations\versions\fresh_start_migration.py`**
- Propósito: Criar tabelas do zero
- Tamanho: 3.34 KB
- Funções: upgrade, downgrade

**`backend\app\infrastructure\database\models\__init__.py`**
- Propósito: Inicializador de pacote Python
- Tamanho: 626.00 B

**`backend\app\infrastructure\database\models\admmatao.py`**
- Propósito: Define classes: Admmatao
- Tamanho: 4.24 KB
- Classes: Admmatao

**`backend\app\infrastructure\database\models\audit_log.py`**
- Propósito: Audit Log Model
- Tamanho: 1.25 KB
- Classes: AuditLog

**`backend\app\infrastructure\database\models\report.py`**
- Propósito: Report Model
- Tamanho: 1.42 KB
- Classes: Report

**`backend\app\infrastructure\database\models\shared_conversation.py`**
- Propósito: Shared Conversation Model
- Tamanho: 2.58 KB
- Classes: SharedConversation

**`backend\app\infrastructure\database\models\user.py`**
- Propósito: User Model
- Tamanho: 2.16 KB
- Classes: User

**`backend\app\infrastructure\database\models\user_preference.py`**
- Propósito: User Preference Model
- Tamanho: 1.85 KB
- Classes: UserPreference, Keys

**`backend\app\schemas\analytics.py`**
- Propósito: Analytics Schemas
- Tamanho: 1.17 KB
- Classes: AnalyticsFilter, AnalyticsData, AnalyticsMetric, ExportRequest, CustomQueryRequest

**`backend\app\schemas\auth.py`**
- Propósito: Auth Schemas
- Tamanho: 815.00 B
- Classes: Token, TokenData, LoginRequest, RefreshTokenRequest

**`backend\app\schemas\report.py`**
- Propósito: Report Schemas
- Tamanho: 1.38 KB
- Classes: ReportBase, ReportCreate, ReportUpdate, ReportResponse, ReportListResponse

**`backend\app\schemas\user.py`**
- Propósito: User Schemas
- Tamanho: 2.85 KB
- Classes: UserBase, UserCreate, UserUpdate, UserResponse, UserInDB

**`backend\fix_admin_role.py`**
- Propósito: Não identificado
- Tamanho: 1.89 KB

**`backend\fix_supabase_admin.py`**
- Propósito: Script para verificar e corrigir usuário admin no Supabase
- Tamanho: 6.36 KB
- Funções: main

**`backend\fix_supabase_admin_clean.py`**
- Propósito: Script para verificar e corrigir usuário admin no Supabase
- Tamanho: 6.40 KB
- Funções: main

**`backend\scripts\analyze_parquet.py`**
- Propósito: Script para analisar a estrutura do admmat.parquet
- Tamanho: 3.81 KB
- Funções: analyze_parquet_structure

**`backend\scripts\check_admin.py`**
- Propósito: Verificar se usuário admin existe
- Tamanho: 1.76 KB

**`backend\scripts\check_config.py`**
- Propósito: Script Simples de Verificação - Configurações
- Tamanho: 1.47 KB

**`backend\scripts\check_specific_users.py`**
- Propósito: Funções: check_sql, check_parquet
- Tamanho: 1.65 KB
- Funções: check_sql, check_parquet

**`backend\scripts\check_supabase_users.py`**
- Propósito: Funções: check_supabase
- Tamanho: 2.02 KB
- Funções: check_supabase

**`backend\scripts\clean_corrupted_cache.py`**
- Propósito: Script para limpar cache semantic corrompido com erros "Maximum conversation turns exceeded"
- Tamanho: 1.63 KB
- Funções: clean_corrupted_cache

**`backend\scripts\create_dummy_parquet.py`**
- Propósito: Funções: create_dummy_data
- Tamanho: 3.52 KB
- Funções: create_dummy_data

**`backend\scripts\create_parquet_users.py`**
- Propósito: Create users.parquet file for authentication when SQL Server is not available
- Tamanho: 1.81 KB

**`backend\scripts\create_users.py`**
- Propósito: Create users.parquet file for authentication
- Tamanho: 1.66 KB

**`backend\scripts\diagnostico_auth.py`**
- Propósito: Script de Diagnóstico - Autenticação Backend
- Tamanho: 11.49 KB
- Funções: print_header, print_check

**`backend\scripts\init_db.py`**
- Propósito: Script to initialize SQL Server database.
- Tamanho: 1.70 KB
- Funções: create_database

**`backend\scripts\inspect_parquet.py`**
- Propósito: Inspect Parquet Schema
- Tamanho: 832.00 B

**`backend\scripts\list_segments.py`**
- Propósito: Funções: list_segments
- Tamanho: 1.05 KB
- Funções: list_segments

**`backend\scripts\load_data.py`**
- Propósito: Load data from Parquet to SQL Server
- Tamanho: 3.48 KB

**`backend\scripts\seed_admin.py`**
- Propósito: Seed Admin User Script
- Tamanho: 1.90 KB

**`backend\scripts\sync_admmat.py`**
- Propósito: Script de Migração: SQL Server -> Parquet (admmat.parquet)
- Tamanho: 4.23 KB
- Funções: get_row_count, sync_data

**`backend\scripts\sync_sql_to_parquet.py`**
- Propósito: Sync SQL Server to Parquet (Ajustado)
- Tamanho: 1.98 KB
- Funções: sync_data

**`backend\scripts\sync_sql_to_parquet_batch.py`**
- Propósito: Sync SQL Server to Parquet - OTIMIZADO COM BATCHES
- Tamanho: 2.98 KB
- Funções: sync_data

**`backend\scripts\sync_supabase_to_sql.py`**
- Propósito: Funções: sync_users
- Tamanho: 2.80 KB
- Funções: sync_users

**`backend\scripts\update_env.py`**
- Propósito: Atualizar DATABASE_URL no arquivo .env do backend
- Tamanho: 3.45 KB

**`backend\scripts\validate_modernization.py`**
- Propósito: Script de validação rápida das melhorias de modernização.
- Tamanho: 4.34 KB
- Classes: DummyTool

**`backend\scripts\verify_parquet_data.py`**
- Propósito: Script de Verificação de Dados (Data Integrity Check)
- Tamanho: 3.99 KB
- Funções: verify_data

**`backend\tests\manual_benchmark.py`**
- Propósito: Não identificado
- Tamanho: 6.04 KB

**`backend\tests\validate_implementation.py`**
- Propósito: Validation script - checks that all files were created correctly
- Tamanho: 5.27 KB
- Funções: check_file, main

**`scripts\create_users_parquet.py`**
- Propósito: Create users.parquet file with test admin user for authentication fallback
- Tamanho: 1.48 KB
- Funções: create_users_parquet

**`scripts\index_codebase.py`**
- Propósito: Code Indexer - Generate RAG Index for Entire Codebase
- Tamanho: 9.56 KB
- Funções: configure_llamaindex, load_code_documents, create_or_update_index, save_stats, main

**`scripts\kill_port.py`**
- Propósito: Não identificado
- Tamanho: 633.00 B

**`scripts\kill_ports.py`**
- Propósito: Script para liberar portas 8000 e 3000
- Tamanho: 5.47 KB
- Funções: get_pids_on_port, kill_process, kill_port, kill_python_processes, main

**`scripts\legacy_tests\reproduce_gemini_error.py`**
- Propósito: Não identificado
- Tamanho: 1.55 KB

### Categoria: temp

**`backend\logs\api\api.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 2.93 MB

**`backend\logs\app\app.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 649.37 KB

**`backend\logs\audit\audit.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 148.16 KB

**`backend\logs\chat\chat.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 0.00 B

**`backend\logs\errors\critical.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 399.91 KB

**`backend\logs\errors\errors.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 484.39 KB

**`backend\logs\security\security.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 111.91 KB

**`backend\test_login_debug.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 570.00 B

**`logs\api\api.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 941.00 B

**`logs\app\app.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 8.11 KB

**`logs\audit\audit.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 0.00 B

**`logs\backend.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 363.90 KB

**`logs\chat\chat.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 0.00 B

**`logs\errors\critical.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 1.42 KB

**`logs\errors\errors.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 0.00 B

**`logs\security\security.log`**
- Propósito: Arquivo temporário (pode ser excluído)
- Tamanho: 0.00 B

### Categoria: test

**`backend\app\api\v1\endpoints\test.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 450.00 B

**`backend\scripts\seed_test_user.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.10 KB

**`backend\scripts\test_continuous_learning.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 7.71 KB
- Funções: print_section

**`backend\scripts\test_db_connection_headless.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 3.57 KB

**`backend\scripts\test_graph_fix.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 3.10 KB

**`backend\scripts\test_integration.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 4.55 KB

**`backend\scripts\test_login.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 947.00 B

**`backend\scripts\test_product_analysis_fix.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 4.27 KB

**`backend\scripts\test_windows_auth.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 1.73 KB
- Funções: test_windows_auth

**`backend\test_chart_tools.py`**
- Propósito: Ferramentas: Testes unitários (1 testes)
- Tamanho: 1.68 KB
- Funções: test_chart_tool

**`backend\test_supabase_login.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 3.94 KB

**`backend\tests\conftest.py`**
- Propósito: Testes unitários (2 testes)
- Tamanho: 923.00 B
- Funções: admin_token, user_token

**`backend\tests\integration\test_auth.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 1.60 KB

**`backend\tests\integration\test_chat_endpoint.py`**
- Propósito: Endpoints API: Testes unitários (1 testes)
- Tamanho: 8.71 KB
- Funções: mock_dependencies

**`backend\tests\integration\test_transfers_endpoint.py`**
- Propósito: Endpoints API: Testes unitários (9 testes)
- Tamanho: 7.40 KB
- Funções: mock_auth_and_tools, clean_transfer_requests_dir, test_validate_transfer_success, test_validate_transfer_invalid_payload, test_get_transfer_suggestions_success

**`backend\tests\manual\test_filters.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 5.31 KB
- Funções: test_filters

**`backend\tests\test_all_phases.py`**
- Propósito: Testes unitários (2 testes)
- Tamanho: 11.57 KB
- Classes: TestRunner, MockAgent
- Funções: print_header, print_result

**`backend\tests\test_changes.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 8.96 KB
- Classes: TestTransferFiltersUI, TestChatBIResponses, TestIntegration

**`backend\tests\test_chatbi_complete.py`**
- Propósito: Testes unitários (6 testes)
- Tamanho: 5.77 KB
- Funções: test_1_imports, test_2_model_config, test_3_flexible_tool, test_4_agent_tools, test_5_parquet_config

**`backend\tests\test_system.py`**
- Propósito: Testes unitários (11 testes)
- Tamanho: 10.18 KB
- Funções: print_header, print_success, print_error, print_warning, test_backend_health

**`backend\tests\test_tool_modernization.py`**
- Propósito: Ferramentas: Testes unitários (2 testes)
- Tamanho: 8.52 KB
- Classes: TestChartToolsConsolidation, TestSemanticSearch, TestToolScoping, TestAgentIntegration, DummyTool
- Funções: pytest_addoption, pytest_configure

**`backend\tests\unit\test_agent_graph_cache.py`**
- Propósito: Agente BI: Testes unitários (10 testes)
- Tamanho: 5.12 KB
- Funções: temp_agent_graph_cache_dir, mock_settings, test_agent_graph_cache_init, test_get_current_version, test_set_and_get_cache_hit

**`backend\tests\unit\test_caculinha_bi_agent.py`**
- Propósito: Agente BI: Testes unitários (4 testes)
- Tamanho: 7.12 KB
- Classes: MockLLM
- Funções: mock_llm, mock_field_mapper, mock_code_gen_agent, caculinha_bi_agent

**`backend\tests\unit\test_code_gen_agent.py`**
- Propósito: Agente BI: Testes unitários (7 testes)
- Tamanho: 9.08 KB
- Classes: MockLLM
- Funções: mock_llm, mock_field_mapper, mock_query_retriever, mock_pattern_matcher, mock_response_cache

**`backend\tests\unit\test_learning.py`**
- Propósito: Testes unitários (4 testes)
- Tamanho: 1.98 KB
- Funções: test_get_insights_success, test_get_insights_unauthorized, test_get_insights_types, test_get_insights_with_admin

**`backend\tests\unit\test_response_cache.py`**
- Propósito: Testes unitários (10 testes)
- Tamanho: 3.94 KB
- Funções: temp_cache_dir, mock_settings, test_response_cache_init, test_generate_key, test_normalize_query

**`backend\tests\unit\test_transfers.py`**
- Propósito: Testes unitários (5 testes)
- Tamanho: 2.65 KB
- Funções: test_get_transfers_success, test_get_transfers_with_limit, test_get_transfers_unauthorized, test_get_transfers_data_quality, test_get_transfers_with_admin

**`backend\tests\unit\test_une_tools.py`**
- Propósito: Ferramentas: Testes unitários (16 testes)
- Tamanho: 8.97 KB
- Classes: MockHybridAdapter
- Funções: mock_hybrid_adapter, test_normalize_dataframe, test_load_data_basic_filter, test_load_data_with_columns, test_calcular_abastecimento_une_urgente

**`scripts\create_supabase_test_user.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.27 KB

**`scripts\create_test_user.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 1.15 KB
- Funções: create_test_user

**`scripts\legacy_tests\test_chat_robust.py`**
- Propósito: Testes unitários (3 testes)
- Tamanho: 25.37 KB
- Classes: Colors, ChatTester, CodeChatTester
- Funções: login, test_semantic_cache, main

**`scripts\legacy_tests\test_code_chat.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 788.00 B

**`scripts\legacy_tests\test_critical_fixes.py`**
- Propósito: Testes unitários (4 testes)
- Tamanho: 6.15 KB
- Funções: test_empty_query, test_complex_query, test_cache, main

**`scripts\legacy_tests\test_diagnostics.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.22 KB

**`scripts\legacy_tests\test_kpis.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 1005.00 B

**`scripts\legacy_tests\test_sql_connection.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 10.42 KB
- Funções: check_port

**`scripts\signup_test_user.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 2.15 KB
- Funções: signup_test_user

**`scripts\test_llm_v3.py`**
- Propósito: Testes unitários (1 testes)
- Tamanho: 1.77 KB
- Funções: test_v3_connection

**`tests\test_agent_comprehensive.py`**
- Propósito: Agente BI: Testes unitários (0 testes)
- Tamanho: 7.75 KB

**`tests\test_agent_quick.py`**
- Propósito: Agente BI: Testes unitários (0 testes)
- Tamanho: 4.21 KB

**`tests\test_chat_interactions.py`**
- Propósito: Testes unitários (3 testes)
- Tamanho: 2.36 KB
- Funções: get_token, ask, main

**`tests\test_duckdb_performance.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.67 KB

**`tests\test_extreme_performance.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.52 KB

**`tests\test_graph_vs_text.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.83 KB

**`tests\test_performance_v2.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 2.71 KB

**`tests\test_rls_data_manager.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 1.27 KB

**`tests\test_textual_analysis.py`**
- Propósito: Testes unitários (0 testes)
- Tamanho: 6.97 KB

### Categoria: test_orphan

**`test_agent_http.py`**
- Propósito: Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (3 testes)
- Tamanho: 5.36 KB
- Funções: login, test_query, main

**`test_agent_intelligence.py`**
- Propósito: Agente BI: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- Tamanho: 5.56 KB

**`test_final_fix.py`**
- Propósito: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- Tamanho: 3.48 KB

**`test_oxford_direct.py`**
- Propósito: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- Tamanho: 2.25 KB

**`test_query_oxford.py`**
- Propósito: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- Tamanho: 2.49 KB

**`test_query_oxford_simple.py`**
- Propósito: [SCRIPT DE TESTE NA RAIZ] Testes unitários (0 testes)
- Tamanho: 1.99 KB

### Categoria: unknown

**`.gitattributes`**
- Propósito: Não identificado
- Tamanho: 47.00 B

**`Taskfile.yml`**
- Propósito: Não identificado
- Tamanho: 5.90 KB

**`backend\...backend-log.txt`**
- Propósito: Não identificado
- Tamanho: 94.00 B

**`backend\.env.example`**
- Propósito: Não identificado
- Tamanho: 1.88 KB

**`backend\.env.supabase`**
- Propósito: Não identificado
- Tamanho: 438.00 B

**`backend\alembic.ini`**
- Propósito: Não identificado
- Tamanho: 766.00 B

**`backend\app\api\v1\endpoints\chat.py.backup`**
- Propósito: Não identificado
- Tamanho: 8.01 KB

**`backend\app\core\prompts\chart_system_prompt.txt`**
- Propósito: Não identificado
- Tamanho: 4.70 KB

**`backend\app\data\sessions\.json`**
- Propósito: Não identificado
- Tamanho: 947.00 B

**`backend\app\infrastructure\database\migrations\script.py.mako`**
- Propósito: Não identificado
- Tamanho: 661.00 B

**`backend\app\templates\login.html`**
- Propósito: Não identificado
- Tamanho: 1.09 KB

**`backend\data\cache\semantic\cache_files.txt`**
- Propósito: Não identificado
- Tamanho: 0.00 B

**`backend\install_missing_deps.bat`**
- Propósito: Não identificado
- Tamanho: 3.74 KB

**`backend\migrations\create_new_tables.sql`**
- Propósito: Não identificado
- Tamanho: 2.29 KB

**`backend\requirements-code-chat.txt`**
- Propósito: Não identificado
- Tamanho: 517.00 B

**`backend\requirements-docker.txt`**
- Propósito: Não identificado
- Tamanho: 4.06 KB

**`cleanup.bat`**
- Propósito: Não identificado
- Tamanho: 2.28 KB

**`data\learning\error_log_20251108.jsonl`**
- Propósito: Não identificado
- Tamanho: 4.72 KB

**`data\learning\error_log_20251109.jsonl`**
- Propósito: Não identificado
- Tamanho: 24.96 KB

**`data\learning\error_log_20251207.jsonl`**
- Propósito: Não identificado
- Tamanho: 6.12 KB

**`data\learning\successful_queries_20251108.jsonl`**
- Propósito: Não identificado
- Tamanho: 33.52 KB

**`data\learning\successful_queries_20251109.jsonl`**
- Propósito: Não identificado
- Tamanho: 86.84 KB

**`data\learning\successful_queries_20251111.jsonl`**
- Propósito: Não identificado
- Tamanho: 8.90 KB

**`data\learning\successful_queries_20251116.jsonl`**
- Propósito: Não identificado
- Tamanho: 5.05 KB

**`data\learning\successful_queries_20251120.jsonl`**
- Propósito: Não identificado
- Tamanho: 23.40 KB

**`data\learning\successful_queries_20251122.jsonl`**
- Propósito: Não identificado
- Tamanho: 5.81 KB

**`docs\ARQUITETURA_VISUAL.html`**
- Propósito: Não identificado
- Tamanho: 3.81 KB

**`docs\archive\test_results.txt`**
- Propósito: Não identificado
- Tamanho: 10.00 KB

**`docs\queries\validacao_ranking_rls.sql`**
- Propósito: Não identificado
- Tamanho: 3.60 KB

**`docs\troubleshooting\SOLUCAO_ERRO_LOGIN.txt`**
- Propósito: Não identificado
- Tamanho: 3.31 KB

**`frontend-solid\eslint.config.mjs`**
- Propósito: Não identificado
- Tamanho: 318.00 B

**`frontend-solid\index.html`**
- Propósito: Não identificado
- Tamanho: 317.00 B

**`frontend-solid\pnpm-lock.yaml`**
- Propósito: Não identificado
- Tamanho: 148.88 KB

**`frontend-solid\postcss.config.mjs`**
- Propósito: Não identificado
- Tamanho: 75.00 B

**`frontend-solid\public\banner-cacula.png`**
- Propósito: Não identificado
- Tamanho: 8.50 KB

**`frontend-solid\public\clear-cache.html`**
- Propósito: Não identificado
- Tamanho: 7.52 KB

**`frontend-solid\public\clear-session.html`**
- Propósito: Não identificado
- Tamanho: 4.08 KB

**`frontend-solid\public\diagnostico.html`**
- Propósito: Não identificado
- Tamanho: 11.71 KB

**`frontend-solid\public\logo-cacula.svg`**
- Propósito: Não identificado
- Tamanho: 14.37 KB

**`frontend-solid\src\components\TypingIndicator.css`**
- Propósito: Não identificado
- Tamanho: 681.00 B

**`frontend-solid\src\index.css`**
- Propósito: Não identificado
- Tamanho: 7.89 KB

**`frontend-solid\src\index.tsx.backup`**
- Propósito: Não identificado
- Tamanho: 5.62 KB

**`frontend-solid\src\migrated-components\globals.css`**
- Propósito: Não identificado
- Tamanho: 2.01 KB

**`frontend-solid\src\pages\chat-markdown.css`**
- Propósito: Não identificado
- Tamanho: 3.28 KB

**`frontend-solid\test.html`**
- Propósito: Não identificado
- Tamanho: 2.66 KB

**`pnpm-lock.yaml`**
- Propósito: Não identificado
- Tamanho: 6.80 KB

**`restore.bat`**
- Propósito: Não identificado
- Tamanho: 1.36 KB

**`scripts\create_supabase_users.sql`**
- Propósito: Não identificado
- Tamanho: 3.00 KB

**`scripts\create_user_profiles.sql`**
- Propósito: Não identificado
- Tamanho: 1.99 KB

**`scripts\insert_user_profiles.sql`**
- Propósito: Não identificado
- Tamanho: 1.46 KB

**`scripts\legacy_tests\diagnostico_sql_server.bat`**
- Propósito: Não identificado
- Tamanho: 2.42 KB

**`scripts\utils\HARD_RESET_LOGIN.bat`**
- Propósito: Não identificado
- Tamanho: 823.00 B

**`scripts\utils\RESET_LOGIN.ps1`**
- Propósito: Não identificado
- Tamanho: 1.04 KB

**`scripts\utils\add_nodejs_to_path.ps1`**
- Propósito: Não identificado
- Tamanho: 2.61 KB

**`scripts\utils\kill_python.bat`**
- Propósito: Não identificado
- Tamanho: 169.00 B

**`scripts\utils\run-with-logs.bat`**
- Propósito: Não identificado
- Tamanho: 2.21 KB

**`scripts\utils\run.ps1`**
- Propósito: Não identificado
- Tamanho: 3.85 KB

**`scripts\utils\run_backend_only.ps1`**
- Propósito: Não identificado
- Tamanho: 1.90 KB

**`scripts\utils\start_system.ps1`**
- Propósito: Não identificado
- Tamanho: 3.70 KB

**`scripts\utils\validate_changes.ps1`**
- Propósito: Não identificado
- Tamanho: 8.78 KB

**`tests\verify_run_bat.ps1`**
- Propósito: Não identificado
- Tamanho: 3.15 KB


---

*Relatório gerado em 28/12/2025 às 15:18:29*
