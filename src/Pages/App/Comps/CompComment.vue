<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// COMP COMMENT — compact, Facebook-style comment row.
//
// Visual contract:
//   - Small avatar/emoji + name + inline body + tiny actions row.
//   - No "#id" noise, no "reply to #N" — the tree indent tells you.
//   - Reply/react/share are inline text buttons, not chips.
//   - Deep threads stop indenting past `maxDepth` so mobile stays usable.
//   - Clicking the row (or Reply) sets `replyToId` on the parent.
// ═══════════════════════════════════════════════════════════════════════════

import { computed } from 'vue';
import UiOptions from '@/Ui/UiOptions.vue';
import UiMD from '@/Ui/UiMD.vue';
import { RouterLink } from 'vue-router';
import type { Comment } from '../Types/feed.type';

const props = defineProps<{
    comment: Comment;
    /** All comments for this post — used to find this comment's children. */
    all: Comment[];
    /** Nesting depth, 0 = top-level. */
    depth?: number;
    replyToId?: number | null;
}>();

const emit = defineEmits<{
    (e: 'react', commentId: number, reaction: string): void;
    (e: 'reply', commentId: number): void;
}>();

const depth = computed(() => props.depth ?? 0);

/** Direct children of this comment. */
const children = computed(() =>
    props.all.filter((c) => c.replyTo === props.comment.id),
);

/** Cap visual indent so deep threads don't run off screen. */
const maxDepth = 4;
const indent = computed(() => Math.min(depth.value, maxDepth));

/** Only show reactions that have a non-zero count. */
const reactionItems = computed(() =>
    Object.entries(props.comment.reactions).filter(([, count]) => count > 0),
);

const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];
const isSelected = computed(() => props.comment.id === props.replyToId);
</script>

<template>
    <li class="flex min-w-0 flex-col gap-1.5"> <!-- ── Comment row ────────────────────────────────────────── -->
        <div class="flex flex-row gap-2 cursor-pointer rounded-lg px-2 py-1.5 transition-colors"
            :class="isSelected ? 'bg-accent-soft' : 'hover:bg-bg-hover'" role="button" tabindex="0"
            :aria-pressed="isSelected" @click="emit('reply', comment.id)"
            @keydown.enter.prevent="emit('reply', comment.id)" @keydown.space.prevent="emit('reply', comment.id)">
            <!-- Avatar bubble -->
            <span
                class="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-sm leading-none"
                aria-hidden="true">
                {{ comment.profile?.emoji ?? '😊' }}
            </span>

            <div class="flex min-w-0 flex-1 flex-col">
                <!-- Bubble: name + body, Facebook style -->
                <div class="rounded-2xl bg-bg-sunken px-3 py-1.5">
                    <RouterLink v-if="comment.profile"
                        :to="{ name: 'profile', params: { profile: comment.profile.username } }"
                        class="text-xs font-semibold text-text-h capitalize hover:text-accent" @click.stop>
                        {{ comment.profile.display_name || comment.profile.username }}
                    </RouterLink>
                    <span v-else class="text-xs font-semibold text-text-muted">Anonymous</span>

                    <div class="text-sm text-text">
                        <UiMD :source="comment.content" />
                    </div>
                </div>

                <!-- Inline meta + actions row -->
                <div class="mt-0.5 flex flex-row items-center gap-3 px-3 text-xs text-text-faint">
                    <time class="tabular-nums">{{ comment.createdAt }}</time>

                    <button type="button" class="font-medium hover:text-accent transition-colors"
                        @click.stop="emit('reply', comment.id)">
                        Reply
                    </button>

                    <!-- Reactions: existing chips (compact) + add-reaction menu -->
                    <span v-for="[reaction, count] in reactionItems" :key="reaction"
                        class="cursor-pointer rounded-full bg-bg-sunken px-1.5 py-0.5 tabular-nums transition-colors hover:bg-bg-hover"
                        @click.stop="emit('react', comment.id, reaction)">
                        {{ reaction }} {{ count }}
                    </span>

                    <UiOptions :options="reactionPalette.map((r) => ({ value: r, label: r, icon: r }))" size="sm"
                        label="React to comment" align="start" @select="(r) => emit('react', comment.id, String(r))">
                        <template #trigger>
                            <button type="button" class="font-medium hover:text-accent transition-colors"
                                aria-label="Add reaction" @click.stop>
                                React
                            </button>
                        </template>
                    </UiOptions>
                </div>
            </div>
        </div>

        <!-- ── Recursive children ─────────────────────────────────── -->
        <ul v-if="children.length" class="flex flex-col gap-1.5 border-l border-border pl-2"
            :class="indent > 0 ? 'ml-3' : ''">
            <CompComment v-for="child in children" :key="child.id" :comment="child" :all="all" :depth="depth + 1"
                :reply-to-id="replyToId" @react="(commentId, reaction) => emit('react', commentId, reaction)"
                @reply="emit('reply', $event)" />
        </ul>
    </li>
</template>