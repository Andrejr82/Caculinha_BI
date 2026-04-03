import { render, screen, waitFor } from '@solidjs/testing-library';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

let mockPathname = '/dashboard';
let mockRole = 'admin';
let mockPlaygroundEnabled = true;

vi.mock('@solidjs/router', async () => {
  const solid = await import('solid-js');
  return {
    A: (props: any) => <a href={props.href} class={props.class}>{props.children}</a>,
    useLocation: () => ({ pathname: mockPathname }),
    useNavigate: () => vi.fn(),
    Router: (props: any) => props.children,
    Show: solid.Show,
    For: solid.For,
  };
});

vi.mock('@/store/auth', () => ({
  default: {
    user: () => ({
      username: 'andre',
      role: mockRole,
      allowed_segments: mockRole === 'admin' ? ['*'] : ['sales'],
    }),
    isAuthenticated: () => true,
    logout: vi.fn(),
  },
}));

vi.mock('@/hooks/useKeyboardShortcut', () => ({
  useKeyboardShortcut: () => undefined,
}));

vi.mock('@/components', () => ({
  Logo: (props: any) => <div data-testid="logo">{props.size || 'logo'}</div>,
}));

vi.mock('../components/ErrorBoundary', () => ({
  ErrorBoundary: (props: any) => props.children,
}));

import Layout from '../Layout';

describe('Layout Component', () => {
  beforeEach(() => {
    mockPathname = '/dashboard';
    mockRole = 'admin';
    mockPlaygroundEnabled = true;
    localStorage.clear();
    sessionStorage.clear();
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ playground_access_enabled: mockPlaygroundEnabled }),
      })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders layout shell and branding', () => {
    const { container } = render(() => (
      <Layout>
        <div>Test Content</div>
      </Layout>
    ));

    expect(container).toBeDefined();
    expect(container.textContent).toContain('CAÇULINHA');
  });

  it('shows a human breadcrumb label for playground ops', () => {
    mockPathname = '/playground';

    const { container } = render(() => (
      <Layout>
        <div>Playground Content</div>
      </Layout>
    ));

    const breadcrumb = container.querySelector('header .text-foreground.font-medium');
    expect(breadcrumb?.textContent).toBe('Playground Ops');
  });

  it('hides playground entries for non-admin users without playground access', async () => {
    mockRole = 'user';
    mockPlaygroundEnabled = false;

    render(() => (
      <Layout>
        <div>User Content</div>
      </Layout>
    ));

    await waitFor(() => {
      expect(screen.queryAllByText('Playground')).toHaveLength(0);
    });
  });
});
