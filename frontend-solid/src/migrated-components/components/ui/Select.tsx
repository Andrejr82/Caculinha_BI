import { createSignal, type JSX, ParentComponent, Show } from "solid-js";
import { cn } from "../../utils/cn";

interface SelectProps extends JSX.SelectHTMLAttributes<HTMLSelectElement> {}

/**
 * Select component - native select dropdown
 * Migrated from React to SolidJS (simplified, native select)
 */
export function Select(props: SelectProps) {
  return (
    <select
      data-slot="select"
      class={cn(
        "flex h-9 w-full items-center justify-between rounded-md border border-input",
        "bg-transparent px-3 py-2 text-sm shadow-xs",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        props.class
      )}
      {...props}
    />
  );
}

interface SelectOptionProps extends JSX.OptionHTMLAttributes<HTMLOptionElement> {}

export function SelectOption(props: SelectOptionProps) {
  return <option {...props} />;
}
