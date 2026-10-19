/**
 * BlockchainInvestigationPage — Main investigative UI for Phase 2 Ethereum forensics.
 */
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Shield,
  Layers,
  ArrowRightLeft,
  ExternalLink,
  AlertTriangle,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { EmptyState } from '@/components/ui/EmptyState';
import { InvestigationGraph } from '@/components/blockchain/InvestigationGraph';
import { TransactionExplorer } from '@/components/blockchain/TransactionExplorer';
import { EvidencePanel } from '@/components/blockchain/EvidencePanel';
import {
  useBlockchainStatus,
  useBlockchainInvestigation,
  useAddressTransactions,
  useAddressTokenTransfers,
  useTransaction,
  useExpandInvestigation,
} from '@/hooks/useBlockchain';
import type {
  BlockchainInvestigateResponse,
  CytoscapeNodeData,
} from '@/types/blockchain';
import { getErrorMessage } from '@/lib/utils';

const LIMIT_OPTIONS = [
  { value: '10', label: '10 records' },
  { value: '25', label: '25 records (Default)' },
  { value: '50', label: '50 records' },
  { value: '100', label: '100 records' },
];

export function BlockchainInvestigationPage() {
  const [target, setTarget] = useState('');
  const [customTitle, setCustomTitle] = useState('');
  const [limit, setLimit] = useState(25);
  const [includeTokens, setIncludeTokens] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'graph' | 'transactions'>('graph');
  const [investigationResult, setInvestigationResult] = useState<BlockchainInvestigateResponse | null>(null);
  const [selectedNode, setSelectedNode] = useState<CytoscapeNodeData | null>(null);

  // Status check
  const { data: statusData, isLoading: statusLoading } = useBlockchainStatus();

  // Investigation mutation
  const investigateMutation = useBlockchainInvestigation();

  // Expansion mutation
  const expandMutation = useExpandInvestigation(investigationResult?.investigation_id ?? '');

  // Fetch transactions if target is an address
  const isAddress = investigationResult?.target_type === 'wallet_address';
  const { data: addrTxData } = useAddressTransactions(
    isAddress ? investigationResult.target : '',
    { limit }
  );
  const { data: addrTokenData } = useAddressTokenTransfers(
    isAddress && includeTokens ? investigationResult.target : '',
    { limit }
  );

  // Fetch transaction if target is a tx hash
  const isTxHash = investigationResult?.target_type === 'transaction_hash';
  const { data: singleTxData } = useTransaction(
    isTxHash ? investigationResult.target : ''
  );

  const validateTarget = (val: string): boolean => {
    const trimmed = val.trim();
    if (!trimmed) {
      setValidationError('Target address or transaction hash is required.');
      return false;
    }
    // Check Ethereum address: 0x followed by 40 hex chars
    const isEthAddr = /^0x[a-fA-F0-9]{40}$/.test(trimmed);
    // Check Tx hash: 0x followed by 64 hex chars
    const isEthTx = /^0x[a-fA-F0-9]{64}$/.test(trimmed);

    if (!isEthAddr && !isEthTx) {
      setValidationError(
        'Invalid target. Must be a 20-byte address (0x... 40 hex) or 32-byte tx hash (0x... 64 hex).'
      );
      return false;
    }
    setValidationError(null);
    return true;
  };

  const handleInvestigate = async (e: FormEvent) => {
    e.preventDefault();
    if (!validateTarget(target)) return;

    try {
      const res = await investigateMutation.mutateAsync({
        target: target.trim(),
        title: customTitle.trim() || undefined,
        limit,
        include_token_transfers: includeTokens,
      });
      setInvestigationResult(res);
      setSelectedNode(null);
    } catch {
      // Error is captured in investigateMutation.error
    }
  };

  const handleExpandNode = async (node: CytoscapeNodeData) => {
    if (!node.address || !investigationResult) return;
    try {
      const expandedGraph = await expandMutation.mutateAsync({
        address: node.address,
        max_depth: 1,
        max_nodes: 30,
        request_limit: 10,
      });
      setInvestigationResult((prev) =>
        prev
          ? {
              ...prev,
              graph: expandedGraph,
            }
          : null
      );
    } catch (err) {
      console.error('Failed to expand graph node', err);
    }
  };

  const operationalStatus = statusData?.operational_status;
  const statusBadgeVariant =
    operationalStatus === 'reachable'
      ? 'success'
      : operationalStatus === 'ready'
      ? 'info'
      : operationalStatus === 'degraded'
      ? 'warning'
      : 'error';

  // Consolidate normalized transactions for table
  const transactions = isAddress
    ? addrTxData?.transactions ?? []
    : singleTxData?.transaction
    ? [singleTxData.transaction]
    : [];

  const tokenTransfers = isAddress ? addrTokenData?.token_transfers ?? [] : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Blockchain Forensics"
        description="Inspect Ethereum Mainnet addresses, trace transaction flows, and collect cryptographic evidence."
        actions={
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Provider:</span>
            <Badge variant={statusBadgeVariant}>
              {statusLoading
                ? 'Checking...'
                : statusData?.operational_status ?? 'Unknown'}
            </Badge>
          </div>
        }
      />

      {statusData && !statusData.is_configured && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/20 p-4 text-xs text-accent-amber flex items-start gap-2.5">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Etherscan API Key Not Configured</p>
            <p className="mt-0.5 text-text-secondary">
              The backend is running without an <code className="text-primary">ETHERSCAN_API_KEY</code>.
              Requests will operate on public community rate limits or be throttled. Add your API key in
              <code className="text-primary ml-1">backend/.env</code> for full investigation capabilities.
            </p>
          </div>
        </div>
      )}

      {/* Input Query Card */}
      <Card>
        <CardHeader>
          <CardTitle>Investigate Target</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleInvestigate} className="space-y-4">
            <div className="flex flex-col gap-1">
              <label htmlFor="target-input" className="text-xs font-medium text-text-secondary uppercase tracking-wider">
                Ethereum Address or Transaction Hash *
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
                <input
                  id="target-input"
                  type="text"
                  placeholder="0x... (e.g. 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 or 0x... 64-hex tx hash)"
                  value={target}
                  onChange={(e) => {
                    setTarget(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded border border-border bg-background text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary font-mono"
                />
              </div>
              {validationError && (
                <p className="text-xs text-accent-red mt-1">{validationError}</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input
                label="Custom Case Title (Optional)"
                placeholder="e.g. Suspicious Drainer Analysis"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
              />

              <Select
                label="Transaction Retrieval Limit"
                value={String(limit)}
                onChange={(e) => setLimit(Number(e.target.value))}
                options={LIMIT_OPTIONS}
              />

              <div className="flex flex-col justify-end pb-2">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-text-secondary">
                  <input
                    type="checkbox"
                    checked={includeTokens}
                    onChange={(e) => setIncludeTokens(e.target.checked)}
                    className="rounded border-border bg-background text-primary focus:ring-primary"
                  />
                  <span>Include ERC-20 Token Transfers</span>
                </label>
              </div>
            </div>

            {investigateMutation.isError && (
              <ErrorAlert
                title="Investigation Failed"
                message={getErrorMessage(investigateMutation.error)}
              />
            )}

            <div className="flex gap-2">
              <Button
                type="submit"
                variant="primary"
                loading={investigateMutation.isPending}
              >
                <Zap className="h-4 w-4" />
                Start Investigation
              </Button>
              {investigationResult && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setInvestigationResult(null);
                    setTarget('');
                    setCustomTitle('');
                  }}
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Clear
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Investigation Details & Visualizations */}
      {investigateMutation.isPending && (
        <LoadingSpinner className="py-24" label="Connecting to Ethereum Mainnet and querying on-chain data..." />
      )}

      {investigationResult && !investigateMutation.isPending && (
        <div className="space-y-6">
          {/* Top metadata panel */}
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-text-primary flex items-center gap-2">
              <Shield className="h-4 w-4 text-primary" />
              Active Forensics Case
            </h2>
            <Link
              to={`/investigations/${investigationResult.investigation_id}`}
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              Open Full Case Dossier <ExternalLink className="h-3 w-3" />
            </Link>
          </div>

          <EvidencePanel investigationResult={investigationResult} />

          {/* View Selection Tabs */}
          <div className="flex items-center gap-2 border-b border-border pb-2">
            <button
              onClick={() => setActiveTab('graph')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                activeTab === 'graph'
                  ? 'bg-surface-active text-primary'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              Interactive Graph View
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                activeTab === 'transactions'
                  ? 'bg-surface-active text-primary'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              <ArrowRightLeft className="h-3.5 w-3.5" />
              Transaction Explorer ({investigationResult.transactions_count + investigationResult.token_transfers_count})
            </button>
          </div>

          {/* Active Tab Content */}
          {activeTab === 'graph' && (
            <div className="space-y-3">
              <InvestigationGraph
                graph={investigationResult.graph}
                onNodeClick={(node) => setSelectedNode(node)}
              />

              {/* Bounded Node Expansion Card */}
              {selectedNode && selectedNode.node_type === 'wallet' && selectedNode.address && (
                <Card className="animate-fade-in border-primary/30">
                  <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 py-2">
                    <div className="text-xs">
                      <span className="text-text-muted">Selected Wallet Node:</span>{' '}
                      <span className="font-mono text-primary font-medium">{selectedNode.address}</span>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={expandMutation.isPending}
                      onClick={() => handleExpandNode(selectedNode)}
                    >
                      <Zap className="h-3.5 w-3.5 text-primary" />
                      Expand Node (1 Hop)
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'transactions' && (
            <TransactionExplorer
              transactions={transactions}
              tokenTransfers={tokenTransfers}
            />
          )}
        </div>
      )}

      {/* Empty State when no query has been run */}
      {!investigationResult && !investigateMutation.isPending && (
        <EmptyState
          icon={<Search className="h-8 w-8 text-primary" />}
          title="Ready for Ethereum Analysis"
          description="Enter an Ethereum wallet address or transaction hash above to inspect native ETH transfers, ERC-20 tokens, and generate interactive graph visualizations."
        />
      )}
    </div>
  );
}
