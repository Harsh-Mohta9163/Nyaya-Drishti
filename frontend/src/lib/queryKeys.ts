import type { CaseListParams } from '../types';

export const queryKeys = {
  auth: { me: ['auth', 'me'] },
  cases: {
    all: (params: CaseListParams) => ['cases', 'list', params],
    detail: (id: number) => ['cases', id],
    pdf: (id: number) => ['cases', id, 'pdf'],
    extraction: (id: number) => ['cases', id, 'extraction'],
    actionPlan: (id: number) => ['cases', id, 'action-plan'],
    reviewHistory: (id: number) => ['cases', id, 'review-history'],
  },
  reviews: { pending: ['reviews', 'pending'] },
  dashboard: {
    stats: ['dashboard', 'stats'],
    deadlines: (days: number) => ['dashboard', 'deadlines', days],
    highRisk: ['dashboard', 'high-risk'],
  },
  notifications: { all: ['notifications'] },
};
