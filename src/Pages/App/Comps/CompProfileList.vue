<script setup lang="ts">
import type { Profile } from '../Types/feed.type';
import UiChip from '@/Ui/UiChip.vue';

const props = defineProps<{
    profiles: Profile[];
    /** 1 or 2 columns. Defaults to 1. */
    cols?: 1 | 2;
    emptyText?: string;
}>();

const emit = defineEmits<{ (e: 'open', profile: Profile): void }>();
</script>

<template>
    <div v-if="profiles.length" class="grid gap-2" :class="cols === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'">
        <div v-for="p in profiles" :key="p.id" :profile="p">
            <button type="button" class="w-full flex flex-row items-start gap-3 rounded-lg border border-border
                bg-bg-elevated p-3 text-left
                hover:bg-bg-hover transition-colors" @click="emit('open', p)">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl
                    border border-border bg-bg-sunken text-xl leading-none" aria-hidden="true">
                    {{ p.emoji ?? '😊' }}
                </span>

                <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                    <span class="text-sm font-semibold text-text-h truncate capitalize">
                        {{ p.display_name || p.username }}
                    </span>
                    <span v-if="p.display_name" class="text-xs text-text-faint truncate">@{{ p.username }}</span>
                    <p v-if="p.powerline" class="text-xs text-text-muted truncate">{{ p.powerline }}</p>
                    <p v-if="p.about" class="text-xs text-text-muted line-clamp-2">
                        {{ p.about }}
                    </p>
                    <div v-if="p.birthday || (p.isOwner && (p.email || p.phone))" class="flex flex-wrap gap-x-3 text-[11px] text-text-faint">
                        <span v-if="p.birthday">🎂 {{ p.birthday }}</span>
                        <span v-if="p.isOwner && p.email">✉️ {{ p.email }}</span>
                        <span v-if="p.isOwner && p.phone">📞 {{ p.phone }}</span>
                    </div>
                    <div v-if="p.followedByMe || p.starredByMe" class="flex flex-wrap gap-1 pt-1">
                        <UiChip v-if="p.followedByMe" size="sm" variant="accent">Following</UiChip>
                        <UiChip v-if="p.starredByMe" size="sm" variant="soft">Starred</UiChip>
                    </div>
                </div>
            </button>

        </div>
    </div>

    <p v-else class="text-sm text-text-muted py-4 text-center">
        {{ emptyText ?? 'Nothing here yet.' }}
    </p>
</template>