<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// PROFILE — same viewer UX as Feed.vue:
//   MOBILE: selecting a post swaps the list out for a full-width viewer.
//   DESKTOP (lg+): list and viewer render side-by-side.
// ═══════════════════════════════════════════════════════════════════════════

import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ApiError } from '@/Core/api';
import { setSharedPostLocation, sharedPostIdFromLocation, sharePost } from '@/Core/postShare';
import { useAppDataStore } from '@/Stores/appDataStore';
import { useFeedStore } from '@/Stores/feedStore';
import {
    setProfileFollow,
    setProfileStar,
    toggleProfileReaction,
} from '@/Pages/_commons/Services/chipService';
import { createPostComment, getPostComments, togglePostReaction } from '@/Pages/_commons/Services/postService';
import { useMeStore } from '@/Stores/meStore';
import UiInput from '@/Ui/UiInput.vue';
import UiChip from '@/Ui/UiChip.vue';
import CompProfileHero from '../Comps/CompProfileHero.vue';
import CompProfileTabs from '../Comps/CompProfileTabs.vue';
import CompProfileList from '../Comps/CompProfileList.vue';
import CompPost from '../Comps/CompPost.vue';
import CompPostViewer from '../Comps/CompPostViewer.vue';
import type { Profile, Post, Comments } from '../Types/feed.type';

const props = defineProps<{ profile: string }>();
const router = useRouter();
const appData = useAppDataStore();
const feedStore = useFeedStore();

const profile = ref<Profile | null>(null);
const profileLoading = ref(true);
const profileError = ref('');
const postsError = ref('');
const posts = ref<Post[]>([]);
const followers = ref<Profile[]>([]);
const following = ref<Profile[]>([]);
const connectionsLoading = ref(false);
const chipError = ref('');
const isUpdatingChip = ref(false);
let profileRequest = 0;

async function loadProfile(username: string) {
    const request = ++profileRequest;
    profileLoading.value = true;
    profileError.value = '';
    postsError.value = '';
    profile.value = null;
    posts.value = [];

    try {
        const data = await appData.loadProfile(username);
        if (request !== profileRequest) return;

        const loadedProfile: Profile = {
            id: data.id,
            userId: data.user_id,
            username: data.username,
            display_name: data.display_name,
            emoji: data.emoji ?? undefined,
            powerline: data.powerline ?? undefined,
            about: data.about ?? undefined,
            bannerColor: data.banner_color ?? undefined,
            birthday: data.birthday ?? undefined,
            // Privacy: only owners see contact fields.
            phone: data.is_owner ? data.phone ?? undefined : undefined,
            email: data.is_owner ? data.email ?? undefined : undefined,
            isOwner: data.is_owner,
            followers: data.followers,
            following: data.following,
            stars: data.stars,
            followedByMe: data.followed_by_me,
            starredByMe: data.starred_by_me,
            reactions: data.reactions,
            myReactions: data.my_reactions,
        };
        profile.value = loadedProfile;

        try {
            await feedStore.load();
            if (request !== profileRequest) return;
            posts.value = feedStore.posts.filter((post) => post.profile.username === data.username);
            loadedProfile.posts = posts.value.length;
            const sharedPostId = sharedPostIdFromLocation();
            if (sharedPostId !== null && posts.value.some((post) => post.id === sharedPostId)) {
                selectedId.value = sharedPostId;
            }
        } catch (error) {
            if (request === profileRequest) {
                postsError.value = error instanceof Error ? error.message : 'Unable to load posts.';
            }
        }
    } catch (error) {
        if (request !== profileRequest) return;
        profileError.value = error instanceof ApiError && error.status === 404
            ? `No profile was found for @${username}.`
            : error instanceof Error
                ? error.message
                : 'Unable to load this profile.';
    } finally {
        if (request === profileRequest) profileLoading.value = false;
    }
}

const tab = ref<'posts' | 'followers' | 'following'>('posts');
const selectedId = ref<number | null>(null);
const selectedPost = computed(
    () => posts.value.find((post) => post.id === selectedId.value) ?? null,
);
const selectedComments = ref<Comments | null>(null);
const replyToId = ref<number | null>(null);
const isCommenting = ref(false);
const commentError = ref('');
const commentsLoading = ref(false);
let commentsRequest = 0;

const me = useMeStore();
const searchQuery = ref('');
const selectedTag = ref('');
const involvementFilter = ref<'all' | 'involved' | 'standalone'>('all');

const profileTags = computed(() => {
    const counts: Record<string, number> = {};
    for (const post of posts.value) {
        if (!post.content) continue;
        const matches = post.content.match(/#[a-zA-Z0-9_]+/g);
        if (matches) {
            for (const tag of new Set(matches)) {
                counts[tag] = (counts[tag] || 0) + 1;
            }
        }
    }
    return Object.entries(counts)
        .map(([tag, count]) => ({ tag, count }))
        .sort((a, b) => b.count - a.count);
});

const filteredPosts = computed(() => {
    let list = posts.value;
    const q = searchQuery.value.trim().toLowerCase();
    if (q) {
        list = list.filter(p => p.content.toLowerCase().includes(q));
    }
    if (selectedTag.value) {
        list = list.filter(p => p.content.toLowerCase().includes(selectedTag.value.toLowerCase()));
    }
    if (involvementFilter.value === 'involved') {
        const myUsername = me.user?.username;
        list = list.filter(p => {
            const isReplyToMe = Boolean(myUsername && p.replyToAuthor === myUsername);
            const hasMyReaction = Boolean(p.myReactions && p.myReactions.length > 0);
            return isReplyToMe || hasMyReaction;
        });
    } else if (involvementFilter.value === 'standalone') {
        list = list.filter(p => !p.replyTo);
    }
    return list;
});

const tabProfiles = computed<Profile[]>(() => {
    if (tab.value === 'followers') return followers.value;
    if (tab.value === 'following') return following.value;
    return [];
});

const filteredTabProfiles = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return tabProfiles.value;
    return tabProfiles.value.filter(p =>
        p.username.toLowerCase().includes(q) ||
        Boolean(p.display_name && p.display_name.toLowerCase().includes(q))
    );
});

async function onFollow() {
    if (!profile.value?.userId || profile.value.isOwner) return;
    isUpdatingChip.value = true;
    chipError.value = '';
    try {
        profile.value = await setProfileFollow(profile.value.userId, !profile.value.followedByMe);
        await loadConnections();
    } catch (error) {
        chipError.value = error instanceof Error ? error.message : 'Unable to update follow status.';
    } finally {
        isUpdatingChip.value = false;
    }
}

async function onStar() {
    if (!profile.value?.userId || profile.value.isOwner) return;
    isUpdatingChip.value = true;
    chipError.value = '';
    try {
        profile.value = await setProfileStar(profile.value.userId, !profile.value.starredByMe);
    } catch (error) {
        chipError.value = error instanceof Error ? error.message : 'Unable to update star status.';
    } finally {
        isUpdatingChip.value = false;
    }
}

async function onProfileReact(reaction: string) {
    if (!profile.value?.userId) return;
    chipError.value = '';
    try {
        profile.value = await toggleProfileReaction(profile.value.userId, reaction);
    } catch (error) {
        chipError.value = error instanceof Error ? error.message : 'Unable to react to profile.';
    }
}

function openPost(post: Post) { selectedId.value = post.id; }

function closePost() {
    selectedId.value = null;
    selectedComments.value = null;
    replyToId.value = null;
}

function openProfile(item: Profile) {
    void router.push({ name: 'profile', params: { profile: item.username } });
}

async function loadConnections() {
    const current = profile.value;
    if (!current?.userId || (tab.value !== 'followers' && tab.value !== 'following')) return;
    connectionsLoading.value = true;
    chipError.value = '';
    try {
        const profiles = await appData.loadConnections(current.userId, tab.value);
        if (tab.value === 'followers') followers.value = profiles;
        else following.value = profiles;
    } catch (error) {
        chipError.value = error instanceof Error ? error.message : 'Unable to load profile connections.';
    } finally {
        connectionsLoading.value = false;
    }
}

async function onReact(postId: number, reaction: string) {
    try {
        const updated = await togglePostReaction(postId, reaction);
        const index = posts.value.findIndex((post) => post.id === updated.id);
        if (index !== -1) posts.value.splice(index, 1, updated);
    } catch (error) {
        commentError.value = error instanceof Error ? error.message : 'Unable to update reaction.';
    }
}

async function shareProfilePost(post: Post) {
    commentError.value = '';
    try {
        await sharePost(post.id, post.content, post.profile.id);
    } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return;
        commentError.value = error instanceof Error ? error.message : 'Unable to share this post.';
    }
}

async function onCommentReact(commentId: number, reaction: string) {
    try {
        await togglePostReaction(commentId, reaction);
        if (selectedId.value !== null) selectedComments.value = await getPostComments(selectedId.value);
    } catch (error) {
        commentError.value = error instanceof Error ? error.message : 'Unable to update reaction.';
    }
}

async function submitComment(content: string, replyTarget: number | null) {
    const post = selectedPost.value;
    if (!post || !content.trim()) return;
    isCommenting.value = true;
    commentError.value = '';
    try {
        await createPostComment(post.id, content, replyTarget ?? undefined);
        replyToId.value = null;
        selectedComments.value = await getPostComments(post.id);
        const index = posts.value.findIndex((item) => item.id === post.id);
        if (index !== -1) posts.value[index] = { ...post, comments: post.comments + 1 };
    } catch (error) {
        commentError.value = error instanceof Error ? error.message : 'Unable to add comment.';
    } finally {
        isCommenting.value = false;
    }
}

// Comments race guard — same pattern as Feed.vue.
watch(selectedId, async (postId) => {
    const request = ++commentsRequest;
    setSharedPostLocation(postId);
    commentError.value = '';
    replyToId.value = null;
    if (postId === null) {
        selectedComments.value = null;
        commentsLoading.value = false;
        return;
    }
    commentsLoading.value = true;
    try {
        const comments = await getPostComments(postId);
        if (request === commentsRequest) selectedComments.value = comments;
    } catch (error) {
        if (request === commentsRequest) {
            commentError.value = error instanceof Error ? error.message : 'Unable to load comments.';
        }
    } finally {
        if (request === commentsRequest) commentsLoading.value = false;
    }
});

watch(() => props.profile, (username) => {
    selectedId.value = null;
    tab.value = 'posts';
    void loadProfile(username);
}, { immediate: true });

watch(() => me.token, () => {
    void loadProfile(props.profile);
});

watch(() => feedStore.posts, (feedPosts) => {
    const current = profile.value;
    if (!current) return;
    posts.value = feedPosts.filter((post) => post.profile.username === current.username);
    current.posts = posts.value.length;
}, { deep: true });

watch(tab, () => {
    void loadConnections();
});
</script>

<template>
    <div class="mx-auto flex w-full min-w-0 max-w-5xl flex-col gap-4 px-3 py-4 lg:px-4 lg:py-6">
        <p v-if="profileLoading" class="py-12 text-center text-sm text-text-muted" role="status">
            Loading profile...
        </p>

        <section v-else-if="profileError" class="rounded-lg border border-border bg-bg-elevated p-6 text-center">
            <h1 class="text-lg font-semibold text-text-h">Profile unavailable</h1>
            <p class="mt-2 text-sm text-text-muted">{{ profileError }}</p>
        </section>

        <template v-else-if="profile">
            <!--
              Hero + tabs hide on mobile when the viewer is open, so the
              viewer gets the entire viewport below the fixed header.
              On lg+ they stay visible since the viewer is only half-width.
            -->
            <div :class="selectedPost && 'hidden lg:block'">
                <CompProfileHero :profile="profile" :following="profile.followedByMe" :starred="profile.starredByMe"
                    :disabled="isUpdatingChip || profile.isOwner" @follow="onFollow" @star="onStar"
                    @react="onProfileReact" />
                <CompProfileTabs class="mt-4" :active="tab"
                    :counts="{ posts: posts.length, followers: profile.followers, following: profile.following }"
                    @change="tab = $event" />
            </div>

            <p v-if="postsError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
                role="alert">
                {{ postsError }}
            </p>
            <p v-if="commentError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
                role="alert">
                {{ commentError }}
            </p>
            <p v-if="chipError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
                role="alert">
                {{ chipError }}
            </p>

            <!--
              Split layout mirrors Feed.vue:
                section  — list, hidden on mobile when a post is selected
                aside    — viewer, full-screen on mobile when selected
              Both share the row on lg+.
            -->
            <div class="flex flex-col items-start gap-4 lg:flex-row lg:gap-6">
                <section class="flex w-full min-w-0 flex-col gap-3"
                    :class="selectedPost ? 'hidden lg:flex lg:flex-1' : 'lg:flex-1'">
                    <template v-if="tab === 'posts'">
                        <!-- Profile Posts Filter Toolbar -->
                        <div class="flex flex-col gap-2 rounded-2xl border border-border bg-bg-elevated p-3 shadow-xs">
                            <div class="flex flex-wrap items-center justify-between gap-2">
                                <div class="min-w-0 flex-1 sm:max-w-xs">
                                    <UiInput
                                        v-model="searchQuery"
                                        type="search"
                                        placeholder="Search in posts…"
                                        aria-label="Search posts"
                                    />
                                </div>

                                <!-- Involvement toggle -->
                                <div class="flex items-center gap-1.5 text-xs">
                                    <span class="text-text-muted font-medium mr-1">Activity:</span>
                                    <UiChip
                                        size="sm"
                                        :variant="involvementFilter === 'all' ? 'accent' : 'soft'"
                                        :selected="involvementFilter === 'all'"
                                        @click="involvementFilter = 'all'"
                                    >
                                        All
                                    </UiChip>
                                    <UiChip
                                        v-if="!profile?.isOwner"
                                        size="sm"
                                        :variant="involvementFilter === 'involved' ? 'accent' : 'soft'"
                                        :selected="involvementFilter === 'involved'"
                                        title="Posts involving you (replies to you or reacted by you)"
                                        @click="involvementFilter = involvementFilter === 'involved' ? 'all' : 'involved'"
                                    >
                                        ⚡ With Me
                                    </UiChip>
                                    <UiChip
                                        size="sm"
                                        :variant="involvementFilter === 'standalone' ? 'accent' : 'soft'"
                                        :selected="involvementFilter === 'standalone'"
                                        @click="involvementFilter = involvementFilter === 'standalone' ? 'all' : 'standalone'"
                                    >
                                        Standalone
                                    </UiChip>
                                </div>
                            </div>

                            <!-- Tag chips row if tags exist -->
                            <div v-if="profileTags.length" class="flex flex-wrap items-center gap-1.5 border-t border-border/60 pt-2 text-xs">
                                <span class="text-text-muted mr-1 font-medium">Tags:</span>
                                <UiChip
                                    v-for="t in profileTags.slice(0, 6)"
                                    :key="t.tag"
                                    size="sm"
                                    :variant="selectedTag === t.tag ? 'accent' : 'soft'"
                                    :selected="selectedTag === t.tag"
                                    @click="selectedTag = selectedTag === t.tag ? '' : t.tag"
                                >
                                    {{ t.tag }} ({{ t.count }})
                                </UiChip>
                                <button
                                    v-if="selectedTag || searchQuery || involvementFilter !== 'all'"
                                    type="button"
                                    class="ml-auto text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                                    @click="selectedTag = ''; searchQuery = ''; involvementFilter = 'all'"
                                >
                                    Clear filters ✕
                                </button>
                            </div>
                        </div>

                        <p v-if="!filteredPosts.length && !postsError" class="py-6 text-center text-sm text-text-muted">
                            {{ searchQuery || selectedTag || involvementFilter !== 'all'
                                ? 'No posts match your filters.'
                                : 'No posts yet.' }}
                        </p>
                        <div v-else class="grid gap-3" :class="selectedPost ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2'">
                            <div v-for="post in filteredPosts" :key="post.id"
                                class="cursor-pointer rounded-lg transition-colors"
                                :class="selectedId === post.id && 'ring-2 ring-accent/40'" @click="openPost(post)">
                                <CompPost :post="post" class="w-full" @react="onReact(post.id, $event)"
                                    @share="shareProfilePost(post)" />
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <div class="mb-2">
                            <UiInput
                                v-model="searchQuery"
                                type="search"
                                :placeholder="`Search ${tab}…`"
                                :aria-label="`Search ${tab}`"
                            />
                        </div>
                        <CompProfileList :profiles="filteredTabProfiles" :cols="2"
                            :empty-text="`${tab === 'followers' ? 'Follower' : 'Following'} information is not available yet.`"
                            @open="openProfile" />
                    </template>
                    <p v-if="connectionsLoading" class="text-center text-xs text-text-muted" role="status">Loading
                        profiles...</p>
                </section>

                <!-- Viewer: full-screen on mobile, right column on lg+. -->
                <aside v-if="selectedPost"
                    class="h-[calc(100dvh-3.5rem)] w-full min-w-0 lg:sticky lg:top-18 lg:h-[calc(100dvh-5rem)] lg:w-1/2 lg:shrink-0">
                    <CompPostViewer
                        :post="selectedPost"
                        :comments="selectedComments"
                        :reply-to-id="replyToId"
                        :commenting="isCommenting"
                        :comment-error="commentError"
                        :comments-loading="commentsLoading"
                        @react="onReact(selectedPost.id, $event)"
                        @react-comment="onCommentReact"
                        @reply="replyToId = $event"
                        @comment="submitComment"
                        @close="closePost"
                    />
                </aside>
            </div>
        </template>
    </div>
</template>