import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockActionPlan } from '../lib/mockData';
import type { ActionPlan } from '../types';

export function useActionPlan(caseId: number) {
  return useQuery({
    queryKey: queryKeys.cases.actionPlan(caseId),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockActionPlan;
      }
      return api.get<ActionPlan>(`/api/cases/${caseId}/action-plan/`).then(r => r.data);
    },
  });
}
