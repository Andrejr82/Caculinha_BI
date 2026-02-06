// frontend-solid/src/components/Logo.tsx
import { Component } from 'solid-js';

interface LogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeMap = {
  xs: 'h-6',      // 24px - para sidebar fechada
  sm: 'h-8',      // 32px - para sidebar compacta
  md: 'h-10',     // 40px - padrão sidebar
  lg: 'h-12',     // 48px - login
  xl: 'h-16',     // 64px - destaque
};

export const Logo: Component<LogoProps> = (props) => {
  const size = props.size || 'md';

  return (
    <img
      src="/logo-cacula.svg"
      alt="Lojas Caçula - 40 anos de tradição"
      class={`${sizeMap[size]} w-auto ${props.className || ''}`}
      style={{ "max-width": "none" }}
    />
  );
};
