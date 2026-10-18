<script setup lang="ts">
import { computed, useAttrs } from 'vue';

type Variant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'soft';
type Size = 'sm' | 'md' | 'lg' | 'icon';
type Type = 'button' | 'submit' | 'reset';

const props = withDefaults(defineProps<{
    variant?: Variant;
    size?: Size;
    /** Native button type — defaults to "button" to avoid accidental form submits. */
    type?: Type;
    /** Show a spinner and disable interaction. */
    loading?: boolean;
    disabled?: boolean;
    /** Stretch to container width. */
    block?: boolean;
    /** Render as an <a> when an href is provided. */
    href?: string;
    /** Optional target for anchor mode. */
    target?: string;
}>(), {
    variant: 'primary',
    size: 'md',
    type: 'button',
    loading: false,
    disabled: false,
    block: false,
});

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

/* ── Size ─────────────────────────────────────────────────────────────── */
const sizeClass = computed(() => ({
    sm:   'h-8  px-3   text-xs  gap-1.5 rounded-md',
    md:   'h-10 px-4   text-sm  gap-2   rounded-md',
    lg:   'h-12 px-6   text-base gap-2  rounded-lg',
    icon: 'h-10 w-10   p-0     text-sm  gap-0  rounded-full',
}[props.size]));

/* ── Variant ──────────────────────────────────────────────────────────── */
const variantClass = computed(() => ({
    primary:
        'bg-accent text-accent-fg ' +
        'hover:bg-accent-hover active:bg-accent-active ' +
        'focus-visible:ring-2 focus-visible:ring-accent/40',
    secondary:
        'bg-bg-elevated text-text-h border border-border ' +
        'hover:bg-bg-hover active:bg-bg-active ' +
        'focus-visible:ring-2 focus-visible:ring-accent/30',
    outline:
        'bg-transparent text-text border border-border-strong ' +
        'hover:bg-bg-hover active:bg-bg-active ' +
        'focus-visible:ring-2 focus-visible:ring-accent/30',
    ghost:
        'bg-transparent text-text-muted ' +
        'hover:bg-bg-hover hover:text-text-h active:bg-bg-active ' +
        'focus-visible:ring-2 focus-visible:ring-accent/30',
    soft:
        'bg-accent-bg text-accent border border-accent-border ' +
        'hover:bg-accent-soft active:bg-accent/15 ' +
        'focus-visible:ring-2 focus-visible:ring-accent/40',
    danger:
        'bg-danger text-white ' +
        'hover:brightness-110 active:brightness-95 ' +
        'focus-visible:ring-2 focus-visible:ring-danger/40',
}[props.variant]));

/* ── Composed classes ─────────────────────────────────────────────────── */
const classes = computed(() => [
    'inline-flex items-center justify-center select-none whitespace-nowrap',
    'font-semibold transition-colors duration-150',
    'outline-none disabled:opacity-50 disabled:pointer-events-none',
    sizeClass.value,
    variantClass.value,
    props.block && 'w-full',
]);

const isDisabled = computed(() => props.disabled || props.loading);
const tag = computed(() => (props.href ? 'a' : 'button'));
</script>

<template>
    <component
        :is="tag"
        v-bind="attrs"
        :class="classes"
        :type="!href ? type : undefined"
        :href="href"
        :target="target"
        :disabled="!href ? isDisabled : undefined"
        :aria-disabled="isDisabled || undefined"
        :aria-busy="loading || undefined"
    >
        <!-- Loading spinner (replaces leading slot) -->
        <svg
            v-if="loading"
            class="animate-spin"
            :class="size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
        >
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3" />
            <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
        </svg>

        <!-- Leading icon slot -->
        <slot v-else name="leading" />

        <!-- Default content -->
        <span v-if="!loading || $slots.default" class="truncate">
            <slot />
        </span>

        <!-- Trailing icon slot -->
        <slot name="trailing" />
    </component>
</template>