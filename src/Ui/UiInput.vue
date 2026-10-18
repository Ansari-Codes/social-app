<script setup lang="ts">
import { computed, ref, useAttrs, useId } from 'vue';
import UiLabel from '@/Ui/UiLabel.vue';

type Size = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
    /** v-model value */
    modelValue?: string | number | null;
    /** Native input type */
    type?: string;
    /** Field label (rendered as <UiLabel>). */
    label?: string;
    /** Helper text shown below the input. */
    hint?: string;
    /** Error message. Overrides hint and switches the field to error styling. */
    error?: string;
    /** Placeholder text. */
    placeholder?: string;
    /** Marks the field as required (adds asterisk to label, aria-required). */
    required?: boolean;
    /** Disabled state. */
    disabled?: boolean;
    /** Read-only state. */
    readonly?: boolean;
    /** Visual size. */
    size?: Size;
    /** Render as a textarea. */
    textarea?: boolean;
    /** Textarea rows (only when textarea=true). */
    rows?: number;
    /** Stretch to container width (default true). */
    block?: boolean;
    /** Optional explicit id (otherwise auto-generated). */
    id?: string;
}>(), {
    type: 'text',
    size: 'md',
    textarea: false,
    rows: 4,
    block: true,
    required: false,
    disabled: false,
    readonly: false,
});

const emit = defineEmits<{
    'update:modelValue': [value: string | number | null];
    'blur': [event: FocusEvent];
    'focus': [event: FocusEvent];
}>();

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

const autoId = useId();
const inputId = computed(() => props.id ?? `input-${autoId}`);

const isTextarea = computed(() => props.textarea);
const hasError = computed(() => !!props.error);

/* ── Size classes ────────────────────────────────────────────────────── */
const sizeClass = computed(() => ({
    sm: 'h-8  px-2.5 text-xs  rounded-md',
    md: 'h-10 px-3   text-sm  rounded-md',
    lg: 'h-12 px-4   text-base rounded-lg',
}[props.size]));

const textareaSizeClass = computed(() => ({
    sm: 'px-2.5 py-1.5 text-xs  rounded-md',
    md: 'px-3   py-2   text-sm  rounded-md',
    lg: 'px-4   py-3   text-base rounded-lg',
}[props.size]));

/* ── Wrapper / field classes ─────────────────────────────────────────── */
const fieldClasses = computed(() => [
    'w-full bg-bg-sunken border outline-none transition-colors duration-150',
    'placeholder:text-text-faint',
    'disabled:opacity-60 disabled:cursor-not-allowed',
    'read-only:cursor-default',
    hasError.value
        ? 'border-danger focus:border-danger focus:ring-2 focus:ring-danger/25'
        : 'border-border hover:border-border-strong focus:border-accent focus:ring-2 focus:ring-accent/20',
    isTextarea.value ? textareaSizeClass.value : sizeClass.value,
    attrs.class, // allow caller to override
]);

/* Remove `class` from attrs so we don't double-apply it */
const passthroughAttrs = computed(() => {
    const { class: _c, ...rest } = attrs as Record<string, unknown>;
    return rest;
});

/* ── v-model plumbing ────────────────────────────────────────────────── */
const value = computed({
    get: () => props.modelValue ?? '',
    set: (v) => emit('update:modelValue', v),
});

/* ── Expose a way to focus programmatically ──────────────────────────── */
const el = ref<HTMLInputElement | HTMLTextAreaElement | null>(null);
defineExpose({
    focus: () => el.value?.focus(),
    blur: () => el.value?.blur(),
    el,
});
</script>

<template>
    <div :class="['flex flex-col gap-1.5', block && 'w-full']">
        <!-- Label -->
        <UiLabel
            v-if="label || $slots.label"
            :for="inputId"
            :required="required"
        >
            <slot name="label">{{ label }}</slot>
        </UiLabel>

        <!-- Field wrapper (for leading/trailing icons) -->
        <div class="relative flex items-center">
            <!-- Leading slot -->
            <span
                v-if="$slots.leading"
                class="pointer-events-none absolute left-3 flex items-center text-text-faint"
            >
                <slot name="leading" />
            </span>

            <!-- Input or textarea -->
            <textarea
                v-if="isTextarea"
                :id="inputId"
                ref="el"
                v-model="value"
                v-bind="passthroughAttrs"
                :rows="rows"
                :placeholder="placeholder"
                :required="required"
                :disabled="disabled"
                :readonly="readonly"
                :aria-invalid="hasError || undefined"
                :aria-describedby="(hint || error) ? `${inputId}-desc` : undefined"
                :class="[
                    fieldClasses,
                    'resize-none',
                    $slots.leading && 'pl-9',
                    $slots.trailing && 'pr-9',
                ]"
                @blur="emit('blur', $event)"
                @focus="emit('focus', $event)"
            />

            <input
                v-else
                :id="inputId"
                ref="el"
                v-model="value"
                v-bind="passthroughAttrs"
                :type="type"
                :placeholder="placeholder"
                :required="required"
                :disabled="disabled"
                :readonly="readonly"
                :aria-invalid="hasError || undefined"
                :aria-describedby="(hint || error) ? `${inputId}-desc` : undefined"
                :class="[
                    fieldClasses,
                    $slots.leading && 'pl-9',
                    $slots.trailing && 'pr-9',
                ]"
                @blur="emit('blur', $event)"
                @focus="emit('focus', $event)"
            />

            <!-- Trailing slot -->
            <span
                v-if="$slots.trailing"
                class="absolute right-3 flex items-center text-text-faint"
            >
                <slot name="trailing" />
            </span>
        </div>

        <!-- Hint / error -->
        <p
            v-if="error || hint"
            :id="`${inputId}-desc`"
            :class="[
                'text-xs',
                hasError ? 'text-danger' : 'text-text-faint',
            ]"
        >
            {{ error || hint }}
        </p>
    </div>
</template>