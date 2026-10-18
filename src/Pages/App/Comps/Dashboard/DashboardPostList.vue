<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD POSTS / COMMENTS MANAGER
// Dual-mode component: renders either the user's own posts or their comments
// based on the `kind` prop. Left column = list, right column = detail viewer.
//
// Mobile: selecting a post swaps the list out for a full-width viewer,
//         matching the Feed.vue pattern.
// ═══════════════════════════════════════════════════════════════════════════

import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import UiInput from '@/Ui/UiInput.vue';
import UiButton from '@/Ui/UiButton.vue';
import UiChip from '@/Ui/UiChip.vue';
import UiOptions, { type MenuOption } from '@/Ui/UiOptions.vue';
import { setSharedPostLocation, sharedPostIdFromLocation } from '@/Core/postShare';
import CompPost from '../CompPost.vue';
import CompPostViewer from '../CompPostViewer.vue';
import type { Post, Comments, Comment } from '../../Types/feed.type';
import {
    createPost,
    createPostComment,
    deletePost,
    getPostComments,
    togglePostReaction,
    updatePost,
} from '@/Pages/_commons/Services/postService';
import { useAppDataStore } from '@/Stores/appDataStore';

// ─── Props ─────────────────────────────────────────────────────────────────
// `kind` picks which bucket of posts to render — top-level posts or comments.
const props = defineProps<{ kind: 'posts' | 'comments' }>();
const appData = useAppDataStore();

// ─── Core state ────────────────────────────────────────────────────────────
const posts = ref<Post[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);
const pageError = ref('');
const actionError = ref('');
const query = ref('');
const editorOpen = ref(false);
const editorContent = ref('');
const editingId = ref<number | null>(null);   // null => creating, else editing

// ─── Additional Filters ────────────────────────────────────────────────────
const selectedTag = ref<string>('');
const involvementFilter = ref<'all' | 'root' | 'discussions' | 'reacted'>('all');

// ─── Detail panel state ────────────────────────────────────────────────────
const selectedId = ref<number | null>(null);
const selectedPost = computed(() => posts.value.find((post) => post.id === selectedId.value) ?? null);
const selectedComments = ref<Comments | null>(null);
const replyToId = ref<number | null>(null);
const commentsLoading = ref(false);
const isCommenting = ref(false);

// Race guard for out-of-order comments fetches when the user clicks quickly.
let commentsRequest = 0;

// ─── Sorting ───────────────────────────────────────────────────────────────
type SortKey = 'newest' | 'oldest' | 'reactions' | 'comments';
const sort = ref<SortKey>('newest');
const sortOptions: MenuOption[] = [
    { value: 'newest', label: 'Newest first', icon: '🆕' },
    { value: 'oldest', label: 'Oldest first', icon: '🕰️' },
    { value: 'reactions', label: 'Most reactions', icon: '🔥' },
    { value: 'comments', label: 'Most comments', icon: '💬' },
];

// ─── Helpers ───────────────────────────────────────────────────────────────
function toMessage(error: unknown): string {
    return error instanceof Error ? error.message : 'Something went wrong.';
}

async function loadPosts() {
    isLoading.value = true;
    pageError.value = '';
    try {
        posts.value = await appData.loadMyPosts();
        const sharedPostId = sharedPostIdFromLocation();
        if (sharedPostId !== null && posts.value.some((post) => post.id === sharedPostId)) {
            selectedId.value = sharedPostId;
        }
    } catch (error) {
        pageError.value = toMessage(error);
    } finally {
        isLoading.value = false;
    }
}

function sumReactions(post: Post) {
    return Object.values(post.reactions).reduce((total, count) => total + count, 0);
}

// Extract tags present across posts
const availableTags = computed(() => {
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

// ─── Derived list: filter by kind, search, tag, involvement, then sort ────
const visiblePosts = computed(() => {
    const isComment = props.kind === 'comments';
    let list = posts.value.filter((post) => (post.isComment === true) === isComment);

    const search = query.value.trim().toLowerCase();
    if (search) {
        list = list.filter((post) => post.content.toLowerCase().includes(search));
    }

    if (selectedTag.value) {
        list = list.filter((post) => post.content.toLowerCase().includes(selectedTag.value.toLowerCase()));
    }

    if (involvementFilter.value === 'root') {
        list = list.filter((post) => !post.replyTo && !post.isComment);
    } else if (involvementFilter.value === 'discussions') {
        list = list.filter((post) => Boolean(post.replyTo) || Boolean(post.isComment) || post.comments > 0);
    } else if (involvementFilter.value === 'reacted') {
        list = list.filter((post) => sumReactions(post) > 0);
    }

    switch (sort.value) {
        case 'newest': return list.sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt));
        case 'oldest': return list.sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));
        case 'comments': return list.sort((a, b) => b.comments - a.comments);
        case 'reactions': return list.sort((a, b) => sumReactions(b) - sumReactions(a));
    }
});

function onSortSelect(value: string | number) {
    sort.value = value as SortKey;
}

// ─── Inline editor (create / edit) ─────────────────────────────────────────
function openCreate() {
    editingId.value = null;
    editorContent.value = '';
    actionError.value = '';
    editorOpen.value = true;
}

function closeEditor() {
    editorOpen.value = false;
    editingId.value = null;
    editorContent.value = '';
}

function onEdit(post: Post, event: MouseEvent) {
    event.stopPropagation();   // don't also trigger the card's open-post click
    editingId.value = post.id;
    editorContent.value = post.content;
    actionError.value = '';
    editorOpen.value = true;
}

async function savePost() {
    if (!editorContent.value.trim()) {
        actionError.value = 'Write something before saving.';
        return;
    }
    isSaving.value = true;
    actionError.value = '';
    try {
        if (editingId.value !== null) {
            const updated = await updatePost(editingId.value, editorContent.value);
            const index = posts.value.findIndex((post) => post.id === updated.id);
            if (index !== -1) posts.value.splice(index, 1, updated);
        } else {
            posts.value.unshift(await createPost(editorContent.value));
        }
        closeEditor();
    } catch (error) {
        actionError.value = toMessage(error);
    } finally {
        isSaving.value = false;
    }
}

// ─── Detail panel: open / close / comments ─────────────────────────────────
function openPost(post: Post) {
    selectedId.value = post.id;
}

function closePost() {
    selectedId.value = null;
    selectedComments.value = null;
    replyToId.value = null;
}

async function loadComments(postId: number) {
    const request = ++commentsRequest;
    commentsLoading.value = true;
    selectedComments.value = null;
    try {
        const result = await getPostComments(postId);
        if (request === commentsRequest) selectedComments.value = result;
    } catch (error) {
        if (request === commentsRequest) actionError.value = toMessage(error);
    } finally {
        if (request === commentsRequest) commentsLoading.value = false;
    }
}

// React to selection changes; cancel in-flight fetches when the panel closes.
watch(selectedId, (postId) => {
    setSharedPostLocation(postId);
    actionError.value = '';
    replyToId.value = null;
    if (postId === null) {
        commentsRequest += 1;
        selectedComments.value = null;
        commentsLoading.value = false;
        return;
    }
    void loadComments(postId);
});

// ─── Mutations ─────────────────────────────────────────────────────────────
function replacePost(updated: Post) {
    const index = posts.value.findIndex((post) => post.id === updated.id);
    if (index !== -1) posts.value.splice(index, 1, updated);
}

async function onReact(postId: number, reaction: string) {
    actionError.value = '';
    try {
        replacePost(await togglePostReaction(postId, reaction));
    } catch (error) {
        actionError.value = toMessage(error);
    }
}

async function onCommentReact(commentId: number, reaction: string) {
    actionError.value = '';
    try {
        await togglePostReaction(commentId, reaction);
        // Comments are nested — reload the tree so counts refresh.
        if (selectedId.value !== null) await loadComments(selectedId.value);
    } catch (error) {
        actionError.value = toMessage(error);
    }
}

async function onDelete(post: Post, event: MouseEvent) {
    event.stopPropagation();   // don't open the post when deleting
    if (!confirm(`Delete this ${post.isComment ? 'comment' : 'post'} and its replies?`)) return;
    actionError.value = '';
    try {
        await deletePost(post.id);
        posts.value = posts.value.filter((item) => item.id !== post.id);
        if (selectedId.value === post.id) closePost();
    } catch (error) {
        actionError.value = toMessage(error);
    }
}

function onSelect(post: Post, event: MouseEvent) {
    event.stopPropagation();
    openPost(post);
}

// ─── Comment composer ──────────────────────────────────────────────────────
async function submitComment(content: string, replyTarget: number | null) {
    const post = selectedPost.value;
    if (!post || !content.trim()) return;
    isCommenting.value = true;
    actionError.value = '';
    try {
        const created: Comment = await createPostComment(post.id, content, replyTarget ?? undefined);
        if (!selectedComments.value) selectedComments.value = { postId: post.id, comments: [] };
        selectedComments.value.comments.push(created);
        replyToId.value = null;
        // Refresh the list so the card's comment counter updates.
        posts.value = await appData.loadMyPosts(true);
    } catch (error) {
        actionError.value = toMessage(error);
    } finally {
        isCommenting.value = false;
    }
}

onMounted(() => {
    void loadPosts();
});
</script>

<template>
    <section class="flex w-full min-w-0 flex-col gap-4" :aria-label="kind === 'posts' ? 'Your posts' : 'Your comments'">
        <!--
          Header / editor / search bar all hide on mobile when a post is
          open, so the viewer owns the full viewport below the app header.
        -->
        <template v-if="!selectedPost || !isLoading">
            <header v-show="!selectedPost || false" class="flex flex-wrap items-center justify-between gap-3 lg:flex">
                <h2 class="text-lg font-semibold text-text-h">{{ kind === 'posts' ? 'Posts' : 'Comments' }}</h2>
                <UiButton v-if="kind === 'posts'" @click="openCreate">＋ Create post</UiButton>
            </header>
        </template>

        <!-- Editor: hidden on mobile while a post is open. -->
        <form v-if="editorOpen" v-show="!selectedPost" class="rounded-lg border border-border bg-bg-elevated p-4"
            @submit.prevent="savePost">
            <label class="block text-sm font-medium text-text-h" for="dashboard-post-content">
                {{ editingId === null ? 'New post' : 'Edit post' }}
            </label>
            <textarea id="dashboard-post-content" v-model="editorContent" rows="5" maxlength="10000" autofocus
                class="mt-2 w-full resize-y rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none focus:border-accent"
                placeholder="What would you like to share? Markdown is supported." />
            <div class="mt-2 flex flex-wrap items-center justify-between gap-3">
                <span class="text-xs text-text-muted">{{ editorContent.length }} / 10000</span>
                <div class="flex gap-2">
                    <UiButton variant="ghost" type="button" @click="closeEditor">Cancel</UiButton>
                    <UiButton type="submit" :loading="isSaving">
                        {{ editingId === null ? 'Publish' : 'Save changes' }}
                    </UiButton>
                </div>
            </div>
        </form>

        <p v-if="pageError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
            role="alert">
            {{ pageError }}</p>
        <p v-if="actionError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
            role="alert">{{ actionError }}</p>

        <!-- Search + filter toolbar: hidden on mobile while a post is open. -->
        <div v-show="!selectedPost" class="flex flex-col gap-3" :class="selectedPost && 'hidden lg:flex'">
            <div class="flex w-full flex-row items-center gap-2">
                <div class="min-w-0 flex-1">
                    <UiInput v-model="query" type="search" :placeholder="`Search your ${kind}…`"
                        :aria-label="`Search your ${kind}`" />
                </div>
                <UiOptions :options="sortOptions" size="sm" align="end" label="Sort activity" @select="onSortSelect">
                    <template #trigger>
                        <UiButton variant="soft" aria-label="Sort activity">
                            <template #leading><span aria-hidden="true">↕</span></template>
                            Sort
                        </UiButton>
                    </template>
                </UiOptions>
            </div>

            <!-- Filter Chips Row (Involvement + Tags) -->
            <div class="flex flex-wrap items-center gap-1.5 text-xs">
                <span class="text-text-muted font-medium mr-1">Filter:</span>
                <UiChip
                    size="sm"
                    :variant="involvementFilter === 'all' && !selectedTag ? 'accent' : 'soft'"
                    :selected="involvementFilter === 'all' && !selectedTag"
                    @click="involvementFilter = 'all'; selectedTag = ''"
                >
                    All
                </UiChip>
                <UiChip
                    size="sm"
                    :variant="involvementFilter === 'root' ? 'accent' : 'soft'"
                    :selected="involvementFilter === 'root'"
                    @click="involvementFilter = involvementFilter === 'root' ? 'all' : 'root'"
                >
                    Root Posts
                </UiChip>
                <UiChip
                    size="sm"
                    :variant="involvementFilter === 'discussions' ? 'accent' : 'soft'"
                    :selected="involvementFilter === 'discussions'"
                    @click="involvementFilter = involvementFilter === 'discussions' ? 'all' : 'discussions'"
                >
                    💬 Discussions & Replies
                </UiChip>
                <UiChip
                    size="sm"
                    :variant="involvementFilter === 'reacted' ? 'accent' : 'soft'"
                    :selected="involvementFilter === 'reacted'"
                    @click="involvementFilter = involvementFilter === 'reacted' ? 'all' : 'reacted'"
                >
                    ❤️ With Reactions
                </UiChip>

                <!-- Dynamic Tag Chips -->
                <template v-if="availableTags.length">
                    <span class="text-border mx-1" aria-hidden="true">|</span>
                    <UiChip
                        v-for="t in availableTags.slice(0, 5)"
                        :key="t.tag"
                        size="sm"
                        :variant="selectedTag === t.tag ? 'accent' : 'soft'"
                        :selected="selectedTag === t.tag"
                        @click="selectedTag = selectedTag === t.tag ? '' : t.tag"
                    >
                        {{ t.tag }} ({{ t.count }})
                    </UiChip>
                </template>

                <button
                    v-if="selectedTag || involvementFilter !== 'all' || query"
                    type="button"
                    class="ml-auto text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                    @click="selectedTag = ''; involvementFilter = 'all'; query = ''"
                >
                    Clear filters ✕
                </button>
            </div>
        </div>

        <p v-if="isLoading" class="py-8 text-center text-sm text-text-muted" role="status">Loading {{ kind }}...</p>

        <!--
          Split layout:
            section — list, hidden on mobile when a post is selected
            aside   — viewer, full-screen on mobile when selected
          Both share the row on lg+.
        -->
        <div v-else class="flex w-full flex-col items-start gap-4 lg:flex-row lg:gap-6">
            <section class="flex w-full min-w-0 flex-col gap-3"
                :class="selectedPost ? 'hidden lg:flex lg:flex-1' : 'lg:flex-2'">
                <p v-if="!visiblePosts.length" class="py-6 text-center text-sm text-text-muted">
                    {{ query || selectedTag || involvementFilter !== 'all'
                        ? `No ${kind} match your active filters.`
                        : (kind === 'posts' ? 'You have not posted anything yet.' : 'You have not commented yet.') }}
                </p>
                <div class="grid gap-3" :class="selectedPost ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2'">
                    <div v-for="post in visiblePosts" :key="post.id"
                        class="group relative flex flex-col cursor-pointer overflow-hidden rounded-2xl border border-border bg-bg-elevated shadow-xs transition-all hover:border-border-strong hover:shadow-card"
                        :class="selectedId === post.id && 'ring-2 ring-accent/40'" @click="openPost(post)">
                        <CompPost :post="post" class="w-full" :show-actions="false" @react="onReact(post.id, $event)" />
                        <p v-if="kind === 'comments' && post.rootPostId" class="px-3 pb-1 pt-1 text-xs text-text-muted" @click.stop>
                            On post
                            <RouterLink
                                :to="{ name: 'post-detail', params: { id: post.rootPostId } }"
                                class="font-semibold text-accent hover:underline"
                            >
                                #{{ post.rootPostId }}
                            </RouterLink>
                        </p>

                        <!-- Bottom Action Chips -->
                        <div class="mt-auto flex flex-wrap items-center justify-between gap-1.5 border-t border-border/70 bg-bg-sunken/40 px-3 py-2" @click.stop>
                            <div class="flex flex-wrap items-center gap-1.5">
                                <UiChip
                                    size="sm"
                                    variant="accent"
                                    aria-label="View post"
                                    @click="onSelect(post, $event)"
                                >
                                    <template #leading><span aria-hidden="true">👁️</span></template>
                                    View
                                </UiChip>
                                <UiChip
                                    v-if="kind === 'posts'"
                                    size="sm"
                                    variant="soft"
                                    aria-label="Edit post"
                                    @click="onEdit(post, $event)"
                                >
                                    <template #leading><span aria-hidden="true">✏️</span></template>
                                    Edit
                                </UiChip>
                                <RouterLink
                                    :to="{ name: 'post-detail', params: { id: post.isComment ? (post.rootPostId || post.id) : post.id } }"
                                    class="no-underline"
                                    @click.stop
                                >
                                    <UiChip size="sm" variant="soft" aria-label="Open Thread">
                                        <template #leading><span aria-hidden="true">↗</span></template>
                                        Thread
                                    </UiChip>
                                </RouterLink>
                            </div>

                            <UiChip
                                size="sm"
                                variant="soft"
                                class="text-danger hover:border-danger/40"
                                aria-label="Delete post"
                                @click="onDelete(post, $event)"
                            >
                                <template #leading><span aria-hidden="true">🗑️</span></template>
                                Delete
                            </UiChip>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Viewer: full-screen on mobile, right column on lg+. -->
            <aside v-if="selectedPost"
                class="h-[calc(100dvh-3.5rem)] w-full min-w-0 lg:sticky lg:top-18 lg:h-[calc(100dvh-5rem)] lg:w-1/2 lg:shrink-0">
                <div class="h-full min-h-0">
                    <div class="h-full min-h-0">
                        <CompPostViewer
                            :post="selectedPost"
                            :comments="selectedComments"
                            :reply-to-id="replyToId"
                            :commenting="isCommenting"
                            :comment-error="actionError"
                            :comments-loading="commentsLoading"
                            @react="onReact(selectedPost.id, $event)" @react-comment="onCommentReact"
                            @reply="replyToId = $event" @comment="submitComment" @close="closePost" />
                    </div>
                </div>
            </aside>
        </div>
    </section>
</template>