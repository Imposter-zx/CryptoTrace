import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from './Card';

export interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  subtitle?: string;
  className?: string;
  loading?: boolean;
}

export function MetricCard({ title, value, icon, subtitle, className, loading }: MetricCardProps) {
  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">{title}</p>
          {loading ? (
            <div className="h-7 w-20 bg-surface-hover animate-pulse rounded mt-1" />
          ) : (
            <p className="text-2xl font-bold text-text-primary font-mono tracking-tight">{value}</p>
          )}
          {subtitle && !loading && (
            <p className="text-xs text-text-muted">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="rounded border border-border bg-background p-2 text-primary">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
