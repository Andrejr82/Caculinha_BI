import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina classes CSS com suporte a Tailwind
 * Útil para mesclar classes condicionais
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
