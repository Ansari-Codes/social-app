<script setup lang="ts">
import { computed, useAttrs } from 'vue';

type Variant = 'default' | 'muted' | 'accent' | 'inherit';
type Underline = 'none' | 'hover' | 'always';

const props = withDefaults(defineProps<{
    /** Link destination. */
    href?: string;
    /** Force external styling (opens in new tab, shows icon). Auto-detected from href when omitted. */
    external?: boolean;
    /** RouterLink or other component to render instead of <a>. */
    as?: string | object;
    /** Text color variant. */
    variant?: Variant;
    /** Underline behavior. */
    underline?: Underline;
    /** Show an external-link glyph after the text (auto for external). */
    showExternalIcon?: boolean;
    /** Disabled — removes href and pointer events. */
    disabled?: boolean;
    /** Small/medium/large text. */
    size?: 'sm' | 'md' | 'lg';
}>(), {
    external: undefined, // undefined = auto-detect
    variant: 'accent',
    underline: 'hover',
    showExternalIcon: undefined, // undefined = auto for external
    disabled: false,
    size: 'md',
});

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

/* ── Auto-detect external ─────────────────────────────────────────────── */
const isExternal = computed(() => {
    if (props.external !== undefined) return props.external;
    const h = props.href ?? '';
    return /^(https?:)?\/\//i.test(h) || h.startsWith('mailto:') || h.startsWith('tel:');
});

const showIcon = computed(() =>
    props.showExternalIcon !== undefined ? props.showExternalIcon : isExternal.value,
);

/* ── Variant + underline classes ─────────────────────────────────────── */
const variantClass = computed(() => ({
    default: 'text-text-h hover:text-accent',
    muted:   'text-text-muted hover:text-text-h',
    accent:  'text-accent hover:text-accent-hover',
    inherit: '',
}[props.variant]));

const underlineClass = computed(() => ({
    none:   'no-underline',
    hover:  'no-underline hover:underline underline-offset-2',
    always: 'underline underline-offset-2',
}[props.underline]));

const sizeClass = computed(() => ({
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
}[props.size]));

/* ── Composed ────────────────────────────────────────────────────────── */
const classes = computed(() => [
    'inline-flex items-center gap-1 font-medium transition-colors duration-150',
    'outline-none focus-visible:ring-2 focus-visible:ring-accent/40 rounded-sm',
    variantClass.value,
    underlineClass.value,
    sizeClass.value,
    props.disabled && 'opacity-50 pointer-events-none',
]);

const tag = computed(() => props.as ?? 'a');

const bindings = computed(() => ({
    ...attrs,
    ...(props.as ? { to: props.href } : { href: props.disabled ? undefined : props.href }),
    ...(isExternal.value && !props.as
        ? { target: '_blank', rel: 'noopener noreferrer' }
        : {}),
    'aria-disabled': props.disabled || undefined,
}));
</script>

<template>
    <component :is="tag" :class="classes" v-bind="bindings">
        <slot />
        <svg
            v-if="showIcon"
            viewBox="0 0 24 24"
            fill="none"
            class="w-3 h-3 opacity-70"
            aria-hidden="true"
        >
            <path
                d="M14 5h5v5M19 5l-8 8M10 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"
                stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round"
            />
        </svg>
    </component>
</template>