<script setup lang="ts">
defineProps<{
    active: 'posts' | 'followers' | 'following';
    counts?: { posts?: number; followers?: number; following?: number };
}>();

const emit = defineEmits<{
    (e: 'change', tab: 'posts' | 'followers' | 'following'): void;
}>();

const tabs = [
    { id: 'posts', label: 'Posts', icon: '📝' },
    { id: 'followers', label: 'Followers', icon: '👥' },
    { id: 'following', label: 'Following', icon: '👤' },
] as const;
</script>

<template>
    <nav class="flex flex-row items-center gap-1 border-b border-border" aria-label="Profile sections">
        <button v-for="t in tabs" :key="t.id" type="button" class="relative inline-flex items-center gap-1.5 px-4 py-2 text-sm
                   text-text-muted hover:text-text-h transition-colors"
            :class="active === t.id && 'text-text-h font-semibold'" @click="emit('change', t.id)">
            <span aria-hidden="true">{{ t.icon }}</span>
            <span>{{ t.label }}</span>
            <span v-if="counts?.[t.id] != null" class="text-xs text-text-faint tabular-nums">
                {{ counts[t.id] }}
            </span>

            <span v-if="active === t.id" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent" />
        </button>
    </nav>
</template>