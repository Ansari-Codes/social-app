<script setup lang="ts">
import { computed } from 'vue';

type Size = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
    /** Visible label text. Can also be provided via the default slot. */
    label?: string;
    /** Associates the label with a form control (id of the input). */
    for?: string;
    /** Show a red asterisk after the text. */
    required?: boolean;
    /** Optional hint rendered to the right, muted. */
    hint?: string;
    /** Visual size. */
    size?: Size;
    /** Muted / de-emphasized styling. */
    muted?: boolean;
    /** Uppercase, tracked-out "section label" style. */
    uppercase?: boolean;
}>(), {
    required: false,
    size: 'md',
    muted: false,
    uppercase: false,
});

const sizeClass = computed(() => ({
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
}[props.size]));

const classes = computed(() => [
    'inline-flex items-baseline gap-1 font-medium leading-none',
    sizeClass.value,
    props.muted ? 'text-text-muted' : 'text-text',
    props.uppercase && 'uppercase tracking-wider text-text-muted',
]);
</script>

<template>
    <label :for="for" :class="classes">
        <span>
            <slot>{{ label }}</slot>
        </span>

        <span v-if="required" class="text-accent" aria-hidden="true">*</span>

        <span v-if="hint" class="ml-1 text-text-faint font-normal">
            {{ hint }}
        </span>
    </label>
</template>