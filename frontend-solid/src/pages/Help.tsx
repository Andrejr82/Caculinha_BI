import { createSignal, For, Show } from 'solid-js';
import { HelpCircle, Book, AlertCircle, Database, Search, ChevronDown, ChevronUp, Sparkles, TrendingUp, BarChart3, Truck } from 'lucide-solid';
import auth from '@/store/auth';

type TabType = 'guia' | 'faq' | 'troubleshooting' | 'dados';

interface FAQItem {
  pergunta: string;
  resposta: string;
}

interface TroubleshootingItem {
  problema: string;
  solucao: string[];
}

export default function Help() {
  const [activeTab, setActiveTab] = createSignal<TabType>('guia');
  const [searchTerm, setSearchTerm] = createSignal('');
  const [expandedFAQ, setExpandedFAQ] = createSignal<number | null>(null);
  
  const isAdmin = () => auth.user()?.role === 'admin';

  const FAQ_ITEMS: FAQItem[] = [
    {
      pergunta: 'Como faço para consultar produtos em ruptura?',
      resposta: 'Navegue até a página "Rupturas" no menu Dashboards. O sistema identifica rupturas quando um produto possui histórico de vendas positivo mas o estoque atual está zerado ou abaixo de 5 dias de cobertura. Você pode filtrar por Segmento ou Categoria.'
    },
    {
      pergunta: 'Como solicitar uma transferência de estoque?',
      resposta: 'Acesse a página "Transferências" no menu Operacional. O sistema sugere transferências do CD (Centro de Distribuição) para as Lojas quando detecta que a loja está com estoque crítico e o CD possui saldo parado.'
    },
    {
      pergunta: 'O que é Cobertura de Estoque e como ela é calculada?',
      resposta: 'A Cobertura representa quantos dias o seu estoque atual irá durar com base na média de vendas dos últimos 30 dias. O ideal para o varejo de armarinhos é entre 15 a 30 dias. Menos de 5 dias é considerado Risco de Ruptura.'
    },
    {
      pergunta: 'Como funciona a Curva ABC (Pareto) neste sistema?',
      resposta: 'A Curva ABC classifica os produtos por contribuição de Receita (Pareto): Classe A (80% da receita), Classe B (15% da receita) e Classe C (5% finais). Isso ajuda a focar a gestão nos itens que realmente sustentam o faturamento.'
    },
    {
      pergunta: 'O que são os "AI Insights" no Dashboard?',
      resposta: 'São análises proativas geradas pelo Gemini 3.0 Flash que cruzam dados de venda, estoque e crescimento. A IA identifica anomalias (como o TNT sem estoque na loja mas com 16 mil unidades no CD) e sugere planos de ação imediatos.'
    },
    {
      pergunta: 'Posso exportar dados para Excel?',
      resposta: 'Sim! Gráficos e tabelas possuem botões de download. No Chat BI, você pode solicitar "Exportar para CSV" e o sistema gerará um link para download dos dados analisados.'
    },
    {
      pergunta: 'Qual a diferença entre "Metrics" e "Analytics"?',
      resposta: 'Metrics exibe KPIs de performance do sistema (tempo de resposta da IA, hits de cache). Analytics exibe o desempenho do negócio (Curva de Pareto, Giro de Estoque, Ranking de Categorias).'
    },
    {
      pergunta: 'Como o Chat BI entende meus dados?',
      resposta: 'O Chat utiliza um adaptador do Gemini integrado ao nosso banco de dados Parquet. Ele "lê" as colunas de venda e estoque em tempo real e aplica regras de negócio específicas da Caçula para responder suas perguntas.'
    },
    {
      pergunta: 'Administradores podem gerenciar usuários e segmentos?',
      resposta: 'Sim. Usuários Admin podem definir quais segmentos cada usuário pode visualizar (ex: Tecidos, Armarinho, Papelaria). Isso garante que cada gestor veja apenas o que é relevante para sua área.'
    },
    {
      pergunta: 'O sistema utiliza dados em tempo real?',
      resposta: 'O sistema utiliza uma arquitetura híbrida. Os dados são sincronizados do SQL Server para arquivos Parquet de alta performance para garantir que as análises de IA e gráficos sejam instantâneos, mesmo com milhões de registros.'
    }
  ];

  const TROUBLESHOOTING_ITEMS: TroubleshootingItem[] = [
    {
      problema: 'Chat BI não está respondendo ou apresenta erro de modelo',
      solucao: [
        'Verifique se o backend está ativo e a chave do Gemini configurada',
        'Confirme sua conexão com a internet',
        'Tente reformular a pergunta de forma mais clara',
        'Verifique se o serviço do Google AI está disponível na sua região'
      ]
    },
    {
      problema: 'Dados de vendas ou estoque parecem desatualizados',
      solucao: [
        'Clique no botão "Atualizar" no Dashboard',
        'Admins podem forçar uma nova sincronização SQL → Parquet',
        'Verifique o campo "Última Atualização" no rodapé das páginas'
      ]
    },
    {
      problema: 'Não vejo o segmento de Tecidos (ou outro específico)',
      solucao: [
        'Verifique suas permissões em Perfil > Segmentos Permitidos',
        'Solicite ao Administrador para liberar o acesso ao segmento desejado',
        'Somente administradores possuem "Visão Global" de todos os segmentos'
      ]
    }
  ];

  const filteredFAQ = () => {
    if (!searchTerm()) return FAQ_ITEMS;
    const term = searchTerm().toLowerCase();
    return FAQ_ITEMS.filter(item =>
      item.pergunta.toLowerCase().includes(term) ||
      item.resposta.toLowerCase().includes(term)
    );
  };

  return (
    <div class="flex flex-col h-full p-6 gap-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 class="text-3xl font-bold flex items-center gap-3">
            <HelpCircle size={32} class="text-primary" />
            Central de Ajuda & Documentação
          </h2>
          <p class="text-muted-foreground mt-1">Guia completo para extrair o máximo do Agente BI Caçula</p>
        </div>
      </div>

      {/* Tabs Layout */}
      <div class="flex flex-col lg:flex-row gap-8 mt-4">
        {/* Sidebar Nav */}
        <div class="lg:w-64 flex-shrink-0">
          <div class="flex flex-col gap-1 sticky top-6">
            <button
              onClick={() => setActiveTab('guia')}
              class={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab() === 'guia' ? 'bg-primary text-white shadow-md' : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <Book size={20} />
              <span class="font-bold">Guia Rápido</span>
            </button>
            <button
              onClick={() => setActiveTab('faq')}
              class={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab() === 'faq' ? 'bg-primary text-white shadow-md' : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <HelpCircle size={20} />
              <span class="font-bold">FAQ</span>
            </button>
            <Show when={isAdmin()}>
              <button
                onClick={() => setActiveTab('troubleshooting')}
                class={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  activeTab() === 'troubleshooting' ? 'bg-primary text-white shadow-md' : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                <AlertCircle size={20} />
                <span class="font-bold">Troubleshooting</span>
              </button>
              <button
                onClick={() => setActiveTab('dados')}
                class={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  activeTab() === 'dados' ? 'bg-primary text-white shadow-md' : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                <Database size={20} />
                <span class="font-bold">Schema de Dados</span>
              </button>
            </Show>
          </div>
        </div>

        {/* Main Content Area */}
        <div class="flex-1">
          {/* Tab: Guia Rápido */}
          <Show when={activeTab() === 'guia'}>
            <div class="space-y-8 animate-in fade-in duration-500">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="card p-6 border bg-blue-50/50 dark:bg-blue-900/10">
                  <Sparkles size={24} class="text-blue-500 mb-4" />
                  <h4 class="font-bold mb-2">IA Generativa</h4>
                  <p class="text-xs text-muted-foreground leading-relaxed">
                    O Gemini analisa milhões de linhas de estoque para encontrar oportunidades que o olho humano não veria de forma rápida.
                  </p>
                </div>
                <div class="card p-6 border bg-green-50/50 dark:bg-green-900/10">
                  <BarChart3 size={24} class="text-green-500 mb-4" />
                  <h4 class="font-bold mb-2">Pareto ABC</h4>
                  <p class="text-xs text-muted-foreground leading-relaxed">
                    Foque no que importa. 80% do seu faturamento vem de apenas 20% do seu mix. Nossa análise identifica esses itens Classe A.
                  </p>
                </div>
                <div class="card p-6 border bg-amber-50/50 dark:bg-amber-900/10">
                  <Truck size={24} class="text-amber-500 mb-4" />
                  <h4 class="font-bold mb-2">Logística Reversa</h4>
                  <p class="text-xs text-muted-foreground leading-relaxed">
                    Sugestões automáticas de transferência entre CD e Lojas para evitar capital imobilizado e rupturas de venda.
                  </p>
                </div>
              </div>

              <div class="card p-8 border">
                <h3 class="text-xl font-bold mb-6 flex items-center gap-2">
                  <TrendingUp size={24} class="text-primary" />
                  Fluxo de Trabalho Recomendado
                </h3>
                <div class="space-y-6 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-muted">
                  <div class="relative pl-10">
                    <div class="absolute left-0 top-0 w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold">1</div>
                    <h5 class="font-bold">Analise o AI Insights</h5>
                    <p class="text-sm text-muted-foreground">No Dashboard, veja as sugestões proativas da IA sobre riscos e oportunidades.</p>
                  </div>
                  <div class="relative pl-10">
                    <div class="absolute left-0 top-0 w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold">2</div>
                    <h5 class="font-bold">Monitore a Cobertura</h5>
                    <p class="text-sm text-muted-foreground">Mantenha seus produtos Classe A com cobertura entre 15 e 30 dias para otimizar o ROI.</p>
                  </div>
                  <div class="relative pl-10">
                    <div class="absolute left-0 top-0 w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold">3</div>
                    <h5 class="font-bold">Use o Chat para Aprofundar</h5>
                    <p class="text-sm text-muted-foreground">Pergunte: "Por que o produto X está vendendo menos este mês?" ou "Compare o giro de Tecidos vs Armarinho".</p>
                  </div>
                </div>
              </div>
            </div>
          </Show>

          {/* Tab: FAQ */}
          <Show when={activeTab() === 'faq'}>
            <div class="space-y-4 animate-in slide-in-from-right-4 duration-300">
              <div class="relative mb-6">
                <Search size={20} class="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  class="w-full pl-12 pr-4 py-4 bg-card border rounded-2xl focus:ring-2 focus:ring-primary outline-none shadow-sm"
                  placeholder="Busque por termos como: ABC, Ruptura, Gemini, Transferência..."
                  value={searchTerm()}
                  onInput={(e) => setSearchTerm(e.currentTarget.value)}
                />
              </div>

              <div class="space-y-3">
                <For each={filteredFAQ()}>
                  {(item, index) => (
                    <div class="card border rounded-2xl overflow-hidden hover:border-primary/50 transition-colors">
                      <button
                        onClick={() => setExpandedFAQ(expandedFAQ() === index() ? null : index())}
                        class="w-full p-5 text-left flex items-center justify-between"
                      >
                        <span class="font-bold text-gray-800 dark:text-gray-200">{item.pergunta}</span>
                        <Show when={expandedFAQ() === index()} fallback={<ChevronDown size={20} />}>
                          <ChevronUp size={20} class="text-primary" />
                        </Show>
                      </button>
                      <Show when={expandedFAQ() === index()}>
                        <div class="px-5 pb-5 text-sm text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-top-2">
                          <div class="h-px bg-muted mb-4"></div>
                          {item.resposta}
                        </div>
                      </Show>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </Show>

          {/* Tab: Troubleshooting */}
          <Show when={activeTab() === 'troubleshooting' && isAdmin()}>
            <div class="space-y-4 animate-in fade-in">
              <For each={TROUBLESHOOTING_ITEMS}>
                {(item) => (
                  <div class="card p-6 border-l-4 border-l-red-500">
                    <h4 class="font-bold text-lg mb-4 flex items-center gap-2">
                      <AlertCircle size={20} class="text-red-500" />
                      {item.problema}
                    </h4>
                    <ul class="space-y-2">
                      <For each={item.solucao}>
                        {(sol) => (
                          <li class="text-sm text-muted-foreground flex items-start gap-2">
                            <div class="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0"></div>
                            {sol}
                          </li>
                        )}
                      </For>
                    </ul>
                  </div>
                )}
              </For>
            </div>
          </Show>

          {/* Tab: Schema de Dados */}
          <Show when={activeTab() === 'dados' && isAdmin()}>
            <div class="card p-8 border space-y-6 animate-in zoom-in-95">
              <div class="flex items-center gap-3 border-b pb-4">
                <Database size={28} class="text-primary" />
                <h3 class="text-xl font-bold">Dicionário de Dados do Negócio</h3>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h5 class="font-bold text-sm uppercase tracking-wider text-muted-foreground mb-4">Identificadores e Categorização</h5>
                  <div class="space-y-3">
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">PRODUTO</code>
                      <span class="text-muted-foreground">Código SKU (ID Único)</span>
                    </div>
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">UNE</code>
                      <span class="text-muted-foreground">Unidade de Negócio (Loja)</span>
                    </div>
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">NOMESEGMENTO</code>
                      <span class="text-muted-foreground">Segmento (Tecidos, Papelaria...)</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h5 class="font-bold text-sm uppercase tracking-wider text-muted-foreground mb-4">Métricas de Estoque e Venda</h5>
                  <div class="space-y-3">
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">VENDA_30DD</code>
                      <span class="text-muted-foreground">Volume vendido nos últimos 30 dias</span>
                    </div>
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">MES_01</code>
                      <span class="text-muted-foreground">Faturamento do mês atual</span>
                    </div>
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">ESTOQUE_UNE</code>
                      <span class="text-muted-foreground">Estoque disponível na Loja</span>
                    </div>
                    <div class="flex justify-between text-sm border-b pb-1">
                      <code class="text-primary">ESTOQUE_CD</code>
                      <span class="text-muted-foreground">Estoque disponível no CD</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-8 p-4 bg-muted/30 rounded-xl text-xs text-muted-foreground">
                <p><strong>Nota:</strong> As métricas de Cobertura e Pareto ABC são calculadas dinamicamente pelo backend utilizando a biblioteca Polars para máxima precisão.</p>
              </div>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
}