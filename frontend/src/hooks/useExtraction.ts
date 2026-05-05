import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { Case, ExtractedData } from '../types';

export function useExtractionStatus(caseId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.cases.detail(caseId),
    queryFn: async () => {
      return api.get<Case>(`/api/cases/${caseId}/`).then(r => r.data);
    },
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && 'status' in data && data.status !== 'processing') return false;
      return 3000;
    },
    enabled,
  });
}

export function useExtractedData(caseId: number) {
  return useQuery({
    queryKey: queryKeys.cases.extraction(caseId),
    queryFn: async () => {
      return api.get<ExtractedData>(`/api/cases/${caseId}/extraction/`).then(r => r.data);
    },
    enabled: !!caseId,
  });
}
