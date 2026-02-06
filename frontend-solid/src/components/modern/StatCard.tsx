import { Component, JSX, Show } from 'solid-js';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: JSX.Element;
  variant?: 'primary' | 'accent' | 'secondary' | 'neutral' | 'dark';
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  loading?: boolean;
}

export const StatCard: Component<StatCardProps> = (props) => {
  const variantStyles = {
    primary: {
      bg: 'bg-gradient-to-br from-cacula-green-50 to-white dark:from-cacula-green-900/20 dark:to-gray-800',
      icon: 'bg-cacula-green-100 text-cacula-green-600 dark:bg-cacula-green-900/50 dark:text-cacula-green-400',
      border: 'border-cacula-green-200 dark:border-cacula-green-800',
      value: 'text-cacula-green-700 dark:text-cacula-green-400'
    },
    accent: {
      bg: 'bg-gradient-to-br from-cacula-red-50 to-white dark:from-cacula-red-900/20 dark:to-gray-800',
      icon: 'bg-cacula-red-100 text-cacula-red-600 dark:bg-cacula-red-900/50 dark:text-cacula-red-400',
      border: 'border-cacula-red-200 dark:border-cacula-red-800',
      value: 'text-cacula-red-600 dark:text-cacula-red-400'
    },
    secondary: {
      bg: 'bg-gradient-to-br from-cacula-yellow-50 to-white dark:from-cacula-yellow-900/20 dark:to-gray-800',
      icon: 'bg-cacula-yellow-100 text-cacula-yellow-600 dark:bg-cacula-yellow-900/50 dark:text-cacula-yellow-400',
      border: 'border-cacula-yellow-200 dark:border-cacula-yellow-800',
      value: 'text-cacula-yellow-700 dark:text-cacula-yellow-400'
    },
    neutral: {
      bg: 'bg-white dark:bg-gray-800',
      icon: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
      border: 'border-gray-200 dark:border-gray-700',
      value: 'text-gray-900 dark:text-white'
    },
    dark: {
      bg: 'bg-gray-900 text-white',
      icon: 'bg-gray-800 text-gray-300',
      border: 'border-gray-700',
      value: 'text-white'
    }
  };
  
  const style = variantStyles[props.variant || 'neutral'];
  
  return (
    <div class={`
      p-6 rounded-2xl border ${style.bg} ${style.border}
      shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300
      relative overflow-hidden group
    `}>
      {/* Background Decorator */}
      <div class="absolute -right-6 -top-6 w-24 h-24 rounded-full bg-current opacity-[0.03] group-hover:scale-150 transition-transform duration-500 pointer-events-none" />
      
      <div class="flex items-start justify-between relative z-10">
        <div class="flex-1">
          <p class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-2">
            {props.title}
          </p>
          
          <Show when={!props.loading} fallback={<div class="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-1" />}>
            <h3 class={`text-3xl font-black mb-1 ${style.value} tracking-tight`}>
              {props.value}
            </h3>
          </Show>
          
          <Show when={props.subtitle}>
            <p class="text-xs text-gray-500 dark:text-gray-400 font-medium">{props.subtitle}</p>
          </Show>
          
          <Show when={props.trend}>
            <div class={`flex items-center gap-1 mt-3 text-xs font-bold px-2 py-1 rounded-full w-fit ${
              props.trend === 'up' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 
              props.trend === 'down' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 
              'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              <span>{props.trend === 'up' ? '↗' : props.trend === 'down' ? '↘' : '→'}</span>
              <span>{props.trendValue}</span>
            </div>
          </Show>
        </div>
        
        <Show when={props.icon}>
          <div class={`p-3 rounded-xl ${style.icon} shadow-inner`}>
            {props.icon}
          </div>
        </Show>
      </div>
    </div>
  );
};
