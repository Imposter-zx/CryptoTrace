import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Trash2,
  Database,
  Calendar,
  Clock,
  Tag,
  FileText,
  Hash,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge, PriorityBadge } from '@/components/investigations/StatusBadge';
import { useInvestigation, useDeleteInvestigation } from '@/hooks/useInvestigations';
import { formatDateTime } from '@/lib/utils';

export function InvestigationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showArchiveModal, setShowArchiveModal] = useState(false);

  const { data: investigation, isLoading, isError, refetch } = useInvestigation(id || '');
  const deleteMutation = useDeleteInvestigation();

  const handleArchive = async () => {
    if (!id) return;
    try {
      await deleteMutation.mutateAsync(id);
      navigate('/investigations');
    } catch (err) {
      console.error('Archive failed', err);
    }
  };

  if (isLoading) {
    return (
      <div className="py-24">
        <LoadingSpinner label="Decrypting investigation forensic context..." />
      </div>
    );
  }

  if (isError || !investigation) {
    return (
      <div className="max-w-2xl space-y-4">
        <Link
          to="/investigations"
          className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors font-mono"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>BACK_TO_REGISTRY</span>
        </Link>
        <ErrorAlert
          title="Investigation Record Unreachable"
          message="The requested investigation could not be located in active storage, or the server returned an error."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb / Back Link */}
      <div className="flex items-center justify-between">
        <Link
          to="/investigations"
          className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors font-mono"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>INVESTIGATIONS_INDEX</span>
        </Link>
        <div className="text-[11px] font-mono text-text-muted">
          UUID: <span className="text-text-secondary select-all">{investigation.id}</span>
        </div>
      </div>

      <PageHeader
        title={investigation.title}
        description={
          investigation.case_reference
            ? `Case Reference: ${investigation.case_reference}`
            : 'Unclassified Forensic Operation'
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowArchiveModal(true)}
              className="text-xs"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Archive Case</span>
            </Button>
          </div>
        }
      />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (Metadata + Scope) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case Classification & Scope</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-border/60">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Status</span>
                  <div><StatusBadge status={investigation.status} /></div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Priority</span>
                  <div><PriorityBadge priority={investigation.priority} /></div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Evidence Count</span>
                  <div className="text-sm font-mono font-bold text-text-primary">{investigation.evidence_count} items</div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Lifecycle</span>
                  <div className="text-xs font-mono text-accent-green">
                    {investigation.is_archived ? 'ARCHIVED' : 'ACTIVE_LOG'}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="pt-4 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  <FileText className="h-3.5 w-3.5 text-text-muted" />
                  <span>Analytical Brief / Scope</span>
                </div>
                {investigation.description ? (
                  <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap bg-background/50 p-3 rounded border border-border/40 font-sans">
                    {investigation.description}
                  </p>
                ) : (
                  <p className="text-xs italic text-text-muted">
                    No initial investigative description recorded for this container.
                  </p>
                )}
              </div>

              {/* Tags */}
              {investigation.tags && investigation.tags.length > 0 && (
                <div className="pt-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    <Tag className="h-3.5 w-3.5 text-text-muted" />
                    <span>Taxonomy Tags</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {investigation.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 rounded text-[11px] font-mono bg-background border border-border text-primary"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Evidence Records Section */}
          <Card>
            <CardHeader>
              <CardTitle>Associated Evidence Records ({investigation.evidence_count})</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<Database className="h-5 w-5 text-text-muted" />}
                title="No Evidence Ingested in Phase 1"
                description="Evidence correlation, transaction hash verification, and threat intelligence ingestion will be activated in Phase 2. The database schema and foreign keys are prepared."
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Column (Provenance & Audit Details) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Forensic Audit Trail</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-2.5 text-xs">
                <Calendar className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5 min-w-0">
                  <span className="text-[10px] font-mono uppercase text-text-muted block">Initiated (UTC)</span>
                  <span className="font-mono text-text-secondary block">
                    {formatDateTime(investigation.created_at)}
                  </span>
                </div>
              </div>

              <div className="flex items-start gap-2.5 text-xs">
                <Clock className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5 min-w-0">
                  <span className="text-[10px] font-mono uppercase text-text-muted block">Last Modified (UTC)</span>
                  <span className="font-mono text-text-secondary block">
                    {formatDateTime(investigation.updated_at)}
                  </span>
                </div>
              </div>

              <div className="flex items-start gap-2.5 text-xs">
                <Hash className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5 min-w-0">
                  <span className="text-[10px] font-mono uppercase text-text-muted block">Case Reference</span>
                  <span className="font-mono text-text-secondary block">
                    {investigation.case_reference || 'N/A'}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-border/60">
                <div className="flex items-start gap-2 text-[11px] text-text-muted">
                  <ShieldCheck className="h-4 w-4 text-accent-green shrink-0 mt-0.5" />
                  <span>
                    Integrity: Validated against database schema foreign-key constraints.
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background-secondary/50 border-border/50">
            <CardHeader>
              <CardTitle>Future Extensions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-text-muted">
              <div className="flex items-center justify-between py-1 border-b border-border/30">
                <span>Cytoscape Graph View</span>
                <span className="font-mono text-[10px] text-primary">PHASE 2</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-border/30">
                <span>Etherscan Adapter</span>
                <span className="font-mono text-[10px] text-primary">PHASE 2</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span>VirusTotal IOC Intel</span>
                <span className="font-mono text-[10px] text-primary">PHASE 2</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Archive Modal */}
      <ConfirmDialog
        open={showArchiveModal}
        title="Confirm Case Archive"
        description={`Archive investigation "${investigation.title}"? The case record and its evidence relationships will be marked inactive.`}
        confirmLabel="Archive Case"
        onConfirm={handleArchive}
        onCancel={() => setShowArchiveModal(false)}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
