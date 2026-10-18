<script setup lang="ts">
import { computed } from 'vue';
import UiButton from '@/Ui/UiButton.vue';
import UiChip from '@/Ui/UiChip.vue';
import UiOptions from '@/Ui/UiOptions.vue';
import type { Profile } from '../../Types/feed.type';

const props = defineProps<{
    profile: Profile;
    following?: boolean;
    starred?: boolean;
    disabled?: boolean;
}>();

const emit = defineEmits<{
    (e: 'follow'): void;
    (e: 'star'): void;
    (e: 'react', reaction: string): void;
}>();

const reactionPalette = ['👍', '❤️', '😂', '😮', '😢', '🔥'];
const profileReactions = computed(() => Object.entries(props.profile.reactions ?? {}));

/* ── Powerline ───────────────────────────────────────────────────── *
 * A single text line. Wraps the banner, or fills it if long.
 * ────────────────────────────────────────────────────────────────── */
const powerline = computed(() => (props.profile.powerline ?? '').trim());
const hasPowerline = computed(() => powerline.value.length > 0);

/** Roughly long enough to fill the banner. Tuned by eye. */
const powerlineIsLong = computed(() => powerline.value.length > 24);

const bannerStyle = computed(() => {
    const s: Record<string, string> = {};
    if (props.profile.bannerColor) s.backgroundColor = props.profile.bannerColor;
    return s;
});

/* ── Stats as badges ────────────────────────────────────────────── */
const badges = computed(() => {
    const p = props.profile;
    const out: { key: string; icon: string; label: string; value: number }[] = [];

    if (p.posts != null) out.push({ key: 'posts', icon: '📝', label: 'Posts', value: p.posts });
    if (p.stars != null) out.push({ key: 'stars', icon: '⭐', label: 'Stars', value: p.stars });
    if (p.followers != null) out.push({ key: 'followers', icon: '👥', label: 'Followers', value: p.followers });
    if (p.following != null) out.push({ key: 'following', icon: '👤', label: 'Following', value: p.following });

    return out;
});
</script>

<template>
    <header class="rounded-lg overflow-hidden border border-border bg-bg-elevated">

        <!-- ── Banner ──────────────────────────────────────────────── -->
        <div class="relative w-full" :class="hasPowerline ? 'h-28 lg:h-36' : 'h-20 lg:h-24'" :style="bannerStyle">
            <!-- Fallback gradient when no bannerColor -->
            <div v-if="!profile.bannerColor" class="absolute inset-0 bg-linear-to-br from-accent to-accent-soft"
                aria-hidden="true" />

            <!-- Powerline: single text line, vertically centered -->
            <div v-if="hasPowerline" class="absolute inset-0 flex items-center px-4 lg:px-6
                        overflow-hidden" :class="powerlineIsLong ? 'justify-start' : 'justify-center'">
                <p class="text-2xl lg:text-3xl leading-none tracking-wide
                            whitespace-nowrap truncate select-none opacity-90" :title="powerline">
                    {{ powerline }}
                </p>
            </div>

            <!-- Bottom fade so the identity row blends in -->
            <div class="absolute inset-x-0 bottom-0 h-12 bg-linear-to-t
                        from-bg-elevated to-transparent pointer-events-none" aria-hidden="true" />
        </div>

        <!-- ── Identity row ────────────────────────────────────────── -->
        <!-- padding-top clears the banner; the avatar floats above it -->
        <div class="relative px-4 lg:px-6 flex flex-row items-end gap-3">
            <!-- Avatar: pulled up over the banner -->
            <span class="inline-flex flex-row items-center gap-2 p-3 h-fit w-fit shrink-0
                    rounded-2xl border border-bg-elevated bg-bg-sunken 
                    text-4xl leading-none shadow-card
                    -mt-10 lg:-mt-12">
                <span aria-hidden="true">{{ profile.emoji ?? '😊' }}</span>
                <span class="min-w-0">
                    <h1 class="font-bold text-text capitalize truncate">
                        {{ profile.display_name || profile.username }}
                    </h1>
                    <p class="text-xs font-normal text-text-muted truncate">
                        @{{ profile.username }}
                    </p>
                </span>
            </span>
            <div class="flex-1 min-w-0 pb-1 flex flex-row items-end justify-between gap-3 flex-wrap">
                <div />
                <div class="flex flex-row items-center gap-2 shrink-0">
                    <UiButton v-if="!profile.isOwner" variant="primary" size="sm" :disabled="disabled" @click="emit('follow')">
                        {{ following ? 'Following' : '＋ Follow' }}
                    </UiButton>
                    <UiButton v-if="!profile.isOwner" variant="ghost" size="sm" :disabled="disabled" @click="emit('star')">
                        {{ starred ? '★ Starred' : '☆ Star' }}
                    </UiButton>
                    <UiChip v-for="[reaction, count] in profileReactions" :key="reaction" size="sm" :variant="profile.myReactions?.includes(reaction) ? 'accent' : 'default'">
                        {{ reaction }} {{ count }}
                    </UiChip>
                    <UiOptions
                        :options="reactionPalette.map((reaction) => ({ value: reaction, label: reaction, icon: reaction }))"
                        size="sm"
                        label="React to profile"
                        @select="(reaction) => emit('react', String(reaction))"
                    >
                        <template #trigger>+</template>
                    </UiOptions>
                </div>
            </div>
        </div>

        <!-- ── Stats as badges ─────────────────────────────────────── -->
        <div class="px-4 lg:px-6 mt-3 flex flex-row flex-wrap gap-1.5">
            <span v-for="b in badges" :key="b.key" class="inline-flex items-center gap-1.5 rounded-full
                       border border-border bg-bg-sunken px-2.5 py-1 text-xs">
                <span aria-hidden="true">{{ b.icon }}</span>
                <span class="text-text-muted">{{ b.label }}</span>
                <span class="text-text-h font-semibold tabular-nums">{{ b.value }}</span>
            </span>
        </div>

        <!-- ── About + birthday ────────────────────────────────────── -->
        <div v-if="profile.about || profile.birthday || profile.email || profile.phone" class="px-4 lg:px-6 mt-3 pb-4 flex flex-col gap-2">
            <p v-if="profile.about" class="text-sm text-text whitespace-pre-wrap wrap-break-word max-w-3xl">
                {{ profile.about }}
            </p>

            <p v-if="profile.birthday" class="text-xs text-text-muted inline-flex items-center gap-1.5">
                <span aria-hidden="true">🎂</span>
                <span>{{ profile.birthday }}</span>
            </p>

            <div v-if="profile.email || profile.phone" class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
                <a v-if="profile.email" :href="`mailto:${profile.email}`" class="hover:text-accent">✉️ {{ profile.email }}</a>
                <a v-if="profile.phone" :href="`tel:${profile.phone}`" class="hover:text-accent">📞 {{ profile.phone }}</a>
            </div>
        </div>
    </header>
</template>