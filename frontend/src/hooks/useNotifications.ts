import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { Notification } from '../types';

export function useNotifications(unreadOnly: boolean = false) {
  return useQuery({
    queryKey: queryKeys.notifications.all,
    queryFn: async () => {
      return api.get<Notification[]>('/api/notifications/', {
        params: unreadOnly ? { unread: 'true' } : {},
      }).then(r => r.data);
    },
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      return api.patch<Notification>(`/api/notifications/${id}/read/`).then(r => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.notifications.all }),
  });
}
