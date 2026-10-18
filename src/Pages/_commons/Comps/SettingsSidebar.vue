<script setup lang="ts">
import type { SettingsTab } from '../Types/settings.type';

interface SettingsTabItem {
    key: SettingsTab;
    label: string;
    icon: string;
    description?: string;
}

const props = defineProps<{
    tabs: readonly SettingsTabItem[];
    active: SettingsTab;
}>();

const emit = defineEmits<{
    (event: 'change', value: SettingsTab): void;
}>();
</script>

<template>
    <aside class="w-full shrink-0 md:w-64" aria-label="Settings navigation">
        <!-- Desktop Sidebar Menu -->
        <div class="rounded-2xl border border-border bg-bg-elevated p-2 shadow-card hidden md:block">
            <div class="px-3 py-2.5 mb-1 border-b border-border/80">
                <p class="text-[11px] font-bold uppercase tracking-wider text-text-muted">Preferences</p>
            </div>

            <nav class="space-y-1">
                <button
                    v-for="tab in props.tabs"
                    :key="tab.key"
                    type="button"
                    class="group flex w-full items-center justify-between rounded-xl px-3 py-3 text-left transition-all cursor-pointer"
                    :class="tab.key === props.active
                        ? 'bg-accent/10 text-accent font-semibold shadow-xs'
                        : 'text-text-muted hover:bg-bg-hover hover:text-text-h'"
                    @click="emit('change', tab.key)"
                >
                    <div class="flex items-center gap-3 min-w-0">
                        <span class="text-lg leading-none" aria-hidden="true">{{ tab.icon }}</span>
                        <div class="min-w-0">
                            <span class="block text-sm font-semibold truncate">{{ tab.label }}</span>
                            <span v-if="tab.description" class="block text-[11px] text-text-faint truncate">
                                {{ tab.description }}
                            </span>
                        </div>
                    </div>
                    <span
                        v-if="tab.key === props.active"
                        class="h-2 w-2 rounded-full bg-accent"
                        aria-hidden="true"
                    />
                </button>
            </nav>
        </div>

        <!-- Mobile Horizontal Tab Pills -->
        <div class="flex items-center gap-2 overflow-x-auto pb-1 md:hidden">
            <button
                v-for="tab in props.tabs"
                :key="tab.key"
                type="button"
                class="flex items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold whitespace-nowrap transition-colors"
                :class="tab.key === props.active
                    ? 'bg-accent text-accent-fg shadow-xs'
                    : 'bg-bg-elevated border border-border text-text hover:bg-bg-hover'"
                @click="emit('change', tab.key)"
            >
                <span aria-hidden="true">{{ tab.icon }}</span>
                <span>{{ tab.label }}</span>
            </button>
        </div>
    </aside>
</template>
