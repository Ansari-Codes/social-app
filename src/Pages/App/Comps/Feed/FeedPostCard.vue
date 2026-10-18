<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink } from 'vue-router';
import UiOptions from '@/Ui/UiOptions.vue';
import UiMD from '@/Ui/UiMD.vue';
import type { Post } from '../../Types/feed.type';
import { sharePost } from '@/Core/postShare';

const props = withDefaults(defineProps<{
    post: Post;
    expanded?: boolean;
    compact?: boolean;
}>(), {
    expanded: false,
    compact: false,
});

const emit = defineEmits<{
    (e: 'react', emoji: string): void;
    (e: 'reply', post: Post): void;
    (e: 'open-post', post: Post): void;
}>();

const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];

const reactionItems = computed(() =>
    Object.entries(props.post.reactions || {})
        .filter(([, count]) => count > 0)
        .map(([emoji, count]) => ({ emoji, count }))
        .sort((a, b) => b.count - a.count),
);

const isMyPost = computed(() => props.post.profile.isOwner);

const isExpanded = ref(props.expanded);
const isTruncatable = computed(
    () => !props.expanded && (props.post.content.length > 220 || props.post.content.split('\n').length > 4),
);

function onCardClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    // Don't navigate if clicking buttons, links, or form elements
    if (target.closest('button, a, input, textarea, [role="button"]')) return;
    emit('open-post', props.post);
}

async function onShareClick() {
    try {
        await sharePost(props.post.id, props.post.content, props.post.profile.id);
    } catch {
        // Abort handled
    }
}

function formatDate(iso: string): string {
    try {
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now.getTime() - d.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 7) return `${diffDays}d`;
        return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(d);
    } catch {
        return iso;
    }
}
</script>

<template>
    <article
        class="group relative flex flex-col rounded-2xl border border-border bg-bg-elevated p-4 sm:p-5 shadow-xs transition-all duration-150 hover:border-border-strong hover:shadow-card cursor-pointer"
        tabindex="0"
        role="article"
        :aria-label="`Post by ${post.profile.display_name || post.profile.username}`"
        @click="onCardClick"
        @keydown.enter.prevent="emit('open-post', post)"
        @keydown.space.prevent="emit('open-post', post)"
    >
        <!-- ── Reply-of Indicator Banner ─────────────────────────────── -->
        <div
            v-if="post.replyTo"
            class="mb-2.5 flex items-center gap-2 rounded-xl border border-accent/20 bg-accent/5 px-2.5 py-1 text-xs text-text-muted"
        >
            <span class="text-accent" aria-hidden="true">↩️</span>
            <span class="font-medium">
                <span class="font-bold text-accent">reply_of #{{ post.replyTo }}</span>
                <span v-if="post.replyToAuthor" class="ml-1 text-text">
                    to <span class="font-semibold text-text-h">@{{ post.replyToAuthor }}</span>
                </span>
            </span>
            <RouterLink
                :to="{ name: 'post-detail', params: { id: post.replyTo } }"
                class="ml-auto text-[11px] font-semibold text-accent no-underline hover:underline"
                @click.stop
            >
                View original →
            </RouterLink>
        </div>

        <!-- ── Quoted Snippet If Available ──────────────────────────── -->
        <blockquote
            v-if="post.replyTo && post.replyToSnippet"
            class="mb-3 border-l-2 border-accent/40 bg-bg-sunken/50 px-3 py-1.5 rounded-r-lg text-xs italic text-text-muted"
        >
            "{{ post.replyToSnippet }}"
        </blockquote>

        <!-- ── Author & Meta Header ─────────────────────────────────── -->
        <header class="flex items-start justify-between gap-3">
            <div class="flex min-w-0 items-center gap-3">
                <RouterLink
                    :to="{ name: 'profile', params: { profile: post.profile.username } }"
                    class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-xl transition-transform hover:scale-105"
                    aria-hidden="true"
                    @click.stop
                >
                    {{ post.profile.emoji || '😊' }}
                </RouterLink>

                <div class="flex min-w-0 flex-col">
                    <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                        <RouterLink
                            :to="{ name: 'profile', params: { profile: post.profile.username } }"
                            class="truncate text-sm font-bold text-text-h no-underline hover:text-accent hover:underline"
                            @click.stop
                        >
                            {{ post.profile.display_name || post.profile.username }}
                        </RouterLink>
                        <span class="text-xs text-text-muted truncate">@{{ post.profile.username }}</span>
                        <span class="text-xs text-text-faint">·</span>
                        <time class="text-xs text-text-muted tabular-nums" :datetime="post.createdAt">
                            {{ formatDate(post.createdAt) }}
                        </time>
                    </div>

                    <div class="flex items-center gap-1.5 mt-0.5">
                        <span v-if="post.profile.followedByMe" class="rounded bg-accent/15 px-1.5 py-0.2 text-[10px] font-medium text-accent">
                            Following
                        </span>
                        <span v-if="post.profile.starredByMe" class="rounded bg-warning/15 px-1.5 py-0.2 text-[10px] font-medium text-warning">
                            ⭐ Starred
                        </span>
                        <span v-if="isMyPost" class="rounded bg-info/15 px-1.5 py-0.2 text-[10px] font-medium text-info">
                            You
                        </span>
                    </div>
                </div>
            </div>

            <!-- Post Detail Link Action -->
            <RouterLink
                :to="{ name: 'post-detail', params: { id: post.id } }"
                class="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-bg-hover hover:text-text-h"
                title="Open full page post"
                @click.stop
            >
                <span class="text-xs" aria-hidden="true">↗</span>
            </RouterLink>
        </header>

        <!-- ── Post Body ────────────────────────────────────────────── -->
        <div class="mt-3 min-w-0 text-[15px] leading-relaxed text-text">
            <div
                class="overflow-hidden wrap-break-word transition-all"
                :class="(!isExpanded && isTruncatable) ? 'line-clamp-4' : ''"
            >
                <UiMD :source="post.content" />
            </div>

            <!-- Expand / Collapse / Open Post Hint -->
            <div v-if="isTruncatable" class="mt-2 flex items-center justify-between text-xs">
                <button
                    type="button"
                    class="font-semibold text-accent hover:underline cursor-pointer"
                    @click.stop="isExpanded = !isExpanded"
                >
                    {{ isExpanded ? 'Show less ▲' : 'Show more ▼' }}
                </button>

                <button
                    type="button"
                    class="text-[11px] text-text-muted hover:text-text-h cursor-pointer"
                    @click.stop="emit('open-post', post)"
                >
                    Expand in full page ↗
                </button>
            </div>
        </div>

        <!-- ── Reaction Badges Summary ──────────────────────────────── -->
        <div v-if="reactionItems.length" class="mt-3.5 flex flex-wrap items-center gap-1.5 pt-1">
            <span
                v-for="r in reactionItems"
                :key="r.emoji"
                class="inline-flex items-center gap-1 rounded-full border border-border bg-bg-sunken px-2 py-0.5 text-xs text-text-muted"
            >
                <span aria-hidden="true">{{ r.emoji }}</span>
                <span class="tabular-nums font-semibold">{{ r.count }}</span>
            </span>
        </div>

        <!-- ── Social Action Bar ────────────────────────────────────── -->
        <footer class="mt-3.5 flex items-center justify-between border-t border-border/80 pt-2.5 text-xs text-text-muted">
            <!-- Reply Button (triggers post over post reply modal) -->
            <button
                type="button"
                class="group/btn flex items-center gap-1.5 rounded-full px-2.5 py-1.5 transition-colors hover:bg-accent/10 hover:text-accent"
                title="Reply to this post"
                @click.stop="emit('reply', post)"
            >
                <span class="text-sm transition-transform group-hover/btn:scale-110" aria-hidden="true">💬</span>
                <span class="font-medium tabular-nums">{{ post.comments }}</span>
                <span class="hidden sm:inline">Reply</span>
            </button>

            <!-- React Options Popover -->
            <UiOptions
                :options="reactionPalette.map(e => ({ value: e, label: e, icon: e }))"
                size="sm"
                align="start"
                label="React"
                trigger-class="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 hover:bg-warning/10 hover:text-warning"
                @select="(e) => emit('react', String(e))"
            >
                <template #trigger>
                    <span class="flex items-center gap-1.5 text-xs text-text-muted group-hover:text-text-h">
                        <span class="text-sm" aria-hidden="true">👍</span>
                        <span class="hidden sm:inline">React</span>
                    </span>
                </template>
            </UiOptions>

            <!-- Share Button -->
            <button
                type="button"
                class="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 transition-colors hover:bg-info/10 hover:text-info"
                title="Share or copy post link"
                @click.stop="onShareClick"
            >
                <span class="text-sm" aria-hidden="true">📤</span>
                <span class="hidden sm:inline">Share</span>
            </button>

            <!-- View Thread Button -->
            <RouterLink
                :to="{ name: 'post-detail', params: { id: post.id } }"
                class="flex items-center gap-1 rounded-full px-2.5 py-1.5 text-text-muted no-underline transition-colors hover:bg-bg-hover hover:text-text-h"
                @click.stop
            >
                <span class="text-xs font-semibold">Thread →</span>
            </RouterLink>
        </footer>
    </article>
</template>
