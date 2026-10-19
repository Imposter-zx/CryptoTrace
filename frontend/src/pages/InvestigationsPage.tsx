import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FilePlus2, FolderSearch, Search, X } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { InvestigationTable } from '@/components/investigations/InvestigationTable';
import { useInvestigations, useDeleteInvestigation } from '@/hooks/useInvestigations';

const STATUS_FILTERS = [
  { value: '', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'draft', label: 'Draft' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'closed', label: 'Closed' },
];

export function InvestigationsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useInvestigations({
    page,
    page_size: 15,
    status: status || undefined,
    search: search.trim() || undefined,
  });

  const deleteMutation = useDeleteInvestigation();

  const handleConfirmArchive = async () => {
    if (!deleteTargetId) return;
    try {
      await deleteMutation.mutateAsync(deleteTargetId);
      setDeleteTargetId(null);
    } catch (err) {
      console.error('Failed to archive investigation', err);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Investigations Registry"
        description="Search, filter, and audit active cryptocurrency forensic investigations."
        actions={
          <Link to="/investigations/new">
            <Button variant="primary" size="sm">
              <FilePlus2 className="h-3.5 w-3.5" />
              <span>New Investigation</span>
            </Button>
          </Link>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="search"
            placeholder="Search by title, description, or case reference..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs rounded border border-border bg-background text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
          />
        </div>

        <div className="w-full sm:w-48">
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 text-xs rounded border border-border bg-background text-text-primary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value} className="bg-background-secondary text-text-primary">
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {(search || status) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearch('');
              setStatus('');
              setPage(1);
            }}
            className="text-text-muted hover:text-text-primary text-xs"
          >
            <X className="h-3.5 w-3.5" />
            <span>Reset</span>
          </Button>
        )}
      </div>

      {/* Main Content Area */}
      {isLoading && (
        <div className="py-20">
          <LoadingSpinner label="Loading forensic records..." />
        </div>
      )}

      {isError && (
        <ErrorAlert
          title="Query Error"
          message="Failed to retrieve investigations from the database. Please ensure backend services are operating."
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && data && data.items.length === 0 && (
        <EmptyState
          icon={<FolderSearch className="h-6 w-6" />}
          title={search || status ? 'No Matching Records' : 'No Investigations Found'}
          description={
            search || status
              ? 'No investigations match your active query criteria. Try clearing search filters.'
              : 'The investigation catalog is empty. Create a new investigation record to begin forensic tracking.'
          }
          action={
            !search && !status ? (
              <Link to="/investigations/new">
                <Button variant="primary" size="sm">
                  <FilePlus2 className="h-3.5 w-3.5" />
                  <span>Initiate First Case</span>
                </Button>
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <div className="space-y-4">
          <InvestigationTable
            investigations={data.items}
            onDelete={(id) => setDeleteTargetId(id)}
            isDeleting={deleteMutation.isPending}
          />

          {/* Pagination Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 text-xs text-text-muted font-mono">
            <div>
              Showing {((data.page - 1) * data.page_size) + 1} -{' '}
              {Math.min(data.page * data.page_size, data.total)} of {data.total} records
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <span>
                Page {data.page} / {data.pages || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.pages}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Archive Modal */}
      <ConfirmDialog
        open={Boolean(deleteTargetId)}
        title="Confirm Case Archive"
        description="Archiving this investigation will mark it inactive and remove it from standard forensic listings. Underlying evidence records will remain tamper-evident in cold storage."
        confirmLabel="Archive Case"
        onConfirm={handleConfirmArchive}
        onCancel={() => setDeleteTargetId(null)}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
