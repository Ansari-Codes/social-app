<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'default' | 'accent' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
type Size = 'sm' | 'md';

const props = withDefaults(defineProps<{
    /** Color variant. */
    variant?: Variant;
    /** Size. */
    size?: Size;
    /** Show a leading colored dot. */
    dot?: boolean;
    /** Pill (rounded-full) vs rounded corners. */
    pill?: boolean;
    /** Uppercase, tracked-out micro label. */
    uppercase?: boolean;
}>(), {
    variant: 'default',
    size: 'md',
    dot: false,
    pill: true,
    uppercase: false,
});

const sizeClass = computed(() => ({
    sm: 'h-4 px-1.5 text-[10px] gap-1',
    md: 'h-5 px-2   text-xs   gap-1',
}[props.size]));

const variantClass = computed(() => ({
    default: 'bg-bg-sunken text-text-muted border border-border',
    accent:  'bg-accent-bg text-accent border border-accent-border',
    success: 'bg-success/10 text-success border border-success/30',
    warning: 'bg-warning/10 text-warning border border-warning/30',
    danger:  'bg-danger/10 text-danger border border-danger/30',
    info:    'bg-info/10 text-info border border-info/30',
    outline: 'bg-transparent text-text border border-border-strong',
}[props.variant]));

const dotColorClass = computed(() => ({
    default: 'bg-text-muted',
    accent:  'bg-accent',
    success: 'bg-success',
    warning: 'bg-warning',
    danger:  'bg-danger',
    info:    'bg-info',
    outline: 'bg-text',
}[props.variant]));

const classes = computed(() => [
    'inline-flex items-center justify-center font-medium whitespace-nowrap align-middle',
    props.pill ? 'rounded-full' : 'rounded-sm',
    props.uppercase && 'uppercase tracking-wider',
    sizeClass.value,
    variantClass.value,
]);
</script>

<template>
    <span :class="classes">
        <span
            v-if="dot"
            class="w-1.5 h-1.5 rounded-full flex-shrink-0"
            :class="dotColorClass"
            aria-hidden="true"
        />
        <slot />
    </span>
</template>