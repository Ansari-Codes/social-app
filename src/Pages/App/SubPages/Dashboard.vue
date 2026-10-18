<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import UiTabs, { type UiTabOption } from '@/Ui/UiTabs.vue';
import UiButton from '@/Ui/UiButton.vue';
import DashboardPosts from '../Comps/Dashboard/DashboardPosts.vue';
import DashboardPostList from '../Comps/Dashboard/DashboardPostList.vue';
import DashboardAnalytics from '../Comps/Dashboard/DashboardAnalytics.vue';
import { useMeStore } from '@/Stores/meStore';
import { useAppDataStore } from '@/Stores/appDataStore';
import type { Profile } from '../Types/feed.type';

const me = useMeStore();
const appData = useAppDataStore();
const activeTab = ref('analytics');
const profile = ref<Profile | null>(null);

const tabs: UiTabOption[] = [
    { id: 'analytics', label: '📈 Analytics & Growth' },
    { id: 'posts', label: '📝 Published Posts' },
    { id: 'comments', label: '💬 My Comments' },
];

onMounted(async () => {
    try {
        const data = await appData.loadMyProfile();
        profile.value = {
            id: data.id,
            username: data.username,
            display_name: data.display_name,
            emoji: data.emoji ?? undefined,
            about: data.about ?? undefined,
            followers: data.followers,
            following: data.following,
            stars: data.stars,
            reactions: data.reactions,
        };
    } catch {
        // Handled
    }
});
</script>

<template>
    <main class="mx-auto flex w-full max-w-6xl flex-col gap-6 px-3 py-5 sm:px-5 lg:py-8">
        <!-- ── Executive Creator Dashboard Banner ─────────────────── -->
        <header class="relative overflow-hidden rounded-3xl border border-border bg-linear-to-r from-bg-elevated via-bg-elevated to-bg-sunken/60 p-6 shadow-card sm:p-8">
            <div class="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                <div class="flex items-center gap-4">
                    <div class="grid h-16 w-16 shrink-0 place-items-center rounded-2xl border border-border bg-bg-sunken text-3xl shadow-sm">
                        {{ profile?.emoji || '📊' }}
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="rounded-full bg-accent/15 px-2.5 py-0.5 text-xs font-bold text-accent">
                                Creator Studio
                            </span>
                            <span class="text-xs text-text-muted">Pro Analytics</span>
                        </div>
                        <h1 class="mt-1 text-2xl font-black tracking-tight text-text-h sm:text-3xl">
                            {{ me.user?.display_name || me.user?.username || 'Creator' }}'s Studio
                        </h1>
                        <p class="text-xs text-text-muted">
                            Manage your content, monitor community engagement, and optimize reach.
                        </p>
                    </div>
                </div>

                <div class="flex items-center gap-2.5">
                    <RouterLink :to="{ name: 'app' }" class="no-underline">
                        <UiButton size="sm" variant="ghost">
                            <template #leading><span aria-hidden="true">🏠</span></template>
                            Go to Feed
                        </UiButton>
                    </RouterLink>
                    <RouterLink :to="{ name: 'settings' }" class="no-underline">
                        <UiButton size="sm" variant="soft">
                            <template #leading><span aria-hidden="true">⚙️</span></template>
                            Settings
                        </UiButton>
                    </RouterLink>
                </div>
            </div>
        </header>

        <!-- ── Section Tabs ───────────────────────────────────────── -->
        <div class="flex items-center justify-between border-b border-border pb-1">
            <UiTabs v-model="activeTab" :tabs="tabs" label="Dashboard sections" />
        </div>

        <!-- ── Active Tab Panel ───────────────────────────────────── -->
        <section role="tabpanel" :aria-label="`${activeTab} dashboard`" class="min-w-0">
            <DashboardPostList v-if="activeTab === 'comments'" kind="comments" />
            <DashboardPosts v-else-if="activeTab === 'posts'" />
            <DashboardAnalytics v-else />
        </section>
    </main>
</template>
