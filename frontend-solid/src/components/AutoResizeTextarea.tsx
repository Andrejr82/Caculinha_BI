import { createEffect, createSignal, splitProps, JSX } from 'solid-js';

interface AutoResizeTextareaProps extends JSX.TextareaHTMLAttributes<HTMLTextAreaElement> {
    value: string;
    onInput: (e: InputEvent & { currentTarget: HTMLTextAreaElement; target: HTMLTextAreaElement }) => void;
    maxHeight?: number;
}

export function AutoResizeTextarea(props: AutoResizeTextareaProps) {
    const [local, others] = splitProps(props, ['value', 'onInput', 'maxHeight', 'class', 'ref']);
    let textareaRef: HTMLTextAreaElement | undefined;

    const handleInput = (e: InputEvent & { currentTarget: HTMLTextAreaElement; target: HTMLTextAreaElement }) => {
        local.onInput(e);
        adjustHeight();
    };

    const adjustHeight = () => {
        if (textareaRef) {
            textareaRef.style.height = 'auto'; // Reset height
            const scrollHeight = textareaRef.scrollHeight;
            const max = local.maxHeight || 200;
            textareaRef.style.height = `${Math.min(scrollHeight, max)}px`;

            // Overflow auto only if we hit max height
            textareaRef.style.overflowY = scrollHeight > max ? 'auto' : 'hidden';
        }
    };

    // Adjust on value change (e.g. clear)
    createEffect(() => {
        if (local.value !== undefined) {
            adjustHeight();
        }
    });

    return (
        <textarea
            ref={(el) => {
                textareaRef = el;
                if (typeof local.ref === 'function') local.ref(el);
            }}
            value={local.value}
            onInput={handleInput}
            rows={1}
            class={`resize-none overflow-hidden ${local.class || ''}`}
            {...others}
        />
    );
}
