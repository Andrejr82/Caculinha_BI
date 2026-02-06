import { ParentComponent, JSX, Show } from 'solid-js';

interface ModernButtonProps {
  variant?: 'primary' | 'accent' | 'secondary' | 'outline' | 'ghost' | 'gradient' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  icon?: JSX.Element;
  children: JSX.Element;
  disabled?: boolean;
  loading?: boolean;
  onClick?: (e: MouseEvent) => void;
  type?: 'button' | 'submit' | 'reset';
  class?: string;
  fullWidth?: boolean;
}

export const ModernButton: ParentComponent<ModernButtonProps> = (props) => {
  const variants = {
    primary: 'bg-cacula-green-500 hover:bg-cacula-green-600 text-white shadow-cacula-green-500/20 shadow-lg hover:shadow-xl',
    accent: 'bg-cacula-yellow-500 hover:bg-cacula-yellow-600 text-white shadow-cacula-yellow-500/20 shadow-lg hover:shadow-xl',
    danger: 'bg-cacula-red-500 hover:bg-cacula-red-600 text-white shadow-cacula-red-500/20 shadow-lg hover:shadow-xl',
    gradient: 'bg-gradient-primary hover:opacity-90 text-white shadow-lg hover:shadow-xl',
    outline: 'border-2 border-cacula-green-500 text-cacula-green-600 hover:bg-cacula-green-50 dark:hover:bg-cacula-green-900/20',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-200',
    ghost: 'text-cacula-green-600 hover:bg-cacula-green-50 dark:hover:bg-cacula-green-900/20',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-xl',
    md: 'px-5 py-2.5 text-sm rounded-2xl',
    lg: 'px-8 py-3.5 text-base rounded-2xl',
    xl: 'px-10 py-4 text-lg rounded-3xl',
  };
  
  return (
    <button
      type={props.type || 'button'}
      disabled={props.disabled || props.loading}
      onClick={props.onClick}
      class={`
        inline-flex items-center justify-center gap-2 font-bold tracking-wide
        transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
        active:scale-95
        ${sizes[props.size || 'md']}
        ${variants[props.variant || 'primary']}
        ${props.fullWidth ? 'w-full' : ''}
        ${props.class || ''}
      `}
    >
      <Show when={props.loading}>
        <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </Show>
      
      <Show when={props.icon && !props.loading}>
        <span class="opacity-90">{props.icon}</span>
      </Show>
      
      <span>{props.children}</span>
    </button>
  );
};
