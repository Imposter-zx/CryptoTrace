import { Link } from 'react-router-dom';
import {
  FolderSearch,
  Database,
  Activity,
  FilePlus2,
  AlertTriangle,
  ArrowRight,
  Shield,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { MetricCard } from '@/components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { StatusBadge } from '@/components/investigations/StatusBadge';
import { useInvestigations, useInvestigationSummary } from '@/hooks/useInvestigations';
import { formatDate } from '@/lib/utils';

export function DashboardPage() {
  const { data: investigations, isLoading, isError, refetch } = useInvestigations({ page_size: 5 });
  const { data: summary, isLoading: summaryLoading } = useInvestigationSummary();

  const statusCounts = summary?.status_counts || {};
  const totalInvestigations = investigations?.total || 0;
  const activeCount = statusCounts['active'] || 0;
  const criticalPriorityCount = statusCounts['critical'] || 0;
  const evidenceCountTotal = investigations?.items.reduce((acc, inv) => acc + inv.evidence_count, 0) || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Forensic Operations Dashboard"
        description="Real-time oversight of cryptocurrency investigations and evidence feeds."
        actions={
          <div className="flex gap-2">
            <Link to="/blockchain">
              <Button variant="secondary" size="sm">
                <Shield className="h-3.5 w-3.5 text-primary" />
                <span>Blockchain Forensics</span>
              </Button>
            </Link>
            <Link to="/investigations/new">
              <Button variant="primary" size="sm">
                <FilePlus2 className="h-3.5 w-3.5" />
                <span>Initiate Investigation</span>
              </Button>
            </Link>
          </div>
        }
      />

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Investigations"
          value={totalInvestigations}
          icon={<FolderSearch className="h-4 w-4" />}
          subtitle="All active and pending cases"
          loading={isLoading}
        />
        <MetricCard
          title="Active Traces"
          value={activeCount}
          icon={<Activity className="h-4 w-4" />}
          subtitle="Currently under investigation"
          loading={summaryLoading}
        />
        <MetricCard
          title="Evidence Records"
          value={evidenceCountTotal}
          icon={<Database className="h-4 w-4" />}
          subtitle="Chain transactions, wallets & IOCs"
          loading={isLoading}
        />
        <MetricCard
          title="Critical Priority"
          value={criticalPriorityCount}
          icon={<AlertTriangle className="h-4 w-4" />}
          subtitle="Immediate action required"
          loading={summaryLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Cases */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Investigations</CardTitle>
              <Link
                to="/investigations"
                className="text-xs font-mono text-primary hover:text-primary-hover flex items-center gap-1"
              >
                <span>EXPLORE_ALL</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="py-12">
                  <LoadingSpinner label="Querying forensic registry..." />
                </div>
              )}

              {isError && (
                <ErrorAlert
                  title="Backend Disconnected"
                  message="Could not communicate with the CryptoTrace API service. Please verify your local backend server is running."
                  onRetry={() => refetch()}
                />
              )}

              {!isLoading && !isError && investigations?.items.length === 0 && (
                <EmptyState
                  icon={<FolderSearch className="h-6 w-6" />}
                  title="No investigations initiated"
                  description="Begin a forensic blockchain tracing workflow by creating your first case record."
                  action={
                    <Link to="/investigations/new">
                      <Button variant="primary" size="sm">
                        <FilePlus2 className="h-3.5 w-3.5" />
                        Create Investigation
                      </Button>
                    </Link>
                  }
                />
              )}

              {!isLoading && !isError && investigations?.items && investigations.items.length > 0 && (
                <div className="divide-y divide-border/60">
                  {investigations.items.map((inv) => (
                    <div key={inv.id} className="py-3 flex items-center justify-between gap-4">
                      <div className="min-w-0 space-y-1">
                        <Link
                          to={`/investigations/${inv.id}`}
                          className="text-sm font-medium text-text-primary hover:text-primary transition-colors truncate block"
                        >
                          {inv.title}
                        </Link>
                        <div className="flex items-center gap-2 text-[11px] text-text-muted font-mono">
                          <span>REF: {inv.case_reference || inv.id.slice(0, 8)}</span>
                          <span>·</span>
                          <span>CREATED: {formatDate(inv.created_at)}</span>
                        </div>
                      </div>
                      <div className="shrink-0">
                        <StatusBadge status={inv.status} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Status Breakdown & Security Notice */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Status Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <div className="py-8">
                  <LoadingSpinner size="sm" />
                </div>
              ) : Object.keys(statusCounts).length === 0 ? (
                <p className="text-xs text-text-muted font-mono">NO_DATA_AVAILABLE</p>
              ) : (
                <div className="space-y-2.5">
                  {[
                    { label: 'Active', key: 'active', color: 'bg-emerald-500' },
                    { label: 'Draft', key: 'draft', color: 'bg-slate-500' },
                    { label: 'On Hold', key: 'on_hold', color: 'bg-amber-500' },
                    { label: 'Closed', key: 'closed', color: 'bg-zinc-600' },
                  ].map(({ label, key, color }) => (
                    <div key={key} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${color}`} />
                        <span className="text-text-secondary">{label}</span>
                      </div>
                      <span className="font-mono font-medium text-text-primary">
                        {statusCounts[key] || 0}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-background-secondary/60">
            <div className="flex items-start gap-3">
              <Shield className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-xs font-semibold text-text-primary font-mono uppercase">Forensic Integrity</p>
                <p className="text-[11px] text-text-muted leading-relaxed">
                  Observed raw facts are strictly segregated from analyst hypotheses. No automatic funds transfer or wallet key storage is permitted.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
