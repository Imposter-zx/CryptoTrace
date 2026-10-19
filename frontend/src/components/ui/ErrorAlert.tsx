import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ErrorAlertProps {
  title?: string;
  message: string;
  className?: string;
  onRetry?: () => void;
}

export function ErrorAlert({ title = 'Error Encountered', message, className, onRetry }: ErrorAlertProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border border-red-800/80 bg-red-950/40 p-3.5',
        className
      )}
      role="alert"
    >
      <AlertTriangle className="h-4 w-4 text-accent-red shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-accent-red uppercase tracking-wider">{title}</p>
        <p className="text-xs text-text-secondary mt-0.5">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-xs font-medium text-primary hover:text-primary-hover hover:underline cursor-pointer"
          >
            Retry operation →
          </button>
        )}
      </div>
    </div>
  );
}
