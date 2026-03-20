import { render, screen } from '@solidjs/testing-library';
import { describe, it, expect } from 'vitest';
import Chat from '@/pages/Chat';

describe('Chat page', () => {
  it('renders initial assistant greeting', () => {
    render(() => <Chat />);
    expect(screen.getByText(/Olá! Sou o Caçulinha/i)).toBeInTheDocument();
  });

  it('renders input and send controls', () => {
    render(() => <Chat />);
    expect(screen.getByPlaceholderText(/Enviar mensagem para o Caçulinha/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0);
  });
});
