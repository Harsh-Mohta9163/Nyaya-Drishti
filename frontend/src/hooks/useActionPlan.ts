import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { ActionPlan } from '../types';

export function useActionPlan(caseId: number) {
  return useQuery({
    queryKey: queryKeys.cases.actionPlan(caseId),
    queryFn: async () => {
      return api.get<ActionPlan>(`/api/cases/${caseId}/action-plan/`).then(r => r.data);
    },
    enabled: !!caseId,
  });
}
