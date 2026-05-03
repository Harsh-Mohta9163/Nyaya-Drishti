import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import { mockNotifications } from '../lib/mockData';
import type { Notification } from '../types';

export function useNotifications(unreadOnly: boolean = false) {
  return useQuery({
    queryKey: queryKeys.notifications.all,
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return unreadOnly ? mockNotifications.filter(n => !n.is_read) : mockNotifications;
      }
      return api.get<Notification[]>('/api/notifications/', {
        params: unreadOnly ? { unread: true } : {},
      }).then(r => r.data);
    },
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      if (USE_MOCK) {
        await mockDelay(200);
        return { id } as Notification;
      }
      return api.patch<Notification>(`/api/notifications/${id}/read/`).then(r => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.notifications.all }),
  });
}
