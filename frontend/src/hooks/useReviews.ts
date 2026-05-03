import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockPendingReviews, mockReviewLogs } from '../lib/mockData';
import type { PendingReview, ReviewLog, ReviewRequest } from '../types';

export function usePendingReviews() {
  return useQuery({
    queryKey: queryKeys.reviews.pending,
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockPendingReviews;
      }
      return api.get<PendingReview[]>('/api/reviews/pending/').then(r => r.data);
    },
  });
}

export function useReviewHistory(caseId: number) {
  return useQuery({
    queryKey: queryKeys.cases.reviewHistory(caseId),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockReviewLogs;
      }
      return api.get<ReviewLog[]>(`/api/cases/${caseId}/review-history/`).then(r => r.data);
    },
  });
}

export function useSubmitReview(caseId: number) {
  return useMutation({
    mutationFn: async (review: ReviewRequest) => {
      if (USE_MOCK) {
        await mockDelay();
        return { id: Date.now(), ...review } as unknown as ReviewLog;
      }
      return api.post<ReviewLog>(`/api/cases/${caseId}/review/`, review).then(r => r.data);
    },
  });
}
