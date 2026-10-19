import { Link } from 'react-router-dom';
import { ExternalLink, Trash2, Hash } from 'lucide-react';
import type { Investigation } from '@/types/api';
import { StatusBadge, PriorityBadge } from './StatusBadge';
import { Button } from '@/components/ui/Button';
import { formatDate } from '@/lib/utils';

export interface InvestigationTableProps {
  investigations: Investigation[];
  onDelete?: (id: string) => void;
  isDeleting?: boolean;
}

export function InvestigationTable({ investigations, onDelete, isDeleting }: InvestigationTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-border bg-background-secondary text-text-muted font-mono uppercase tracking-wider">
            <th className="px-4 py-3 font-semibold">Title / Case Ref</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 font-semibold">Priority</th>
            <th className="px-4 py-3 font-semibold text-center">Evidence Count</th>
            <th className="px-4 py-3 font-semibold">Initiated</th>
            <th className="px-4 py-3 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {investigations.map((inv) => (
            <tr key={inv.id} className="hover:bg-surface-hover/70 transition-colors">
              <td className="px-4 py-3">
                <div className="space-y-0.5">
                  <Link
                    to={`/investigations/${inv.id}`}
                    className="font-medium text-text-primary hover:text-primary transition-colors text-sm"
                  >
                    {inv.title}
                  </Link>
                  <div className="flex items-center gap-1.5 text-[11px] text-text-muted font-mono">
                    <Hash className="h-3 w-3 text-text-muted shrink-0" />
                    <span>{inv.case_reference || inv.id.slice(0, 8)}</span>
                    {inv.tags && inv.tags.length > 0 && (
                      <span className="text-text-muted">· {inv.tags.slice(0, 2).join(', ')}</span>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={inv.status} />
              </td>
              <td className="px-4 py-3">
                <PriorityBadge priority={inv.priority} />
              </td>
              <td className="px-4 py-3 text-center font-mono font-medium text-text-secondary">
                {inv.evidence_count}
              </td>
              <td className="px-4 py-3 text-text-muted font-mono">
                {formatDate(inv.created_at)}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-1">
                  <Link
                    to={`/investigations/${inv.id}`}
                    className="inline-flex items-center justify-center h-7 w-7 rounded hover:bg-surface-active text-text-muted hover:text-primary transition-colors"
                    title="View Investigation Details"
                    aria-label={`View ${inv.title}`}
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onDelete(inv.id)}
                      disabled={isDeleting}
                      title="Archive Investigation"
                      aria-label={`Archive ${inv.title}`}
                      className="h-7 w-7 text-text-muted hover:text-accent-red hover:bg-red-950/30"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
