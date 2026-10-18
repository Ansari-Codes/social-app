import { callAPI } from '@/Core/api';
import type { DashboardAnalyticsData } from '../Types/analytics.type';

export async function getDashboardAnalytics(days: number): Promise<DashboardAnalyticsData> {
  return callAPI<DashboardAnalyticsData>('/analytics/me', { params: { days } });
}
