import { callAPI, getToken } from '@/Core/api';
import type { Post } from '@/Pages/App/Types/feed.type';
import { mapApiPost, type DataPosts } from './postService';

export interface FeedPage {
  posts: Post[];
  nextCursor: number | null;
}

let feedCache: { data: FeedPage; timestamp: number; viewerKey: string } | null = null;
const inFlightFeedPromises = new Map<string, Promise<FeedPage>>();
let feedCacheGeneration = 0;
const FEED_CACHE_TTL_MS = 4000;
const FEED_PAGE_SIZE = 20;

export function invalidateFeedCache(): void {
  feedCache = null;
  feedCacheGeneration += 1;
}

export async function getFeedPage(beforeId?: number, force = false): Promise<FeedPage> {
  const now = Date.now();
  const viewerKey = getToken() ?? 'guest';
  const requestKey = `${viewerKey}:${beforeId ?? 'first'}`;
  if (
    beforeId === undefined &&
    !force &&
    feedCache &&
    feedCache.viewerKey === viewerKey &&
    now - feedCache.timestamp < FEED_CACHE_TTL_MS
  ) {
    return feedCache.data;
  }

  const inFlight = inFlightFeedPromises.get(requestKey);
  if (inFlight) return inFlight;

  let promise!: Promise<FeedPage>;
  const cacheGeneration = feedCacheGeneration;
  promise = (async () => {
    try {
      const data = await callAPI<DataPosts>('/feed/', {
        params: { limit: FEED_PAGE_SIZE, before_id: beforeId },
      });
      const page = {
        posts: data.posts.map(mapApiPost),
        nextCursor: data.next_cursor ?? null,
      };
      if (beforeId === undefined && cacheGeneration === feedCacheGeneration) {
        feedCache = { data: page, timestamp: Date.now(), viewerKey };
      }
      return page;
    } finally {
      inFlightFeedPromises.delete(requestKey);
    }
  })();
  inFlightFeedPromises.set(requestKey, promise);

  return promise;
}

export async function getFeedPosts(force = false): Promise<Post[]> {
  return (await getFeedPage(undefined, force)).posts;
}
