import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TransactionExplorer } from '@/components/blockchain/TransactionExplorer';
import type { NormalizedTransaction, NormalizedTokenTransfer } from '@/types/blockchain';

describe('TransactionExplorer', () => {
  const mockTransactions: NormalizedTransaction[] = [
    {
      tx_hash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      block_number: 18000000,
      block_timestamp: 1695000000,
      datetime_utc: '2023-09-18T00:00:00Z',
      from_address: '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed',
      to_address: '0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359',
      value_wei: '1000000000000000000',
      value_eth: '1.0',
      gas_price_wei: '20000000000',
      gas_used: 21000,
      transaction_fee_eth: '0.00042',
      status: 'success',
      is_error: false,
      method_id: '0x',
      function_name: null,
      source_provider: 'etherscan_v2',
      chain_id: 1,
      retrieved_at: '2023-09-18T01:00:00Z',
    },
  ];

  const mockTokenTransfers: NormalizedTokenTransfer[] = [
    {
      tx_hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
      block_number: 18000001,
      block_timestamp: 1695000010,
      datetime_utc: '2023-09-18T00:00:10Z',
      from_address: '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed',
      to_address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
      token_contract_address: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      token_name: 'Tether USD',
      token_symbol: 'USDT',
      token_decimals: 6,
      raw_amount: '50000000',
      normalized_amount: '50',
      event_index: 0,
      source_provider: 'etherscan_v2',
      chain_id: 1,
      retrieved_at: '2023-09-18T01:00:00Z',
    },
  ];

  it('renders ETH transactions table by default', () => {
    render(
      <TransactionExplorer
        transactions={mockTransactions}
        tokenTransfers={mockTokenTransfers}
      />
    );

    expect(screen.getByText('ETH (1)')).toBeInTheDocument();
    expect(screen.getByText('ERC-20 (1)')).toBeInTheDocument();
    expect(screen.getByText('1.0')).toBeInTheDocument();
    expect(screen.getByText('0.00042')).toBeInTheDocument();
  });

  it('switches to ERC-20 tab when clicked', () => {
    render(
      <TransactionExplorer
        transactions={mockTransactions}
        tokenTransfers={mockTokenTransfers}
      />
    );

    const erc20Tab = screen.getByRole('button', { name: /ERC-20/i });
    fireEvent.click(erc20Tab);

    expect(screen.getByText('USDT')).toBeInTheDocument();
    expect(screen.getByText(/50/)).toBeInTheDocument();
  });

  it('handles empty states gracefully', () => {
    render(<TransactionExplorer transactions={[]} tokenTransfers={[]} />);
    expect(screen.getByText('No ETH transactions')).toBeInTheDocument();

    const erc20Tab = screen.getByRole('button', { name: /ERC-20/i });
    fireEvent.click(erc20Tab);
    expect(screen.getByText('No ERC-20 transfers')).toBeInTheDocument();
  });
});
