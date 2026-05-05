import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { Case, CaseListParams, CaseListResponse } from '../types';

export function useCasesList(params: CaseListParams = {}) {
  return useQuery({
    queryKey: queryKeys.cases.all(params),
    queryFn: async () => {
      const res = await api.get<CaseListResponse>('/api/cases/', { params });
      // Backend uses DRF pagination: { count, next, previous, results }
      // If backend returns paginated, use it; otherwise wrap raw array
      if (res.data && Array.isArray(res.data)) {
        return { count: res.data.length, next: null, previous: null, results: res.data } as CaseListResponse;
      }
      return res.data;
    },
    staleTime: 1000 * 60 * 2,
  });
}

export function useCaseDetail(id: number) {
  return useQuery({
    queryKey: queryKeys.cases.detail(id),
    queryFn: async () => {
      return api.get<Case>(`/api/cases/${id}/`).then(r => r.data);
    },
    enabled: !!id,
    staleTime: 1000 * 30,
  });
}

export function useUploadCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, caseNumber }: { file: File; caseNumber?: string }) => {
      const form = new FormData();
      form.append('pdf_file', file);
      form.append('case_number', caseNumber || `AUTO_${Date.now()}`);
      // Send required fields with defaults — backend requires these
      form.append('court', 'Pending Extraction');
      form.append('petitioner', 'Pending Extraction');
      form.append('respondent', 'Pending Extraction');
      form.append('case_type', 'WP');
      form.append('judgment_date', new Date().toISOString().split('T')[0]);
      return api.post<Case>('/api/cases/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cases', 'list'] }),
  });
}

export function useTriggerExtraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (caseId: number) => {
      return api.post(`/api/cases/${caseId}/extract/`).then(r => r.data);
    },
    onSuccess: (_data, caseId) => {
      qc.invalidateQueries({ queryKey: queryKeys.cases.detail(caseId) });
      qc.invalidateQueries({ queryKey: queryKeys.cases.extraction(caseId) });
    },
  });
}
