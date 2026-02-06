import { createSignal, For, Show } from 'solid-js';
import { Search, MessageSquare, TrendingUp, Package, DollarSign, AlertTriangle, BarChart3 } from 'lucide-solid';
import { useNavigate } from '@solidjs/router';

interface ExampleQuery {
  id: number;
  categoria: string;
  pergunta: string;
  icone: any;
}

const CATEGORIAS = [
  { nome: 'Todas', icone: MessageSquare },
  { nome: 'Vendas', icone: TrendingUp },
  { nome: 'Estoque', icone: Package },
  { nome: 'Produtos', icone: BarChart3 },
  { nome: 'Rupturas', icone: AlertTriangle },
];

// Perguntas baseadas nas colunas REAIS do admmat.parquet:
// UNE, PRODUTO, NOME, UNE_NOME, NOMESEGMENTO, NOMECATEGORIA, NOMEFABRICANTE,
// ESTOQUE_UNE, ESTOQUE_LV, ESTOQUE_CD, VENDA_30DD, PRECO_VENDA, SITUACAO
const EXAMPLE_QUERIES: ExampleQuery[] = [
  // Categoria: Vendas (baseado em VENDA_30DD)
  { id: 1, categoria: 'Vendas', pergunta: 'Quais os 10 produtos com maior VENDA_30DD?', icone: TrendingUp },
  { id: 2, categoria: 'Vendas', pergunta: 'Qual o total de vendas da UNE 261?', icone: TrendingUp },
  { id: 3, categoria: 'Vendas', pergunta: 'Mostre vendas agrupadas por NOMESEGMENTO', icone: TrendingUp },
  { id: 4, categoria: 'Vendas', pergunta: 'Quais UNEs têm maior volume de VENDA_30DD?', icone: TrendingUp },
  { id: 5, categoria: 'Vendas', pergunta: 'Liste produtos sem vendas nos últimos 30 dias', icone: TrendingUp },

  // Categoria: Estoque (baseado em ESTOQUE_UNE, ESTOQUE_LV, ESTOQUE_CD)
  { id: 6, categoria: 'Estoque', pergunta: 'Quais produtos têm ESTOQUE_UNE abaixo de 10?', icone: Package },
  { id: 7, categoria: 'Estoque', pergunta: 'Mostre o total de ESTOQUE_UNE por UNE', icone: Package },
  { id: 8, categoria: 'Estoque', pergunta: 'Liste produtos com ESTOQUE_UNE zerado', icone: Package },
  { id: 9, categoria: 'Estoque', pergunta: 'Qual o estoque do CD (ESTOQUE_CD) por segmento?', icone: Package },
  { id: 10, categoria: 'Estoque', pergunta: 'Produtos com ESTOQUE_UNE acima de 1000', icone: Package },

  // Categoria: Produtos (baseado em NOMEFABRICANTE, NOMESEGMENTO, NOMECATEGORIA)
  { id: 11, categoria: 'Produtos', pergunta: 'Quais produtos são do NOMEFABRICANTE igual a NESTLE?', icone: BarChart3 },
  { id: 12, categoria: 'Produtos', pergunta: 'Liste produtos do NOMESEGMENTO HIGIENE', icone: BarChart3 },
  { id: 13, categoria: 'Produtos', pergunta: 'Mostre a quantidade de produtos por NOMECATEGORIA', icone: BarChart3 },
  { id: 14, categoria: 'Produtos', pergunta: 'Quais fabricantes têm mais produtos cadastrados?', icone: BarChart3 },
  { id: 15, categoria: 'Produtos', pergunta: 'Liste as UNE_NOME disponíveis no sistema', icone: BarChart3 },

  // Categoria: Rupturas (baseado em comparação ESTOQUE_UNE vs ESTOQUE_LV)
  { id: 16, categoria: 'Rupturas', pergunta: 'Produtos com ESTOQUE_UNE abaixo da linha verde (ESTOQUE_LV)', icone: AlertTriangle },
  { id: 17, categoria: 'Rupturas', pergunta: 'Quais UNEs têm mais produtos em ruptura?', icone: AlertTriangle },
  { id: 18, categoria: 'Rupturas', pergunta: 'Liste rupturas críticas do NOMESEGMENTO ALIMENTOS', icone: AlertTriangle },
  { id: 19, categoria: 'Rupturas', pergunta: 'Produtos da UNE 261 com estoque zerado', icone: AlertTriangle },
  { id: 20, categoria: 'Rupturas', pergunta: 'Sugira transferências para resolver rupturas', icone: AlertTriangle },
];

export default function Examples() {
  const navigate = useNavigate();
  const [categoriaAtiva, setCategoriaAtiva] = createSignal('Todas');
  const [searchTerm, setSearchTerm] = createSignal('');

  const perguntasFiltradas = () => {
    let perguntas = EXAMPLE_QUERIES;

    if (categoriaAtiva() !== 'Todas') {
      perguntas = perguntas.filter(q => q.categoria === categoriaAtiva());
    }

    if (searchTerm()) {
      const term = searchTerm().toLowerCase();
      perguntas = perguntas.filter(q => q.pergunta.toLowerCase().includes(term));
    }

    return perguntas;
  };

  const handleTestarPergunta = (pergunta: string) => {
    localStorage.setItem('example_query', pergunta);
    navigate('/chat');
  };

  return (
    <div class="flex flex-col h-full p-6 gap-6">
      {/* Header */}
      <div>
        <h2 class="text-2xl font-bold flex items-center gap-2">
          <MessageSquare size={28} />
          Exemplos de Perguntas
        </h2>
        <p class="text-muted-foreground text-sm">
          Perguntas baseadas nas colunas reais: VENDA_30DD, ESTOQUE_UNE, NOMEFABRICANTE, etc.
        </p>
      </div>

      {/* Search */}
      <div class="relative">
        <Search size={20} class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          class="w-full pl-10 pr-4 py-3 bg-card border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="Buscar perguntas..."
          value={searchTerm()}
          onInput={(e) => setSearchTerm(e.currentTarget.value)}
        />
      </div>

      {/* Categories */}
      <div class="flex gap-2 flex-wrap">
        <For each={CATEGORIAS}>
          {(cat) => {
            const Icon = cat.icone;
            return (
              <button
                onClick={() => setCategoriaAtiva(cat.nome)}
                class={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  categoriaAtiva() === cat.nome
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
              >
                <Icon size={16} />
                {cat.nome}
              </button>
            );
          }}
        </For>
      </div>

      {/* Results */}
      <div class="text-sm text-muted-foreground">
        {perguntasFiltradas().length} perguntas
      </div>

      {/* Grid */}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-auto">
        <For each={perguntasFiltradas()}>
          {(query) => {
            const Icon = query.icone;
            return (
              <div 
                class="card p-4 border hover:border-primary/50 transition-all cursor-pointer group"
                onClick={() => handleTestarPergunta(query.pergunta)}
              >
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-primary/10 text-primary rounded-lg">
                    <Icon size={20} />
                  </div>
                  <div class="flex-1">
                    <div class="text-xs text-muted-foreground mb-1">{query.categoria}</div>
                    <p class="text-sm">{query.pergunta}</p>
                  </div>
                </div>
              </div>
            );
          }}
        </For>
      </div>

      <Show when={perguntasFiltradas().length === 0}>
        <div class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <Search size={48} class="mx-auto mb-4 opacity-20" />
            <p class="text-muted-foreground">Nenhuma pergunta encontrada</p>
            <button
              onClick={() => {
                setSearchTerm('');
                setCategoriaAtiva('Todas');
              }}
              class="btn btn-outline mt-4"
            >
              Limpar Filtros
            </button>
          </div>
        </div>
      </Show>
    </div>
  );
}
