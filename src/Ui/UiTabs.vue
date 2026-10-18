<script setup lang="ts">
export interface UiTabOption {
  id: string;
  label: string;
  count?: number;
}

defineProps<{
  tabs: readonly UiTabOption[];
  modelValue: string;
  label: string;
}>();

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
}>();
</script>

<template>
  <div class="overflow-x-auto border-b border-border">
    <nav class="flex min-w-max items-stretch gap-1" role="tablist" :aria-label="label">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        :aria-selected="modelValue === tab.id"
        class="relative inline-flex min-h-10 items-center gap-1.5 px-4 text-sm font-medium transition-colors"
        :class="modelValue === tab.id ? 'text-accent' : 'text-text-muted hover:text-text'"
        @click="emit('update:modelValue', tab.id)"
      >
        <span>{{ tab.label }}</span>
        <span v-if="tab.count !== undefined" class="tabular-nums text-xs text-text-faint">
          {{ tab.count }}
        </span>
        <span v-if="modelValue === tab.id" class="absolute inset-x-2 bottom-0 h-0.5 bg-accent" aria-hidden="true" />
      </button>
    </nav>
  </div>
</template>
