import axios from 'axios';
import type {
  CreateInvestigationRequest,
  HealthStatus,
  Investigation,
  InvestigationSummary,
  PaginatedResponse,
  UpdateInvestigationRequest,
} from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const healthApi = {
  checkRoot: (): Promise<{ status: string; service: string }> =>
    apiClient.get('/health').then((r) => r.data),

  check: (): Promise<HealthStatus> =>
    apiClient.get<HealthStatus>('/api/v1/health').then((r) => r.data),

  checkV1: (): Promise<HealthStatus> =>
    apiClient.get<HealthStatus>('/api/v1/health').then((r) => r.data),
};

export const investigationsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }): Promise<PaginatedResponse<Investigation>> =>
    apiClient.get<PaginatedResponse<Investigation>>('/api/v1/investigations', { params }).then((r) => r.data),

  get: (id: string): Promise<Investigation> =>
    apiClient.get<Investigation>(`/api/v1/investigations/${id}`).then((r) => r.data),

  create: (data: CreateInvestigationRequest): Promise<Investigation> =>
    apiClient.post<Investigation>('/api/v1/investigations', data).then((r) => r.data),

  update: (id: string, data: UpdateInvestigationRequest): Promise<Investigation> =>
    apiClient.patch<Investigation>(`/api/v1/investigations/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<{ message: string }> =>
    apiClient.delete<{ message: string }>(`/api/v1/investigations/${id}`).then((r) => r.data),

  getSummary: (): Promise<InvestigationSummary> =>
    apiClient.get<InvestigationSummary>('/api/v1/investigations/summary').then((r) => r.data),
};
