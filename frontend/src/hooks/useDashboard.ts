import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockDashboardStats, mockDeadlines, mockHighRisk } from '../lib/mockData';
import type { DashboardStats, DeadlineItem, HighRiskCase } from '../types';

export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboard.stats,
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockDashboardStats;
      }
      return api.get<DashboardStats>('/api/dashboard/stats/').then(r => r.data);
    },
  });
}

export function useDeadlines(days: number = 7) {
  return useQuery({
    queryKey: queryKeys.dashboard.deadlines(days),
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockDeadlines;
      }
      return api.get<DeadlineItem[]>('/api/dashboard/deadlines/', { params: { days } }).then(r => r.data);
    },
  });
}

export function useHighRiskCases() {
  return useQuery({
    queryKey: queryKeys.dashboard.highRisk,
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return mockHighRisk;
      }
      return api.get<HighRiskCase[]>('/api/dashboard/high-risk/').then(r => r.data);
    },
  });
}
