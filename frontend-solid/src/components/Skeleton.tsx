import { JSX } from 'solid-js';

interface SkeletonProps {
  class?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string;
  height?: string;
}

export function Skeleton(props: SkeletonProps) {
  const variant = props.variant || 'rectangular';

  const baseClasses = 'animate-pulse bg-muted/50';

  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg'
  };

  const style: JSX.CSSProperties = {};
  if (props.width) style.width = props.width;
  if (props.height) style.height = props.height;

  return (
    <div
      class={`${baseClasses} ${variantClasses[variant]} ${props.class || ''}`}
      style={style}
    />
  );
}

// Skeleton presets for common use cases

export function SkeletonCard() {
  return (
    <div class="bg-card border rounded-lg p-4 space-y-3">
      <Skeleton variant="text" width="60%" height="20px" />
      <Skeleton variant="text" width="40%" height="16px" />
      <div class="pt-2 space-y-2">
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="90%" />
        <Skeleton variant="text" width="95%" />
      </div>
    </div>
  );
}

export function SkeletonTable(props: { rows?: number }) {
  const rows = props.rows || 5;

  return (
    <div class="border rounded-lg overflow-hidden">
      {/* Header */}
      <div class="bg-muted/30 p-3 border-b flex gap-4">
        <Skeleton width="20%" height="12px" />
        <Skeleton width="30%" height="12px" />
        <Skeleton width="15%" height="12px" />
        <Skeleton width="20%" height="12px" />
        <Skeleton width="15%" height="12px" />
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div class="p-3 border-b last:border-0 flex gap-4 items-center">
          <Skeleton width="20%" height="16px" />
          <Skeleton width="30%" height="16px" />
          <Skeleton width="15%" height="16px" />
          <Skeleton width="20%" height="16px" />
          <Skeleton width="15%" height="16px" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div class="bg-card border rounded-lg p-4 space-y-4">
      <Skeleton variant="text" width="40%" height="20px" />
      <div class="h-64 flex items-end gap-2 px-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton
            class="flex-1"
            height={`${Math.random() * 60 + 40}%`}
          />
        ))}
      </div>
      <div class="flex justify-between px-4">
        {Array.from({ length: 8 }).map(() => (
          <Skeleton width="40px" height="12px" />
        ))}
      </div>
    </div>
  );
}

export function SkeletonKPI() {
  return (
    <div class="bg-card border rounded-lg p-5 space-y-3">
      <Skeleton variant="text" width="50%" height="14px" />
      <Skeleton width="80px" height="32px" />
      <Skeleton variant="text" width="60%" height="12px" />
    </div>
  );
}

export function SkeletonList(props: { items?: number }) {
  const items = props.items || 5;

  return (
    <div class="space-y-3">
      {Array.from({ length: items }).map(() => (
        <div class="flex items-center gap-3 p-3 border rounded-lg">
          <Skeleton variant="circular" width="40px" height="40px" />
          <div class="flex-1 space-y-2">
            <Skeleton width="60%" height="16px" />
            <Skeleton width="40%" height="12px" />
          </div>
          <Skeleton width="80px" height="32px" />
        </div>
      ))}
    </div>
  );
}
