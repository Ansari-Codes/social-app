<script setup lang="ts">
import { computed } from 'vue';
import UiSection from '@/Ui/UiSection.vue';
import UiChip from '@/Ui/UiChip.vue';
import { useTheme, type Theme } from '@/Core/composables/useTheme';

const { theme, setTheme, resolvedTheme } = useTheme();

const options: Array<{
  value: Theme;
  label: string;
  description: string;
  icon: string;
  previewClass: string;
}> = [
  {
    value: 'auto',
    label: 'System Sync',
    description: 'Automatically adjust based on your operating system preferences',
    icon: '☼',
    previewClass: 'bg-linear-to-r from-slate-100 to-slate-900',
  },
  {
    value: 'light',
    label: 'Clean Light',
    description: 'Crisp bright backgrounds with high readability and soft borders',
    icon: '☀️',
    previewClass: 'bg-slate-50 border border-slate-200',
  },
  {
    value: 'dark',
    label: 'Obsidian Dark',
    description: 'Deep contrast dark theme designed for low-light environments and focus',
    icon: '🌙',
    previewClass: 'bg-zinc-950 border border-zinc-800',
  },
];

const currentLabel = computed(
  () => options.find((option) => option.value === theme.value)?.label ?? 'System Sync',
);
</script>

<template>
  <UiSection
    title="Appearance & Color Theme"
    description="Customize how SilenceBook looks on your screen across all devices"
    bordered
    shadow
    radius="xl"
    padding="lg"
  >
    <!-- Current Mode Capsule -->
    <div class="mb-5 flex items-center justify-between rounded-xl border border-border bg-bg-sunken/60 p-3 text-xs">
      <div class="flex items-center gap-2">
        <span class="text-text-muted">Active Preference:</span>
        <strong class="font-bold text-text-h">{{ currentLabel }}</strong>
      </div>
      <UiChip size="sm" variant="accent" :clickable="false">
        Resolved: {{ resolvedTheme }}
      </UiChip>
    </div>

    <!-- Theme Cards Selection -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="group relative flex flex-col justify-between overflow-hidden rounded-2xl border p-4 text-left transition-all hover:scale-[1.02] cursor-pointer"
        :class="theme === option.value
          ? 'border-accent bg-accent/5 ring-2 ring-accent/30 shadow-card'
          : 'border-border bg-bg hover:border-border-strong hover:bg-bg-hover'"
        @click="setTheme(option.value)"
      >
        <!-- Mockup Preview Bar -->
        <div
          class="h-16 w-full rounded-xl mb-3 flex items-center justify-center p-2 shadow-xs transition-transform group-hover:scale-105"
          :class="option.previewClass"
        >
          <div class="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg bg-bg/80 border border-border/40 backdrop-blur-xs">
            <span class="h-2 w-2 rounded-full bg-accent" />
            <div class="h-1.5 w-12 rounded-full bg-border" />
          </div>
        </div>

        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-base" aria-hidden="true">{{ option.icon }}</span>
              <span class="text-sm font-bold text-text-h">{{ option.label }}</span>
            </div>
            <p class="mt-1 text-[11px] leading-relaxed text-text-muted">
              {{ option.description }}
            </p>
          </div>
          <span
            v-if="theme === option.value"
            class="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-accent font-bold text-[11px] text-accent-fg"
            aria-hidden="true"
          >
            ✓
          </span>
        </div>
      </button>
    </div>
  </UiSection>
</template>
