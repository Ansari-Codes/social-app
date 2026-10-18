<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import UiTabs, { type UiTabOption } from '@/Ui/UiTabs.vue';
import DashboardTrendChart, { type TrendPoint } from './DashboardTrendChart.vue';
import { useAppDataStore } from '@/Stores/appDataStore';
import type { DashboardAnalyticsData } from '@/Pages/_commons/Types/analytics.type';

const ranges: UiTabOption[] = [
    { id: '7', label: '7 days' },
    { id: '30', label: '30 days' },
    { id: '90', label: '90 days' },
    { id: '365', label: '1 year' },
];
const selectedRange = ref('30');
const appData = useAppDataStore();
const analytics = computed<DashboardAnalyticsData | null>(
    () => appData.analytics[Number(selectedRange.value)] ?? null,
);
const isLoading = ref(!appData.analyticsLoaded[Number(selectedRange.value)]);
const error = ref('');
let requestId = 0;

const metrics = computed(() => {
    const data = analytics.value;
    const totalPosts = data?.total_posts ?? 0;
    const totalComments = data?.total_comments ?? 0;
    const totalReactions = data?.total_reactions ?? 0;
    const engagementRate = data?.engagement_rate ?? (totalPosts > 0 ? ((totalReactions + totalComments) / totalPosts).toFixed(1) : '0');
    const followers = data?.total_followers ?? (data?.time_series?.at(-1)?.followers ?? 0);
    const stars = data?.total_stars ?? (data?.time_series?.at(-1)?.stars ?? 0);

    return [
        {
            label: 'Total Posts',
            value: totalPosts,
            icon: '📝',
            desc: 'Published by you',
            accent: 'text-text-h',
        },
        {
            label: 'Total Reactions',
            value: totalReactions,
            icon: '❤️',
            desc: 'Interactions across posts',
            accent: 'text-accent',
        },
        {
            label: 'Discussions & Comments',
            value: totalComments,
            icon: '💬',
            desc: 'Replies received',
            accent: 'text-info',
        },
        {
            label: 'Engagement Score',
            value: `${engagementRate}x`,
            icon: '⚡',
            desc: 'Avg responses per post',
            accent: 'text-warning',
        },
        {
            label: 'Active Followers',
            value: followers,
            icon: '👥',
            desc: 'Community subscribers',
            accent: 'text-success',
        },
        {
            label: 'Profile Stars',
            value: stars,
            icon: '⭐',
            desc: 'Community reputation',
            accent: 'text-warning',
        },
    ];
});

function formatDate(value: string): string {
    try {
        return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(`${value}T12:00:00`));
    } catch {
        return value;
    }
}

const followerPoints = computed<TrendPoint[]>(() =>
    (analytics.value?.time_series ?? []).map((point) => ({
        label: formatDate(point.date),
        value: point.followers,
    })),
);

const starPoints = computed<TrendPoint[]>(() =>
    (analytics.value?.time_series ?? []).map((point) => ({
        label: formatDate(point.date),
        value: point.stars,
    })),
);

// Reaction Breakdown items with percentages
const reactionBreakdown = computed(() => {
    const breakdown = analytics.value?.reaction_breakdown || {};
    const total = Object.values(breakdown).reduce((sum, count) => sum + count, 0);
    if (!total) {
        if (analytics.value?.dominant_reaction && analytics.value?.dominant_reaction_count) {
            return [{
                emoji: analytics.value.dominant_reaction,
                count: analytics.value.dominant_reaction_count,
                percentage: 100,
            }];
        }
        return [];
    }

    return Object.entries(breakdown)
        .map(([emoji, count]) => ({
            emoji,
            count,
            percentage: Math.round((count / total) * 100),
        }))
        .sort((a, b) => b.count - a.count);
});

// Descriptive community insights
const insights = computed(() => {
    const data = analytics.value;
    if (!data) return [];

    const list: Array<{ title: string; desc: string; icon: string }> = [];

    if (data.total_reactions > 5 || data.total_comments > 2) {
        list.push({
            title: 'High Audience Responsiveness',
            desc: `Your posts are generating strong resonance with ${data.total_reactions} reactions and ${data.total_comments} comments.`,
            icon: '🚀',
        });
    } else {
        list.push({
            title: 'Early Stage Growth',
            desc: 'Publish interactive prompts and ask open-ended questions to increase community replies.',
            icon: '🌱',
        });
    }

    if (data.dominant_reaction) {
        list.push({
            title: 'Sentiment Alignment',
            desc: `The community predominantly responds with ${data.dominant_reaction} (${data.dominant_reaction_count} times), indicating high positive sentiment.`,
            icon: '💖',
        });
    }

    const followers = data.total_followers ?? 0;
    const stars = data.total_stars ?? 0;
    if (followers > 0 || stars > 0) {
        list.push({
            title: 'Community Loyalty',
            desc: `You have accumulated ${followers} followers and ${stars} stars. Keep your posting cadence steady to maintain momentum.`,
            icon: '⭐',
        });
    }

    return list;
});

async function loadAnalytics() {
    const currentRequest = ++requestId;
    const days = Number(selectedRange.value);
    isLoading.value = !appData.analyticsLoaded[days];
    error.value = '';
    try {
        await appData.loadAnalytics(days);
    } catch (cause) {
        if (currentRequest === requestId) {
            error.value = cause instanceof Error ? cause.message : 'Unable to load analytics.';
        }
    } finally {
        if (currentRequest === requestId) isLoading.value = false;
    }
}

watch(selectedRange, () => {
    isLoading.value = !appData.analyticsLoaded[Number(selectedRange.value)];
    void loadAnalytics();
});

onMounted(() => {
    void loadAnalytics();
});
</script>

<template>
    <section class="flex min-w-0 flex-col gap-6" aria-label="Dashboard analytics">
        <!-- Date Range Filter Header -->
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 pb-3">
            <div>
                <h2 class="text-lg font-bold text-text-h">Performance Overview</h2>
                <p class="text-xs text-text-muted">Descriptive metrics, audience growth, and content engagement</p>
            </div>
            <UiTabs v-model="selectedRange" :tabs="ranges" label="Analytics date range" />
        </header>

        <p v-if="error" class="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
            {{ error }}
        </p>
        <p v-if="isLoading" class="py-12 text-center text-sm text-text-muted" role="status">Loading comprehensive analytics...</p>

        <template v-else-if="analytics">
            <!-- ── KPI Metrics Grid ───────────────────────────────── -->
            <div class="grid grid-cols-2 gap-3.5 sm:grid-cols-3 xl:grid-cols-6">
                <article
                    v-for="metric in metrics"
                    :key="metric.label"
                    class="flex flex-col justify-between rounded-2xl border border-border bg-bg-elevated p-4 shadow-card transition-transform hover:-translate-y-0.5"
                >
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-semibold text-text-muted">{{ metric.label }}</span>
                        <span class="text-base" aria-hidden="true">{{ metric.icon }}</span>
                    </div>
                    <div class="mt-3">
                        <p class="text-2xl font-black tabular-nums tracking-tight" :class="metric.accent">
                            {{ metric.value }}
                        </p>
                        <p class="mt-0.5 text-[11px] text-text-faint truncate">{{ metric.desc }}</p>
                    </div>
                </article>
            </div>

            <!-- ── Growth Trend Charts ────────────────────────────── -->
            <div class="grid min-w-0 gap-5 lg:grid-cols-2">
                <DashboardTrendChart
                    title="Follower Growth Trend"
                    :points="followerPoints"
                    color="var(--color-accent)"
                />
                <DashboardTrendChart
                    title="Profile Stars Accumulated"
                    :points="starPoints"
                    color="var(--color-info)"
                />
            </div>

            <!-- ── Emotional Sentiment & Reaction Breakdown ───────── -->
            <div class="grid min-w-0 gap-5 lg:grid-cols-2">
                <!-- Reaction Distribution -->
                <div class="rounded-2xl border border-border bg-bg-elevated p-5 shadow-card">
                    <div class="mb-4 flex items-center justify-between">
                        <div>
                            <h3 class="text-sm font-bold text-text-h">Sentiment & Reaction Breakdown</h3>
                            <p class="text-xs text-text-muted">How users react to your thoughts</p>
                        </div>
                        <span class="text-xs font-bold text-accent">{{ analytics.total_reactions }} total</span>
                    </div>

                    <div v-if="reactionBreakdown.length" class="flex flex-col gap-3">
                        <div v-for="rx in reactionBreakdown" :key="rx.emoji" class="flex flex-col gap-1">
                            <div class="flex items-center justify-between text-xs">
                                <span class="flex items-center gap-1.5 font-medium text-text">
                                    <span class="text-base">{{ rx.emoji }}</span>
                                    <span>{{ rx.count }} reactions</span>
                                </span>
                                <span class="font-bold text-text-muted tabular-nums">{{ rx.percentage }}%</span>
                            </div>
                            <div class="h-2 w-full overflow-hidden rounded-full bg-bg-sunken">
                                <div
                                    class="h-full rounded-full bg-accent transition-all duration-500"
                                    :style="{ width: `${rx.percentage}%` }"
                                />
                            </div>
                        </div>
                    </div>
                    <p v-else class="py-6 text-center text-xs text-text-muted">
                        No reactions recorded yet in this time frame.
                    </p>
                </div>

                <!-- Descriptive Insights Panel -->
                <div class="rounded-2xl border border-border bg-bg-elevated p-5 shadow-card">
                    <div class="mb-4">
                        <h3 class="text-sm font-bold text-text-h">Creator Intelligence & Insights</h3>
                        <p class="text-xs text-text-muted">Automated performance recommendations</p>
                    </div>

                    <div class="flex flex-col gap-3.5">
                        <div
                            v-for="(insight, idx) in insights"
                            :key="idx"
                            class="flex items-start gap-3 rounded-xl border border-border/80 bg-bg-sunken/40 p-3"
                        >
                            <span class="text-xl shrink-0" aria-hidden="true">{{ insight.icon }}</span>
                            <div class="min-w-0">
                                <p class="text-xs font-bold text-text-h">{{ insight.title }}</p>
                                <p class="mt-0.5 text-xs leading-relaxed text-text-muted">{{ insight.desc }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ── Top Performing Content Leaderboard ──────────────── -->
            <div v-if="analytics.top_posts && analytics.top_posts.length" class="rounded-2xl border border-border bg-bg-elevated p-5 shadow-card">
                <div class="mb-4 flex items-center justify-between">
                    <div>
                        <h3 class="text-sm font-bold text-text-h">🏆 Top Performing Content</h3>
                        <p class="text-xs text-text-muted">Posts with highest engagement and discussions</p>
                    </div>
                </div>

                <div class="divide-y divide-border/80">
                    <div
                        v-for="(topPost, idx) in analytics.top_posts"
                        :key="topPost.id"
                        class="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                    >
                        <div class="flex items-center gap-3 min-w-0">
                            <span class="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent/10 font-bold text-xs text-accent">
                                #{{ idx + 1 }}
                            </span>
                            <div class="min-w-0">
                                <p class="truncate text-sm font-medium text-text-h">
                                    "{{ topPost.content }}"
                                </p>
                                <div class="mt-0.5 flex items-center gap-3 text-xs text-text-muted">
                                    <span>❤️ {{ topPost.reactions }} reactions</span>
                                    <span>💬 {{ topPost.comments }} comments</span>
                                </div>
                            </div>
                        </div>

                        <RouterLink
                            :to="{ name: 'post-detail', params: { id: topPost.id } }"
                            class="shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold text-accent no-underline hover:bg-accent/10 transition-colors"
                        >
                            View Post →
                        </RouterLink>
                    </div>
                </div>
            </div>
        </template>
    </section>
</template>
