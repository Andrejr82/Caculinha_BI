import type { JSX, ParentComponent } from "solid-js";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../utils/cn";

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm grid has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] grid-cols-[0_1fr] has-[>svg]:gap-x-3 gap-y-0.5 items-start [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        destructive:
          "text-destructive bg-card [&>svg]:text-current *:data-[slot=alert-description]:text-destructive/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface AlertProps
  extends JSX.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {}

/**
 * Alert component - notification container
 * Migrated from React to SolidJS
 */
export const Alert: ParentComponent<AlertProps> = (props) => {
  return (
    <div
      data-slot="alert"
      role="alert"
      class={cn(alertVariants({ variant: props.variant }), props.class)}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * AlertTitle component - alert title
 */
export const AlertTitle: ParentComponent<AlertProps> = (props) => {
  return (
    <div
      data-slot="alert-title"
      class={cn(
        "col-start-2 line-clamp-1 min-h-4 font-medium tracking-tight",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * AlertDescription component - alert description
 */
export const AlertDescription: ParentComponent<AlertProps> = (props) => {
  return (
    <div
      data-slot="alert-description"
      class={cn(
        "text-muted-foreground col-start-2 grid justify-items-start gap-1 text-sm [&_p]:leading-relaxed",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};
