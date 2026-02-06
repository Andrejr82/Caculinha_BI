import { createSignal, type JSX, ParentComponent, Show } from "solid-js";
import { Portal } from "solid-js/web";
import { cn } from "../../utils/cn";

interface DropdownMenuProps extends JSX.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

/**
 * DropdownMenu component - dropdown menu
 * Migrated from React to SolidJS (simplified native implementation)
 */
export const DropdownMenu: ParentComponent<DropdownMenuProps> = (props) => {
  const [isOpen, setIsOpen] = createSignal(props.open || false);
  
  const open = () => props.open !== undefined ? props.open : isOpen();
  const setOpen = (value: boolean) => {
    setIsOpen(value);
    props.onOpenChange?.(value);
  };

  return (
    <div data-slot="dropdown" class="relative inline-block">
      {props.children}
    </div>
  );
};

export const DropdownMenuTrigger: ParentComponent<JSX.ButtonHTMLAttributes<HTMLButtonElement>> = (props) => {
  return (
    <button data-slot="dropdown-trigger" {...props}>
      {props.children}
    </button>
  );
};

export const DropdownMenuContent: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div
      data-slot="dropdown-content"
      class={cn(
        "absolute right-0 mt-2 w-56 rounded-md border bg-popover p-1 shadow-md z-50",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

export const DropdownMenuItem: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div
      data-slot="dropdown-item"
      class={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm",
        "hover:bg-accent hover:text-accent-foreground",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};
