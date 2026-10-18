<script setup lang="ts">
import { computed, useAttrs } from 'vue';

type Variant = 'default' | 'accent' | 'soft' | 'outline';
type Size = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
    variant?: Variant;
    size?: Size;
    /** Selected / active state — usually tied to a filter. */
    selected?: boolean;
    /** Show a dismiss (×) button. */
    dismissable?: boolean;
    /** Disabled — non-interactive, muted. */
    disabled?: boolean;
    /** Renders as a button; set false for a static pill. */
    clickable?: boolean;
    /** Pill (default) vs rounded corners. */
    pill?: boolean;
    /** Show a leading colored dot. */
    dot?: boolean;
    /** Accessible label for the dismiss button (fallback: "Remove"). */
    dismissLabel?: string;
}>(), {
    variant: 'default',
    size: 'md',
    selected: false,
    dismissable: false,
    disabled: false,
    clickable: true,
    pill: true,
    dot: false,
});

const emit = defineEmits<{
    click: [event: MouseEvent];
    dismiss: [];
}>();

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

const sizeClass = computed(() => ({
    sm: 'h-6 px-2   text-xs   gap-1',
    md: 'h-7 px-2.5 text-xs   gap-1.5',
    lg: 'h-8 px-3   text-sm   gap-2',
}[props.size]));

const variantClass = computed(() => {
    // Selected always wins for consistency across variants
    if (props.selected) {
        return 'bg-accent text-accent-fg border border-accent shadow-accent';
    }
    return {
        default: 'bg-bg-sunken text-text border border-border hover:bg-bg-hover hover:border-border-strong',
        accent: 'bg-accent-bg text-accent border border-accent-border hover:bg-accent-soft',
        soft: 'bg-bg-elevated text-text-muted border border-transparent hover:bg-bg-hover hover:text-text',
        outline: 'bg-transparent text-text border border-border-strong hover:bg-bg-hover',
    }[props.variant];
});

const dotColorClass = computed(() => {
    if (props.selected) return 'bg-accent-fg';
    return {
        default: 'bg-text-muted',
        accent: 'bg-accent',
        soft: 'bg-text-muted',
        outline: 'bg-text',
    }[props.variant];
});

const tag = computed(() => (props.clickable ? 'button' : 'span'));

const classes = computed(() => [
    'inline-flex items-center justify-center font-medium whitespace-nowrap',
    'transition-colors duration-150 outline-none select-none',
    'focus-visible:ring-2 focus-visible:ring-accent/40',
    props.pill ? 'rounded-full' : 'rounded-md',
    sizeClass.value,
    variantClass.value,
    props.disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
    props.clickable && !props.disabled && 'cursor-pointer',
]);

function onClick(e: MouseEvent) {
    if (props.disabled) return;
    emit('click', e);
}

function onDismiss(e: MouseEvent) {
    e.stopPropagation();
    if (props.disabled) return;
    emit('dismiss');
}
</script>

<template>
    <component :is="tag" v-bind="attrs" :type="clickable ? 'button' : undefined"
        :disabled="clickable && disabled ? true : undefined" :aria-pressed="clickable && $attrs['aria-pressed'] === undefined
            ? (selected || undefined)
            : $attrs['aria-pressed']" :class="classes" @click="onClick">
        <!-- Leading dot -->
        <span v-if="dot" class="w-1.5 h-1.5 rounded-full flex-shrink-0" :class="dotColorClass" aria-hidden="true" />

        <!-- Leading slot (avatar / icon) -->
        <slot name="leading" />

        <!-- Content -->
        <span class="truncate">
            <slot />
        </span>

        <!-- Trailing slot (custom content) -->
        <slot name="trailing" />

        <!-- Dismiss -->
        <button v-if="dismissable" type="button" :aria-label="dismissLabel ?? 'Remove'" class="flex-shrink-0 -mr-1 ml-0.5 grid place-items-center w-4 h-4 rounded-full
                   hover:bg-black/10 active:bg-black/20
                   dark:hover:bg-white/10 dark:active:bg-white/20
                   transition-colors" @click="onDismiss">
            <svg viewBox="0 0 24 24" fill="none" class="w-3 h-3">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
            </svg>
        </button>
    </component>
</template>