import { createSignal, type JSX, ParentComponent } from "solid-js";
import { Portal } from "solid-js/web";
import { cn } from "../../utils/cn";

interface DialogProps extends JSX.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

/**
 * Dialog component - modal dialog
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 */
export const Dialog: ParentComponent<DialogProps> = (props) => {
  const [isOpen, setIsOpen] = createSignal(props.open || false);
  
  const open = () => props.open !== undefined ? props.open : isOpen();
  const setOpen = (value: boolean) => {
    setIsOpen(value);
    props.onOpenChange?.(value);
  };

  return (
    <>
      {open() && (
        <Portal>
          <div
            data-slot="dialog-overlay"
            class="fixed inset-0 z-50 bg-black/80"
            onClick={() => setOpen(false)}
          />
          <div
            data-slot="dialog"
            class={cn(
              "fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%]",
              "w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg",
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

export const DialogContent: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div data-slot="dialog-content" class={cn("space-y-4", props.class)} {...props}>
      {props.children}
    </div>
  );
};

export const DialogHeader: ParentComponent<JSX.HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div data-slot="dialog-header" class={cn("space-y-2", props.class)} {...props}>
      {props.children}
    </div>
  );
};

export const DialogTitle: ParentComponent<JSX.HTMLAttributes<HTMLHeadingElement>> = (props) => {
  return (
    <h2 data-slot="dialog-title" class={cn("text-lg font-semibold", props.class)} {...props}>
      {props.children}
    </h2>
  );
};

export const DialogDescription: ParentComponent<JSX.HTMLAttributes<HTMLParagraphElement>> = (props) => {
  return (
    <p data-slot="dialog-description" class={cn("text-sm text-muted-foreground", props.class)} {...props}>
      {props.children}
    </p>
  );
};
