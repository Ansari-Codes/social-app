<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import UiButton from '@/Ui/UiButton.vue';
import { useMeStore } from '@/Stores/meStore';
import type { Profile } from '../../Types/feed.type';

const props = defineProps<{
    currentFilter: 'all' | 'following' | 'starred' | 'discussions';
    unreadCount?: number;
    profile?: Profile | null;
}>();

const emit = defineEmits<{
    (e: 'filter', filter: 'all' | 'following' | 'starred' | 'discussions'): void;
    (e: 'compose'): void;
}>();

const me = useMeStore();

const streams = [
    { id: 'all', label: 'For You', icon: '🌐', desc: 'Latest community posts' },
    { id: 'following', label: 'Following', icon: '👥', desc: 'People you follow' },
    { id: 'starred', label: 'Starred', icon: '⭐', desc: 'Favorite creators' },
    { id: 'discussions', label: 'Discussions', icon: '💬', desc: 'Active reply threads' },
] as const;

const userProfileName = computed(() => {
    return me.user?.display_name || me.user?.username || 'You';
});

const userProfileHandle = computed(() => {
    return me.user?.username ? `@${me.user.username}` : '';
});
</script>

<template>
    <nav class="sticky top-20 flex w-full flex-col gap-4" aria-label="Feed channels and navigation">
        <!-- Feed Stream Filters -->
        <div class="rounded-2xl border border-border bg-bg-elevated p-3 shadow-card">
            <p class="px-2 pb-2 text-[11px] font-bold uppercase tracking-wider text-text-muted">
                Feed Channels
            </p>
            <div class="flex flex-col gap-1">
                <button
                    v-for="s in streams"
                    :key="s.id"
                    type="button"
                    class="group flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm font-medium transition-all"
                    :class="currentFilter === s.id
                        ? 'bg-accent/10 text-accent font-semibold shadow-xs'
                        : 'text-text hover:bg-bg-hover hover:text-text-h'"
                    @click="emit('filter', s.id)"
                >
                    <div class="flex items-center gap-2.5">
                        <span class="text-base" aria-hidden="true">{{ s.icon }}</span>
                        <span>{{ s.label }}</span>
                    </div>
                    <span
                        v-if="currentFilter === s.id"
                        class="h-1.5 w-1.5 rounded-full bg-accent"
                        aria-hidden="true"
                    />
                </button>
            </div>
        </div>

        <!-- Quick Compose Button -->
        <UiButton
            size="lg"
            block
            class="shadow-accent/20 hover:shadow-accent/30 font-semibold shadow-md transition-transform active:scale-[0.98]"
            @click="emit('compose')"
        >
            <template #leading><span aria-hidden="true">✏️</span></template>
            Create Post
        </UiButton>

        <!-- Quick Navigation -->
        <div class="rounded-2xl border border-border bg-bg-elevated p-3 shadow-card">
            <p class="px-2 pb-2 text-[11px] font-bold uppercase tracking-wider text-text-muted">
                Quick Shortcuts
            </p>
            <div class="flex flex-col gap-1">
                <RouterLink
                    :to="{ name: 'notifications' }"
                    class="flex items-center justify-between rounded-xl px-3 py-2 text-sm font-medium text-text no-underline transition-colors hover:bg-bg-hover hover:text-text-h"
                >
                    <div class="flex items-center gap-2.5">
                        <span aria-hidden="true">🔔</span>
                        <span>Notifications</span>
                    </div>
                    <span
                        v-if="unreadCount && unreadCount > 0"
                        class="rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-accent-fg"
                    >
                        {{ unreadCount > 99 ? '99+' : unreadCount }}
                    </span>
                </RouterLink>

                <RouterLink
                    :to="{ name: 'dashboard' }"
                    class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-text no-underline transition-colors hover:bg-bg-hover hover:text-text-h"
                >
                    <span aria-hidden="true">📊</span>
                    <span>Dashboard</span>
                </RouterLink>

                <RouterLink
                    v-if="me.user"
                    :to="{ name: 'profile', params: { profile: me.user.username } }"
                    class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-text no-underline transition-colors hover:bg-bg-hover hover:text-text-h"
                >
                    <span aria-hidden="true">👤</span>
                    <span>My Profile</span>
                </RouterLink>

                <RouterLink
                    :to="{ name: 'settings' }"
                    class="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-text no-underline transition-colors hover:bg-bg-hover hover:text-text-h"
                >
                    <span aria-hidden="true">⚙️</span>
                    <span>Settings</span>
                </RouterLink>
            </div>
        </div>

        <!-- Mini User Account Capsule (compact instead of large profile card) -->
        <div
            v-if="me.user"
            class="flex items-center justify-between rounded-2xl border border-border bg-bg-elevated p-3 shadow-card"
        >
            <RouterLink
                :to="{ name: 'profile', params: { profile: me.user.username } }"
                class="flex min-w-0 items-center gap-2.5 no-underline hover:opacity-90"
            >
                <div class="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-border bg-bg-sunken text-lg">
                    {{ profile?.emoji || '👤' }}
                </div>
                <div class="min-w-0 flex-1">
                    <p class="truncate text-xs font-semibold text-text-h">{{ userProfileName }}</p>
                    <p class="truncate text-[11px] text-text-muted">{{ userProfileHandle }}</p>
                </div>
            </RouterLink>
            <span class="rounded-full bg-success/15 px-2 py-0.5 text-[10px] font-medium text-success">Online</span>
        </div>
        <div v-else class="rounded-xl border border-border bg-bg-elevated p-4">
            <p class="text-sm font-semibold text-text-h">Welcome to the feed</p>
            <p class="mt-1 text-xs text-text-muted">Sign in or create an account to join in.</p>
            <div class="mt-3 flex gap-2">
                <RouterLink
                    :to="{ name: 'login' }"
                    class="flex h-9 flex-1 items-center justify-center rounded-md border border-border text-xs font-semibold text-text-h no-underline hover:bg-bg-hover"
                >
                    Log in
                </RouterLink>
                <RouterLink
                    :to="{ name: 'signup' }"
                    class="flex h-9 flex-1 items-center justify-center rounded-md bg-accent text-xs font-semibold text-accent-fg no-underline hover:bg-accent-hover"
                >
                    Sign up
                </RouterLink>
            </div>
        </div>
    </nav>
</template>
