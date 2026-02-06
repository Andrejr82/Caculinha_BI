import { ParentComponent, JSX } from 'solid-js';

interface ModernCardProps {
  variant?: 'default' | 'glass' | 'gradient' | 'elevated' | 'outlined';
  hover?: boolean;
  class?: string;
  children: JSX.Element;
  onClick?: () => void;
}

export const ModernCard: ParentComponent<ModernCardProps> = (props) => {
  const variants = {
    default: "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
    glass: "bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-lg",
    gradient: "bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700",
    elevated: "bg-white dark:bg-gray-800 shadow-xl border-none",
    outlined: "bg-transparent border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-cacula-green-500 hover:bg-cacula-green-50/10 transition-colors"
  };
  
  return (
    <div 
      onClick={props.onClick}
      class={`
        rounded-3xl transition-all duration-300 relative overflow-hidden
        ${variants[props.variant || 'default']}
        ${props.hover ? 'hover:shadow-2xl hover:-translate-y-1 cursor-pointer' : ''}
        ${props.class || ''}
      `}
    >
      {/* Optional Glow Effect for Hover */}
      {props.hover && (
        <div class="absolute inset-0 bg-gradient-to-tr from-cacula-green-500/0 via-cacula-green-500/0 to-cacula-green-500/5 opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
      )}
      <div class="relative z-10 h-full">
        {props.children}
      </div>
    </div>
  );
};
