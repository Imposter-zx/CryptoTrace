/**
 * TransactionExplorer — Multi-tab transaction table.
 *
 * Displays native ETH transactions and ERC-20 token transfers in
 * separate tabs with sortable columns and truncated address displays.
 */
import { useState } from 'react';
import type { NormalizedTransaction, NormalizedTokenTransfer } from '@/types/blockchain';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ArrowRightLeft, Coins, ExternalLink, Copy, Check } from 'lucide-react';
import { cn, formatDateTime } from '@/lib/utils';

function truncateAddress(address: string): string {
  if (address.length <= 14) return address;
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="text-text-muted hover:text-primary transition-colors ml-1" aria-label="Copy">
      {copied ? <Check className="h-3 w-3 text-accent-green" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant = status === 'success' ? 'success' : status === 'failed' ? 'error' : 'default';
  return <Badge variant={variant}>{status}</Badge>;
}

interface TransactionExplorerProps {
  transactions: NormalizedTransaction[];
  tokenTransfers: NormalizedTokenTransfer[];
  className?: string;
}

type Tab = 'eth' | 'erc20';

export function TransactionExplorer({
  transactions,
  tokenTransfers,
  className,
}: TransactionExplorerProps) {
  const [activeTab, setActiveTab] = useState<Tab>('eth');

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Transaction Explorer</CardTitle>
        <div className="flex items-center gap-1 bg-background rounded p-0.5">
          <button
            onClick={() => setActiveTab('eth')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors',
              activeTab === 'eth'
                ? 'bg-surface-active text-primary'
                : 'text-text-muted hover:text-text-secondary'
            )}
          >
            <ArrowRightLeft className="h-3.5 w-3.5" />
            ETH ({transactions.length})
          </button>
          <button
            onClick={() => setActiveTab('erc20')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors',
              activeTab === 'erc20'
                ? 'bg-surface-active text-primary'
                : 'text-text-muted hover:text-text-secondary'
            )}
          >
            <Coins className="h-3.5 w-3.5" />
            ERC-20 ({tokenTransfers.length})
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {activeTab === 'eth' ? (
          <EthTransactionsTable transactions={transactions} />
        ) : (
          <TokenTransfersTable transfers={tokenTransfers} />
        )}
      </CardContent>
    </Card>
  );
}

function EthTransactionsTable({ transactions }: { transactions: NormalizedTransaction[] }) {
  if (transactions.length === 0) {
    return (
      <EmptyState
        icon={<ArrowRightLeft className="h-6 w-6" />}
        title="No ETH transactions"
        description="No native ETH transactions found for this target."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Tx Hash</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">From</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">To</th>
            <th className="text-right px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Value (ETH)</th>
            <th className="text-right px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Fee (ETH)</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Status</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {transactions.map((tx) => (
            <tr key={tx.tx_hash} className="hover:bg-surface-hover transition-colors">
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-primary">{truncateAddress(tx.tx_hash)}</span>
                  <CopyButton text={tx.tx_hash} />
                  <a
                    href={`https://etherscan.io/tx/${tx.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-text-muted hover:text-primary"
                    aria-label="View on Etherscan"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-text-secondary">{truncateAddress(tx.from_address)}</span>
                  <CopyButton text={tx.from_address} />
                </div>
              </td>
              <td className="px-3 py-2">
                {tx.to_address ? (
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-text-secondary">{truncateAddress(tx.to_address)}</span>
                    <CopyButton text={tx.to_address} />
                  </div>
                ) : (
                  <Badge variant="warning">Contract Create</Badge>
                )}
              </td>
              <td className="px-3 py-2 text-right font-mono text-text-primary">{tx.value_eth}</td>
              <td className="px-3 py-2 text-right font-mono text-text-muted">
                {tx.transaction_fee_eth ?? '—'}
              </td>
              <td className="px-3 py-2">
                <StatusBadge status={tx.status} />
              </td>
              <td className="px-3 py-2 text-text-muted whitespace-nowrap">
                {tx.datetime_utc ? formatDateTime(tx.datetime_utc) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TokenTransfersTable({ transfers }: { transfers: NormalizedTokenTransfer[] }) {
  if (transfers.length === 0) {
    return (
      <EmptyState
        icon={<Coins className="h-6 w-6" />}
        title="No ERC-20 transfers"
        description="No ERC-20 token transfer events found for this target."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Tx Hash</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Token</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">From</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">To</th>
            <th className="text-right px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Amount</th>
            <th className="text-left px-3 py-2 text-text-muted uppercase tracking-wider font-medium">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {transfers.map((tt, idx) => (
            <tr key={`${tt.tx_hash}-${tt.event_index ?? idx}`} className="hover:bg-surface-hover transition-colors">
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-primary">{truncateAddress(tt.tx_hash)}</span>
                  <CopyButton text={tt.tx_hash} />
                </div>
              </td>
              <td className="px-3 py-2">
                <Badge variant="info">{tt.token_symbol ?? 'TOKEN'}</Badge>
                {tt.token_name && (
                  <span className="text-text-muted ml-1">{tt.token_name}</span>
                )}
              </td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-text-secondary">{truncateAddress(tt.from_address)}</span>
                  <CopyButton text={tt.from_address} />
                </div>
              </td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-mono text-text-secondary">{truncateAddress(tt.to_address)}</span>
                  <CopyButton text={tt.to_address} />
                </div>
              </td>
              <td className="px-3 py-2 text-right font-mono text-text-primary">
                {tt.normalized_amount != null ? (
                  <span>{tt.normalized_amount} {tt.token_symbol ?? ''}</span>
                ) : (
                  <span className="text-text-muted" title="Token decimals unknown; raw integer units shown">
                    {tt.raw_amount} <span className="text-accent-amber text-[10px]">(raw)</span>
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-text-muted whitespace-nowrap">
                {tt.datetime_utc ? formatDateTime(tt.datetime_utc) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
