<script setup lang="ts">
import { computed } from 'vue';
import { type Profile } from '../Types/feed.type';
import UiChip from '@/Ui/UiChip.vue';

const props = defineProps<{ profile: Profile }>();

/** Stats: things about the account's activity. */
const stats = computed(() => {
    const p = props.profile;
    const out: { key: string; icon: string; label: string; value: string | number }[] = [];

    if (p.stars != null) out.push({ key: 'stars', icon: '⭐', label: 'Stars', value: p.stars });
    if (p.posts != null) out.push({ key: 'posts', icon: '📝', label: 'Posts', value: p.posts });
    if (p.followers != null) out.push({ key: 'followers', icon: '👥', label: 'Followers', value: p.followers });
    if (p.following != null) out.push({ key: 'following', icon: '➡️', label: 'Following', value: p.following });

    return out;
});

/** Contact / personal info. */
const contact = computed(() => {
    const p = props.profile;
    const out: { key: string; icon: string; label: string; value: string }[] = [];

    if (p.birthday) out.push({ key: 'birthday', icon: '🎂', label: 'Birthday', value: p.birthday });
    if (p.phone) out.push({ key: 'phone', icon: '📞', label: 'Phone', value: p.phone });
    if (p.email) out.push({ key: 'email', icon: '✉️', label: 'Email', value: p.email });

    return out;
});
</script>

<template>
    <div class="w-full rounded-lg border border-border bg-bg-elevated p-4 flex flex-col gap-4">
        <!-- Header: emoji + title -->
        <div class="flex flex-row items-center gap-2 min-w-0">
            <span
                class="grid h-10 w-fit px-1 shrink-0 place-items-center rounded-2xl border border-border bg-bg-sunken text-xl leading-none"
                aria-hidden="true">
                {{ profile.emoji ?? '😊' }}
            </span>
            <h2 class="text-base font-semibold text-text-h truncate">
                {{ profile.display_name || profile.username }}
            </h2>
        </div>

        <p v-if="profile.display_name" class="-mt-3 text-xs text-text-faint">@{{ profile.username }}</p>

        <p v-if="profile.powerline" class="text-sm font-medium text-text">
            {{ profile.powerline }}
        </p>

        <div v-if="profile.followedByMe || profile.starredByMe" class="flex flex-wrap gap-1">
            <UiChip v-if="profile.followedByMe" size="sm" variant="accent">Following</UiChip>
            <UiChip v-if="profile.starredByMe" size="sm" variant="soft">Starred</UiChip>
        </div>

        <!-- About -->
        <p v-if="profile.about" class="text-sm text-text-muted whitespace-pre-wrap wrap-break-word">
            {{ profile.about }}
        </p>

        <!-- Stats: grid of icon + value + label -->
        <div v-if="stats.length" class="grid grid-cols-2 gap-2">
            <div v-for="s in stats" :key="s.key"
                class="flex flex-col rounded-md border border-border bg-bg-sunken px-3 py-2">
                <span class="text-xs text-text-faint inline-flex items-center gap-1">
                    <span aria-hidden="true">{{ s.icon }}</span>
                    <span>{{ s.label }}</span>
                </span>
                <span class="text-base font-semibold text-text-h tabular-nums">
                    {{ s.value }}
                </span>
            </div>
        </div>

        <!-- Contact: definition-list style rows -->
        <dl v-if="contact.length" class="flex flex-col gap-1.5">
            <div
                v-for="c in contact"
                :key="c.key"
                class="flex flex-row items-baseline gap-2 text-sm"
            >
                <dt class="inline-flex items-center gap-1 text-text-faint shrink-0 w-24">
                    <span aria-hidden="true">{{ c.icon }}</span>
                    <span>{{ c.label }}</span>
                </dt>
                <dd class="text-text min-w-0 truncate">{{ c.value }}</dd>
            </div>
        </dl>
    </div>
</template>