import { useQuery } from '@tanstack/react-query';
import {
  Server,
  Database,
  Layers,
  ShieldCheck,
  RefreshCw,
  HardDrive,
  FileCheck2,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { healthApi } from '@/services/api';
import { useBlockchainStatus } from '@/hooks/useBlockchain';

export function SettingsPage() {
  const {
    data: health,
    isLoading,
    isRefetching,
    refetch,
  } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 30_000,
  });

  const { data: blockchainStatus } = useBlockchainStatus();

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Forensic Station Configuration & Health"
        description="Environment diagnostics, storage integrity policies, and external provider adapter configurations."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading || isRefetching}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefetching ? 'animate-spin' : ''}`} />
            <span>Diagnostic Check</span>
          </Button>
        }
      />

      {/* Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle>System Diagnostic Status</CardTitle>
          <div className="flex items-center gap-1.5 text-xs font-mono text-text-muted">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>DIAGNOSTIC_SERVICE_ACTIVE</span>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8">
              <LoadingSpinner label="Querying local subsystem health..." />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-3.5 rounded border border-border bg-background/60 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-4 w-4 text-primary" />
                    <span className="text-xs font-medium text-text-primary">FastAPI Backend</span>
                  </div>
                  <Badge variant={health?.status === 'ok' ? 'active' : 'error'}>
                    {health?.status === 'ok' ? 'ONLINE' : 'OFFLINE'}
                  </Badge>
                </div>
                <div className="text-[11px] font-mono text-text-muted flex justify-between">
                  <span>Version:</span>
                  <span className="text-text-secondary">{health?.version || '0.1.0'}</span>
                </div>
              </div>

              <div className="p-3.5 rounded border border-border bg-background/60 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-primary" />
                    <span className="text-xs font-medium text-text-primary">PostgreSQL</span>
                  </div>
                  <Badge variant={health?.database === 'ok' ? 'active' : 'error'}>
                    {health?.database === 'ok' ? 'CONNECTED' : 'UNAVAILABLE'}
                  </Badge>
                </div>
                <div className="text-[11px] font-mono text-text-muted flex justify-between">
                  <span>Schema:</span>
                  <span className="text-text-secondary">v1_initial</span>
                </div>
              </div>

              <div className="p-3.5 rounded border border-border bg-background/60 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-4 w-4 text-primary" />
                    <span className="text-xs font-medium text-text-primary">Local Storage</span>
                  </div>
                  <Badge variant="active">ISOLATED</Badge>
                </div>
                <div className="text-[11px] font-mono text-text-muted flex justify-between">
                  <span>Mode:</span>
                  <span className="text-text-secondary">Local-First</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Forensic Policy Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Forensic Integrity Safeguards</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {[
              {
                title: 'Raw Data Segregation',
                desc: 'Observed blockchain receipts and threat reports are preserved as immutable payloads with SHA-256 integrity verification.',
                status: 'ENFORCED',
                icon: FileCheck2,
              },
              {
                title: 'No Autonomous Wallet Execution',
                desc: 'Signing mechanisms, private key collection, and automated fund transfers are disabled by architectural policy.',
                status: 'ENFORCED',
                icon: ShieldCheck,
              },
              {
                title: 'Multi-Source Provenance Verification',
                desc: 'Attributions must reference independent corroborated evidence sources before being accepted as factual conclusions.',
                status: 'ENFORCED',
                icon: Layers,
              },
            ].map(({ title, desc, status, icon: Icon }) => (
              <div
                key={title}
                className="flex items-start justify-between gap-4 p-3 rounded border border-border/80 bg-background/40"
              >
                <div className="flex items-start gap-3">
                  <Icon className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-text-primary">{title}</h4>
                    <p className="text-[11px] text-text-muted mt-0.5 leading-relaxed">{desc}</p>
                  </div>
                </div>
                <Badge variant="active">{status}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Adapter Extensions */}
      <Card>
        <CardHeader>
          <CardTitle>External Adapter Extension Points</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-text-muted leading-relaxed">
            In accordance with Phase 1 design, external network adapters are abstracted behind provider contracts. Configuration parameters will become editable as provider adapters are activated in Phase 2 and 3.
          </p>
          <div className="divide-y divide-border/60">
            <div className="py-2.5 flex items-center justify-between text-xs">
              <div>
                <span className="font-medium text-text-primary">Etherscan API V2 Adapter</span>
                <span className="text-[11px] text-text-muted ml-2 font-mono">(Blockchain Forensics · Chain ID 1)</span>
              </div>
              <Badge
                variant={
                  blockchainStatus?.operational_status === 'reachable'
                    ? 'active'
                    : blockchainStatus?.operational_status === 'ready'
                    ? 'info'
                    : blockchainStatus?.operational_status === 'unconfigured'
                    ? 'default'
                    : 'warning'
                }
              >
                {blockchainStatus
                  ? `${blockchainStatus.operational_status.toUpperCase()}`
                  : 'PHASE 2 (ACTIVE)'}
              </Badge>
            </div>
            {[
              { name: 'Bitcoin Mempool Adapter', category: 'Blockchain Forensics', phase: 'Phase 3' },
              { name: 'VirusTotal Threat Intel', category: 'Threat Intelligence', phase: 'Phase 3' },
              { name: 'Static Binary / YARA Engine', category: 'Malware Analysis', phase: 'Phase 3' },
              { name: 'Hybrid AI Correlation Agent', category: 'Reasoning Engine', phase: 'Phase 3' },
            ].map(({ name, category, phase }) => (
              <div key={name} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <span className="font-medium text-text-primary">{name}</span>
                  <span className="text-[11px] text-text-muted ml-2 font-mono">({category})</span>
                </div>
                <Badge variant="default">{phase}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
