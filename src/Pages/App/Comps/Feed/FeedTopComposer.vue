<script setup lang="ts">
import { ref } from 'vue';
import UiButton from '@/Ui/UiButton.vue';
import { useMeStore } from '@/Stores/meStore';

const props = defineProps<{
    isPublishing?: boolean;
}>();

const emit = defineEmits<{
    (e: 'publish', content: string): void;
}>();

const me = useMeStore();
const draft = ref('');
const isExpanded = ref(false);

const quickTags = ['#Silence', '#TechTalk', '#Discussion', '#Ideas', '#Community'];

function addTag(tag: string) {
    if (!draft.value.includes(tag)) {
        draft.value = draft.value ? `${draft.value} ${tag}` : tag;
        isExpanded.value = true;
    }
}

function submitPost() {
    if (!draft.value.trim() || props.isPublishing) return;
    emit('publish', draft.value.trim());
    draft.value = '';
    isExpanded.value = false;
}
</script>

<template>
    <div class="rounded-2xl border border-border bg-bg-elevated p-4 shadow-card transition-all">
        <form @submit.prevent="submitPost">
            <div class="flex items-start gap-3">
                <!-- User Avatar -->
                <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-xl">
                    {{ me.user?.display_name ? '👤' : '✨' }}
                </div>

                <!-- Input area -->
                <div class="min-w-0 flex-1">
                    <label for="top-feed-composer" class="sr-only">What is happening?</label>
                    <textarea
                        id="top-feed-composer"
                        v-model="draft"
                        :rows="isExpanded ? 3 : 2"
                        maxlength="10000"
                        placeholder="What's happening? Share a thought with the community..."
                        class="w-full resize-none bg-transparent text-sm text-text placeholder:text-text-muted outline-none"
                        @focus="isExpanded = true"
                    />

                    <!-- Tag recommendations -->
                    <div v-if="isExpanded" class="mt-2 flex flex-wrap items-center gap-1.5 pt-1">
                        <span class="text-[11px] text-text-muted">Tags:</span>
                        <button
                            v-for="tag in quickTags"
                            :key="tag"
                            type="button"
                            class="rounded-full border border-border/80 bg-bg-sunken/80 px-2 py-0.5 text-[11px] font-medium text-text-muted transition-colors hover:border-accent hover:text-accent"
                            @click="addTag(tag)"
                        >
                            {{ tag }}
                        </button>
                    </div>

                    <!-- Actions & Submit Bar -->
                    <div class="mt-3 flex items-center justify-between border-t border-border/60 pt-2.5">
                        <span class="text-xs text-text-muted tabular-nums">
                            {{ draft.length }} / 10,000
                        </span>

                        <div class="flex items-center gap-2">
                            <UiButton
                                v-if="isExpanded && draft.length"
                                type="button"
                                variant="ghost"
                                size="sm"
                                @click="draft = ''; isExpanded = false"
                            >
                                Clear
                            </UiButton>
                            <UiButton
                                type="submit"
                                size="sm"
                                :loading="isPublishing"
                                :disabled="!draft.trim()"
                                class="font-semibold px-4"
                            >
                                Post
                            </UiButton>
                        </div>
                    </div>
                </div>
            </div>
        </form>
    </div>
</template>
