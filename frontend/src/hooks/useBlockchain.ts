import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { blockchainApi } from '@/services/blockchainApi';
import type { BlockchainInvestigateRequest, BoundedExpansionRequest } from '@/types/blockchain';

export const BLOCKCHAIN_KEY = 'blockchain';

export function useBlockchainStatus() {
  return useQuery({
    queryKey: [BLOCKCHAIN_KEY, 'status'],
    queryFn: () => blockchainApi.getStatus(),
    staleTime: 60_000,
  });
}

export function useTransaction(txHash: string) {
  return useQuery({
    queryKey: [BLOCKCHAIN_KEY, 'tx', txHash],
    queryFn: () => blockchainApi.getTransaction(txHash),
    enabled: !!txHash,
  });
}

export function useAddressTransactions(address: string, params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [BLOCKCHAIN_KEY, 'address', address, 'transactions', params],
    queryFn: () => blockchainApi.getAddressTransactions(address, params),
    enabled: !!address,
  });
}

export function useAddressTokenTransfers(address: string, params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [BLOCKCHAIN_KEY, 'address', address, 'token-transfers', params],
    queryFn: () => blockchainApi.getAddressTokenTransfers(address, params),
    enabled: !!address,
  });
}

export function useBlockchainInvestigation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BlockchainInvestigateRequest) => blockchainApi.investigate(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [BLOCKCHAIN_KEY] });
      qc.invalidateQueries({ queryKey: ['investigations'] });
    },
  });
}

export function useInvestigationGraph(investigationId: string) {
  return useQuery({
    queryKey: [BLOCKCHAIN_KEY, 'graph', investigationId],
    queryFn: () => blockchainApi.getInvestigationGraph(investigationId),
    enabled: !!investigationId,
  });
}

export function useExpandInvestigation(investigationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BoundedExpansionRequest) => blockchainApi.expandInvestigation(investigationId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [BLOCKCHAIN_KEY, 'graph', investigationId] });
    },
  });
}
