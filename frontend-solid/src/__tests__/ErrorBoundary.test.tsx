import { render } from '@solidjs/testing-library';
import { describe, it, expect } from 'vitest';
import { ErrorBoundary } from '../components/ErrorBoundary';

describe('ErrorBoundary Component', () => {
  it('should render children when no error', () => {
    const { container } = render(() => (
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    ));

    expect(container.textContent).toContain('Test Content');
  });

  it('should render error message when error occurs', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    const { container } = render(() => (
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    ));

    expect(container.textContent).toContain('Ops! Algo deu errado');
  });
});
