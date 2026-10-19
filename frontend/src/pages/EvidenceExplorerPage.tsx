import { Database, ShieldAlert, Cpu, Network, FileCode } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export function EvidenceExplorerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Evidence Explorer & Taxonomy"
        description="Global indexing of cryptocurrency transactions, wallet clusters, network artifacts, and file hashes."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <Network className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wide">Blockchain Entities</span>
          </div>
          <p className="text-xs text-text-muted leading-relaxed">
            Support for transaction hashes, wallet addresses, and exchange accounts across EVM, Bitcoin, and Tron protocols.
          </p>
          <div className="mt-3">
            <Badge variant="medium">Schema Ready</Badge>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-2">
            <FileCode className="h-4 w-4 text-accent-green" />
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wide">Threat Intel Artifacts</span>
          </div>
          <p className="text-xs text-text-muted leading-relaxed">
            Domain names, IP infrastructure, autonomous systems, and external threat actor attribution dossiers.
          </p>
          <div className="mt-3">
            <Badge variant="medium">Schema Ready</Badge>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-2">
            <Cpu className="h-4 w-4 text-accent-amber" />
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wide">Static Malware IOCs</span>
          </div>
          <p className="text-xs text-text-muted leading-relaxed">
            Cryptographic SHA-256 hashes, extracted wallet clipper strings, and isolated static analysis signatures.
          </p>
          <div className="mt-3">
            <Badge variant="medium">Schema Ready</Badge>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Evidence Catalog Status (Phase 1 Foundation)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-border bg-background/50 p-6 text-center space-y-3">
            <div className="inline-flex rounded-full bg-surface p-3 ring-1 ring-border text-primary">
              <Database className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-text-primary">
              Evidence Schema & Storage Pipeline Ready
            </h3>
            <p className="text-xs text-text-muted max-w-md mx-auto leading-relaxed">
              Phase 1 establishes the relational models (`evidence`, `evidence_sources`, and `investigation_relationships`) with integrity hashes and qualitative assessment fields. Ingestion adapters (Etherscan, VirusTotal) will be connected in Phase 2.
            </p>
          </div>

          <div className="p-4 rounded border border-border/80 bg-background-secondary/40 text-xs text-text-secondary space-y-2">
            <div className="flex items-center gap-2 font-mono text-[11px] text-primary">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>FORENSIC_INTEGRITY_PRINCPLE</span>
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Every evidence record preserves its source provider, collection timestamp, raw payload integrity hash, and analyst evaluation rationale. Raw observed data is strictly separated from subjective conclusions.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
