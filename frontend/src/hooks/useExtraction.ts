import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockExtractedData } from '../lib/mockData';
import type { Case, ExtractedData } from '../types';

export function useExtractionStatus(caseId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.cases.detail(caseId),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return { id: caseId, status: 'extracted' } as Case;
      }
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
      if (USE_MOCK) {
        await mockDelay();
        return mockExtractedData;
      }
      return api.get<ExtractedData>(`/api/cases/${caseId}/extraction/`).then(r => r.data);
    },
  });
}
