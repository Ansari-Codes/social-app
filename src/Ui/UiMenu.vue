<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue';

type Align = 'start' | 'center' | 'end';
type Side = 'bottom' | 'top';

const props = withDefaults(defineProps<{
    open?: boolean;
    align?: Align;
    side?: Side;
    offset?: number;
    closeOnOutside?: boolean;
    closeOnEscape?: boolean;
    matchWidth?: boolean;
    disabled?: boolean;
}>(), {
    open: undefined,
    align: 'start',
    side: 'bottom',
    offset: 6,
    closeOnOutside: true,
    closeOnEscape: true,
    matchWidth: false,
    disabled: false,
});

const emit = defineEmits<{
    'update:open': [value: boolean];
    'open': [];
    'close': [];
}>();

const internalOpen = ref(false);
const isOpen = computed({
    get: () => (props.open !== undefined ? props.open : internalOpen.value),
    set: (v) => {
        if (props.disabled) return;
        if (props.open === undefined) internalOpen.value = v;
        emit('update:open', v);
        if (v) emit('open'); else emit('close');
    },
});

function toggle() {
    if (props.disabled) return;
    isOpen.value = !isOpen.value;
}
function close() { isOpen.value = false; }

const root = ref<HTMLElement | null>(null);
const trigger = ref<HTMLElement | null>(null);
const panel = ref<HTMLElement | null>(null);

const panelStyle = ref<Record<string, string>>({});

function computePosition() {
    const t = trigger.value;
    const p = panel.value;
    if (!t || !p) return;

    const rect = t.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return; // trigger not laid out yet

    const style: Record<string, string> = {};

    if (props.matchWidth) {
        style.left = `${rect.left}px`;
        style.width = `${rect.width}px`;
    } else if (props.align === 'start') {
        style.left = `${rect.left}px`;
    } else if (props.align === 'end') {
        style.left = `${rect.right}px`;
        style.transform = 'translateX(-100%)';
    } else {
        style.left = `${rect.left + rect.width / 2}px`;
        style.transform = 'translateX(-50%)';
    }

    if (props.side === 'bottom') {
        style.top = `${rect.bottom + props.offset}px`;
    } else {
        style.top = `${rect.top - props.offset}px`;
        style.transform = `${style.transform ?? ''} translateY(-100%)`.trim();
    }

    panelStyle.value = style;
}

/* ── THE FIX ─────────────────────────────────────────────────────────
   Watch the panel ref itself. When the teleported panel finally mounts,
   `panel.value` transitions null → HTMLElement. That's the earliest
   moment its rect is real. Position immediately (single rAF for safety).
   ──────────────────────────────────────────────────────────────────── */
watch(panel, (el) => {
    if (el) {
        requestAnimationFrame(computePosition);
    }
});

/* ── Outside click / Escape / scroll / resize ──────────────────────── */
function onDocPointerDown(e: PointerEvent) {
    if (!props.closeOnOutside) return;
    const target = e.target as Node;
    if (root.value?.contains(target)) return;
    if (panel.value?.contains(target)) return;
    close();
}

function onKeydown(e: KeyboardEvent) {
    if (props.closeOnEscape && e.key === 'Escape') close();
}

function onScrollOrResize() {
    if (isOpen.value) computePosition();
}

watch(isOpen, (open) => {
    if (open) {
        // Backup attempt in case `panel` ref watcher doesn't fire for some reason
        nextTick(() => requestAnimationFrame(computePosition));

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

defineExpose({ open: () => (isOpen.value = true), close, toggle });
</script>

<template>
    <!-- Root wraps the trigger only — no visible layout impact -->
    <span
        ref="root"
        class="inline-block"
        @pointerdown.stop
    >
        <!-- Trigger -->
        <span
            ref="trigger"
            class="inline-block"
            @click="toggle"
            @keydown.enter.prevent="toggle"
            @keydown.space.prevent="toggle"
            :aria-haspopup="'menu'"
            :aria-expanded="isOpen"
        >
            <slot name="trigger" :open="isOpen" :toggle="toggle" />
        </span>

        <!-- Panel -->
        <Teleport to="body">
            <Transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="opacity-0 scale-95"
                enter-to-class="opacity-100 scale-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="opacity-100 scale-100"
                leave-to-class="opacity-0 scale-95"
            >
                <div
                    v-if="isOpen"
                    ref="panel"
                    role="menu"
                    :style="panelStyle"
                    class="ui-menu-panel fixed z-50 min-w-[10rem] rounded-lg py-1 text-sm text-text"
                >
                    <slot :close="close" />
                </div>
            </Transition>
        </Teleport>
    </span>
</template>

<style scoped>
/*
 * The theme's `--shadow-pop` is a black shadow — invisible on dark surfaces.
 * Layer a hairline ring + accent-tinted shadow so the panel reads on both
 * light and dark backgrounds.
 */
.ui-menu-panel {
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    box-shadow:
        0 0 0 1px var(--color-border),                       /* crisp hairline */
        0 1px 2px rgba(0, 0, 0, 0.06),                       /* subtle depth (light) */
        0 12px 32px -8px rgba(0, 0, 0, 0.18),                /* soft bloom (light) */
        0 2px 8px -2px rgba(0, 0, 0, 0.08);
}

/* Dark: swap in a lighter bloom + brighter ring so it still floats */
:root[data-theme="dark"] .ui-menu-panel,
.dark .ui-menu-panel {
    border-color: var(--color-border-strong);
    box-shadow:
        0 0 0 1px var(--color-border-strong),
        0 1px 2px rgba(0, 0, 0, 0.6),
        0 16px 40px -8px rgba(0, 0, 0, 0.7),
        0 4px 12px -2px rgba(0, 0, 0, 0.5);
}

/* Auto dark when no data-theme override is set */
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) .ui-menu-panel {
        border-color: var(--color-border-strong);
        box-shadow:
            0 0 0 1px var(--color-border-strong),
            0 1px 2px rgba(0, 0, 0, 0.6),
            0 16px 40px -8px rgba(0, 0, 0, 0.7),
            0 4px 12px -2px rgba(0, 0, 0, 0.5);
    }
}
</style>