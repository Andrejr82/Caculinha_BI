import type { JSX, ParentComponent } from "solid-js";
import { cn } from "../../utils/cn";

interface LabelProps extends JSX.LabelHTMLAttributes<HTMLLabelElement> {}

/**
 * Label component for form fields
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 * 
 * @example
 * ```tsx
 * <Label for="email">Email</Label>
 * ```
 */
export const Label: ParentComponent<LabelProps> = (props) => {
  return (
    <label
      data-slot="label"
      class={cn(
        "flex items-center gap-2 text-sm leading-none font-medium select-none",
        "group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50",
        "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        props.class
      )}
      {...props}
    >
      {props.children}
    </label>
  );
};
