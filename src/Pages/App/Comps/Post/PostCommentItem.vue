<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink } from 'vue-router';
import UiMD from '@/Ui/UiMD.vue';
import UiButton from '@/Ui/UiButton.vue';
import UiOptions from '@/Ui/UiOptions.vue';
import type { Comment } from '../../Types/feed.type';

const props = withDefaults(defineProps<{
    comment: Comment;
    allComments: Comment[];
    depth?: number;
    canInteract?: boolean;
}>(), {
    canInteract: true,
});

const emit = defineEmits<{
    (e: 'react', commentId: number, emoji: string): void;
    (e: 'reply', commentId: number, content: string): void;
    (e: 'auth-required'): void;
}>();

const replyOpen = ref(false);
const replyDraft = ref('');
const isSubmitting = ref(false);
const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];

const currentDepth = computed(() => props.depth || 0);

// Find replies to this comment
const childReplies = computed(() =>
    props.allComments.filter(c => c.replyTo === props.comment.id && c.id !== props.comment.id)
);

const reactionItems = computed(() =>
    Object.entries(props.comment.reactions || {})
        .filter(([, count]) => count > 0)
        .map(([emoji, count]) => ({ emoji, count }))
        .sort((a, b) => b.count - a.count)
);

function submitReply() {
    if (!props.canInteract) {
        emit('auth-required');
        return;
    }
    if (!replyDraft.value.trim() || isSubmitting.value) return;
    emit('reply', props.comment.id, replyDraft.value.trim());
    replyDraft.value = '';
    replyOpen.value = false;
}

function react(emoji: string) {
    if (!props.canInteract) {
        emit('auth-required');
        return;
    }
    emit('react', props.comment.id, emoji);
}

function toggleReply() {
    if (!props.canInteract) {
        emit('auth-required');
        return;
    }
    replyOpen.value = !replyOpen.value;
}

function formatDate(iso: string): string {
    try {
        const d = new Date(iso);
        return new Intl.DateTimeFormat(undefined, {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
        }).format(d);
    } catch {
        return iso;
    }
}
</script>

<template>
    <li class="relative flex flex-col pt-3">
        <!-- Thread Line Connector for nested replies -->
        <div
            v-if="childReplies.length"
            class="absolute left-4.5 top-12 bottom-0 w-0.5 bg-border z-0"
            aria-hidden="true"
        />

        <div class="relative z-10 flex items-start gap-3">
            <!-- Author Avatar -->
            <RouterLink
                :to="{ name: 'profile', params: { profile: comment.profile.username } }"
                class="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-lg shadow-xs hover:opacity-90"
            >
                {{ comment.profile.emoji || '💬' }}
            </RouterLink>

            <div class="min-w-0 flex-1 rounded-2xl border border-border/80 bg-bg-elevated p-3.5 shadow-xs">
                <!-- Header -->
                <div class="flex items-center justify-between gap-2">
                    <div class="flex flex-wrap items-center gap-1.5 min-w-0">
                        <RouterLink
                            :to="{ name: 'profile', params: { profile: comment.profile.username } }"
                            class="truncate text-xs font-bold text-text-h no-underline hover:text-accent hover:underline"
                        >
                            {{ comment.profile.display_name || comment.profile.username }}
                        </RouterLink>
                        <span class="text-xs text-text-muted">@{{ comment.profile.username }}</span>
                        <span class="text-xs text-text-faint">·</span>
                        <time class="text-[11px] text-text-muted tabular-nums">
                            {{ formatDate(comment.createdAt) }}
                        </time>
                    </div>

                    <span class="text-[10px] text-text-faint font-mono">#{{ comment.id }}</span>
                </div>

                <!-- Body -->
                <div class="mt-1.5 text-sm text-text leading-relaxed">
                    <UiMD :source="comment.content" />
                </div>

                <!-- Reaction Badges Summary -->
                <div v-if="reactionItems.length" class="mt-2 flex flex-wrap gap-1">
                    <span
                        v-for="r in reactionItems"
                        :key="r.emoji"
                        class="inline-flex items-center gap-1 rounded-full border border-border bg-bg-sunken px-2 py-0.5 text-[10px] text-text-muted"
                    >
                        <span>{{ r.emoji }}</span>
                        <span class="font-semibold tabular-nums">{{ r.count }}</span>
                    </span>
                </div>

                <!-- Action Bar -->
                <div class="mt-2.5 flex items-center gap-3 border-t border-border/50 pt-2 text-xs text-text-muted">
                    <!-- React Picker -->
                    <UiOptions
                        :options="reactionPalette.map(e => ({ value: e, label: e, icon: e }))"
                        size="sm"
                        align="start"
                        label="React"
                        trigger-class="flex items-center gap-1 hover:text-warning"
                        @select="(e) => react(String(e))"
                    >
                        <template #trigger>
                            <span class="hover:text-warning cursor-pointer flex items-center gap-1">
                                <span>👍</span>
                                <span>React</span>
                            </span>
                        </template>
                    </UiOptions>

                    <!-- Reply Trigger -->
                    <button
                        type="button"
                        class="hover:text-accent cursor-pointer flex items-center gap-1"
                        @click="toggleReply"
                    >
                        <span>💬</span>
                        <span>Reply</span>
                    </button>
                </div>

                <!-- Inline Reply Box for Comment -->
                <form
                    v-if="replyOpen"
                    class="mt-3 flex flex-col gap-2 rounded-xl border border-border bg-bg p-2.5"
                    @submit.prevent="submitReply"
                >
                    <p class="text-[11px] font-semibold text-text-muted">
                        Replying to @{{ comment.profile.username }}
                    </p>
                    <textarea
                        v-model="replyDraft"
                        rows="2"
                        placeholder="Write a reply..."
                        class="w-full resize-none bg-transparent text-xs text-text outline-none"
                        autofocus
                    />
                    <div class="flex items-center justify-end gap-2 pt-1 border-t border-border/40">
                        <UiButton
                            type="button"
                            size="sm"
                            variant="ghost"
                            class="text-xs h-7 py-0 px-2"
                            @click="replyOpen = false"
                        >
                            Cancel
                        </UiButton>
                        <UiButton
                            type="submit"
                            size="sm"
                            class="text-xs h-7 py-0 px-3"
                            :disabled="!replyDraft.trim()"
                        >
                            Reply
                        </UiButton>
                    </div>
                </form>
            </div>
        </div>

        <!-- Nested Children -->
        <ul
            v-if="childReplies.length"
            class="ml-6 sm:ml-9 flex flex-col gap-2"
        >
            <PostCommentItem
                v-for="child in childReplies"
                :key="child.id"
                :comment="child"
                :all-comments="allComments"
                :depth="currentDepth + 1"
                :can-interact="canInteract"
                @react="(id, emoji) => emit('react', id, emoji)"
                @reply="(id, text) => emit('reply', id, text)"
                @auth-required="emit('auth-required')"
            />
        </ul>
    </li>
</template>
