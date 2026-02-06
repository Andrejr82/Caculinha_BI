import type { JSX, ParentComponent } from "solid-js";
import { cn } from "../../utils/cn";

interface CardProps extends JSX.HTMLAttributes<HTMLDivElement> {}

/**
 * Card component - main container
 */
export const Card: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card"
      class={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardHeader component - header section
 */
export const CardHeader: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-header"
      class={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-2 px-6",
        "has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardTitle component - title text
 */
export const CardTitle: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-title"
      class={cn("leading-none font-semibold", props.class)}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardDescription component - description text
 */
export const CardDescription: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-description"
      class={cn("text-muted-foreground text-sm", props.class)}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardAction component - action buttons area
 */
export const CardAction: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-action"
      class={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardContent component - main content area
 */
export const CardContent: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-content"
      class={cn("px-6", props.class)}
      {...props}
    >
      {props.children}
    </div>
  );
};

/**
 * CardFooter component - footer section
 */
export const CardFooter: ParentComponent<CardProps> = (props) => {
  return (
    <div
      data-slot="card-footer"
      class={cn("flex items-center px-6 [.border-t]:pt-6", props.class)}
      {...props}
    >
      {props.children}
    </div>
  );
};
