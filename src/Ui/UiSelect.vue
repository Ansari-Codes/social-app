<script setup lang="ts">
import {
    ref, computed, watch, onBeforeUnmount, nextTick, useId,
} from 'vue';

/* ──────────────────────────────────────────────────────────────────── *
 * Types
 * ──────────────────────────────────────────────────────────────────── */
export interface SelectOption {
    value: string | number;
    label: string;
    disabled?: boolean;
    /** Optional group heading — consecutive options with the same group render together. */
    group?: string;
}

type Size = 'sm' | 'md' | 'lg';

/* ──────────────────────────────────────────────────────────────────── *
 * Props / emits
 * ──────────────────────────────────────────────────────────────────── */
const props = withDefaults(defineProps<{
    /** Single value (string/number) OR array of values when `multiple`. */
    modelValue?: string | number | Array<string | number> | null;
    options?: SelectOption[];
    /** Allow selecting multiple options. */
    multiple?: boolean;
    /** Show a text input to filter the options. */
    searchable?: boolean;
    /** Allow typing a value not present in `options` (single mode only). */
    allowCustom?: boolean;
    /** Placeholder shown when nothing selected. */
    placeholder?: string;
    /** Field label (uses UiLabel internally). */
    label?: string;
    /** Helper text under the field. */
    hint?: string;
    /** Error message. Overrides hint. */
    error?: string;
    /** Disabled. */
    disabled?: boolean;
    /** Visual size. */
    size?: Size;
    /** Text shown on multi-select when more than N selected (e.g. "2 selected"). */
    maxDisplayed?: number;
    /** Max panel height before scrolling (px). */
    maxHeight?: number;
    /** Auto-open on focus. */
    openOnFocus?: boolean;
    /** Native id for the trigger button (label association). */
    id?: string;
}>(), {
    modelValue: null,
    options: () => [],
    multiple: false,
    searchable: false,
    allowCustom: false,
    placeholder: 'Select…',
    maxDisplayed: 3,
    maxHeight: 280,
    openOnFocus: false,
    size: 'md',
    disabled: false,
});

const emit = defineEmits<{
    'update:modelValue': [value: string | number | Array<string | number> | null];
    'change': [value: string | number | Array<string | number> | null];
    'open': [];
    'close': [];
}>();

const autoId = useId();
const fieldId = computed(() => props.id ?? `select-${autoId}`);

/* ──────────────────────────────────────────────────────────────────── *
 * Normalized selection state
 * ──────────────────────────────────────────────────────────────────── */
const selectedValues = computed<Array<string | number>>(() => {
    const v = props.modelValue;
    if (v == null) return [];
    return Array.isArray(v) ? v : [v];
});

const selectedOptions = computed(() =>
    selectedValues.value.map(
        (v) => props.options.find((o) => o.value === v)
            ?? { value: v, label: String(v) }, // custom value fallback
    ),
);

const isSelected = (v: string | number) => selectedValues.value.includes(v);

/* ──────────────────────────────────────────────────────────────────── *
 * Display text on the trigger
 * ──────────────────────────────────────────────────────────────────── */
const triggerLabel = computed(() => {
    const sel = selectedOptions.value;
    if (sel.length === 0) return props.placeholder;

    if (props.multiple) {
        if (sel.length <= props.maxDisplayed) {
            return sel.map((o) => o.label).join(', ');
        }
        return `${sel.length} selected`;
    }
    return sel[0].label;
});

const hasValue = computed(() => selectedValues.value.length > 0);

/* ──────────────────────────────────────────────────────────────────── *
 * Open state
 * ──────────────────────────────────────────────────────────────────── */
const open = ref(false);
const query = ref('');
const inputEl = ref<HTMLInputElement | null>(null);

function toggleOpen() {
    if (props.disabled) return;
    open.value = !open.value;
}
function close() {
    if (!open.value) return;
    open.value = false;
    emit('close');
}
function openPanel() {
    if (props.disabled || open.value) return;
    open.value = true;
    emit('open');
    position();
    nextTick(() => {
        if (props.searchable) inputEl.value?.focus();
    });
}

/* ──────────────────────────────────────────────────────────────────── *
 * Selection logic
 * ──────────────────────────────────────────────────────────────────── */
function select(value: string | number) {
    const opt = props.options.find((o) => o.value === value);
    if (opt?.disabled) return;

    if (props.multiple) {
        const current = [...selectedValues.value];
        const idx = current.indexOf(value);
        if (idx === -1) current.push(value);
        else current.splice(idx, 1);
        emit('update:modelValue', current);
        emit('change', current);
        // Keep the panel open for multi
    } else {
        emit('update:modelValue', value);
        emit('change', value);
        close();
    }
    query.value = '';
}

function clearAll(e?: Event) {
    e?.stopPropagation();
    emit('update:modelValue', props.multiple ? [] : null);
    emit('change', props.multiple ? [] : null);
}

function commitCustom() {
    const q = query.value.trim();
    if (!q || !props.allowCustom) return;
    // Custom values only apply in single mode
    emit('update:modelValue', q);
    emit('change', q);
    query.value = '';
    close();
}

/* ──────────────────────────────────────────────────────────────────── *
 * Filtering / grouping
 * ──────────────────────────────────────────────────────────────────── */
const filteredOptions = computed<SelectOption[]>(() => {
    if (!query.value) return props.options;
    const q = query.value.toLowerCase();
    return props.options.filter((o) => o.label.toLowerCase().includes(q));
});

const groupedOptions = computed(() => {
    const groups: Array<{ name: string | null; items: SelectOption[] }> = [];
    for (const opt of filteredOptions.value) {
        const name = opt.group ?? null;
        const last = groups[groups.length - 1];
        if (last && last.name === name) last.items.push(opt);
        else groups.push({ name, items: [opt] });
    }
    return groups;
});

const showCustomRow = computed(() => {
    if (!props.allowCustom || props.multiple) return false;
    const q = query.value.trim();
    if (!q) return false;
    return !filteredOptions.value.some(
        (o) => o.label.toLowerCase() === q.toLowerCase(),
    );
});

/* ──────────────────────────────────────────────────────────────────── *
 * Keyboard nav
 * ──────────────────────────────────────────────────────────────────── */
const activeIndex = ref(0);

watch([open, filteredOptions], () => {
    if (open.value && filteredOptions.value.length) activeIndex.value = 0;
});

function onTriggerKeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openPanel();
    }
}

function onPanelKeydown(e: KeyboardEvent) {
    if (!open.value) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (filteredOptions.value.length) {
            activeIndex.value = (activeIndex.value + 1) % filteredOptions.value.length;
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (filteredOptions.value.length) {
            activeIndex.value =
                (activeIndex.value - 1 + filteredOptions.value.length)
                % filteredOptions.value.length;
        }
    } else if (e.key === 'Enter') {
        e.preventDefault();
        const opt = filteredOptions.value[activeIndex.value];
        if (opt) select(opt.value);
        else if (showCustomRow.value) commitCustom();
    } else if (e.key === 'Escape') {
        e.preventDefault();
        close();
    } else if (e.key === 'Backspace' && props.multiple && !query.value && selectedValues.value.length) {
        // Quick-remove last chip
        const last = selectedValues.value[selectedValues.value.length - 1];
        select(last);
    }
}

/* ──────────────────────────────────────────────────────────────────── *
 * Positioning (fixed in viewport — bypasses overflow: hidden parents)
 * ──────────────────────────────────────────────────────────────────── */
const trigger = ref<HTMLElement | null>(null);
const panel = ref<HTMLElement | null>(null);
const panelStyle = ref<Record<string, string>>({});

function computePosition() {
    const t = trigger.value;
    const p = panel.value;
    if (!t || !p) return;

    const r = t.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;

    const panelH = p.offsetHeight;
    const spaceBelow = window.innerHeight - r.bottom;
    const spaceAbove = r.top;

    const openUp = spaceBelow < panelH + 8 && spaceAbove > spaceBelow;

    const style: Record<string, string> = {
        left: `${r.left}px`,
        width: `${r.width}px`,
    };

    if (openUp) {
        style.top = `${r.top - 6}px`;
        style.transform = 'translateY(-100%)';
    } else {
        style.top = `${r.bottom + 6}px`;
    }

    panelStyle.value = style;
}

function position() {
    nextTick(() => {
        requestAnimationFrame(() => {
            requestAnimationFrame(computePosition);
        });
    });
}

watch(panel, (el) => {
    if (el) position();
});

/* ──────────────────────────────────────────────────────────────────── *
 * Outside click / escape / scroll / resize
 * ──────────────────────────────────────────────────────────────────── */
function onDocPointerDown(e: PointerEvent) {
    const target = e.target as Node;
    if (trigger.value?.contains(target)) return;
    if (panel.value?.contains(target)) return;
    close();
}

function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
}

function onScrollOrResize() {
    if (open.value) computePosition();
}

watch(open, (isOpen) => {
    if (isOpen) {
        position();
        document.addEventListener('pointerdown', onDocPointerDown);
        document.addEventListener('keydown', onKeydown);
        window.addEventListener('scroll', onScrollOrResize, true);
        window.addEventListener('resize', onScrollOrResize);
    } else {
        query.value = '';
        document.removeEventListener('pointerdown', onDocPointerDown);
        document.removeEventListener('keydown', onKeydown);
        window.removeEventListener('scroll', onScrollOrResize, true);
        window.removeEventListener('resize', onScrollOrResize);
    }
});

onBeforeUnmount(() => {
    document.removeEventListener('pointerdown', onDocPointerDown);
    document.removeEventListener('keydown', onKeydown);
    window.removeEventListener('scroll', onScrollOrResize, true);
    window.removeEventListener('resize', onScrollOrResize);
});

/* ──────────────────────────────────────────────────────────────────── *
 * Size classes
 * ──────────────────────────────────────────────────────────────────── */
const sizeClass = computed(() => ({
    sm: 'min-h-8  px-2.5 text-xs  rounded-md',
    md: 'min-h-10 px-3   text-sm  rounded-md',
    lg: 'min-h-12 px-4   text-base rounded-lg',
}[props.size]));

defineExpose({ open: openPanel, close, toggle: toggleOpen });
</script>

<template>
    <div class="flex flex-col gap-1.5 w-full">
        <!-- Label -->
        <label
            v-if="label"
            :for="fieldId"
            class="text-sm font-medium text-text inline-flex items-baseline gap-1"
        >
            <span>{{ label }}</span>
        </label>

        <!-- Trigger -->
        <div
            ref="trigger"
            :id="fieldId"
            role="combobox"
            :aria-expanded="open"
            :aria-haspopup="'listbox'"
            :aria-disabled="disabled || undefined"
            tabindex="0"
            :class="[
                'relative flex items-center gap-2 cursor-pointer outline-none',
                'bg-bg-sunken border transition-colors duration-150',
                'focus-visible:ring-2 focus-visible:ring-accent/30',
                error
                    ? 'border-danger focus-visible:ring-danger/30'
                    : open
                        ? 'border-accent ring-2 ring-accent/20'
                        : 'border-border hover:border-border-strong',
                disabled && 'opacity-60 cursor-not-allowed',
                sizeClass,
            ]"
            @click="toggleOpen"
            @keydown="onTriggerKeydown"
        >
            <!-- Multi chips -->
            <div v-if="multiple && hasValue" class="flex flex-wrap items-center gap-1 py-1 min-w-0 flex-1">
                <template v-for="opt in selectedOptions.slice(0, maxDisplayed)" :key="opt.value">
                    <span
                        class="inline-flex items-center gap-1 bg-accent-bg text-accent border border-accent-border
                               rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
                    >
                        {{ opt.label }}
                        <button
                            type="button"
                            class="hover:text-accent-hover leading-none"
                            :aria-label="`Remove ${opt.label}`"
                            @click.stop="select(opt.value)"
                        >×</button>
                    </span>
                </template>
                <span
                    v-if="selectedValues.length > maxDisplayed"
                    class="text-xs text-text-muted"
                >
                    +{{ selectedValues.length - maxDisplayed }}
                </span>
            </div>

            <!-- Single / placeholder -->
            <span
                v-else
                :class="[
                    'flex-1 truncate',
                    hasValue ? 'text-text' : 'text-text-faint',
                ]"
            >
                {{ triggerLabel }}
            </span>

            <!-- Clear (only when has value and not disabled) -->
            <button
                v-if="hasValue && !disabled"
                type="button"
                class="text-text-faint hover:text-text-h leading-none px-0.5"
                aria-label="Clear selection"
                @click.stop="clearAll"
            >×</button>

            <!-- Chevron -->
            <svg
                viewBox="0 0 24 24"
                fill="none"
                class="w-4 h-4 flex-shrink-0 text-text-faint transition-transform duration-150"
                :class="open && 'rotate-180'"
                aria-hidden="true"
            >
                <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2"
                      stroke-linecap="round" stroke-linejoin="round" />
            </svg>
        </div>

        <!-- Hint / error -->
        <p
            v-if="error || hint"
            class="text-xs"
            :class="error ? 'text-danger' : 'text-text-faint'"
        >
            {{ error || hint }}
        </p>

        <!-- Panel -->
        <Teleport to="body">
            <Transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-1"
            >
                <div
                    v-if="open"
                    ref="panel"
                    role="listbox"
                    :aria-multiselectable="multiple || undefined"
                    :style="[panelStyle, { maxHeight: maxHeight + 'px' }]"
                    class="ui-select-panel"
                    @keydown="onPanelKeydown"
                    tabindex="-1"
                >
                    <!-- Search / custom input -->
                    <div v-if="searchable || allowCustom" class="p-2 border-b border-border">
                        <input
                            ref="inputEl"
                            v-model="query"
                            type="text"
                            :placeholder="allowCustom ? 'Search or type a value…' : 'Search…'"
                            class="w-full bg-bg border border-border rounded-md px-2.5 py-1.5 text-sm
                                   placeholder:text-text-faint outline-none
                                   focus:border-accent focus:ring-2 focus:ring-accent/20"
                            @keydown="onPanelKeydown"
                        />
                    </div>

                    <!-- Options -->
                    <div class="overflow-y-auto py-1" :style="{ maxHeight: (maxHeight - (searchable || allowCustom ? 52 : 0)) + 'px' }">
                        <template v-for="(group, gi) in groupedOptions" :key="gi">
                            <p
                                v-if="group.name"
                                class="px-3 pt-2 pb-1 text-[10px] uppercase tracking-wider text-text-faint font-semibold"
                            >
                                {{ group.name }}
                            </p>

                            <button
                                v-for="opt in group.items"
                                :key="opt.value"
                                type="button"
                                role="option"
                                :aria-selected="isSelected(opt.value)"
                                :disabled="opt.disabled"
                                :class="[
                                    'w-full flex items-center gap-2 px-3 py-1.5 text-left text-sm outline-none',
                                    'transition-colors duration-75',
                                    opt.disabled
                                        ? 'opacity-50 cursor-not-allowed'
                                        : 'cursor-pointer hover:bg-bg-hover',
                                    isSelected(opt.value) && 'text-accent font-medium',
                                    !opt.disabled
                                        && filteredOptions[activeIndex] === opt
                                        && 'bg-bg-hover',
                                ]"
                                @click="select(opt.value)"
                                @mouseenter="activeIndex = filteredOptions.indexOf(opt)"
                            >
                                <!-- Checkmark for selected -->
                                <span class="w-4 flex-shrink-0">
                                    <svg
                                        v-if="isSelected(opt.value)"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        class="w-4 h-4"
                                    >
                                        <path d="M20 6L9 17l-5-5"
                                              stroke="currentColor" stroke-width="2"
                                              stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span class="flex-1 truncate">{{ opt.label }}</span>
                            </button>
                        </template>

                        <!-- Custom value row -->
                        <button
                            v-if="showCustomRow"
                            type="button"
                            class="w-full flex items-center gap-2 px-3 py-1.5 text-left text-sm text-accent hover:bg-bg-hover"
                            @click="commitCustom"
                        >
                            <span class="w-4 flex-shrink-0">+</span>
                            <span class="flex-1 truncate">
                                Use "<span class="font-medium">{{ query.trim() }}</span>"
                            </span>
                        </button>

                        <!-- Empty state -->
                        <p
                            v-if="!filteredOptions.length && !showCustomRow"
                            class="px-3 py-6 text-center text-xs text-text-faint"
                        >
                            No options
                        </p>
                    </div>
                </div>
            </Transition>
        </Teleport>
    </div>
</template>

<style>
/*
 * NOT scoped — panel is teleported to <body>, so scoped styles won't reach it.
 */
.ui-select-panel {
    position: fixed;
    z-index: 9999;
    min-width: 8rem;
    border-radius: 0.75rem;
    font-size: 0.875rem;
    line-height: 1.25rem;
    background: var(--color-bg-elevated);
    color: var(--color-text);
    border: 1px solid var(--color-border);
    box-shadow:
        0 0 0 1px var(--color-border),
        0 8px 24px -6px rgba(0, 0, 0, 0.18),
        0 2px 6px -2px rgba(0, 0, 0, 0.10);
    overflow: hidden;
    transform-origin: top center;
}

@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) .ui-select-panel {
        border-color: var(--color-border-strong);
        box-shadow:
            0 0 0 1px var(--color-border-strong),
            0 12px 32px -6px rgba(0, 0, 0, 0.7),
            0 4px 10px -2px rgba(0, 0, 0, 0.5);
    }
}
:root[data-theme="dark"] .ui-select-panel {
    border-color: var(--color-border-strong);
    box-shadow:
        0 0 0 1px var(--color-border-strong),
        0 12px 32px -6px rgba(0, 0, 0, 0.7),
        0 4px 10px -2px rgba(0, 0, 0, 0.5);
}
</style>