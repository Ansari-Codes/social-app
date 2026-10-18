export interface NotificationItem {
  id: number;
  kind: string;
  content: string;
  actor_profile_id: number | null;
  actor_username: string | null;
  actor_display_name: string | null;
  actor_emoji: string | null;
  target_type: string | null;
  target_id: number | null;
  target_post_id?: number | null;
  target_post_snippet?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationData {
  notifications: NotificationItem[];
  unread_count: number;
}
