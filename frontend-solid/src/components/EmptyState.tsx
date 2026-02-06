import { JSX } from 'solid-js';
import { Package, Search, AlertCircle, FileText, Inbox, Users } from 'lucide-solid';

interface EmptyStateProps {
  icon?: 'package' | 'search' | 'alert' | 'file' | 'inbox' | 'users' | 'custom';
  customIcon?: JSX.Element;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'default' | 'success' | 'warning' | 'info';
}

export function EmptyState(props: EmptyStateProps) {
  const variant = props.variant || 'default';

  const getIcon = () => {
    if (props.customIcon) return props.customIcon;

    const iconProps = { size: 64, class: 'opacity-20' };

    switch (props.icon) {
      case 'package':
        return <Package {...iconProps} />;
      case 'search':
        return <Search {...iconProps} />;
      case 'alert':
        return <AlertCircle {...iconProps} />;
      case 'file':
        return <FileText {...iconProps} />;
      case 'users':
        return <Users {...iconProps} />;
      case 'inbox':
      default:
        return <Inbox {...iconProps} />;
    }
  };

  const getColorClasses = () => {
    switch (variant) {
      case 'success':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div class="flex flex-col items-center justify-center p-12 text-center">
      <div class={`mb-4 ${getColorClasses()}`}>
        {getIcon()}
      </div>

      <h3 class="text-lg font-semibold text-foreground mb-2">
        {props.title}
      </h3>

      {props.description && (
        <p class="text-sm text-muted-foreground max-w-md mb-6">
          {props.description}
        </p>
      )}

      {props.action && (
        <button
          onClick={props.action.onClick}
          class="btn btn-primary"
        >
          {props.action.label}
        </button>
      )}
    </div>
  );
}

// Preset empty states for common scenarios

export function EmptyStateNoData(props: { onRefresh?: () => void }) {
  return (
    <EmptyState
      icon="inbox"
      title="Nenhum dado encontrado"
      description="Não há informações disponíveis para exibir no momento."
      action={props.onRefresh ? {
        label: "Recarregar",
        onClick: props.onRefresh
      } : undefined}
    />
  );
}

export function EmptyStateNoResults(props: { onClearFilters?: () => void }) {
  return (
    <EmptyState
      icon="search"
      title="Nenhum resultado encontrado"
      description="Tente ajustar os filtros ou termos de busca."
      action={props.onClearFilters ? {
        label: "Limpar Filtros",
        onClick: props.onClearFilters
      } : undefined}
    />
  );
}

export function EmptyStateSuccess(props: { title: string; description?: string }) {
  return (
    <EmptyState
      icon="package"
      variant="success"
      title={props.title}
      description={props.description}
    />
  );
}

export function EmptyStateError(props: { title: string; description?: string; onRetry?: () => void }) {
  return (
    <EmptyState
      icon="alert"
      variant="warning"
      title={props.title}
      description={props.description}
      action={props.onRetry ? {
        label: "Tentar Novamente",
        onClick: props.onRetry
      } : undefined}
    />
  );
}
