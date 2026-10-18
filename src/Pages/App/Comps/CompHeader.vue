<script setup lang="ts">
// ═══════════════════════════════════════════════════════════════════════════
// APP HEADER — top bar with brand, centered nav tabs, and settings link.
//
// Layout is a 3-column grid using flex:
//   [ w-64 brand ]  [ flex-1 nav (centered) ]  [ w-64 settings ]
// The fixed-width flanks keep the nav optically centered regardless of how
// long the brand or settings labels are.
// ═══════════════════════════════════════════════════════════════════════════

import { computed, onMounted, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import UiButton from '@/Ui/UiButton.vue';
import { useMeStore } from '@/Stores/meStore';
import { useAppDataStore } from '@/Stores/appDataStore';
import { APP_NAME } from '@/Core/config';

// `unreadCount` is declared as a prop for API compatibility, but the real
// value is fetched locally below — the prop is intentionally unused.
defineProps<{
    unreadCount?: number;
}>();

const route = useRoute();
const me = useMeStore();
const appData = useAppDataStore();

// ─── Unread badge ──────────────────────────────────────────────────────────
// Local state for the notification count. Refreshed on mount and on every
// route change so the badge stays roughly in sync without a live socket.
const unreadCount = computed(() => appData.notifications?.unread_count ?? 0);

async function refreshUnreadCount() {
    try {
        await appData.loadNotifications();
    } catch {
        // Keep the cached badge if the request fails.
    }
}

onMounted(() => {
    if (me.isAuthenticated) void refreshUnreadCount();
});

watch(() => me.token, (token) => {
    if (token) void refreshUnreadCount();
});

/* ── Center nav tabs ─────────────────────────────────────────────── */
interface NavTab {
    label: string;
    icon: string;
    /** Router target — either { name: '...' } or a path string. */
    to: { name: string; params?: Record<string, string> } | string;
    /**
     * Optional. Route names (or path prefixes) that should highlight this tab.
     * If omitted, we derive from `to`.
     */
    match?: string[];
}

// Tabs are computed (not static) because the Profile tab's target depends on
// whether the current user is signed in — guests fall back to the app root.
const navTabs = computed<NavTab[]>(() => [
    {
        label: 'Feed',
        icon: '🏠',
        to: { name: 'app' },
        match: ['app', 'post-detail'],
    },
    {
        label: 'My Profile',
        icon: '👤',
        to: me.user
            ? { name: 'profile', params: { profile: me.user.username } }
            : { name: 'app' },   // graceful fallback for signed-out users
        match: ['profile'],
    },
    {
        label: 'Dashboard',
        icon: '▦',
        to: { name: 'dashboard' },
        match: ['dashboard', 'posts'],
    },
    {
        label: 'Notifications',
        icon: '🔔',
        to: { name: 'notifications' },
        match: ['notifications', 'analytics'],
    },
]);

/**
 * Unique key per tab. Falls back to the string path when `to` is a string,
 * and to `name` when it's an object.
 */
function tabKey(tab: NavTab): string {
    if (typeof tab.to === 'string') return tab.to;
    return tab.to.name;
}

/**
 * A tab is active if the current route name equals one of its `match`
 * entries, or starts with that entry + '.' (so children highlight parents).
 */
function isTabActive(tab: NavTab): boolean {
    const current = route.name?.toString() ?? '';
    const patterns = tab.match ?? tabKey(tab).split(',');

    return patterns.some((p) => current === p || current.startsWith(p + '.'));
}
</script>
<template>
    <header class="fixed top-0 z-50 w-full border-b border-border bg-bg-elevated/90 backdrop-blur-md shadow-xs transition-colors">
        <div class="mx-auto flex w-full max-w-6xl items-center h-14 px-3 gap-2">
            <!-- ── LEFT: brand ─────────────────────────────────── -->
            <div class="flex items-center gap-2.5 shrink-0 md:w-64">
                <RouterLink :to="{ name: 'app' }" class="flex items-center gap-2.5 no-underline text-inherit group">
                    <span class="grid h-9 w-9 place-items-center rounded-xl bg-accent text-accent-fg font-black text-sm shadow-xs transition-transform group-hover:scale-105" aria-hidden="true">
                        SB
                    </span>
                    <span class="hidden sm:inline font-black tracking-tight text-base text-text-h">
                        {{ APP_NAME }}
                    </span>
                </RouterLink>
            </div>

            <!-- ── CENTER: nav tabs ────────────────────────────── -->
            <nav class="flex-1 min-w-0 h-full flex items-stretch justify-center overflow-x-auto">
                <RouterLink v-for="tab in navTabs" :key="tabKey(tab)" :to="tab.to"
                    class="relative flex items-center justify-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 md:px-5 h-full
                           text-xs sm:text-sm font-semibold transition-colors whitespace-nowrap
                           text-text-muted hover:bg-bg-hover hover:text-text-h"
                    :class="isTabActive(tab) && 'text-accent'"
                    :aria-current="isTabActive(tab) ? 'page' : undefined" :title="tab.label">
                    <span class="text-lg leading-none" aria-hidden="true">{{ tab.icon }}</span>
                    <span class="hidden md:inline">{{ tab.label }}</span>

                    <span v-if="tab.match?.includes('notifications') && unreadCount"
                        class="min-w-4.5 rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-bold leading-none text-accent-fg">
                        {{ unreadCount > 99 ? '99+' : unreadCount }}
                    </span>

                    <span v-if="isTabActive(tab)"
                        class="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-accent" aria-hidden="true" />
                </RouterLink>
            </nav>

            <!-- ── RIGHT: settings ─────────────────────────────── -->
            <div class="flex items-center justify-end gap-2 shrink-0 md:w-64">
                <RouterLink :to="{ name: 'settings' }" custom v-slot="{ navigate }">
                    <UiButton variant="ghost" size="sm" class="gap-1.5 font-medium" @click="navigate" aria-label="Settings">
                        <span aria-hidden="true">⚙️</span>
                        <span class="hidden sm:inline">Settings</span>
                    </UiButton>
                </RouterLink>
            </div>
        </div>
    </header>

    <div class="h-14" aria-hidden="true"></div>
</template>