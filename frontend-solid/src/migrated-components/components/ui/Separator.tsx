import type { JSX } from "solid-js";
import { cn } from "../../utils/cn";

interface SeparatorProps extends JSX.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
}

/**
 * Separator component for visual division
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Separator />
 * <Separator orientation="vertical" />
 * ```
 */
export function Separator(props: SeparatorProps) {
  const orientation = () => props.orientation || "horizontal";
  const decorative = () => props.decorative !== undefined ? props.decorative : true;

  return (
    <div
      role={decorative() ? "none" : "separator"}
      aria-orientation={!decorative() ? orientation() : undefined}
      data-slot="separator"
      data-orientation={orientation()}
      class={cn(
        "bg-border shrink-0",
        orientation() === "horizontal" ? "h-px w-full" : "h-full w-px",
        props.class
      )}
      {...props}
    />
  );
}
