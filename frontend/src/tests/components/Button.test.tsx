import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders button label', () => {
    render(<Button>Run Analysis</Button>);
    expect(screen.getByText('Run Analysis')).toBeInTheDocument();
  });

  it('triggers onClick handler on click', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Trigger</Button>);
    fireEvent.click(screen.getByText('Trigger'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled and displays spinner when loading is true', () => {
    render(<Button loading>Submit Trace</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button.querySelector('svg')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is provided', () => {
    render(<Button disabled>Disabled Action</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
