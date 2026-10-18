<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import UiMD from '@/Ui/UiMD.vue';
import UiOptions from '@/Ui/UiOptions.vue';
import type { Post } from '../../Types/feed.type';
import { sharePost } from '@/Core/postShare';

const props = defineProps<{
    post: Post;
    parentPost?: Post | null;
}>();

const emit = defineEmits<{
    (e: 'react', emoji: string): void;
    (e: 'focus-reply'): void;
}>();

const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];

const reactionItems = computed(() =>
    Object.entries(props.post.reactions || {})
        .filter(([, count]) => count > 0)
        .map(([emoji, count]) => ({ emoji, count }))
        .sort((a, b) => b.count - a.count)
);

const totalReactionsCount = computed(() =>
    reactionItems.value.reduce((sum, r) => sum + r.count, 0)
);

function formatFullDate(iso: string): string {
    try {
        const d = new Date(iso);
        return new Intl.DateTimeFormat(undefined, {
            dateStyle: 'medium',
            timeStyle: 'short',
        }).format(d);
    } catch {
        return iso;
    }
}

async function onShare() {
    try {
        await sharePost(props.post.id, props.post.content, props.post.profile.id);
    } catch {
        // Handled
    }
}
</script>

<template>
    <article class="flex flex-col rounded-2xl border border-border bg-bg-elevated p-5 sm:p-7 shadow-card">
        <!-- ── Parent Thread Item If This Post Is A Reply ─────────── -->
        <div v-if="parentPost" class="relative pb-6 mb-4 border-b border-border/80">
            <!-- Connecting Vertical Line -->
            <div class="absolute left-5 top-11 bottom-0 w-0.5 bg-accent/40" aria-hidden="true" />

            <div class="flex items-start gap-3">
                <RouterLink
                    :to="{ name: 'profile', params: { profile: parentPost.profile.username } }"
                    class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-lg"
                >
                    {{ parentPost.profile.emoji || '😊' }}
                </RouterLink>
                <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2">
                        <RouterLink
                            :to="{ name: 'profile', params: { profile: parentPost.profile.username } }"
                            class="text-xs font-bold text-text-h hover:text-accent no-underline truncate"
                        >
                            {{ parentPost.profile.display_name || parentPost.profile.username }}
                        </RouterLink>
                        <span class="text-xs text-text-muted">@{{ parentPost.profile.username }}</span>
                        <RouterLink
                            :to="{ name: 'post-detail', params: { id: parentPost.id } }"
                            class="ml-auto text-[11px] font-semibold text-accent no-underline hover:underline"
                        >
                            #{{ parentPost.id }}
                        </RouterLink>
                    </div>
                    <div class="mt-1 text-sm text-text-muted line-clamp-2">
                        <UiMD :source="parentPost.content" />
                    </div>
                </div>
            </div>
        </div>

        <!-- ── Single Reply-Of Indicator If Parent Post Not Loaded ─── -->
        <div
            v-else-if="post.replyTo"
            class="mb-4 flex items-center gap-2 rounded-xl border border-accent/20 bg-accent/5 px-3 py-2 text-xs text-text-muted"
        >
            <span class="text-accent" aria-hidden="true">↩️</span>
            <span>Replying to <strong class="text-accent">reply_of #{{ post.replyTo }}</strong></span>
            <RouterLink
                :to="{ name: 'post-detail', params: { id: post.replyTo } }"
                class="ml-auto text-xs font-semibold text-accent no-underline hover:underline"
            >
                View parent post →
            </RouterLink>
        </div>

        <!-- ── Main Post Author Header ────────────────────────────── -->
        <header class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3.5 min-w-0">
                <RouterLink
                    :to="{ name: 'profile', params: { profile: post.profile.username } }"
                    class="grid h-12 w-12 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-2xl shadow-xs transition-transform hover:scale-105"
                >
                    {{ post.profile.emoji || '😊' }}
                </RouterLink>
                <div class="min-w-0 flex flex-col">
                    <div class="flex items-center gap-2 flex-wrap">
                        <RouterLink
                            :to="{ name: 'profile', params: { profile: post.profile.username } }"
                            class="text-base font-bold text-text-h hover:text-accent no-underline truncate"
                        >
                            {{ post.profile.display_name || post.profile.username }}
                        </RouterLink>
                        <span v-if="post.profile.followedByMe" class="rounded bg-accent/15 px-2 py-0.5 text-[10px] font-bold text-accent">
                            Following
                        </span>
                        <span v-if="post.profile.starredByMe" class="rounded bg-warning/15 px-2 py-0.5 text-[10px] font-bold text-warning">
                            ⭐ Starred
                        </span>
                    </div>
                    <span class="text-xs text-text-muted">@{{ post.profile.username }}</span>
                </div>
            </div>

            <span class="rounded-lg bg-bg-sunken px-2.5 py-1 font-mono text-xs text-text-muted">
                #{{ post.id }}
            </span>
        </header>

        <!-- ── Large Post Body (Twitter Style) ────────────────────── -->
        <div class="my-5 text-lg leading-relaxed text-text">
            <UiMD :source="post.content" />
        </div>

        <!-- ── Full Timestamp ─────────────────────────────────────── -->
        <div class="border-t border-border/80 pt-3 text-xs text-text-muted tabular-nums">
            <time :datetime="post.createdAt">{{ formatFullDate(post.createdAt) }}</time>
        </div>

        <!-- ── Engagement Metrics Row ─────────────────────────────── -->
        <div class="my-3 flex flex-wrap items-center gap-5 border-y border-border/80 py-3 text-sm">
            <div>
                <strong class="font-bold text-text-h tabular-nums">{{ totalReactionsCount }}</strong>
                <span class="ml-1.5 text-text-muted">Reactions</span>
            </div>
            <div>
                <strong class="font-bold text-text-h tabular-nums">{{ post.comments }}</strong>
                <span class="ml-1.5 text-text-muted">Comments</span>
            </div>
        </div>

        <!-- ── Reaction Palette Badges ────────────────────────────── -->
        <div v-if="reactionItems.length" class="mb-3 flex flex-wrap gap-2">
            <button
                v-for="r in reactionItems"
                :key="r.emoji"
                type="button"
                class="flex items-center gap-1.5 rounded-full border border-border bg-bg-sunken px-3 py-1 text-sm transition-transform hover:scale-105 active:scale-95"
                @click="emit('react', r.emoji)"
            >
                <span>{{ r.emoji }}</span>
                <span class="font-bold tabular-nums text-text-h">{{ r.count }}</span>
            </button>
        </div>

        <!-- ── Action Bar ─────────────────────────────────────────── -->
        <footer class="flex items-center justify-around border-t border-border/80 pt-3 text-text-muted">
            <!-- React Picker -->
            <UiOptions
                :options="reactionPalette.map(e => ({ value: e, label: e, icon: e }))"
                size="md"
                align="start"
                label="React"
                trigger-class="flex items-center gap-2 rounded-full px-4 py-2 hover:bg-warning/10 hover:text-warning"
                @select="(e) => emit('react', String(e))"
            >
                <template #trigger>
                    <span class="flex items-center gap-2 font-medium cursor-pointer">
                        <span class="text-lg" aria-hidden="true">👍</span>
                        <span class="hidden sm:inline">React</span>
                    </span>
                </template>
            </UiOptions>

            <!-- Reply Button -->
            <button
                type="button"
                class="flex items-center gap-2 rounded-full px-4 py-2 font-medium transition-colors hover:bg-accent/10 hover:text-accent cursor-pointer"
                @click="emit('focus-reply')"
            >
                <span class="text-lg" aria-hidden="true">💬</span>
                <span class="hidden sm:inline">Reply</span>
            </button>

            <!-- Share Button -->
            <button
                type="button"
                class="flex items-center gap-2 rounded-full px-4 py-2 font-medium transition-colors hover:bg-info/10 hover:text-info cursor-pointer"
                @click="onShare"
            >
                <span class="text-lg" aria-hidden="true">📤</span>
                <span class="hidden sm:inline">Share</span>
            </button>
        </footer>
    </article>
</template>
