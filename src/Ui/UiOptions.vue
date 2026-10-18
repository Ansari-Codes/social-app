<script setup lang="ts">
import {
    ref, computed, watch, onBeforeUnmount, useId, nextTick,
} from 'vue';

/* ──────────────────────────────────────────────────────────────────── *
 * Types
 * ──────────────────────────────────────────────────────────────────── */
export interface MenuOption {
    /** Stable id emitted on select. */
    value: string | number;
    label: string;
    /** Emoji shown before the label, e.g. "✏️". */
    icon?: string;
    disabled?: boolean;
    /** Optional group heading — consecutive options with the same group render together. */
    group?: string;
    /** Render in the danger color (e.g. "Delete"). */
    danger?: boolean;
    /** Optional keyboard hint shown on the right (e.g. "⌘K"). */
    shortcut?: string;
}

type Size = 'sm' | 'md' | 'lg';
type Align = 'start' | 'end';

/* ──────────────────────────────────────────────────────────────────── *
 * Props / emits
 * ──────────────────────────────────────────────────────────────────── */
const props = withDefaults(defineProps<{
    options?: MenuOption[];
    /** Visual size of the trigger icon button. */
    size?: Size;
    /** Horizontal alignment of the panel relative to the trigger. */
    align?: Align;
    /** Disabled. */
    disabled?: boolean;
    /** Max panel height before scrolling (px). */
    maxHeight?: number;
    /** aria-label for the icon-only trigger. */
    label?: string;
    /** id for the trigger button (label association / testing). */
    id?: string;
    /** Custom trigger sizing, used when the trigger slot contains a chip. */
    triggerClass?: string;
}>(), {
    options: () => [],
    size: 'md',
    align: 'end',
    disabled: false,
    maxHeight: 280,
    label: 'More actions',
    triggerClass: '',
});

const emit = defineEmits<{
    /** Fired when the user picks an option. */
    select: [value: string | number, option: MenuOption];
    open: [];
    close: [];
}>();

const autoId = useId();
const fieldId = computed(() => props.id ?? `menu-${autoId}`);

/* ──────────────────────────────────────────────────────────────────── *
 * Open state
 * ──────────────────────────────────────────────────────────────────── */
const open = ref(false);

function toggleOpen() {
    if (props.disabled) return;
    open.value ? close() : openPanel();
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
}

/* ──────────────────────────────────────────────────────────────────── *
 * Selection — always closes, never mutates a displayed value
 * ──────────────────────────────────────────────────────────────────── */
function select(opt: MenuOption) {
    if (opt.disabled) return;
    emit('select', opt.value, opt);
    close();
}

/* ──────────────────────────────────────────────────────────────────── *
 * Grouping
 * ──────────────────────────────────────────────────────────────────── */
const groupedOptions = computed(() => {
    const groups: Array<{ name: string | null; items: MenuOption[] }> = [];
    for (const opt of props.options) {
        const name = opt.group ?? null;
        const last = groups[groups.length - 1];
        if (last && last.name === name) last.items.push(opt);
        else groups.push({ name, items: [opt] });
    }
    return groups;
});

/** Flat list for keyboard nav. */
const flatOptions = computed(() => groupedOptions.value.flatMap((g) => g.items));

/* ──────────────────────────────────────────────────────────────────── *
 * Keyboard nav
 * ──────────────────────────────────────────────────────────────────── */
const activeIndex = ref(0);

watch([open, flatOptions], () => {
    if (open.value && flatOptions.value.length) {
        const firstEnabled = flatOptions.value.findIndex((o) => !o.disabled);
        activeIndex.value = firstEnabled === -1 ? 0 : firstEnabled;
    }
});

function move(delta: number) {
    const list = flatOptions.value;
    if (!list.length) return;
    let i = activeIndex.value;
    for (let step = 0; step < list.length; step++) {
        i = (i + delta + list.length) % list.length;
        if (!list[i].disabled) break;
    }
    activeIndex.value = i;
}

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
        move(1);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        move(-1);
    } else if (e.key === 'Home') {
        e.preventDefault();
        activeIndex.value = 0;
    } else if (e.key === 'End') {
        e.preventDefault();
        activeIndex.value = flatOptions.value.length - 1;
    } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const opt = flatOptions.value[activeIndex.value];
        if (opt) select(opt);
    } else if (e.key === 'Escape') {
        e.preventDefault();
        close();
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
    const panelW = p.offsetWidth;
    const spaceBelow = window.innerHeight - r.bottom;
    const spaceAbove = r.top;

    const openUp = spaceBelow < panelH + 8 && spaceAbove > spaceBelow;

    // Horizontal alignment: anchor panel's left or right edge to the trigger.
    let left = props.align === 'end' ? r.right - panelW : r.left;
    // Clamp so it never leaves the viewport.
    const margin = 8;
    left = Math.max(margin, Math.min(left, window.innerWidth - panelW - margin));

    const style: Record<string, string> = {
        left: `${left}px`,
        width: `${Math.max(panelW, r.width)}px`,
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
 * Trigger size classes (square, icon-only)
 * ──────────────────────────────────────────────────────────────────── */
const sizeClass = computed(() => ({
    sm: 'h-8  w-8  rounded-md',
    md: 'h-10 w-10 rounded-md',
    lg: 'h-12 w-12 rounded-lg',
}[props.size]));

defineExpose({ open: openPanel, close, toggle: toggleOpen });
</script>

<template>
    <!-- Trigger: single icon, no label swap -->
    <button
        ref="trigger"
        :id="fieldId"
        type="button"
        role="button"
        :aria-label="label"
        :aria-expanded="open"
        :aria-haspopup="'menu'"
        :aria-disabled="disabled || undefined"
        :class="[
            'inline-flex items-center justify-center shrink-0 select-none',
            !triggerClass && 'bg-transparent text-text-muted transition-colors duration-150',
            !triggerClass && 'hover:bg-bg-hover hover:text-text-h',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30',
            open && !triggerClass && 'bg-bg-hover text-text-h',
            disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
            triggerClass || sizeClass,
        ]"
        @click="toggleOpen"
        @keydown="onTriggerKeydown"
    >
        <!-- Default trigger icon: kebab. Override with the `trigger` slot. -->
        <slot name="trigger">
            <svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor" aria-hidden="true">
                <circle cx="12" cy="5"  r="1.75" />
                <circle cx="12" cy="12" r="1.75" />
                <circle cx="12" cy="19" r="1.75" />
            </svg>
        </slot>
    </button>

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
                role="menu"
                :style="[panelStyle, { maxHeight: maxHeight + 'px' }]"
                class="ui-option-menu"
                tabindex="-1"
                @keydown="onPanelKeydown"
            >
                <div class="overflow-y-auto py-1" :style="{ maxHeight: maxHeight + 'px' }">
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
                            role="menuitem"
                            :disabled="opt.disabled"
                            :class="[
                                'w-full flex items-center gap-2 px-3 py-1.5 text-left text-sm outline-none',
                                'transition-colors duration-75',
                                opt.disabled
                                    ? 'opacity-50 cursor-not-allowed'
                                    : 'cursor-pointer hover:bg-bg-hover',
                                opt.danger && !opt.disabled && 'text-danger',
                                !opt.disabled
                                    && flatOptions[activeIndex] === opt
                                    && 'bg-bg-hover',
                            ]"
                            @click="select(opt)"
                            @mouseenter="activeIndex = flatOptions.indexOf(opt)"
                        >
                            <!-- Emoji icon (falls back to a spacer to keep labels aligned) -->
                            <span
                                class="w-4 text-center text-base leading-none flex-shrink-0"
                                aria-hidden="true"
                            >{{ opt.icon ?? '' }}</span>

                            <span class="flex-1 truncate">{{ opt.label }}</span>

                            <span
                                v-if="opt.shortcut"
                                class="text-[10px] text-text-faint tabular-nums"
                            >
                                {{ opt.shortcut }}
                            </span>
                        </button>
                    </template>

                    <p
                        v-if="!flatOptions.length"
                        class="px-3 py-6 text-center text-xs text-text-faint"
                    >
                        No actions
                    </p>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style>
/*
 * NOT scoped — panel is teleported to <body>, so scoped styles won't reach it.
 * Mirrors .ui-select-panel so both feel like the same primitive.
 */
.ui-option-menu {
    position: fixed;
    z-index: 9999;
    min-width: 10rem;
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
    :root:not([data-theme="light"]) .ui-option-menu {
        border-color: var(--color-border-strong);
        box-shadow:
            0 0 0 1px var(--color-border-strong),
            0 12px 32px -6px rgba(0, 0, 0, 0.7),
            0 4px 10px -2px rgba(0, 0, 0, 0.5);
    }
}
:root[data-theme="dark"] .ui-option-menu {
    border-color: var(--color-border-strong);
    box-shadow:
        0 0 0 1px var(--color-border-strong),
        0 12px 32px -6px rgba(0, 0, 0, 0.7),
        0 4px 10px -2px rgba(0, 0, 0, 0.5);
}
</style>