// frontend-solid/src/components/__tests__/Chat.test.tsx

import { render, screen, fireEvent, cleanup } from 'solid-testing-library';
import { Show } from 'solid-js';
import { vi, beforeEach, afterEach, expect, test } from 'vitest';

import Chat from '../../pages/Chat';
import auth from '@/store/auth';

// Mock the Typewriter component as it's just visual
vi.mock('@/components', () => ({
  Typewriter: (props: any) => <span data-testid="typewriter">{props.text}</span>,
}));

// Mock PlotlyChart and DataTable
vi.mock('@/components/PlotlyChart', () => ({
  PlotlyChart: (props: any) => <div data-testid="plotly-chart">{JSON.stringify(props.chartSpec())}</div>,
}));

vi.mock('@/components/DataTable', () => ({
  DataTable: (props: any) => <div data-testid="data-table">{JSON.stringify(props.data())}</div>,
}));

// Mock FeedbackButtons and DownloadButton (for rendering only, not functionality)
vi.mock('@/components/FeedbackButtons', () => ({
    FeedbackButtons: (props: any) => <button data-testid="feedback-button" onClick={() => props.onFeedback(props.messageId, 'positive')}>Feedback</button>,
}));

vi.mock('@/components/DownloadButton', () => ({
    DownloadButton: (props: any) => <button data-testid="download-button">Download {props.filename}</button>,
}));

// Mock formatTimestamp
vi.mock('@/lib/formatters', () => ({
  formatTimestamp: vi.fn(() => '12:00 PM'),
}));


// Mock EventSource for SSE
class MockEventSource {
  onmessage: (event: MessageEvent) => void = () => {};
  onerror: (event: Event) => void = () => {};
  close = vi.fn();
  url: string;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  // Static array to hold all instances for easy access in tests
  static instances: MockEventSource[] = [];
  static reset() {
    MockEventSource.instances = [];
  }
}

vi.stubGlobal('EventSource', MockEventSource);

beforeEach(() => {
  cleanup(); // Clean up DOM after each test
  MockEventSource.reset(); // Reset mock instances
  auth.setToken('mock_valid_token'); // Ensure auth token is set
  auth.setUser({ id: '1', username: 'testuser' });
  vi.clearAllMocks(); // Clear mocks
});

afterEach(() => {
    cleanup();
});

test('Chat component renders initial message', () => {
  render(() => <Chat />);
  expect(screen.getByText(/Olá! Sou seu assistente de BI./i)).toBeInTheDocument();
});

test('sends user message and starts streaming', async () => {
  render(() => <Chat />);
  const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
  const sendButton = screen.getByRole('button', { name: /Enviar/i });

  fireEvent.input(inputElement, { target: { value: 'Test message' } });
  fireEvent.click(sendButton);

  expect(screen.getByText('Test message')).toBeInTheDocument();
  expect(inputElement.value).toBe('');
  expect(sendButton).toBeDisabled(); // Should be disabled while streaming
  
  expect(MockEventSource.instances.length).toBe(1);
  expect(MockEventSource.instances[0].url).toContain('q=Test%20message');
});

test('receives streaming text response', async () => {
    render(() => <Chat />);
    const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /Enviar/i });

    fireEvent.input(inputElement, { target: { value: 'Stream test' } });
    fireEvent.click(sendButton);

    const es = MockEventSource.instances[0];

    // Simulate streaming chunks
    es.onmessage({ data: JSON.stringify({ type: 'text', text: 'First part ', done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'text', text: 'second part.', done: false }) } as MessageEvent);

    // Final chunk
    es.onmessage({ data: JSON.stringify({ type: 'final', text: '', done: true }) } as MessageEvent);

    await vi.waitFor(() => {
        expect(screen.getByTestId('typewriter')).toHaveTextContent('First part second part.');
        expect(sendButton).toBeEnabled(); // Should be enabled after streaming ends
    });
    expect(es.close).toHaveBeenCalledTimes(1);
});

test('renders chart response', async () => {
    render(() => <Chat />);
    const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /Enviar/i });

    fireEvent.input(inputElement, { target: { value: 'Show me a chart' } });
    fireEvent.click(sendButton);

    const es = MockEventSource.instances[0];
    const mockChartSpec = { data: [{ type: 'bar', y: [1, 2, 3] }], layout: { title: 'Test Chart' } };

    es.onmessage({ data: JSON.stringify({ type: 'text', text: 'Here is your chart: ', done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'chart', chart_spec: mockChartSpec, done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'final', text: '', done: true }) } as MessageEvent);

    await vi.waitFor(() => {
        expect(screen.getByTestId('plotly-chart')).toBeInTheDocument();
        expect(screen.getByTestId('plotly-chart')).toHaveTextContent(JSON.stringify(mockChartSpec));
    });
});

test('renders table response with download button', async () => {
    render(() => <Chat />);
    const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /Enviar/i });

    fireEvent.input(inputElement, { target: { value: 'Show me table data' } });
    fireEvent.click(sendButton);

    const es = MockEventSource.instances[0];
    const mockTableData = [{ id: 1, name: 'Item A' }, { id: 2, name: 'Item B' }];

    es.onmessage({ data: JSON.stringify({ type: 'table', data: mockTableData, done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'final', text: '', done: true }) } as MessageEvent);

    await vi.waitFor(() => {
        expect(screen.getByTestId('data-table')).toBeInTheDocument();
        expect(screen.getByTestId('data-table')).toHaveTextContent(JSON.stringify(mockTableData));
        expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });
});

test('handles error during streaming', async () => {
  render(() => <Chat />);
  const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
  const sendButton = screen.getByRole('button', { name: /Enviar/i });

  fireEvent.input(inputElement, { target: { value: 'Error test' } });
  fireEvent.click(sendButton);

  const es = MockEventSource.instances[0];

  es.onmessage({ data: JSON.stringify({ type: 'error', error: 'Simulated backend error', details: { code: 500 } }) } as MessageEvent);

  await vi.waitFor(() => {
    expect(screen.getByText(/Erro do servidor/i)).toBeInTheDocument();
    expect(screen.getByText(/Simulated backend error/i)).toBeInTheDocument();
    expect(sendButton).toBeEnabled();
  });
  expect(es.close).toHaveBeenCalledTimes(1);
});

test('feedback button appears after streaming ends', async () => {
    render(() => <Chat />);
    const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /Enviar/i });

    fireEvent.input(inputElement, { target: { value: 'Feedback test' } });
    fireEvent.click(sendButton);

    const es = MockEventSource.instances[0];
    es.onmessage({ data: JSON.stringify({ type: 'text', text: 'This is a test message.', done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'final', text: '', done: true }) } as MessageEvent);

    await vi.waitFor(() => {
        expect(screen.getByTestId('feedback-button')).toBeInTheDocument();
    });
});

test('feedback submission handler is called', async () => {
    render(() => <Chat />);
    const inputElement = screen.getByPlaceholderText(/Faça uma pergunta sobre os dados.../i) as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /Enviar/i });

    fireEvent.input(inputElement, { target: { value: 'Feedback test' } });
    fireEvent.click(sendButton);

    const es = MockEventSource.instances[0];
    es.onmessage({ data: JSON.stringify({ type: 'text', text: 'Response with ID', done: false }) } as MessageEvent);
    es.onmessage({ data: JSON.stringify({ type: 'final', text: '', done: true }) } as MessageEvent);

    // Mock the fetch call for feedback
    const mockFetch = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal('fetch', mockFetch);

    await vi.waitFor(() => {
        const feedbackButton = screen.getByTestId('feedback-button');
        fireEvent.click(feedbackButton); // Click the mock feedback button
    });
    
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/chat/feedback', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"feedback_type":"positive"')
    }));
});
