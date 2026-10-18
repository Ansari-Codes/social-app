<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import UiButton from '@/Ui/UiButton.vue';
import NotificationCard from '../Comps/Notifications/NotificationCard.vue';
import type { NotificationItem } from '@/Pages/_commons/Types/notification.type';
import { useAppDataStore } from '@/Stores/appDataStore';

const appData = useAppDataStore();
const notifications = computed(() => appData.notifications?.notifications ?? []);
const unreadCount = computed(() => appData.notifications?.unread_count ?? 0);
const isLoading = ref(!appData.notificationsLoaded);
const isMarkingAll = ref(false);
const error = ref('');
const markingId = ref<number | null>(null);
const activeTab = ref<'all' | 'reply' | 'comment' | 'reaction' | 'star'>('all');

const tabs = [
    { id: 'all', label: 'All Activity' },
    { id: 'reply', label: '↩️ Replies' },
    { id: 'comment', label: '💬 Comments' },
    { id: 'reaction', label: '❤️ Reactions' },
    { id: 'star', label: '⭐ Stars & Follows' },
] as const;

const filteredNotifications = computed(() => {
    if (activeTab.value === 'all') return notifications.value;
    if (activeTab.value === 'star') {
        return notifications.value.filter(n => n.kind === 'star' || n.kind === 'follow');
    }
    return notifications.value.filter(n => n.kind === activeTab.value);
});

async function loadNotifications() {
    error.value = '';
    isLoading.value = !appData.notificationsLoaded;
    try {
        await appData.loadNotifications();
    } catch (cause) {
        error.value = cause instanceof Error ? cause.message : 'Unable to load notifications.';
    } finally {
        isLoading.value = false;
    }
}

async function markRead(notification: NotificationItem) {
    if (notification.is_read) return;
    markingId.value = notification.id;
    error.value = '';
    try {
        await appData.markRead(notification.id);
    } catch (cause) {
        error.value = cause instanceof Error ? cause.message : 'Unable to update notification.';
    } finally {
        markingId.value = null;
    }
}

async function markAllRead() {
    if (!unreadCount.value) return;
    isMarkingAll.value = true;
    error.value = '';
    try {
        await appData.markAllRead();
    } catch (cause) {
        error.value = cause instanceof Error ? cause.message : 'Unable to update notifications.';
    } finally {
        isMarkingAll.value = false;
    }
}

onMounted(() => {
    void loadNotifications();
});
</script>

<template>
    <main class="mx-auto flex w-full max-w-3xl flex-col gap-5 px-3 py-5 sm:px-5 lg:py-8">
        <!-- ── Header ─────────────────────────────────────────────── -->
        <header class="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-4">
            <div>
                <div class="flex items-center gap-2">
                    <p class="text-xs font-bold uppercase tracking-wider text-text-muted">Activity Stream</p>
                    <span
                        v-if="unreadCount > 0"
                        class="rounded-full bg-accent px-2 py-0.5 text-[11px] font-bold text-accent-fg"
                    >
                        {{ unreadCount }} new
                    </span>
                </div>
                <h1 class="mt-1 text-2xl font-black tracking-tight text-text-h">Notifications</h1>
                <p class="text-xs text-text-muted">Stay informed when people react, comment, or reply to your posts.</p>
            </div>

            <UiButton
                variant="ghost"
                size="sm"
                :disabled="isMarkingAll || unreadCount === 0"
                @click="markAllRead"
            >
                {{ isMarkingAll ? 'Updating...' : 'Mark all read' }}
            </UiButton>
        </header>

        <!-- ── Filter Tabs ────────────────────────────────────────── -->
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                class="rounded-full px-3.5 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors"
                :class="activeTab === tab.id
                    ? 'bg-accent text-accent-fg shadow-xs'
                    : 'bg-bg-elevated border border-border text-text hover:bg-bg-hover'"
                @click="activeTab = tab.id"
            >
                {{ tab.label }}
            </button>
        </div>

        <!-- ── Error Alert ────────────────────────────────────────── -->
        <p
            v-if="error"
            class="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
            role="alert"
        >
            {{ error }}
        </p>

        <!-- ── Loading State ──────────────────────────────────────── -->
        <div v-if="isLoading" class="flex flex-col gap-3" role="status" aria-label="Loading notifications">
            <div
                v-for="n in 4"
                :key="n"
                class="animate-pulse rounded-2xl border border-border bg-bg-elevated p-4 flex items-center gap-3"
            >
                <div class="h-10 w-10 rounded-full bg-bg-sunken shrink-0" />
                <div class="flex-1 space-y-2">
                    <div class="h-3.5 w-48 rounded bg-bg-sunken" />
                    <div class="h-2.5 w-24 rounded bg-bg-sunken" />
                </div>
            </div>
        </div>

        <!-- ── Empty State ────────────────────────────────────────── -->
        <div
            v-else-if="!filteredNotifications.length"
            class="rounded-2xl border border-dashed border-border bg-bg-elevated px-4 py-16 text-center shadow-card"
        >
            <span class="text-3xl" aria-hidden="true">🔔</span>
            <p class="mt-2 text-base font-bold text-text-h">No notifications in this filter</p>
            <p class="mt-1 text-xs text-text-muted">You are all caught up on community interactions.</p>
        </div>

        <!-- ── Notifications List ─────────────────────────────────── -->
        <div v-else class="flex flex-col gap-3">
            <NotificationCard
                v-for="notification in filteredNotifications"
                :key="notification.id"
                :notification="notification"
                :is-marking="markingId === notification.id"
                @read="markRead"
            />
        </div>
    </main>
</template>
