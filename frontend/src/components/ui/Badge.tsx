import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-mono font-medium ring-1 ring-inset',
  {
    variants: {
      variant: {
        default: 'bg-surface text-text-secondary ring-border',
        draft: 'bg-slate-800/80 text-slate-300 ring-slate-600',
        active: 'bg-emerald-950/70 text-accent-green ring-emerald-700/60',
        on_hold: 'bg-amber-950/70 text-accent-amber ring-amber-700/60',
        closed: 'bg-slate-900 text-text-muted ring-slate-700',
        archived: 'bg-zinc-900 text-zinc-500 ring-zinc-700',
        low: 'bg-slate-800 text-slate-300 ring-slate-600',
        medium: 'bg-cyan-950/70 text-primary ring-cyan-700/60',
        high: 'bg-amber-950/70 text-accent-amber ring-amber-700/60',
        critical: 'bg-red-950/80 text-accent-red ring-red-700/60',
        success: 'bg-emerald-950/70 text-accent-green ring-emerald-700/60',
        warning: 'bg-amber-950/70 text-accent-amber ring-amber-700/60',
        error: 'bg-red-950/80 text-accent-red ring-red-700/60',
        info: 'bg-cyan-950/70 text-primary ring-cyan-700/60',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
