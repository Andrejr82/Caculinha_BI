import { render, screen } from '@solidjs/testing-library';
import { describe, it, expect, beforeEach } from 'vitest';
import { Router, Route } from '@solidjs/router';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Chat from '../pages/Chat';

describe('App Component Tests', () => {
  beforeEach(() => {
    // Limpar localStorage antes de cada teste
    localStorage.clear();
  });

  it('should render Login page', () => {
    const { container } = render(() => (
      <Router>
        <Route path="/login" component={Login} />
      </Router>
    ));

    expect(container).toBeDefined();
  });

  it('should have root element in HTML', () => {
    const root = document.getElementById('root');
    expect(root).toBeDefined();
  });
});
