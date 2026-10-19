import { apiClient } from '@/services/api';
import type {
  AddressTokenTransfersResponse,
  AddressTransactionsResponse,
  BlockchainInvestigateRequest,
  BlockchainInvestigateResponse,
  BlockchainStatusResponse,
  BoundedExpansionRequest,
  CytoscapeGraphResponse,
  TransactionDetailResponse,
} from '@/types/blockchain';

export const blockchainApi = {
  getStatus: (): Promise<BlockchainStatusResponse> =>
    apiClient.get<BlockchainStatusResponse>('/api/v1/blockchain/status').then((r) => r.data),

  getTransaction: (txHash: string): Promise<TransactionDetailResponse> =>
    apiClient.get<TransactionDetailResponse>(`/api/v1/blockchain/tx/${txHash}`).then((r) => r.data),

  getAddressTransactions: (
    address: string,
    params?: { limit?: number; offset?: number }
  ): Promise<AddressTransactionsResponse> =>
    apiClient
      .get<AddressTransactionsResponse>(`/api/v1/blockchain/address/${address}/transactions`, { params })
      .then((r) => r.data),

  getAddressTokenTransfers: (
    address: string,
    params?: { limit?: number; offset?: number }
  ): Promise<AddressTokenTransfersResponse> =>
    apiClient
      .get<AddressTokenTransfersResponse>(`/api/v1/blockchain/address/${address}/token-transfers`, { params })
      .then((r) => r.data),

  investigate: (data: BlockchainInvestigateRequest): Promise<BlockchainInvestigateResponse> =>
    apiClient.post<BlockchainInvestigateResponse>('/api/v1/blockchain/investigate', data).then((r) => r.data),

  getInvestigationGraph: (investigationId: string): Promise<CytoscapeGraphResponse> =>
    apiClient
      .get<CytoscapeGraphResponse>(`/api/v1/blockchain/investigations/${investigationId}/graph`)
      .then((r) => r.data),

  expandInvestigation: (
    investigationId: string,
    data: BoundedExpansionRequest
  ): Promise<CytoscapeGraphResponse> =>
    apiClient
      .post<CytoscapeGraphResponse>(`/api/v1/blockchain/investigations/${investigationId}/expand`, data)
      .then((r) => r.data),
};
