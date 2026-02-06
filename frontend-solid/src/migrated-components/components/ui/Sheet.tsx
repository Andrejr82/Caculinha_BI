import { createSignal, type JSX, ParentComponent } from "solid-js";
import { Portal } from "solid-js/web";
import { cn } from "../../utils/cn";

interface SheetProps extends JSX.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  side?: "left" | "right" | "top" | "bottom";
}

/**
 * Sheet component - side panel/drawer
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 */
export const Sheet: ParentComponent<SheetProps> = (props) => {
  const [isOpen, setIsOpen] = createSignal(props.open || false);
  const side = () => props.side || "right";
  
  const open = () => props.open !== undefined ? props.open : isOpen();
  const setOpen = (value: boolean) => {
    setIsOpen(value);
    props.onOpenChange?.(value);
  };

  const sideClasses = () => {
    switch (side()) {
      case "left": return "left-0 top-0 h-full w-3/4 max-w-sm";
      case "right": return "right-0 top-0 h-full w-3/4 max-w-sm";
      case "top": return "top-0 left-0 w-full h-3/4 max-h-sm";
      case "bottom": return "bottom-0 left-0 w-full h-3/4 max-h-sm";
    }
  };

  return (
    <>
      {open() && (
        <Portal>
          <div
            data-slot="sheet-overlay"
            class="fixed inset-0 z-50 bg-black/80"
            onClick={() => setOpen(false)}
          />
          <div
            data-slot="sheet"
            class={cn(
              "fixed z-50 bg-background p-6 shadow-lg",
              sideClasses(),
              props.class
            )}
            {...props}
          >
            {props.children}
          </div>
        </Portal>
      )}
    </>
  );
};

export const SheetHeader: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div data-slot="sheet-header" class={cn("space-y-2", props.class)} {...props}>
      {props.children}
    </div>
  );
};

export const SheetTitle: ParentComponent<JSX.HTMLAttributes<HTMLHeadingElement>> = (props) => {
  return (
    <h2 data-slot="sheet-title" class={cn("text-lg font-semibold", props.class)} {...props}>
      {props.children}
    </h2>
  );
};
