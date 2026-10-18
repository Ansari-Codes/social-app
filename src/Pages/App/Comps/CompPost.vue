<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// COMP POST — post card.
//
// Two shapes controlled by `expanded`:
//   FEED CARD (expanded=false):
//     header + clamped body + reaction summary + action bar (React/Comment/Share)
//   VIEWER BODY (expanded=true):
//     header + full body ONLY. No summary, no action bar.
//     The viewer owns all interactivity so we don't double-render bars.
// ═══════════════════════════════════════════════════════════════════════════

import { computed, ref } from 'vue';
import UiChip from '@/Ui/UiChip.vue';
import UiOptions from '@/Ui/UiOptions.vue';
import UiMD from '@/Ui/UiMD.vue';
import { RouterLink } from 'vue-router';
import { type Post } from '../Types/feed.type';

const props = withDefaults(defineProps<{
    post: Post,
    maxLines?: number,
    /** Feed mode shows the action bar. Viewer mode does not. */
    showActions?: boolean,
    /** Skip clamping + skip chrome. Set by CompPostViewer. */
    expanded?: boolean,
    /** The post viewer renders author details in its pinned header. */
    hideHeader?: boolean,
}>(), {
    showActions: true,
    expanded: false,
    hideHeader: false,
    maxLines: 4,
});

const emit = defineEmits<{
    (e: 'react', emoji: string): void;
    (e: 'comment'): void;
    (e: 'share'): void;
}>();

/* ── Clamping ─────────────────────────────────────────────────────── */

const showMore = ref(false);

// In expanded (viewer) mode, never clamp and never show the toggle.
const canClamp = computed(() => !props.expanded);
const collapsed = computed(() => canClamp.value && !showMore.value);

const maybeTruncatable = computed(
    () => canClamp.value && (props.post.content.length > 200 || props.post.content.split('\n').length > 3),
);

const clampClass = computed(() => (collapsed.value ? 'line-clamp-4' : ''));

/* ── Reactions ────────────────────────────────────────────────────── */

const reactionItems = computed(() =>
    Object.entries(props.post.reactions)
        .filter(([, count]) => count > 0)
        .map(([emoji, count]) => ({ emoji, count }))
        .sort((a, b) => b.count - a.count),
);

const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];

function onAddReaction(value: string | number) {
    emit('react', String(value));
}

const postMenu = [
    { value: 'copy',   label: 'Copy post',      icon: '📋' },
    { value: 'share',  label: 'Copy link',      icon: '🔗' },
    { value: 'follow', label: 'Follow profile', icon: '➕' },
    { value: 'star',   label: 'Give star',      icon: '⭐' },
];
</script>

<template>
    <article
        class="w-full flex flex-col"
        :class="expanded
            ? 'bg-transparent'
            : 'overflow-hidden rounded-xl border border-border bg-bg-elevated shadow-xs'"
    >
        <!-- ── REPLY-OF BANNER ─────────────────────────────────────── -->
        <div
            v-if="post.replyTo && !expanded"
            class="mx-3 mt-3 flex items-center gap-1.5 rounded-lg border border-accent/20 bg-accent/5 px-2.5 py-1 text-xs text-text-muted"
        >
            <span class="text-accent" aria-hidden="true">↩️</span>
            <span class="font-bold text-accent">reply_of #{{ post.replyTo }}</span>
            <span v-if="post.replyToAuthor" class="ml-1 text-text">
                to <strong>@{{ post.replyToAuthor }}</strong>
            </span>
            <RouterLink
                :to="{ name: 'post-detail', params: { id: post.replyTo } }"
                class="ml-auto text-[11px] font-semibold text-accent no-underline hover:underline"
                @click.stop
            >
                View →
            </RouterLink>
        </div>

        <!-- ── HEADER ─────────────────────────────────────────────── -->
        <header
            v-if="!hideHeader"
            class="flex flex-row items-start gap-3"
            :class="expanded ? 'pb-2' : 'p-3 sm:p-4'"
        >
            <span
                class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-xl leading-none"
                aria-hidden="true"
            >
                {{ post.profile.emoji ?? '😊' }}
            </span>

            <div class="flex min-w-0 flex-1 flex-col gap-0.5">
                <div class="flex flex-wrap items-center gap-2 min-w-0">
                    <RouterLink
                        :to="{ name: 'profile', params: { profile: post.profile.username } }"
                        class="text-sm font-semibold text-text-h truncate capitalize hover:text-accent"
                        @click.stop
                    >
                        {{ post.profile.display_name || post.profile.username }}
                    </RouterLink>
                    <UiChip v-if="post.profile.followedByMe" size="sm" variant="accent">Following</UiChip>
                    <UiChip v-if="post.profile.starredByMe" size="sm" variant="soft">Starred</UiChip>
                </div>
                <time class="text-xs text-text-faint tabular-nums">
                    {{ post.createdAt }}
                </time>
            </div>

            <!-- Actions menu only in feed mode. -->
            <UiOptions
                v-if="!expanded && showActions !== false"
                :options="postMenu"
                size="sm"
                align="end"
                label="Post actions"
            />
        </header>

        <!-- ── BODY ───────────────────────────────────────────────── -->
        <div class="min-w-0" :class="expanded ? 'px-4 py-4 sm:px-5' : 'px-3 pb-2 sm:px-4'">
            <div class="overflow-hidden wrap-break-word" :class="clampClass">
                <UiMD :source="post.content" />
            </div>

            <div v-if="maybeTruncatable" class="mt-1 text-sm">
                <button
                    v-if="collapsed"
                    type="button"
                    class="font-medium text-accent underline-offset-2 hover:underline"
                    @click.stop="showMore = true"
                >
                    See more
                </button>
                <button
                    v-else
                    type="button"
                    class="font-medium text-text-faint underline-offset-2 hover:text-text-h hover:underline"
                    @click.stop="showMore = false"
                >
                    See less
                </button>
            </div>
        </div>

        <!-- ── SUMMARY + ACTION BAR: feed mode only ───────────────── -->
        <template v-if="!expanded && showActions !== false">
            <!-- Reaction summary -->
            <div
                v-if="reactionItems.length || post.comments"
                class="flex flex-row items-center justify-between gap-3 px-3 py-3 text-xs text-text-faint sm:px-4"
            >
                <div v-if="reactionItems.length" class="flex min-w-0 flex-row flex-wrap items-center gap-1.5">
                    <UiChip
                        v-for="r in reactionItems"
                        :key="r.emoji"
                        size="lg"
                        variant="soft"
                        :clickable="false"
                        :title="`${r.emoji} ${r.count}`"
                    >
                        <span aria-hidden="true">{{ r.emoji }}</span>
                        <span class="tabular-nums">{{ r.count }}</span>
                    </UiChip>
                </div>
                <span v-else />

                <span v-if="post.comments" class="tabular-nums">
                    {{ post.comments }} {{ post.comments === 1 ? 'comment' : 'comments' }}
                </span>
            </div>

            <!-- Action bar -->
            <footer class="flex flex-row items-center justify-center gap-2 border-t border-border px-3 py-2">
                <UiOptions
                    :options="reactionPalette.map((e) => ({ value: e, label: e, icon: e }))"
                    size="sm"
                    align="start"
                    label="React"
                    trigger-class="h-auto w-auto rounded-full bg-transparent p-0 hover:bg-transparent"
                    @select="onAddReaction"
                >
                    <template #trigger>
                        <UiChip size="lg" variant="soft" :clickable="false" aria-label="React">
                            <template #leading><span aria-hidden="true">👍</span></template>
                            <span class="hidden sm:inline">React</span>
                        </UiChip>
                    </template>
                </UiOptions>

                <UiChip size="lg" variant="soft" aria-label="Comment" @click.stop="emit('comment')">
                    <template #leading><span aria-hidden="true">💬</span></template>
                    <span class="hidden sm:inline">Comment</span>
                </UiChip>

                <UiChip size="lg" variant="soft" aria-label="Share" @click.stop="emit('share')">
                    <template #leading><span aria-hidden="true">📤</span></template>
                    <span class="hidden sm:inline">Share</span>
                </UiChip>
            </footer>
        </template>
    </article>
</template>