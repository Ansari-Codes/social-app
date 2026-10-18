<script setup lang="ts">
import { computed, watch, onBeforeUnmount } from 'vue';
import UiSection from '@/Ui/UiSection.vue';
import UiButton from '@/Ui/UiButton.vue';

type Pos =
    | 'center'
    | 'top' | 'bottom' | 'left' | 'right'
    | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
    | 'top-center' | 'bottom-center';

type Size = 'sm' | 'md' | 'lg' | 'xl' | 'full';

const props = withDefaults(defineProps<{
    /** v-model — controls open/closed. */
    modelValue?: boolean;
    /**
     * If true, the dialog renders inline in the page flow (like a card).
     * If false (default), it renders as an elevated overlay with a backdrop.
     */
    onPage?: boolean;
    /** Placement within the viewport (elevated) or self-align in parent (inline). */
    pos?: Pos;
    /** Width preset for elevated mode. */
    size?: Size;
    /** Title shown in the UiSection header. */
    title?: string;
    /** Description shown under the title. */
    description?: string;
    /** Icon (emoji or slot). */
    icon?: string;
    /** Show the built-in close button in the header. */
    closable?: boolean;
    /** Close when clicking the backdrop (elevated mode only). */
    closeOnBackdrop?: boolean;
    /** Close on Escape. */
    closeOnEscape?: boolean;
    /** Lock body scroll while open (elevated mode only). */
    lockScroll?: boolean;
    /** Rendered tag for the root — useful for <form>, <aside>, etc. */
    as?: string;
}>(), {
    modelValue: false,
    onPage: false,
    pos: 'center',
    size: 'md',
    closable: true,
    closeOnBackdrop: true,
    closeOnEscape: true,
    lockScroll: true,
    as: 'div',
});

const emit = defineEmits<{
    'update:modelValue': [value: boolean];
    'open': [];
    'close': [];
}>();

const isOpen = computed({
    get: () => props.modelValue,
    set: (v) => emit('update:modelValue', v),
});

function close() {
    if (!isOpen.value) return;
    isOpen.value = false;
    emit('close');
}
function open() {
    if (isOpen.value) return;
    isOpen.value = true;
    emit('open');
}
defineExpose({ open, close });

/* ── Size classes (elevated) ─────────────────────────────────────────── */
const sizeClass = computed(() => ({
    sm:   'w-full max-w-sm',
    md:   'w-full max-w-md',
    lg:   'w-full max-w-lg',
    xl:   'w-full max-w-2xl',
    full: 'w-full h-full max-w-none',
}[props.size]));

/* ── Position classes ────────────────────────────────────────────────── */
const positionClass = computed(() => {
    // Elevated: the wrapper is a fixed inset-0 flex container.
    const map: Record<Pos, string> = {
        center:         'items-center justify-center',
        top:            'items-start justify-center pt-6',
        bottom:         'items-end justify-center pb-6',
        left:           'items-center justify-start pl-6',
        right:          'items-center justify-end pr-6',
        'top-left':     'items-start justify-start p-6',
        'top-right':    'items-start justify-end p-6',
        'bottom-left':  'items-end justify-start p-6',
        'bottom-right': 'items-end justify-end p-6',
        'top-center':   'items-start justify-center pt-6',
        'bottom-center':'items-end justify-center pb-6',
    };
    return map[props.pos];
});

const inlinePositionClass = computed(() => {
    // Inline: the root itself is placed via margin within its parent.
    const map: Record<Pos, string> = {
        center:         'mx-auto',
        top:            'mx-auto mt-0',
        bottom:         'mx-auto mb-0',
        left:           'mr-auto',
        right:          'ml-auto',
        'top-left':     'mr-auto',
        'top-right':    'ml-auto',
        'bottom-left':  'mr-auto mb-0',
        'bottom-right': 'ml-auto mb-0',
        'top-center':   'mx-auto',
        'bottom-center':'mx-auto mb-0',
    };
    return map[props.pos];
});

/* ── Body scroll lock ────────────────────────────────────────────────── */
let prevOverflow: string | null = null;
function lock() {
    if (typeof document === 'undefined') return;
    prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
}
function unlock() {
    if (typeof document === 'undefined') return;
    document.body.style.overflow = prevOverflow ?? '';
    prevOverflow = null;
}

/* ── Escape key ──────────────────────────────────────────────────────── */
function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
}

/* ── Reactive side-effects ───────────────────────────────────────────── */
watch(
    () => isOpen.value,
    (open, wasOpen) => {
        if (props.onPage) return; // inline mode has no overlay side-effects

        if (open && !wasOpen) {
            if (props.lockScroll) lock();
            if (props.closeOnEscape) {
                document.addEventListener('keydown', onKeydown);
            }
        } else if (!open && wasOpen) {
            if (props.lockScroll) unlock();
            document.removeEventListener('keydown', onKeydown);
        }
    },
    { immediate: true },
);

onBeforeUnmount(() => {
    document.removeEventListener('keydown', onKeydown);
    if (!props.onPage && props.lockScroll) unlock();
});
</script>

<template>
    <!-- ══════════════ INLINE MODE ══════════════ -->
    <component
        :is="as"
        v-if="onPage"
        v-show="isOpen"
        :class="['w-full', inlinePositionClass]"
        :style="size !== 'full' ? `max-width: ${
            size === 'sm' ? '24rem'
            : size === 'md' ? '28rem'
            : size === 'lg' ? '32rem'
            : '42rem'
        }` : undefined"
    >
        <UiSection
            :title="title"
            :description="description"
            :icon="icon"
            bordered
            shadow
            padding="none"
        >
            <template #actions v-if="closable || $slots.actions">
                <slot name="actions" />
                <UiButton
                    v-if="closable"
                    variant="ghost"
                    size="icon"
                    aria-label="Close"
                    @click="close"
                >
                    <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4">
                        <path d="M6 6l12 12M18 6L6 18"
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                    </svg>
                </UiButton>
            </template>

            <div class="p-4 sm:p-5">
                <slot />
            </div>

            <template v-if="$slots.footer" #footer>
                <slot name="footer" />
            </template>
        </UiSection>
    </component>

    <!-- ══════════════ ELEVATED MODE ══════════════ -->
    <Teleport v-else to="body">
        <Transition
            enter-active-class="transition duration-150 ease-out"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
        >
            <div
                v-if="isOpen"
                class="ui-dialog-backdrop fixed inset-0 z-[60]"
                @click.self="closeOnBackdrop && close()"
            >
                <!-- Inner flex positions the panel -->
                <div
                    :class="['flex h-full w-full p-4 pointer-events-none', positionClass]"
                >
                    <Transition
                        appear
                        enter-active-class="transition duration-150 ease-out"
                        enter-from-class="opacity-0 scale-95"
                        enter-to-class="opacity-100 scale-100"
                        leave-active-class="transition duration-100 ease-in"
                        leave-from-class="opacity-100 scale-100"
                        leave-to-class="opacity-0 scale-95"
                    >
                        <div
                            :class="[
                                'pointer-events-auto',
                                sizeClass,
                                size === 'full' && 'h-full',
                            ]"
                            role="dialog"
                            aria-modal="true"
                            :aria-label="title"
                        >
                            <UiSection
                                :title="title"
                                :description="description"
                                :icon="icon"
                                bordered
                                shadow
                                padding="none"
                                :radius="size === 'full' ? 'none' : 'lg'"
                            >
                                <template #actions v-if="closable || $slots.actions">
                                    <slot name="actions" />
                                    <UiButton
                                        v-if="closable"
                                        variant="ghost"
                                        size="icon"
                                        aria-label="Close"
                                        @click="close"
                                    >
                                        <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4">
                                            <path d="M6 6l12 12M18 6L6 18"
                                                  stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                                        </svg>
                                    </UiButton>
                                </template>

                                <div class="p-4 sm:p-5">
                                    <slot />
                                </div>

                                <template v-if="$slots.footer" #footer>
                                    <slot name="footer" />
                                </template>
                            </UiSection>
                        </div>
                    </Transition>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style>
/* Non-scoped — the elevated dialog is teleported to <body>. */
.ui-dialog-backdrop {
    background: rgba(10, 10, 11, 0.45);
    backdrop-filter: blur(2px);
}
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) .ui-dialog-backdrop {
        background: rgba(0, 0, 0, 0.65);
    }
}
:root[data-theme="dark"] .ui-dialog-backdrop {
    background: rgba(0, 0, 0, 0.65);
}
</style>