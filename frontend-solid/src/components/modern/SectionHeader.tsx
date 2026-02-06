import { Component, JSX, Show } from 'solid-js';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: JSX.Element;
  action?: JSX.Element;
  gradient?: boolean;
}

export const SectionHeader: Component<SectionHeaderProps> = (props) => {
  return (
    <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8 pb-6 border-b border-gray-100 dark:border-gray-800">
      <div class="flex items-center gap-4">
        <Show when={props.icon}>
          <div class={`
            p-3.5 rounded-2xl shadow-lg text-white
            ${props.gradient 
              ? 'bg-gradient-hero' 
              : 'bg-gradient-to-br from-cacula-green-500 to-cacula-green-600'}
          `}>
            {props.icon}
          </div>
        </Show>
        
        <div>
          <h2 class="text-3xl md:text-4xl font-black text-gray-900 dark:text-white tracking-tight leading-none">
            <Show when={props.gradient} fallback={props.title}>
              <span class="bg-gradient-primary bg-clip-text text-transparent">
                {props.title}
              </span>
            </Show>
          </h2>
          
          <Show when={props.subtitle}>
            <p class="text-base text-gray-500 dark:text-gray-400 mt-2 font-medium">
              {props.subtitle}
            </p>
          </Show>
        </div>
      </div>
      
      <Show when={props.action}>
        <div class="flex-shrink-0">
          {props.action}
        </div>
      </Show>
    </div>
  );
};
