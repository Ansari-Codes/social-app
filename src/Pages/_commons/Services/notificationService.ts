import { callAPI } from '@/Core/api';
import type { NotificationData, NotificationItem } from '../Types/notification.type';

interface DataOk {
  ok: boolean;
}

export async function getNotifications(): Promise<NotificationData> {
  return callAPI<NotificationData>('/notifications/');
}

export async function markNotificationRead(notificationId: number): Promise<void> {
  const data = await callAPI<DataOk>(`/notifications/${notificationId}/read`, {
    method: 'PATCH',
  });
  if (!data.ok) throw new Error('Notification could not be marked as read.');
}

export async function markAllNotificationsRead(): Promise<void> {
  const data = await callAPI<DataOk>('/notifications/read-all', { method: 'POST' });
  if (!data.ok) throw new Error('Notifications could not be marked as read.');
}

export function unreadNotifications(items: NotificationItem[]): number {
  return items.reduce((count, item) => count + Number(!item.is_read), 0);
}
