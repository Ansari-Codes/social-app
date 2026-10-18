<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import UiButton from '@/Ui/UiButton.vue';
import PostDetailCard from '../Comps/Post/PostDetailCard.vue';
import PostCommentItem from '../Comps/Post/PostCommentItem.vue';
import FeedRightSidebar from '../Comps/Feed/FeedRightSidebar.vue';
import type { Post, Comments, Comment } from '../Types/feed.type';
import {
    getPost,
    getPostComments,
    createPostComment,
    togglePostReaction,
} from '@/Pages/_commons/Services/postService';
import { useMeStore } from '@/Stores/meStore';
import { useFeedStore } from '@/Stores/feedStore';
import { requestAuthPrompt } from '@/Core/authPrompt';

const props = defineProps<{
    id?: string;
}>();

const route = useRoute();
const router = useRouter();
const me = useMeStore();
const feedStore = useFeedStore();

const postId = computed(() => Number(props.id || route.params.id));

const post = ref<Post | null>(null);
const parentPost = ref<Post | null>(null);
const comments = ref<Comments | null>(null);
const allFeedPosts = computed(() => feedStore.posts);

const isLoading = ref(true);
const isCommenting = ref(false);
const error = ref('');
const replyDraft = ref('');
const replyInputRef = ref<HTMLTextAreaElement | null>(null);

const topLevelComments = computed<Comment[]>(() => {
    if (!comments.value?.comments) return [];
    const rootId = post.value?.id;
    return comments.value.comments.filter(
        c => c.replyTo == null || c.replyTo === rootId
    );
});

async function loadPostData() {
    if (!postId.value || isNaN(postId.value)) {
        error.value = 'Invalid post ID.';
        isLoading.value = false;
        return;
    }

    isLoading.value = true;
    error.value = '';
    parentPost.value = null;

    try {
        const loadedPost = await getPost(postId.value);
        post.value = loadedPost;

        // Load comments
        comments.value = await getPostComments(postId.value);

        // If this post is a reply to another post, fetch parent post for thread view
        if (loadedPost.replyTo) {
            try {
                parentPost.value = await getPost(loadedPost.replyTo);
            } catch {
                parentPost.value = null;
            }
        }

        // Load feed posts for the right sidebar
        try {
            await feedStore.load();
        } catch {
            // Handled
        }
    } catch (err) {
        error.value = err instanceof Error ? err.message : 'Unable to load post.';
    } finally {
        isLoading.value = false;
    }
}

async function handleReact(emoji: string) {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    if (!post.value) return;
    try {
        const updated = await togglePostReaction(post.value.id, emoji);
        post.value = updated;
    } catch (err) {
        error.value = err instanceof Error ? err.message : 'Unable to react.';
    }
}

async function handleCommentReact(commentId: number, emoji: string) {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    try {
        await togglePostReaction(commentId, emoji);
        if (post.value) {
            comments.value = await getPostComments(post.value.id);
        }
    } catch {
        // Handled
    }
}

async function handleReplyToPost() {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    if (!post.value || !replyDraft.value.trim() || isCommenting.value) return;
    isCommenting.value = true;
    error.value = '';
    try {
        await createPostComment(post.value.id, replyDraft.value.trim(), post.value.id);
        replyDraft.value = '';
        comments.value = await getPostComments(post.value.id);
        post.value.comments += 1;
    } catch (err) {
        error.value = err instanceof Error ? err.message : 'Unable to add reply.';
    } finally {
        isCommenting.value = false;
    }
}

async function handleReplyToComment(targetCommentId: number, content: string) {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    if (!post.value || !content.trim()) return;
    try {
        await createPostComment(post.value.id, content, targetCommentId);
        comments.value = await getPostComments(post.value.id);
        post.value.comments += 1;
    } catch {
        // Handled
    }
}

function focusReply() {
    nextTick(() => {
        replyInputRef.value?.focus();
        replyInputRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
}

function handleFocusReply() {
    if (!me.isAuthenticated) {
        requestAuthPrompt();
        return;
    }
    focusReply();
}

function goBack() {
    if (window.history.length > 1) {
        router.back();
    } else {
        void router.push({ name: 'app' });
    }
}

watch(postId, () => {
    void loadPostData();
});

onMounted(() => {
    void loadPostData();
});
</script>

<template>
    <div class="mx-auto flex w-full max-w-6xl items-start justify-center gap-6 px-3 py-4 sm:px-4 lg:px-6 lg:py-6">
        <!-- ── Main Twitter Style Post Column ──────────────────────── -->
        <main class="flex w-full min-w-0 max-w-2xl flex-1 flex-col gap-4">
            <!-- Sticky Header with Back Button -->
            <header class="sticky top-14 z-20 flex items-center gap-3 border-b border-border bg-bg/90 px-2 py-3 backdrop-blur sm:px-0">
                <button
                    type="button"
                    class="flex h-9 w-9 items-center justify-center rounded-full text-lg text-text-muted transition-colors hover:bg-bg-hover hover:text-text-h cursor-pointer"
                    aria-label="Go back"
                    @click="goBack"
                >
                    ←
                </button>
                <div>
                    <h1 class="text-lg font-bold text-text-h">Thread</h1>
                    <p class="text-xs text-text-muted">Full post conversation</p>
                </div>
            </header>

            <!-- Error Banner -->
            <div
                v-if="error"
                class="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-danger"
                role="alert"
            >
                {{ error }}
            </div>

            <!-- Loading State -->
            <div v-if="isLoading" class="flex flex-col gap-4">
                <div class="animate-pulse rounded-2xl border border-border bg-bg-elevated p-6 space-y-4">
                    <div class="flex items-center gap-3">
                        <div class="h-12 w-12 rounded-full bg-bg-sunken" />
                        <div class="space-y-2 flex-1">
                            <div class="h-4 w-32 rounded bg-bg-sunken" />
                            <div class="h-3 w-20 rounded bg-bg-sunken" />
                        </div>
                    </div>
                    <div class="h-16 w-full rounded bg-bg-sunken" />
                </div>
            </div>

            <!-- Main Post & Comments Thread -->
            <template v-else-if="post">
                <!-- Main Post Card -->
                <PostDetailCard
                    :post="post"
                    :parent-post="parentPost"
                    @react="handleReact"
                    @focus-reply="handleFocusReply"
                />

                <!-- Inline Reply Box (Twitter Style) -->
                <section v-if="me.isAuthenticated" class="rounded-2xl border border-border bg-bg-elevated p-4 sm:p-5 shadow-xs">
                    <form @submit.prevent="handleReplyToPost" class="flex flex-col gap-3">
                        <div class="flex items-start gap-3">
                            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-lg">
                                {{ me.user?.display_name ? '👤' : '✨' }}
                            </div>
                            <div class="flex-1 min-w-0">
                                <label for="thread-reply-input" class="sr-only">Post your reply</label>
                                <textarea
                                    id="thread-reply-input"
                                    ref="replyInputRef"
                                    v-model="replyDraft"
                                    rows="3"
                                    maxlength="10000"
                                    :placeholder="`Reply to @${post.profile.username}...`"
                                    class="w-full resize-none bg-transparent text-sm text-text placeholder:text-text-muted outline-none"
                                    :disabled="isCommenting"
                                />
                            </div>
                        </div>

                        <div class="flex items-center justify-between border-t border-border/60 pt-2.5">
                            <span class="text-xs text-text-muted tabular-nums">
                                {{ replyDraft.length }} / 10,000
                            </span>
                            <UiButton
                                type="submit"
                                size="sm"
                                :loading="isCommenting"
                                :disabled="!replyDraft.trim()"
                                class="font-semibold"
                            >
                                Reply
                            </UiButton>
                        </div>
                    </form>
                </section>
                <section v-else class="rounded-xl border border-border bg-bg-elevated p-4 text-center">
                    <p class="text-sm font-semibold text-text-h">Want to reply?</p>
                    <p class="mt-1 text-xs text-text-muted">Sign in or create an account to join the thread.</p>
                    <UiButton size="sm" class="mt-3" @click="requestAuthPrompt">Reply to this post</UiButton>
                </section>

                <!-- Replies & Comments Tree -->
                <section class="flex flex-col gap-3" aria-label="Replies">
                    <div class="flex items-center justify-between px-1">
                        <h2 class="text-sm font-bold text-text-h uppercase tracking-wider">
                            Replies ({{ post.comments }})
                        </h2>
                    </div>

                    <div
                        v-if="!topLevelComments.length"
                        class="rounded-2xl border border-dashed border-border bg-bg-elevated p-8 text-center text-sm text-text-muted"
                    >
                        No replies yet. Be the first to share your thoughts.
                    </div>

                    <ul v-else class="flex flex-col gap-2">
                        <PostCommentItem
                            v-for="comment in topLevelComments"
                            :key="comment.id"
                            :comment="comment"
                            :all-comments="comments?.comments || []"
                            :can-interact="me.isAuthenticated"
                            @react="handleCommentReact"
                            @reply="handleReplyToComment"
                            @auth-required="requestAuthPrompt"
                        />
                    </ul>
                </section>
            </template>
        </main>

        <!-- ── Right Sidebar on Desktop ────────────────────────────── -->
        <aside class="sticky top-20 hidden w-80 shrink-0 xl:block">
            <FeedRightSidebar :posts="allFeedPosts" />
        </aside>
    </div>
</template>
