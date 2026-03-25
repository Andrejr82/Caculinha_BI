import { render, screen } from '@solidjs/testing-library';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/solid-query';
import Chat from '@/pages/Chat';

const renderChat = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(() => (
    <QueryClientProvider client={queryClient}>
      <Chat />
    </QueryClientProvider>
  ));
};

describe('Chat page', () => {
  it('renders initial assistant greeting', () => {
    renderChat();
    expect(screen.getByText(/Olá! Sou o Caçulinha/i)).toBeInTheDocument();
  });

  it('renders input and send controls', () => {
    renderChat();
    expect(screen.getByPlaceholderText(/Enviar mensagem para o Caçulinha/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0);
  });
});
