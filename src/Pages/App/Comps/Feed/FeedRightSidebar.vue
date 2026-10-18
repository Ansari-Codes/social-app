<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import UiButton from '@/Ui/UiButton.vue';
import type { Post } from '../../Types/feed.type';
import { setProfileFollow } from '@/Pages/_commons/Services/chipService';
import { useMeStore } from '@/Stores/meStore';
import { requestAuthPrompt } from '@/Core/authPrompt';

const props = defineProps<{
    posts: Post[];
    currentTag?: string;
}>();

const me = useMeStore();

const emit = defineEmits<{
    (e: 'select-tag', tag: string): void;
    (e: 'followed', profileId: number): void;
}>();

// ── Trending Tags: Top 10 ───────────────────────────────────────
// Extract hashtags ONLY from posts currently in the feed (no seeded tags).
// Score = frequency + engagement weight so genuinely hot tags rise above
// tags that merely appear in many low-engagement posts.
const trendingTopics = computed(() => {
    const map = new Map<string, { tag: string; count: number; score: number }>();

    for (const post of props.posts) {
        if (!post.content) continue;

        const matches = post.content.match(/#[a-zA-Z0-9_]+/g);
        if (!matches || matches.length === 0) continue;

        // De-duplicate within the same post so 1 post = 1 count per tag.
        const uniqueTagsInPost = new Set(matches.map((t) => t.trim().toLowerCase()));

        const reactions = post.reactions
            ? Object.values(post.reactions).reduce((sum, c) => sum + (c || 0), 0)
            : 0;
        const comments = post.comments || 0;
        const engagement = reactions * 2 + comments;

        for (const tag of uniqueTagsInPost) {
            const existing = map.get(tag);
            if (existing) {
                existing.count += 1;
                existing.score += 1 + engagement;
            } else {
                map.set(tag, { tag, count: 1, score: 1 + engagement });
            }
        }
    }

    return Array.from(map.values())
        .sort((a, b) => b.score - a.score || a.tag.localeCompare(b.tag))
        .slice(0, 10);
});

// ── Trending Profiles: Top 5 ────────────────────────────────────
// Dynamically scored by engagement across all posts in the feed.
const trendingProfiles = computed(() => {
    const profileMap = new Map<
        number,
        {
            id: number;
            userId?: number;
            username: string;
            displayName: string;
            emoji: string;
            followers: number;
            followedByMe: boolean;
            postsCount: number;
            reactionsCount: number;
            commentsCount: number;
            score: number;
        }
    >();

    for (const post of props.posts) {
        const p = post.profile;
        if (!p || p.isOwner) continue;

        const postReactions = post.reactions
            ? Object.values(post.reactions).reduce((sum, c) => sum + (c || 0), 0)
            : 0;
        const postComments = post.comments || 0;

        if (!profileMap.has(p.id)) {
            profileMap.set(p.id, {
                id: p.id,
                userId: p.userId,
                username: p.username,
                displayName: p.display_name || p.username,
                emoji: p.emoji || '✨',
                followers: p.followers || 0,
                followedByMe: Boolean(p.followedByMe),
                postsCount: 1,
                reactionsCount: postReactions,
                commentsCount: postComments,
                score: 0,
            });
        } else {
            const entry = profileMap.get(p.id)!;
            entry.postsCount += 1;
            entry.reactionsCount += postReactions;
            entry.commentsCount += postComments;
            entry.followedByMe = entry.followedByMe || Boolean(p.followedByMe);
        }
    }

    // Engagement score: reactions (3x) + comments (2x) + posts (2x) + followers (1x)
    for (const entry of profileMap.values()) {
        entry.score =
            entry.reactionsCount * 3 +
            entry.commentsCount * 2 +
            entry.postsCount * 2 +
            entry.followers;
    }

    return Array.from(profileMap.values())
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);
});

async function followUser(creatorId: number, targetUserId?: number) {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    if (!targetUserId) return;
    try {
        await setProfileFollow(targetUserId, true);
        emit('followed', creatorId);
    } catch {
        // Handled silently
    }
}
</script>

<template>
    <aside class="sticky top-20 flex w-full flex-col gap-4" aria-label="Trending topics and creators">
        <!-- ── Trending in Community (Top 10 Post Hashtags) ────────── -->
        <div class="rounded-2xl border border-border bg-bg-elevated p-4 shadow-card">
            <div class="mb-3 flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                    <span aria-hidden="true">🔥</span>
                    <h3 class="text-sm font-bold text-text-h">Trending in Community</h3>
                </div>
                <span
                    v-if="trendingTopics.length"
                    class="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-semibold text-accent"
                >
                    Top 10
                </span>
            </div>

            <!-- List of tags from posts -->
            <div v-if="trendingTopics.length" class="flex flex-col gap-1.5">
                <button
                    v-for="(topic, i) in trendingTopics"
                    :key="topic.tag"
                    type="button"
                    class="group flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-bg-hover"
                    :class="currentTag === topic.tag && 'bg-accent/10 text-accent font-semibold'"
                    @click="emit('select-tag', topic.tag)"
                >
                    <div class="flex min-w-0 items-center gap-2">
                        <span class="w-4 shrink-0 text-center text-[10px] font-bold text-text-muted">
                            {{ i + 1 }}
                        </span>
                        <div class="min-w-0">
                            <p class="truncate text-xs font-bold text-text group-hover:text-accent">
                                {{ topic.tag }}
                            </p>
                            <p class="text-[10px] text-text-muted">
                                {{ topic.count }} {{ topic.count === 1 ? 'post' : 'posts' }}
                            </p>
                        </div>
                    </div>
                    <span
                        class="text-xs text-text-muted transition-transform group-hover:translate-x-0.5"
                        aria-hidden="true"
                    >
                        →
                    </span>
                </button>
            </div>

            <!-- Empty state when no posts have hashtags -->
            <div
                v-else
                class="rounded-xl border border-dashed border-border/80 px-3 py-6 text-center text-xs text-text-muted"
            >
                <p class="font-medium text-text">No active hashtags</p>
                <p class="mt-1 text-[11px] text-text-faint">
                    Use <span class="font-mono text-accent">#hashtags</span> in your posts to start a topic.
                </p>
            </div>
        </div>

        <!-- ── Who to Follow (Top 5 Trending Profiles) ─────────────── -->
        <div
            v-if="trendingProfiles.length"
            class="rounded-2xl border border-border bg-bg-elevated p-4 shadow-card"
        >
            <div class="mb-3 flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                    <span aria-hidden="true">👥</span>
                    <h3 class="text-sm font-bold text-text-h">Who to Follow</h3>
                </div>
                <span class="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                    Top 5 · Trending
                </span>
            </div>

            <div class="flex flex-col gap-3">
                <div
                    v-for="creator in trendingProfiles"
                    :key="creator.id"
                    class="flex items-center justify-between gap-2.5"
                >
                    <RouterLink
                        :to="{ name: 'profile', params: { profile: creator.username } }"
                        class="flex min-w-0 items-center gap-2.5 no-underline hover:opacity-90"
                    >
                        <span
                            class="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-base shadow-xs"
                        >
                            {{ creator.emoji }}
                        </span>
                        <div class="min-w-0 flex-1">
                            <p class="truncate text-xs font-bold text-text-h hover:text-accent">
                                {{ creator.displayName }}
                            </p>
                            <div class="flex items-center gap-1.5 text-[10px] text-text-muted">
                                <span class="truncate">@{{ creator.username }}</span>
                                <span
                                    v-if="creator.reactionsCount > 0"
                                    class="text-accent font-medium shrink-0"
                                >
                                    · ❤️ {{ creator.reactionsCount }}
                                </span>
                            </div>
                        </div>
                    </RouterLink>

                    <UiButton
                        v-if="!creator.followedByMe"
                        size="sm"
                        variant="soft"
                        class="shrink-0 text-xs py-1 px-3 rounded-full font-semibold"
                        @click="followUser(creator.id, creator.userId)"
                    >
                        Follow
                    </UiButton>
                    <span v-else class="text-[11px] font-semibold text-text-muted shrink-0">
                        Following
                    </span>
                </div>
            </div>
        </div>
    </aside>
</template>