import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { PendingReview, ReviewLog, ReviewRequest } from '../types';

export function usePendingReviews() {
  return useQuery({
    queryKey: queryKeys.reviews.pending,
    queryFn: async () => {
      return api.get<PendingReview[]>('/api/reviews/pending/').then(r => r.data);
    },
  });
}

export function useReviewHistory(caseId: number) {
  return useQuery({
    queryKey: queryKeys.cases.reviewHistory(caseId),
    queryFn: async () => {
      return api.get<ReviewLog[]>(`/api/cases/${caseId}/review-history/`).then(r => r.data);
    },
    enabled: !!caseId,
  });
}

export function useSubmitReview(caseId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (review: ReviewRequest) => {
      return api.post<ReviewLog>(`/api/cases/${caseId}/review/`, review).then(r => r.data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.cases.detail(caseId) });
      qc.invalidateQueries({ queryKey: queryKeys.cases.reviewHistory(caseId) });
      qc.invalidateQueries({ queryKey: queryKeys.reviews.pending });
    },
  });
}
