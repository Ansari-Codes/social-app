<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import UiButton from '@/Ui/UiButton.vue';
import FeedLeftNav from '../Comps/Feed/FeedLeftNav.vue';
import FeedRightSidebar from '../Comps/Feed/FeedRightSidebar.vue';
import FeedPostCard from '../Comps/Feed/FeedPostCard.vue';
import FeedReplyModal from '../Comps/Feed/FeedReplyModal.vue';
import FeedTopComposer from '../Comps/Feed/FeedTopComposer.vue';
import type { Post, Profile } from '../Types/feed.type';
import { useMeStore } from '@/Stores/meStore';
import { requestAuthPrompt } from '@/Core/authPrompt';
import { createPost, togglePostReaction } from '@/Pages/_commons/Services/postService';
import { useFeedStore } from '@/Stores/feedStore';
import { useAppDataStore } from '@/Stores/appDataStore';

const router = useRouter();
const me = useMeStore();
const feedStore = useFeedStore();
const appData = useAppDataStore();
const { posts, nextCursor, loading: isLoading, loadingMore: isLoadingMore } = storeToRefs(feedStore);

const profile = ref<Profile | null>(null);
const feedError = ref('');
const actionError = ref('');
const isPublishing = ref(false);
const unreadNotificationsCount = ref(0);

// Filters and navigation
const currentFilter = ref<'all' | 'following' | 'starred' | 'discussions'>('all');
const searchQuery = ref<string>('');
const usernameQuery = ref<string>('');
const involvementFilter = ref<'all' | 'involved' | 'not_involved'>('all');

// Reply modal state
const replyModalOpen = ref(false);
const replyTargetPost = ref<Post | null>(null);

// Composer dialog state
const composerModalOpen = ref(false);
const composerDraft = ref('');

// Filtered posts based on stream, search/tag query, username query, and involvement
const filteredPosts = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const u = usernameQuery.value.trim().toLowerCase().replace(/^@/, '');

    return posts.value.filter(p => {
        // 1. Tag / Text search filter
        if (q) {
            if (!p.content.toLowerCase().includes(q)) {
                return false;
            }
        }

        // 2. Username filter: matches any profile whose username or display_name includes the entered text
        if (u) {
            const authorUsername = p.profile?.username?.toLowerCase() || '';
            const authorDisplayName = p.profile?.display_name?.toLowerCase() || '';
            if (!authorUsername.includes(u) && !authorDisplayName.includes(u)) {
                return false;
            }
        }

        // 3. Involvement filter
        if (involvementFilter.value === 'involved') {
            const isAuthor = p.profile?.isOwner || (profile.value && p.profile?.username === profile.value.username);
            const isReplyToMe = Boolean(profile.value && p.replyToAuthor === profile.value.username);
            const hasMyReaction = Boolean(p.myReactions && p.myReactions.length > 0);
            if (!isAuthor && !isReplyToMe && !hasMyReaction) return false;
        } else if (involvementFilter.value === 'not_involved') {
            const isAuthor = p.profile?.isOwner || (profile.value && p.profile?.username === profile.value.username);
            const isReplyToMe = Boolean(profile.value && p.replyToAuthor === profile.value.username);
            const hasMyReaction = Boolean(p.myReactions && p.myReactions.length > 0);
            if (isAuthor || isReplyToMe || hasMyReaction) return false;
        }

        // 4. Stream filter
        switch (currentFilter.value) {
            case 'following':
                return p.profile?.followedByMe;
            case 'starred':
                return p.profile?.starredByMe;
            case 'discussions':
                return (p.comments && p.comments > 0) || Boolean(p.replyTo);
            default:
                return true;
        }
    });
});

function clearAllFilters() {
    searchQuery.value = '';
    usernameQuery.value = '';
    involvementFilter.value = 'all';
    currentFilter.value = 'all';
}

function requireAuthentication(): boolean {
    if (me.isAuthenticated) return true;
    requestAuthPrompt();
    return false;
}

async function loadFeed() {
    feedError.value = '';
    try {
        await feedStore.load();
    } catch (error) {
        feedError.value = error instanceof Error ? error.message : 'Unable to load the feed.';
    }
}

async function loadMore() {
    if (nextCursor.value === null || isLoadingMore.value) return;
    feedError.value = '';
    try {
        await feedStore.loadMore();
    } catch (error) {
        feedError.value = error instanceof Error ? error.message : 'Unable to load more posts.';
    }
}

async function loadProfile() {
    try {
        const data = await appData.loadMyProfile();
        profile.value = {
            id: data.id,
            username: data.username,
            display_name: data.display_name,
            emoji: data.emoji ?? undefined,
            about: data.about ?? undefined,
            powerline: data.powerline ?? undefined,
            bannerColor: data.banner_color ?? undefined,
            isOwner: true,
            followers: data.followers,
            following: data.following,
            stars: data.stars,
            reactions: data.reactions,
            myReactions: data.my_reactions,
        };
    } catch {
        // Handled silently
    }
}

async function loadUnreadCount() {
    try {
        const data = await appData.loadNotifications();
        unreadNotificationsCount.value = data.unread_count;
    } catch {
        unreadNotificationsCount.value = 0;
    }
}

function selectFilter(filter: 'all' | 'following' | 'starred' | 'discussions') {
    if ((filter === 'following' || filter === 'starred') && !requireAuthentication()) return;
    searchQuery.value = '';
    currentFilter.value = filter;
}

function selectInvolvement(filter: 'all' | 'involved' | 'not_involved') {
    if (filter !== 'all' && !requireAuthentication()) return;
    involvementFilter.value = filter;
}

function selectTag(tag: string) {
    if (searchQuery.value === tag) {
        searchQuery.value = '';
    } else {
        searchQuery.value = tag;
    }
}

function openPost(post: Post) {
    void router.push({ name: 'post-detail', params: { id: post.id } });
}

function openReplyModal(post: Post) {
    if (!requireAuthentication()) return;
    replyTargetPost.value = post;
    replyModalOpen.value = true;
}

function openComposer() {
    if (!requireAuthentication()) return;
    composerModalOpen.value = true;
}

async function handlePublishPost(content: string) {
    if (!requireAuthentication()) return;
    if (!content.trim()) return;
    isPublishing.value = true;
    actionError.value = '';
    try {
        const newPost = await createPost(content);
        feedStore.addPost(newPost);
        composerModalOpen.value = false;
        composerDraft.value = '';
    } catch (error) {
        actionError.value = error instanceof Error ? error.message : 'Unable to publish post.';
    } finally {
        isPublishing.value = false;
    }
}

async function handleReplySubmit(content: string, parentPostId: number) {
    if (!requireAuthentication()) return;
    if (!content.trim()) return;
    isPublishing.value = true;
    actionError.value = '';
    try {
        const replyPost = await createPost(content, parentPostId);
        feedStore.addPost(replyPost);
        replyModalOpen.value = false;
        replyTargetPost.value = null;
    } catch (error) {
        actionError.value = error instanceof Error ? error.message : 'Unable to publish reply.';
    } finally {
        isPublishing.value = false;
    }
}

async function onReact(postId: number, reaction: string) {
    if (!requireAuthentication()) return;
    actionError.value = '';
    try {
        const updated = await togglePostReaction(postId, reaction);
        feedStore.replacePost(updated);
    } catch (error) {
        actionError.value = error instanceof Error ? error.message : 'Unable to update reaction.';
    }
}

function handleFollowed(profileId: number) {
    posts.value = posts.value.map(p => {
        if (p.profile.id === profileId) {
            return {
                ...p,
                profile: {
                    ...p.profile,
                    followedByMe: true,
                    followers: (p.profile.followers || 0) + 1,
                },
            };
        }
        return p;
    });
}

onMounted(() => {
    const tasks = [loadFeed()];
    if (me.isAuthenticated) tasks.push(loadProfile(), loadUnreadCount());
    void Promise.allSettled(tasks);
});

watch(() => me.token, (token) => {
    profile.value = null;
    unreadNotificationsCount.value = 0;
    const tasks = [loadFeed()];
    if (token) tasks.push(loadProfile(), loadUnreadCount());
    void Promise.allSettled(tasks);
});
</script>

<template>
    <div class="mx-auto flex w-full max-w-7xl items-start justify-center gap-6 px-3 py-4 sm:px-4 lg:px-6 lg:py-6">
        <!-- ── LEFT NAVIGATION RAIL (Desktop) ───────────────────────── -->
        <aside class="sticky top-20 hidden w-64 shrink-0 lg:block">
            <FeedLeftNav
                :current-filter="currentFilter"
                :unread-count="unreadNotificationsCount"
                :profile="profile"
                @filter="selectFilter"
                @compose="openComposer"
            />
        </aside>

        <!-- ── MAIN FEED COLUMN ────────────────────────────────────── -->
        <main class="flex w-full min-w-0 max-w-2xl flex-1 flex-col gap-4">
            <!-- Mobile Stream Switcher Bar (< lg screens) -->
            <div class="flex items-center gap-2 overflow-x-auto pb-1 lg:hidden">
                <button
                    v-for="s in [
                        { id: 'all', label: 'For You' },
                        { id: 'following', label: 'Following' },
                        { id: 'starred', label: 'Starred' },
                        { id: 'discussions', label: 'Discussions' }
                    ] as const"
                    :key="s.id"
                    type="button"
                    class="rounded-full px-3.5 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors"
                    :class="currentFilter === s.id && !searchQuery
                        ? 'bg-accent text-accent-fg shadow-xs'
                        : 'bg-bg-elevated border border-border text-text hover:bg-bg-hover'"
                    @click="selectFilter(s.id)"
                >
                    {{ s.label }}
                </button>
            </div>

            <!-- Top Twitter-Style Post Composer -->
            <FeedTopComposer
                v-if="me.isAuthenticated"
                :is-publishing="isPublishing"
                @publish="handlePublishPost"
            />
            <section v-else class="flex items-center justify-between gap-3 rounded-xl border border-border bg-bg-elevated p-4">
                <div>
                    <h2 class="text-sm font-semibold text-text-h">Join the conversation</h2>
                    <p class="mt-1 text-xs text-text-muted">Sign in to publish a post or reply.</p>
                </div>
                <UiButton size="sm" @click="requestAuthPrompt">Write a post</UiButton>
            </section>

            <!-- ── Feed Filter Bar: Search, Username & Involvement ───────── -->
            <div class="rounded-2xl border border-border bg-bg-elevated p-3 shadow-xs flex flex-col gap-2.5">
                <!-- Top Row: Activity Involvement Tabs + Reset Button -->
                <div class="flex flex-wrap items-center justify-between gap-2">
                    <div class="flex flex-wrap items-center gap-1.5 text-xs">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-text-muted mr-1">Activity:</span>
                        <button
                            type="button"
                            class="rounded-full px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer"
                            :class="involvementFilter === 'all'
                                ? 'bg-accent text-accent-fg shadow-xs'
                                : 'bg-bg-sunken text-text hover:bg-bg-hover'"
                            @click="selectInvolvement('all')"
                        >
                            All Posts
                        </button>
                        <button
                            type="button"
                            class="rounded-full px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer"
                            :class="involvementFilter === 'involved'
                                ? 'bg-accent text-accent-fg shadow-xs'
                                : 'bg-bg-sunken text-text hover:bg-bg-hover'"
                            title="Posts created by you, replies to you, or posts you reacted to"
                            @click="selectInvolvement('involved')"
                        >
                            ⚡ My Activity
                        </button>
                        <button
                            type="button"
                            class="rounded-full px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer"
                            :class="involvementFilter === 'not_involved'
                                ? 'bg-accent text-accent-fg shadow-xs'
                                : 'bg-bg-sunken text-text hover:bg-bg-hover'"
                            title="Explore posts you haven't engaged in yet"
                            @click="selectInvolvement('not_involved')"
                        >
                            🌐 Others
                        </button>
                    </div>

                    <!-- Reset Link -->
                    <button
                        v-if="searchQuery || usernameQuery || involvementFilter !== 'all' || currentFilter !== 'all'"
                        type="button"
                        class="text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                        @click="clearAllFilters"
                    >
                        Reset filters ✕
                    </button>
                </div>

                <!-- Bottom Row: Search Posts/Tags Input Box and Username Input Box -->
                <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 pt-1 border-t border-border/60">
                    <!-- Input 1: Search posts or #tag -->
                    <div class="relative flex items-center">
                        <span class="pointer-events-none absolute left-3 text-text-muted text-xs" aria-hidden="true">🔍</span>
                        <input
                            v-model="searchQuery"
                            type="search"
                            placeholder="Search posts or #tag…"
                            class="h-9 w-full rounded-xl border border-border bg-bg pl-8 pr-7 text-xs text-text placeholder:text-text-muted outline-none focus:border-accent"
                        />
                        <button
                            v-if="searchQuery"
                            type="button"
                            class="absolute right-2 text-xs text-text-muted hover:text-text-h cursor-pointer"
                            title="Clear search"
                            @click="searchQuery = ''"
                        >
                            ✕
                        </button>
                    </div>

                    <!-- Input 2: Enter username to filter posts by matching profiles -->
                    <div class="relative flex items-center">
                        <span class="pointer-events-none absolute left-3 text-text-muted text-xs font-bold" aria-hidden="true">@</span>
                        <input
                            v-model="usernameQuery"
                            type="search"
                            placeholder="Filter by username (e.g. john)…"
                            class="h-9 w-full rounded-xl border border-border bg-bg pl-8 pr-7 text-xs text-text placeholder:text-text-muted outline-none focus:border-accent"
                        />
                        <button
                            v-if="usernameQuery"
                            type="button"
                            class="absolute right-2 text-xs text-text-muted hover:text-text-h cursor-pointer"
                            title="Clear username filter"
                            @click="usernameQuery = ''"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                <!-- Active Filter Indicator -->
                <div
                    v-if="usernameQuery || searchQuery"
                    class="flex flex-wrap items-center gap-2 pt-0.5 text-[11px] text-text-muted"
                >
                    <span v-if="searchQuery">
                        Contains: <strong class="text-accent">{{ searchQuery }}</strong>
                    </span>
                    <span v-if="searchQuery && usernameQuery">·</span>
                    <span v-if="usernameQuery">
                        Creator matching: <strong class="text-accent">@{{ usernameQuery }}</strong>
                    </span>
                    <span>
                        ({{ filteredPosts.length }} {{ filteredPosts.length === 1 ? 'post' : 'posts' }} found)
                    </span>
                </div>
            </div>

            <!-- Error Banner -->
            <div
                v-if="feedError || actionError"
                class="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-danger"
                role="alert"
            >
                {{ feedError || actionError }}
            </div>

            <!-- Loading State -->
            <div v-if="isLoading" class="flex flex-col gap-3" role="status" aria-label="Loading feed">
                <div
                    v-for="n in 3"
                    :key="n"
                    class="animate-pulse rounded-2xl border border-border bg-bg-elevated p-5"
                >
                    <div class="flex items-center gap-3">
                        <div class="h-10 w-10 rounded-full bg-bg-sunken" />
                        <div class="flex-1 space-y-2">
                            <div class="h-3.5 w-32 rounded bg-bg-sunken" />
                            <div class="h-2.5 w-20 rounded bg-bg-sunken" />
                        </div>
                    </div>
                    <div class="mt-4 space-y-2.5">
                        <div class="h-3 w-full rounded bg-bg-sunken" />
                        <div class="h-3 w-4/5 rounded bg-bg-sunken" />
                    </div>
                </div>
            </div>

            <!-- Empty State -->
            <div
                v-else-if="!filteredPosts.length"
                class="rounded-2xl border border-dashed border-border bg-bg-elevated px-4 py-12 text-center shadow-card"
            >
                <span class="text-3xl" aria-hidden="true">🌱</span>
                <p class="mt-2 text-base font-bold text-text-h">No posts match your filters</p>
                <p class="mt-1 text-xs text-text-muted">
                    Try adjusting your stream, tag, creator, or involvement filters.
                </p>
                <UiButton
                    size="sm"
                    class="mt-4"
                    @click="clearAllFilters"
                >
                    Reset all filters
                </UiButton>
            </div>

            <!-- Main Post Stream -->
            <div v-else class="flex flex-col gap-3.5">
                <FeedPostCard
                    v-for="post in filteredPosts"
                    :key="post.id"
                    :post="post"
                    @react="onReact(post.id, $event)"
                    @reply="openReplyModal(post)"
                    @open-post="openPost(post)"
                />
            </div>
            <div v-if="nextCursor !== null && filteredPosts.length" class="flex justify-center py-2">
                <UiButton variant="secondary" :loading="isLoadingMore" @click="loadMore">
                    Load more
                </UiButton>
            </div>
        </main>

        <!-- ── RIGHT SIDEBAR (Desktop) ─────────────────────────────── -->
        <aside class="sticky top-20 hidden w-80 shrink-0 xl:block">
            <FeedRightSidebar
                :posts="posts"
                :current-tag="searchQuery"
                @select-tag="selectTag"
                @followed="handleFollowed"
            />
        </aside>

        <!-- ── Post Over Post Reply Modal ──────────────────────────── -->
        <FeedReplyModal
            v-model="replyModalOpen"
            :target-post="replyTargetPost"
            :is-publishing="isPublishing"
            @reply="handleReplySubmit"
        />

        <!-- ── General Compose Modal (Triggered by Left Nav) ────────── -->
        <FeedReplyModal
            v-if="composerModalOpen"
            :model-value="composerModalOpen"
            :target-post="null"
            :is-publishing="isPublishing"
            @update:model-value="composerModalOpen = $event"
            @reply="(content) => handlePublishPost(content)"
        />
    </div>
</template>