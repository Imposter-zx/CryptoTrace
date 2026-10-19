import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EvidencePanel } from '@/components/blockchain/EvidencePanel';
import type { BlockchainInvestigateResponse } from '@/types/blockchain';

describe('EvidencePanel', () => {
  const mockResult: BlockchainInvestigateResponse = {
    investigation_id: '12345678-1234-5678-1234-567812345678',
    target: '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed',
    target_type: 'wallet_address',
    evidence_created_count: 5,
    evidence_skipped_duplicates_count: 2,
    transactions_count: 4,
    token_transfers_count: 1,
    graph: {
      nodes: [],
      edges: [],
      meta: {
        total_nodes: 0,
        total_edges: 0,
        is_truncated: false,
        max_nodes_reached: false,
        max_depth_reached: false,
        chain_id: 1,
        investigation_id: '12345678-1234-5678-1234-567812345678',
        explanation: 'Observed transfers',
      },
    },
    warnings: ['Provider rate limit near threshold'],
  };

  it('renders target address and case id', () => {
    render(<EvidencePanel investigationResult={mockResult} />);
    expect(screen.getByText('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed')).toBeInTheDocument();
    expect(screen.getByText('12345678-1234-5678-1234-567812345678')).toBeInTheDocument();
  });

  it('renders correct counts for evidence and records', () => {
    render(<EvidencePanel investigationResult={mockResult} />);
    expect(screen.getAllByText('5')).toHaveLength(2); // New Evidence Saved (5) and Total Records (4+1=5)
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Wallet Address')).toBeInTheDocument();
  });

  it('displays warnings when present', () => {
    render(<EvidencePanel investigationResult={mockResult} />);
    expect(screen.getByText('Provider rate limit near threshold')).toBeInTheDocument();
  });

  it('renders integrity notice', () => {
    render(<EvidencePanel investigationResult={mockResult} />);
    expect(screen.getByText(/Integrity Assurance & Scope Notice:/)).toBeInTheDocument();
    expect(screen.getByText(/SHA-256 checksum/)).toBeInTheDocument();
  });
});
