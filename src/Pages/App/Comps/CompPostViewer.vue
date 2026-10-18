<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// COMP POST VIEWER — pinned header, scrollable body, pinned action bar.
//
// Layout:
//   ┌────────────────────────────────────────────────┐
//   │ HEADER (pinned)      avatar · name · close     │
//   ├────────────────────────────────────────────────┤
//   │ SCROLL   post body → reactions → comments      │
//   ├────────────────────────────────────────────────┤
//   │ ACTION BAR (pinned)  React · Comment · Share   │
//   ├────────────────────────────────────────────────┤
//   │ COMPOSER (only when Comment is active)         │
//   └────────────────────────────────────────────────┘
//
// `CompPost` is rendered in `expanded` mode → header + body only.
// The viewer owns the reaction picker, the comment composer, and share.
// ═══════════════════════════════════════════════════════════════════════════

import { computed, nextTick, ref, watch } from 'vue';
import UiChip from '@/Ui/UiChip.vue';
import UiOptions from '@/Ui/UiOptions.vue';
import UiDialog from '@/Ui/UiDialog.vue';
import UiButton from '@/Ui/UiButton.vue';
import { sharePost } from '@/Core/postShare';
import { RouterLink } from 'vue-router';
import CompComment from './CompComment.vue';
import CompPost from './CompPost.vue';
import type { Post, Comment, Comments } from '../Types/feed.type';

const props = defineProps<{
    post: Post;
    comments?: Comments | null;
    replyToId?: number | null;
    commenting?: boolean;
    commentError?: string;
    commentsLoading?: boolean;
}>();

const emit = defineEmits<{
    (e: 'react', emoji: string): void;
    (e: 'react-comment', commentId: number, emoji: string): void;
    (e: 'reply', commentId: number | null): void;
    (e: 'comment', content: string, replyToId: number | null): void;
    (e: 'close'): void;
    (e: 'share'): void;
}>();

/* ── Reactions (own the picker here, not in CompPost) ─────────────── */
const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];

const reactionItems = computed(() =>
    Object.entries(props.post.reactions)
        .filter(([, count]) => count > 0)
        .map(([emoji, count]) => ({ emoji, count }))
        .sort((a, b) => b.count - a.count),
);

const totalReactions = computed(() =>
    reactionItems.value.reduce((n, r) => n + r.count, 0),
);

/* ── Comments tree ────────────────────────────────────────────────── */
const allComments = computed<Comment[]>(() => props.comments?.comments ?? []);

const topLevelComments = computed(() =>
    allComments.value.filter((c) => c.replyTo == null || c.replyTo === props.post.id),
);

/* ── Composer ─────────────────────────────────────────────────────── */
const composerOpen = ref(false);
const commentDraft = ref('');
const commentInput = ref<HTMLTextAreaElement | null>(null);
const shareStatus = ref('');

// If the parent sets replyToId, open the composer automatically.
watch(
    () => props.replyToId,
    (id) => {
        if (id != null) composerOpen.value = true;
    },
    { immediate: true },
);

function openComposer() {
    composerOpen.value = true;
    nextTick(() => commentInput.value?.focus());
}

function closeComposer() {
    composerOpen.value = false;
    commentDraft.value = '';
    emit('reply', null);
}

function submitComment() {
    const content = commentDraft.value.trim();
    if (!content || props.commenting) return;
    emit('comment', content, props.replyToId ?? null);
}

async function onShare() {
    shareStatus.value = '';
    try {
        const result = await sharePost(props.post.id, props.post.content, props.post.profile.id);
        shareStatus.value = result === 'copied' ? 'Post link copied.' : 'Post shared.';
    } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return;
        shareStatus.value = error instanceof Error ? error.message : 'Unable to share this post.';
    }
}

function onReplyFromComment(commentId: number) {
    emit('reply', commentId);
    openComposer();
}

watch(() => props.post.id, () => {
    composerOpen.value = false;
    commentDraft.value = '';
});

watch(() => props.post.comments, (count, previousCount) => {
    if (count > previousCount && composerOpen.value) closeComposer();
});

const replyingTo = computed(() => {
    if (props.replyToId == null) return null;
    return allComments.value.find((c) => c.id === props.replyToId) ?? null;
});
</script>

<template>
    <article class="flex h-full min-h-0 w-full flex-col overflow-hidden rounded-lg border border-border bg-bg-elevated shadow-card">

        <!-- ── PINNED HEADER ──────────────────────────────────────── -->
        <header class="flex shrink-0 items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-5">
            <div class="flex min-w-0 items-center gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-xl leading-none" aria-hidden="true">
                    {{ post.profile.emoji ?? '😊' }}
                </span>
                <div class="flex min-w-0 flex-col gap-0.5">
                    <div class="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                        <RouterLink
                            :to="{ name: 'profile', params: { profile: post.profile.username } }"
                            class="truncate text-sm font-semibold text-text-h hover:text-accent"
                            @click.stop
                        >
                            {{ post.profile.display_name || post.profile.username }}
                        </RouterLink>
                        <UiChip v-if="post.profile.followedByMe" size="sm" variant="accent" :clickable="false">Following</UiChip>
                        <UiChip v-if="post.profile.starredByMe" size="sm" variant="soft" :clickable="false">Starred</UiChip>
                    </div>
                    <div class="flex min-w-0 items-center gap-2 text-xs text-text-faint">
                        <span v-if="post.profile.display_name" class="truncate">@{{ post.profile.username }}</span>
                        <time class="shrink-0 tabular-nums">{{ post.createdAt }}</time>
                    </div>
                </div>
            </div>
            <button
                type="button"
                class="grid h-8 w-8 place-items-center rounded-md text-text-faint transition-colors hover:bg-bg-hover hover:text-text-h"
                aria-label="Close"
                @click="emit('close')"
            >
                ✕
            </button>
        </header>

        <!-- ── SCROLL REGION ──────────────────────────────────────── -->
        <div class="min-h-0 flex-1 overflow-y-auto">
            <!-- Post header + body only (expanded mode). -->
            <div class="pt-2">
                <CompPost :post="post" expanded hide-header :show-actions="false" />
            </div>

            <!-- Reactions row (owned by viewer, sits in the scroll region
                 so long reaction lists stay scrollable with the post). -->
            <section
                v-if="reactionItems.length"
                class="mt-2 flex flex-col gap-3 border-t border-border px-4 py-4 sm:px-5"
            >
                <h4 class="text-xs font-semibold uppercase tracking-wider text-text-faint">
                    Reactions
                    <span class="ml-1 font-normal normal-case tabular-nums text-text-muted">
                        ({{ totalReactions }})
                    </span>
                </h4>
                <div class="flex flex-row flex-wrap gap-2">
                    <UiChip
                        v-for="r in reactionItems"
                        :key="r.emoji"
                        size="lg"
                        variant="soft"
                        :clickable="false"
                    >
                        <span aria-hidden="true">{{ r.emoji }}</span>
                        <span class="tabular-nums">{{ r.count }}</span>
                    </UiChip>
                </div>
            </section>

            <!-- Comments -->
            <section class="mt-2 flex flex-col gap-3 border-t border-border px-4 py-4 sm:px-5">
                <h4 class="text-xs font-semibold uppercase tracking-wider text-text-faint">
                    {{ post.isComment ? 'Replies' : 'Comments' }}
                    <span class="ml-1 font-normal normal-case tabular-nums text-text-muted">
                        ({{ post.comments }})
                    </span>
                </h4>

                <p v-if="commentError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
                    {{ commentError }}
                </p>
                <p v-if="commentsLoading" class="text-sm text-text-muted" role="status">
                    Loading comments...
                </p>
                <p v-else-if="!topLevelComments.length" class="text-sm text-text-muted">
                    {{ post.isComment ? 'No replies yet.' : 'No comments yet. Be the first to reply.' }}
                </p>
                <ul v-else class="flex flex-col gap-1.5">
                    <CompComment
                        v-for="c in topLevelComments"
                        :key="c.id"
                        :comment="c"
                        :all="allComments"
                        :depth="0"
                        :reply-to-id="props.replyToId"
                        @react="(id, emoji) => emit('react-comment', id, emoji)"
                        @reply="onReplyFromComment"
                    />
                </ul>
            </section>
        </div>

        <!-- ── PINNED ACTION BAR ──────────────────────────────────── -->
        <footer class="flex shrink-0 flex-row items-center justify-center gap-2 border-t border-border bg-bg-elevated px-3 py-2">
            <UiOptions
                :options="reactionPalette.map((e) => ({ value: e, label: e, icon: e }))"
                size="sm"
                align="start"
                label="React"
                trigger-class="h-auto w-auto rounded-full bg-transparent p-0 hover:bg-transparent"
                @select="(e) => emit('react', String(e))"
            >
                <template #trigger>
                    <UiChip size="lg" variant="soft" :clickable="false" aria-label="React">
                        <template #leading><span aria-hidden="true">👍</span></template>
                        <span class="hidden sm:inline">React</span>
                    </UiChip>
                </template>
            </UiOptions>

            <UiChip
                size="lg"
                variant="soft"
                :selected="composerOpen"
                aria-label="Comment"
                @click="composerOpen ? closeComposer() : openComposer()"
            >
                <template #leading><span aria-hidden="true">💬</span></template>
                <span class="hidden sm:inline">Comment</span>
            </UiChip>

            <UiChip size="lg" variant="soft" aria-label="Share" @click="onShare">
                <template #leading><span aria-hidden="true">📤</span></template>
                <span class="hidden sm:inline">Share</span>
            </UiChip>
        </footer>

        <span class="sr-only" role="status" aria-live="polite">{{ shareStatus }}</span>

        <!-- ── COMPOSER (only when active) ─────────────────────────── -->
        <UiDialog
            v-model="composerOpen"
            :title="replyingTo ? 'Write a reply' : 'Write a comment'"
            :description="replyingTo ? `Replying to ${replyingTo.profile.display_name || replyingTo.profile.username}` : 'Join the conversation.'"
            size="sm"
            :closable="!commenting"
            :close-on-backdrop="!commenting"
            :close-on-escape="!commenting"
            @close="closeComposer"
        >
            <form :id="`post-comment-form-${post.id}`" class="flex flex-col gap-4" @submit.prevent="submitComment">
                <p v-if="commentError" class="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
                    {{ commentError }}
                </p>
                <label :for="`post-comment-input-${post.id}`" class="text-sm font-medium text-text-h">
                    {{ replyingTo ? 'Your reply' : 'Your comment' }}
                </label>
                <textarea
                    :id="`post-comment-input-${post.id}`"
                    ref="commentInput"
                    v-model="commentDraft"
                    rows="4"
                    maxlength="10000"
                    class="min-h-32 w-full resize-y rounded-lg border border-border bg-bg px-3.5 py-3 text-sm text-text outline-none focus:border-accent"
                    :placeholder="replyingTo ? 'Write a reply...' : 'Write a comment...'"
                    :disabled="commenting"
                />
            </form>
            <template #footer>
                <div class="flex justify-end gap-2 px-4 pb-4 pt-3 sm:px-5 sm:pb-5">
                    <UiButton variant="ghost" :disabled="commenting" @click="closeComposer">Cancel</UiButton>
                    <UiButton
                        type="submit"
                        :form="`post-comment-form-${post.id}`"
                        :loading="commenting"
                        :disabled="!commentDraft.trim()"
                    >
                        {{ replyingTo ? 'Reply' : 'Comment' }}
                    </UiButton>
                </div>
            </template>
        </UiDialog>
    </article>
</template>