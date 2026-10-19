import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, ShieldAlert } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { useCreateInvestigation } from '@/hooks/useInvestigations';
import { getErrorMessage } from '@/lib/utils';
import type { InvestigationPriority, InvestigationStatus } from '@/types/api';

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft (Initial Scoping)' },
  { value: 'active', label: 'Active (Ongoing Forensics)' },
  { value: 'on_hold', label: 'On Hold (Awaiting External Intel)' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low (Ad-hoc Check)' },
  { value: 'medium', label: 'Medium (Standard Case)' },
  { value: 'high', label: 'High (Active Incident)' },
  { value: 'critical', label: 'Critical (High-Value Exploit / Ransom)' },
];

export function NewInvestigationPage() {
  const navigate = useNavigate();
  const createMutation = useCreateInvestigation();

  const [form, setForm] = useState({
    title: '',
    description: '',
    status: 'draft' as InvestigationStatus,
    priority: 'medium' as InvestigationPriority,
    case_reference: '',
    tags: '',
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!form.title.trim()) {
      errors.title = 'Investigation title is strictly required.';
    } else if (form.title.trim().length > 255) {
      errors.title = 'Title cannot exceed 255 characters.';
    }

    if (form.case_reference.trim().length > 100) {
      errors.case_reference = 'Case reference cannot exceed 100 characters.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const parsedTags = form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    try {
      const created = await createMutation.mutateAsync({
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        status: form.status,
        priority: form.priority,
        case_reference: form.case_reference.trim() || undefined,
        tags: parsedTags.length > 0 ? parsedTags : undefined,
      });

      navigate(`/investigations/${created.id}`);
    } catch (err) {
      console.error('Failed to create investigation', err);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          to="/investigations"
          className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors font-mono"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>RETURN_TO_CATALOG</span>
        </Link>
      </div>

      <PageHeader
        title="Initiate Forensic Case"
        description="Establish an authenticated investigation container for blockchain transactions and IOC correlations."
      />

      <Card>
        <CardContent className="pt-2">
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <Input
              label="Investigation Title *"
              placeholder="e.g., Exploit Tracing - Protocol Vault Drain - Oct 2026"
              value={form.title}
              onChange={(e) => {
                setForm((f) => ({ ...f, title: e.target.value }));
                if (validationErrors.title) {
                  setValidationErrors((v) => ({ ...v, title: '' }));
                }
              }}
              error={validationErrors.title}
              hint="Descriptive name identifying the scope or incident."
              required
              autoFocus
            />

            <Textarea
              label="Investigation Brief / Objective"
              placeholder="Document the precipitating incident, known victim wallets, suspected threat actor affiliations, or initial triage notes..."
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={4}
              hint="Analytical conclusions will be appended later via correlated evidence."
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Initial Lifecycle Status"
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as InvestigationStatus }))}
                options={STATUS_OPTIONS}
              />

              <Select
                label="Incident Severity / Priority"
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value as InvestigationPriority }))}
                options={PRIORITY_OPTIONS}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Internal Case Reference (Optional)"
                placeholder="e.g., SEC-INC-2026-904"
                value={form.case_reference}
                onChange={(e) => {
                  setForm((f) => ({ ...f, case_reference: e.target.value }));
                  if (validationErrors.case_reference) {
                    setValidationErrors((v) => ({ ...v, case_reference: '' }));
                  }
                }}
                error={validationErrors.case_reference}
                hint="Identifier used in internal ticket tracking systems."
              />

              <Input
                label="Taxonomy Tags"
                placeholder="defi, tornado_cash, ethereum, botnet"
                value={form.tags}
                onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
                hint="Comma-separated tokens for cross-case correlation."
              />
            </div>

            <div className="rounded border border-border/80 bg-background-secondary/50 p-3 text-[11px] text-text-muted flex items-start gap-2.5">
              <ShieldAlert className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <span>
                All created investigation records are assigned an immutable UUID and cryptographically tracked UTC timestamps.
              </span>
            </div>

            {createMutation.isError && (
              <ErrorAlert
                title="Creation Failed"
                message={getErrorMessage(createMutation.error)}
              />
            )}

            <div className="flex items-center gap-3 pt-2">
              <Button type="submit" variant="primary" loading={createMutation.isPending}>
                Establish Investigation
              </Button>
              <Link to="/investigations">
                <Button type="button" variant="ghost" disabled={createMutation.isPending}>
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
