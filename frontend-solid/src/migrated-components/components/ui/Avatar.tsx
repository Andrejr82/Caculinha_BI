import type { JSX, ParentComponent } from "solid-js";
import { cn } from "../../utils/cn";

interface AvatarProps extends JSX.HTMLAttributes<HTMLDivElement> {}

/**
 * Avatar component - container
 * Migrated from React to SolidJS (Radix UI removed, native implementation)
 */
export const Avatar: ParentComponent<AvatarProps> = (props) => {
  return (
    <div
      data-slot="avatar"
      class={cn(
        "relative flex size-8 shrink-0 overflow-hidden rounded-full",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};

interface AvatarImageProps extends JSX.ImgHTMLAttributes<HTMLImageElement> {}

/**
 * AvatarImage component - image element
 */
export function AvatarImage(props: AvatarImageProps) {
  return (
    <img
      data-slot="avatar-image"
      class={cn("aspect-square size-full", props.class)}
      {...props}
    />
  );
}

/**
 * AvatarFallback component - fallback content
 */
export const AvatarFallback: ParentComponent<AvatarProps> = (props) => {
  return (
    <div
      data-slot="avatar-fallback"
      class={cn(
        "bg-muted flex size-full items-center justify-center rounded-full",
        props.class
      )}
      {...props}
    >
      {props.children}
    </div>
  );
};
