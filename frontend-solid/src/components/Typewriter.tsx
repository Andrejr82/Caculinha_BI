import { createSignal, createEffect, onCleanup } from 'solid-js';

interface TypewriterProps {
  text: string;
  speed?: number; // ms por caractere (padrão: 20ms)
  onComplete?: () => void; // Callback quando terminar de digitar
}

/**
 * Componente Typewriter - Efeito de digitação ChatGPT-like
 *
 * Renderiza texto com efeito de digitação suave, caractere por caractere.
 * Perfeito para respostas de chat/IA que chegam via streaming.
 *
 * @example
 * ```tsx
 * <Typewriter
 *   text={message.text}
 *   speed={15}
 *   onComplete={() => console.log('Digitação concluída!')}
 * />
 * ```
 */
export function Typewriter(props: TypewriterProps) {
  const [displayedText, setDisplayedText] = createSignal('');
  const [currentIndex, setCurrentIndex] = createSignal(0);
  const [isTyping, setIsTyping] = createSignal(false);

  createEffect(() => {
    const targetText = props.text;
    const speed = props.speed || 20;

    // Se o texto alvo mudou (nova atualização do streaming)
    if (targetText !== displayedText()) {
      // Se o novo texto é uma extensão do atual, continuar digitando
      if (targetText.startsWith(displayedText())) {
        setIsTyping(true);

        const interval = setInterval(() => {
          setCurrentIndex((prev) => {
            const nextIndex = prev + 1;

            if (nextIndex <= targetText.length) {
              setDisplayedText(targetText.slice(0, nextIndex));
              return nextIndex;
            } else {
              // Terminou de digitar
              clearInterval(interval);
              setIsTyping(false);
              if (props.onComplete) {
                props.onComplete();
              }
              return prev;
            }
          });
        }, speed);

        onCleanup(() => clearInterval(interval));
      } else {
        // Se o texto é completamente diferente, resetar
        setDisplayedText(targetText);
        setCurrentIndex(targetText.length);
        setIsTyping(false);
      }
    }
  });

  return (
    <span class="whitespace-pre-wrap">
      {displayedText()}
      {/* Cursor piscante quando está digitando */}
      {isTyping() && (
        <span class="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse" />
      )}
    </span>
  );
}

/**
 * Hook alternativo para controle manual do efeito typewriter
 * Útil quando você precisa de mais controle sobre o comportamento
 */
export function createTypewriter(initialText = '', speed = 20) {
  const [displayedText, setDisplayedText] = createSignal('');
  const [targetText, setTargetText] = createSignal(initialText);
  const [isTyping, setIsTyping] = createSignal(false);

  createEffect(() => {
    const target = targetText();
    const current = displayedText();

    if (target === current) {
      setIsTyping(false);
      return;
    }

    setIsTyping(true);

    const interval = setInterval(() => {
      setDisplayedText((prev) => {
        if (prev.length < target.length) {
          return target.slice(0, prev.length + 1);
        } else {
          clearInterval(interval);
          setIsTyping(false);
          return prev;
        }
      });
    }, speed);

    onCleanup(() => clearInterval(interval));
  });

  return {
    displayedText,
    isTyping,
    setTargetText,
    reset: () => {
      setDisplayedText('');
      setTargetText('');
    },
  };
}
