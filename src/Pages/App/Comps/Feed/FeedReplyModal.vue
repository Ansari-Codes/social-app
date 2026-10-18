<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import UiDialog from '@/Ui/UiDialog.vue';
import UiButton from '@/Ui/UiButton.vue';
import type { Post } from '../../Types/feed.type';

const props = defineProps<{
    modelValue: boolean;
    targetPost: Post | null;
    isPublishing?: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void;
    (e: 'reply', content: string, parentPostId: number): void;
}>();

const replyDraft = ref('');
const textareaRef = ref<HTMLTextAreaElement | null>(null);

watch(
    () => props.modelValue,
    (open) => {
        if (open) {
            replyDraft.value = '';
            nextTick(() => {
                textareaRef.value?.focus();
            });
        }
    }
);

function handleClose() {
    emit('update:modelValue', false);
}

function handleReplySubmit() {
    if (!props.targetPost || !replyDraft.value.trim() || props.isPublishing) return;
    emit('reply', replyDraft.value.trim(), props.targetPost.id);
}
</script>

<template>
    <UiDialog
        :model-value="modelValue"
        title="Reply to Post"
        :description="targetPost ? `Replying to @${targetPost.profile.username}` : undefined"
        size="md"
        @close="handleClose"
    >
        <div v-if="targetPost" class="flex flex-col gap-4">
            <!-- Quoted Parent Post Box -->
            <div class="rounded-xl border border-border bg-bg-sunken/60 p-3.5">
                <div class="flex items-center gap-2.5">
                    <span class="grid h-7 w-7 place-items-center rounded-full border border-border bg-bg text-sm">
                        {{ targetPost.profile.emoji || '😊' }}
                    </span>
                    <span class="text-xs font-bold text-text-h">
                        {{ targetPost.profile.display_name || targetPost.profile.username }}
                    </span>
                    <span class="text-xs text-text-muted">@{{ targetPost.profile.username }}</span>
                    <span class="ml-auto text-[11px] font-bold text-accent">#{{ targetPost.id }}</span>
                </div>
                <p class="mt-2 line-clamp-3 text-xs leading-relaxed text-text-muted">
                    {{ targetPost.content }}
                </p>
            </div>

            <!-- Reply Notice Pill -->
            <div class="flex items-center gap-2 text-xs text-text-muted">
                <span class="text-accent" aria-hidden="true">↩️</span>
                <span>This reply will be published to the main feed as <strong class="text-accent">reply_of #{{ targetPost.id }}</strong></span>
            </div>

            <!-- Textarea -->
            <form @submit.prevent="handleReplySubmit" class="flex flex-col gap-2">
                <label for="feed-reply-draft" class="sr-only">Your Reply</label>
                <textarea
                    id="feed-reply-draft"
                    ref="textareaRef"
                    v-model="replyDraft"
                    rows="4"
                    maxlength="10000"
                    placeholder="Post your reply over this post..."
                    class="w-full resize-y rounded-xl border border-border bg-bg px-3.5 py-3 text-sm text-text outline-none focus:border-accent"
                    :disabled="isPublishing"
                />

                <div class="flex items-center justify-between text-xs text-text-muted pt-1">
                    <span class="tabular-nums">{{ replyDraft.length }} / 10,000</span>
                </div>
            </form>
        </div>

        <template #footer>
            <div class="flex items-center justify-end gap-2 px-4 pb-4 pt-2">
                <UiButton variant="ghost" size="sm" :disabled="isPublishing" @click="handleClose">
                    Cancel
                </UiButton>
                <UiButton
                    size="sm"
                    :loading="isPublishing"
                    :disabled="!replyDraft.trim()"
                    @click="handleReplySubmit"
                >
                    <template #leading><span aria-hidden="true">💬</span></template>
                    Publish Reply
                </UiButton>
            </div>
        </template>
    </UiDialog>
</template>
