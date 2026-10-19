/**
 * EvidencePanel — Provenance and Integrity Metadata Card.
 *
 * Displays:
 * - Evidence count & duplicate skip statistics
 * - Provider source info (Etherscan API V2, Chain ID 1)
 * - SHA-256 integrity hash verification notice
 * - Target type & resolution details
 */
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ShieldCheck, Database, FileText, AlertCircle } from 'lucide-react';
import type { BlockchainInvestigateResponse } from '@/types/blockchain';

interface EvidencePanelProps {
  investigationResult: BlockchainInvestigateResponse;
  className?: string;
}

export function EvidencePanel({ investigationResult, className }: EvidencePanelProps) {
  const {
    target,
    target_type,
    evidence_created_count,
    evidence_skipped_duplicates_count,
    transactions_count,
    token_transfers_count,
    warnings,
    investigation_id,
  } = investigationResult;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-accent-green" />
          Evidence & Provenance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {warnings && warnings.length > 0 && (
          <div className="rounded border border-amber-800 bg-amber-950/20 p-3 text-xs text-accent-amber space-y-1">
            <div className="flex items-center gap-1.5 font-medium">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Warnings / Notices</span>
            </div>
            <ul className="list-disc pl-5 space-y-0.5">
              {warnings.map((warn, i) => (
                <li key={i}>{warn}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="rounded border border-border bg-background p-2.5">
            <span className="text-text-muted block mb-1">Target Type</span>
            <Badge variant="info">
              {target_type === 'wallet_address' ? 'Wallet Address' : 'Transaction Hash'}
            </Badge>
          </div>
          <div className="rounded border border-border bg-background p-2.5">
            <span className="text-text-muted block mb-1">New Evidence Saved</span>
            <span className="font-mono text-base font-bold text-accent-green">
              {evidence_created_count}
            </span>
          </div>
          <div className="rounded border border-border bg-background p-2.5">
            <span className="text-text-muted block mb-1">Duplicates Skipped</span>
            <span className="font-mono text-base font-bold text-text-secondary">
              {evidence_skipped_duplicates_count}
            </span>
          </div>
          <div className="rounded border border-border bg-background p-2.5">
            <span className="text-text-muted block mb-1">Total Records</span>
            <span className="font-mono text-base font-bold text-text-primary">
              {transactions_count + token_transfers_count}
            </span>
          </div>
        </div>

        <div className="border-t border-border pt-3 space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-text-muted flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-primary" /> Provider Source
            </span>
            <span className="font-mono text-text-primary">Etherscan API V2 (Ethereum Mainnet / Chain ID 1)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-text-muted flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-primary" /> Case ID
            </span>
            <span className="font-mono text-text-secondary">{investigation_id}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-text-muted">Target Entity</span>
            <span className="font-mono text-text-primary truncate max-w-[260px]" title={target}>
              {target}
            </span>
          </div>
        </div>

        <div className="rounded bg-background-secondary p-3 border border-border-subtle text-[11px] text-text-muted leading-relaxed">
          <p className="font-medium text-text-secondary mb-1">Integrity Assurance & Scope Notice:</p>
          Each ingested record is serialized to deterministic canonical JSON and signed with a SHA-256
          checksum for database tamper-detection. This hash verifies that the stored database representation
          has not been altered or corrupted post-ingestion. It does not independently attest to the truthfulness
          of the upstream provider.
        </div>
      </CardContent>
    </Card>
  );
}
