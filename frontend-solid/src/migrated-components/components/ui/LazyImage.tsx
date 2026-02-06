import { createSignal, type JSX } from "solid-js";
import { cn } from "../../utils/cn";

interface LazyImageProps extends JSX.ImgHTMLAttributes<HTMLImageElement> {
  fallbackSrc?: string;
}

/**
 * LazyImage component - optimized image loading
 * Migrated from React to SolidJS (Next.js Image removed, native img)
 * 
 * @example
 * ```tsx
 * <LazyImage src="/image.jpg" alt="Description" />
 * ```
 */
export function LazyImage(props: LazyImageProps) {
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal(false);
  
  const fallbackSrc = () => props.fallbackSrc || "/placeholder.png";
  const imageSrc = () => error() ? fallbackSrc() : props.src;

  return (
    <div class={cn("relative overflow-hidden", props.class)}>
      <img
        {...props}
        src={imageSrc()}
        class={cn(
          "transition-opacity duration-300",
          isLoading() ? "opacity-0" : "opacity-100"
        )}
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setError(true);
          setIsLoading(false);
        }}
      />
      {isLoading() && (
        <div class="absolute inset-0 bg-muted animate-pulse" />
      )}
    </div>
  );
}
