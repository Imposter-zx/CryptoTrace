import { Badge } from '@/components/ui/Badge';
import type { InvestigationPriority, InvestigationStatus } from '@/types/api';

const STATUS_LABELS: Record<InvestigationStatus, string> = {
  draft: 'DRAFT',
  active: 'ACTIVE',
  on_hold: 'ON HOLD',
  closed: 'CLOSED',
  archived: 'ARCHIVED',
};

const PRIORITY_LABELS: Record<InvestigationPriority, string> = {
  low: 'LOW',
  medium: 'MED',
  high: 'HIGH',
  critical: 'CRIT',
};

export function StatusBadge({ status }: { status: InvestigationStatus }) {
  return <Badge variant={status}>{STATUS_LABELS[status] || status}</Badge>;
}

export function PriorityBadge({ priority }: { priority: InvestigationPriority }) {
  return <Badge variant={priority}>{PRIORITY_LABELS[priority] || priority}</Badge>;
}
