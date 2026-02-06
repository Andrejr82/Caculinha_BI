/**
 * useMediaQuery Hook - SolidJS
 * Hook para detectar breakpoints responsivos
 */

import { createSignal, onMount, onCleanup } from 'solid-js';

export function useMediaQuery(query: string): () => boolean {
  const [matches, setMatches] = createSignal(false);

  onMount(() => {
    const media = window.matchMedia(query);
    
    // Set initial value
    setMatches(media.matches);

    // Create event listener
    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    
    // Add listener
    media.addEventListener('change', listener);

    // Cleanup
    onCleanup(() => media.removeEventListener('change', listener));
  });

  return matches;
}

// Predefined breakpoints
export const useIsMobile = () => useMediaQuery('(max-width: 768px)');
export const useIsTablet = () => useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
export const useIsDesktop = () => useMediaQuery('(min-width: 1025px)');
