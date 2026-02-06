import type { JSX } from "solid-js";
import { cn } from "../../utils/cn";

interface SkeletonProps extends JSX.HTMLAttributes<HTMLDivElement> {}

/**
 * Skeleton component for loading states
 * Migrated from React to SolidJS
 * 
 * @example
 * ```tsx
 * <Skeleton class="w-full h-20" />
 * ```
 */
export function Skeleton(props: SkeletonProps) {
  return (
    <div
      data-slot="skeleton"
      class={cn("bg-accent animate-pulse rounded-md", props.class)}
      {...props}
    />
  );
}
