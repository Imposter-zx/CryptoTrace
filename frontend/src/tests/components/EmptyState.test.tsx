import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from '@/components/ui/EmptyState';

describe('EmptyState', () => {
  it('renders title and description properly', () => {
    render(
      <EmptyState
        title="No investigations found"
        description="Try adjusting your search criteria."
      />
    );
    expect(screen.getByText('No investigations found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your search criteria.')).toBeInTheDocument();
  });

  it('renders action node when provided', () => {
    render(
      <EmptyState
        title="No records"
        action={<button>Create First Case</button>}
      />
    );
    expect(screen.getByRole('button', { name: 'Create First Case' })).toBeInTheDocument();
  });
});
