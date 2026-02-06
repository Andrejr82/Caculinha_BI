import { Component, createSignal } from 'solid-js';
import { 
  Info, 
  Target, 
  Users, 
  TrendingUp, 
  Award, 
  MapPin, 
  ShieldCheck, 
  Heart
} from 'lucide-solid';

const About: Component = () => {
  // Paleta de cores derivada da análise da marca
  const brandColors = {
    primary: '#78B928', // Verde Caçula Estimado
    secondary: '#2C3E50', // Azul escuro para contraste
    accent: '#ED1C24', // Vermelho da pétala para detalhes
    background: '#F8F9FA'
  };

  return (
    <div class="flex flex-col min-h-full bg-slate-50">
      {/* Hero Section com a Imagem da Marca */}
      <div 
        class="w-full h-48 md:h-64 bg-cover bg-center relative shadow-md"
        style={{ 
          "background-color": brandColors.primary,
          "background-image": "url('/banner-cacula.png')",
          "background-size": "contain",
          "background-repeat": "no-repeat",
          "background-position": "center"
        }}
      >
        <div class="absolute inset-0 bg-black/10"></div> {/* Overlay sutil para profundidade */}
      </div>

      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-10 pb-12">
        {/* Card Principal de Introdução */}
        <div class="bg-white rounded-xl shadow-lg p-8 mb-8 border-t-4" style={{ "border-color": brandColors.primary }}>
          <div class="flex items-center gap-3 mb-4">
            <Info class="w-8 h-8" style={{ color: brandColors.primary }} />
            <h1 class="text-3xl font-bold text-gray-800">Sobre o Agente BI Caçula</h1>
          </div>
          <p class="text-lg text-gray-600 leading-relaxed">
            Bem-vindo à central de inteligência de dados das Lojas Caçula. 
            Esta plataforma foi desenvolvida para empoderar nossa equipe com insights rápidos, 
            precisos e acionáveis, combinando a tradição de nossa marca com o que há de mais moderno em Inteligência Artificial.
          </p>
        </div>

        {/* Grid de Valores e Objetivos */}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          
          {/* Nossa Missão com IA */}
          <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow">
            <div class="flex items-center gap-3 mb-3">
              <div class="p-2 rounded-full bg-blue-50">
                <Target class="w-6 h-6 text-blue-600" />
              </div>
              <h2 class="text-xl font-semibold text-gray-800">Missão Tecnológica</h2>
            </div>
            <p class="text-gray-600">
              Democratizar o acesso aos dados corporativos. Permitir que cada gerente, vendedor e 
              analista tome decisões baseadas em evidências, não apenas em intuição.
            </p>
          </div>

          {/* Foco no Cliente */}
          <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow">
            <div class="flex items-center gap-3 mb-3">
              <div class="p-2 rounded-full bg-red-50">
                <Heart class="w-6 h-6 text-red-600" />
              </div>
              <h2 class="text-xl font-semibold text-gray-800">Foco no Cliente</h2>
            </div>
            <p class="text-gray-600">
              Usamos dados para entender melhor nossos clientes. Nossas análises de ruptura, 
              mix de produtos e tendências garantem que o cliente encontre o que precisa para sua arte.
            </p>
          </div>
        </div>

        {/* Estatísticas / Pilares do Projeto */}
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12">
          <div class="bg-white p-6 rounded-lg shadow-sm text-center border-b-4 border-blue-400">
            <div class="text-4xl font-bold text-gray-800 mb-2">100%</div>
            <div class="text-sm text-gray-500 uppercase tracking-wide font-semibold">Integrado ao ERP</div>
          </div>
          <div class="bg-white p-6 rounded-lg shadow-sm text-center border-b-4 border-purple-400">
            <div class="text-4xl font-bold text-gray-800 mb-2">24/7</div>
            <div class="text-sm text-gray-500 uppercase tracking-wide font-semibold">Disponibilidade</div>
          </div>
          <div class="bg-white p-6 rounded-lg shadow-sm text-center border-b-4 border-yellow-400">
            <div class="text-4xl font-bold text-gray-800 mb-2">IA</div>
            <div class="text-sm text-gray-500 uppercase tracking-wide font-semibold">Gemini 3.0 Flash</div>
          </div>
        </div>

        {/* Seção Institucional Resumida */}
        <div class="bg-slate-800 rounded-xl p-8 text-white relative overflow-hidden">
          <div class="relative z-10">
            <h3 class="text-2xl font-bold mb-4 flex items-center gap-2">
              <Award class="w-6 h-6 text-yellow-400" />
              Tradição e Inovação
            </h3>
            <p class="text-slate-300 mb-6 max-w-2xl">
              As Lojas Caçula são referência no varejo de papelaria, informática, desenho e pintura. 
              Este sistema é o próximo passo na nossa evolução, unindo nossa vasta experiência de mercado 
              com a velocidade da análise de dados digital.
            </p>
            
            <div class="flex flex-wrap gap-4 text-sm font-medium text-slate-400">
              <span class="flex items-center gap-1">
                <MapPin class="w-4 h-4" /> Rio de Janeiro
              </span>
              <span class="flex items-center gap-1">
                <Users class="w-4 h-4" /> +1000 Colaboradores
              </span>
              <span class="flex items-center gap-1">
                <ShieldCheck class="w-4 h-4" /> Dados Seguros
              </span>
            </div>
          </div>
          
          {/* Elemento decorativo visual usando as cores da logo de forma abstrata */}
          <div class="absolute right-0 top-0 h-full w-1/3 opacity-10">
            <div class="h-full w-full bg-gradient-to-bl from-green-500 via-yellow-500 to-red-500 transform skew-x-12"></div>
          </div>
        </div>

        {/* Rodapé da Página */}
        <div class="mt-8 text-center text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} Lojas Caçula - Departamento de Tecnologia e Dados
        </div>
      </div>
    </div>
  );
};

export default About;
