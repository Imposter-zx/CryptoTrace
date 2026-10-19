import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { investigationsApi } from '@/services/api';
import type { CreateInvestigationRequest, UpdateInvestigationRequest } from '@/types/api';

export const INVESTIGATIONS_KEY = 'investigations';

export function useInvestigations(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
}) {
  return useQuery({
    queryKey: [INVESTIGATIONS_KEY, params],
    queryFn: () => investigationsApi.list(params),
  });
}

export function useInvestigation(id: string) {
  return useQuery({
    queryKey: [INVESTIGATIONS_KEY, id],
    queryFn: () => investigationsApi.get(id),
    enabled: Boolean(id),
  });
}

export function useCreateInvestigation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateInvestigationRequest) => investigationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVESTIGATIONS_KEY] });
    },
  });
}

export function useUpdateInvestigation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateInvestigationRequest) => investigationsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVESTIGATIONS_KEY] });
    },
  });
}

export function useDeleteInvestigation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => investigationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVESTIGATIONS_KEY] });
    },
  });
}

export function useInvestigationSummary() {
  return useQuery({
    queryKey: [INVESTIGATIONS_KEY, 'summary'],
    queryFn: () => investigationsApi.getSummary(),
  });
}
