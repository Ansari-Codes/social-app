<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
    /** Visible label text. Can also be provided via the default slot. */
    label?: string;

    /** Associates the label with a form control (id of the input). */
    for?: string;

    /** Show a red asterisk after the text. */
    required?: boolean;

    /** Optional hint rendered to the right, muted. */
    subtitle?: string;

    /** Uppercase, tracked-out "section label" style. */
    uppercase?: boolean;
}>(), {
    required: false,
    uppercase: false,
});

const classes = computed(() => [
    'inline-flex items-baseline gap-1 font-medium leading-none',
    props.uppercase && 'uppercase tracking-wider text-text-muted',
]);
</script>

<template>
    <label :for="props.for" :class="classes">
        <span>
            <slot>{{ label }}</slot>
        </span>

        <span
            v-if="subtitle"
            class="ml-1 font-normal"
        >
            {{ subtitle }}
        </span>
    </label>
</template>
