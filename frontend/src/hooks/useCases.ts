import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockCases } from '../lib/mockData';
import type { Case, CaseListParams, CaseListResponse } from '../types';

export function useCasesList(params: CaseListParams) {
  return useQuery({
    queryKey: queryKeys.cases.all(params),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return { count: mockCases.length, next: null, previous: null, results: mockCases } as CaseListResponse;
      }
      return api.get<CaseListResponse>('/api/cases/', { params }).then(r => r.data);
    },
    staleTime: 1000 * 60 * 2,
  });
}

export function useCaseDetail(id: number) {
  return useQuery({
    queryKey: queryKeys.cases.detail(id),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockCases.find(c => c.id === id) || mockCases[0];
      }
      return api.get<Case>(`/api/cases/${id}/`).then(r => r.data);
    },
    staleTime: 1000 * 30,
  });
}

export function useUploadCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      if (USE_MOCK) {
        await mockDelay(1500);
        return { ...mockCases[0], id: Date.now(), status: 'uploaded' as const } as Case;
      }
      const form = new FormData();
      form.append('pdf_file', file);
      form.append('case_number', `AUTO_${Date.now()}`);
      return api.post<Case>('/api/cases/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cases', 'list'] }),
  });
}
