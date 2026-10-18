import type { Post, Profile } from '@/Pages/App/Types/feed.type';
import type { ProfilePublic } from '@/Pages/_commons/Types/profile.type';

export type DataChange =
    | { type: 'viewer-changed' }
    | { type: 'post-created'; post: Post }
    | { type: 'post-updated'; post: Post }
    | { type: 'post-deleted'; postId: number }
    | { type: 'post-reaction'; post: Post }
    | { type: 'comment-created'; postId: number }
    | { type: 'profile-updated'; profile: ProfilePublic }
    | { type: 'account-updated'; userId: number; username: string; email: string }
    | { type: 'profile-relation-updated'; profile: Profile };

const listeners = new Set<(change: DataChange) => void>();

export function publishDataChange(change: DataChange): void {
    for (const listener of listeners) listener(change);
}

export function subscribeDataChanges(listener: (change: DataChange) => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
}