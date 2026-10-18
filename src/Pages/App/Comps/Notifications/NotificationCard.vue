<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import type { NotificationItem } from '@/Pages/_commons/Types/notification.type';

const props = defineProps<{
    notification: NotificationItem;
    isMarking?: boolean;
}>();

const emit = defineEmits<{
    (e: 'read', notification: NotificationItem): void;
}>();

const router = useRouter();

const kindBadge = computed(() => {
    switch (props.notification.kind) {
        case 'reaction':
            return { icon: '❤️', label: 'Reaction', bg: 'bg-rose-500/10 text-rose-500' };
        case 'comment':
            return { icon: '💬', label: 'Comment', bg: 'bg-sky-500/10 text-sky-500' };
        case 'reply':
            return { icon: '↩️', label: 'Reply', bg: 'bg-indigo-500/10 text-indigo-500' };
        case 'star':
            return { icon: '⭐', label: 'Star', bg: 'bg-amber-500/10 text-amber-500' };
        case 'follow':
            return { icon: '👥', label: 'Follow', bg: 'bg-emerald-500/10 text-emerald-500' };
        default:
            return { icon: '🔔', label: 'Activity', bg: 'bg-bg-sunken text-text-muted' };
    }
});

const targetPostId = computed(() => {
    return props.notification.target_post_id || (props.notification.target_type === 'post' ? props.notification.target_id : null);
});

function formatDate(iso: string): string {
    try {
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now.getTime() - d.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
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

function handlePostClick() {
    emit('read', props.notification);
    if (targetPostId.value) {
        void router.push({ name: 'post-detail', params: { id: targetPostId.value } });
    }
}
</script>

<template>
    <article
        class="group relative flex items-start gap-3.5 rounded-2xl border border-border p-4 transition-all"
        :class="notification.is_read
            ? 'bg-bg-elevated hover:border-border-strong hover:shadow-xs'
            : 'bg-accent/5 border-accent/30 shadow-card'"
    >
        <!-- Unread Indicator Dot -->
        <span
            v-if="!notification.is_read"
            class="absolute top-4.5 right-4 h-2 w-2 rounded-full bg-accent"
            aria-label="Unread notification"
        />

        <!-- Actor Avatar with Kind Badge Overlay -->
        <div class="relative shrink-0">
            <RouterLink
                v-if="notification.actor_username"
                :to="{ name: 'profile', params: { profile: notification.actor_username } }"
                class="grid h-10 w-10 place-items-center rounded-full border border-border bg-bg-sunken text-lg shadow-xs transition-transform hover:scale-105"
                @click="emit('read', notification)"
            >
                {{ notification.actor_emoji || '👤' }}
            </RouterLink>
            <div
                v-else
                class="grid h-10 w-10 place-items-center rounded-full border border-border bg-bg-sunken text-lg shadow-xs"
            >
                {{ notification.actor_emoji || '🔔' }}
            </div>

            <!-- Kind Badge icon -->
            <span
                class="absolute -bottom-1 -right-1 grid h-5 w-5 place-items-center rounded-full border border-bg-elevated text-[11px] shadow-xs"
                :class="kindBadge.bg"
                aria-hidden="true"
            >
                {{ kindBadge.icon }}
            </span>
        </div>

        <!-- Notification Content -->
        <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-1.5 text-sm text-text">
                <RouterLink
                    v-if="notification.actor_username"
                    :to="{ name: 'profile', params: { profile: notification.actor_username } }"
                    class="font-bold text-text-h hover:text-accent no-underline"
                    @click="emit('read', notification)"
                >
                    {{ notification.actor_display_name || `@${notification.actor_username}` }}
                </RouterLink>
                <span class="text-text-muted">{{ notification.content }}</span>
            </div>

            <!-- Target Post Details & Preview Box -->
            <div
                v-if="targetPostId"
                class="mt-2.5 rounded-xl border border-border/80 bg-bg-sunken/60 p-2.5 transition-colors hover:border-accent/40 cursor-pointer"
                @click="handlePostClick"
            >
                <div class="flex items-center justify-between text-xs text-text-muted">
                    <span class="font-semibold text-accent flex items-center gap-1">
                        <span>📝 Post #{{ targetPostId }}</span>
                    </span>
                    <span class="text-[11px] font-semibold text-accent group-hover:translate-x-0.5 transition-transform">
                        View post thread →
                    </span>
                </div>
                <p
                    v-if="notification.target_post_snippet"
                    class="mt-1 line-clamp-2 text-xs italic text-text leading-relaxed"
                >
                    "{{ notification.target_post_snippet }}"
                </p>
            </div>

            <!-- Footer: Timestamp & Quick Action -->
            <div class="mt-2 flex items-center gap-3 text-xs text-text-muted">
                <time :datetime="notification.created_at" class="tabular-nums">
                    {{ formatDate(notification.created_at) }}
                </time>

                <button
                    v-if="!notification.is_read"
                    type="button"
                    class="text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                    :disabled="isMarking"
                    @click="emit('read', notification)"
                >
                    Mark as read
                </button>
            </div>
        </div>
    </article>
</template>
