export interface AnalyticsPoint {
  date: string;
  followers: number;
  stars: number;
  posts?: number;
  reactions?: number;
}

export interface TopPostMetric {
  id: number;
  content: string;
  reactions: number;
  comments: number;
  created_at: string;
}

export interface DashboardAnalyticsData {
  days: number;
  total_posts: number;
  total_comments: number;
  total_reactions: number;
  dominant_reaction: string | null;
  dominant_reaction_count: number;
  time_series: AnalyticsPoint[];
  reaction_breakdown?: Record<string, number>;
  total_followers?: number;
  total_stars?: number;
  total_following?: number;
  engagement_rate?: number;
  top_posts?: TopPostMetric[];
}
