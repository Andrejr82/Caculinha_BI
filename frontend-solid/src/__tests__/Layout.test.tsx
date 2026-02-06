import { render } from '@solidjs/testing-library';
import { describe, it, expect, beforeEach } from 'vitest';
import { Router } from '@solidjs/router';
import Layout from '../Layout';

describe('Layout Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should render Layout component', () => {
    const { container } = render(() => (
      <Router>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Router>
    ));

    expect(container).toBeDefined();
  });

  it('should display Agent BI branding', () => {
    const { container } = render(() => (
      <Router>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Router>
    ));

    const text = container.textContent;
    expect(text).toContain('Agent BI');
  });
});
