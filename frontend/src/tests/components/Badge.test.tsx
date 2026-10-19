import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/Badge';

describe('Badge', () => {
  it('renders children text correctly', () => {
    render(<Badge>Active Case</Badge>);
    expect(screen.getByText('Active Case')).toBeInTheDocument();
  });

  it('applies active variant styles', () => {
    render(<Badge variant="active">Active</Badge>);
    const badge = screen.getByText('Active');
    expect(badge).toHaveClass('text-accent-green');
  });

  it('applies critical variant styles', () => {
    render(<Badge variant="critical">Critical</Badge>);
    const badge = screen.getByText('Critical');
    expect(badge).toHaveClass('text-accent-red');
  });
});
