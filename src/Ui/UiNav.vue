<script setup lang="ts">
import { computed } from 'vue';
import UiButton from '@/Ui/UiButton.vue';
import UiSelect from '@/Ui/UiSelect.vue';

export interface NavItem {
    /** Unique key — used to identify the active item and as the select value. */
    key: string;
    /** Visible label. */
    label: string;
    /** Route target — used if no `onClick` is provided. */
    to?: string;
    /** Custom click handler — overrides `to` when present. */
    onClick?: (item: NavItem) => void;
    /** Optional emoji / icon glyph shown before the label (desktop + mobile). */
    icon?: string;
    /** Disable the item. */
    disabled?: boolean;
}

const props = withDefaults(defineProps<{
    /** Nav links to render. */
    items: NavItem[];
    /** Currently active item's key. */
    activeKey?: string | null;
    /**
     * Breakpoint (px) at which the nav switches to the select-based mobile mode.
     * Below this width, we render a UiSelect instead of buttons.
     */
    mobileBreakpoint?: number;
    /** Placeholder for the mobile select. */
    mobilePlaceholder?: string;
    /** Optional aria-label for the nav landmark. */
    label?: string;
    /** Full-width buttons (stretch across the nav). */
    block?: boolean;
    /** Optional gap between desktop items. */
    gap?: 'sm' | 'md' | 'lg';
}>(), {
    activeKey: null,
    mobileBreakpoint: 640,
    mobilePlaceholder: 'Go to…',
    label: 'Primary navigation',
    block: false,
    gap: 'sm',
});

const emit = defineEmits<{
    /** Fired when any nav item (desktop button or mobile select) is activated. */
    navigate: [item: NavItem];
    /** Fired when the active item changes. */
    'update:activeKey': [key: string];
}>();

/* ── Responsive mode ─────────────────────────────────────────────────── */
import { ref, onMounted, onBeforeUnmount } from 'vue';

const isMobile = ref(false);
let mql: MediaQueryList | null = null;

function sync(e: MediaQueryList | MediaQueryListEvent) {
    isMobile.value = e.matches;
}

onMounted(() => {
    mql = window.matchMedia(`(max-width: ${props.mobileBreakpoint - 1}px)`);
    sync(mql);
    mql.addEventListener('change', sync);
});
onBeforeUnmount(() => {
    mql?.removeEventListener('change', sync);
});

/* ── Trigger handler ─────────────────────────────────────────────────── */
function activate(item: NavItem) {
    if (item.disabled) return;
    emit('update:activeKey', item.key);
    emit('navigate', item);
    item.onClick?.(item);
}

/* ── Desktop gap ─────────────────────────────────────────────────────── */
const gapClass = computed(() => ({
    sm: 'gap-1',
    md: 'gap-2',
    lg: 'gap-3',
}[props.gap]));

/* ── Select options (mobile) ────────────────────────────────────────── */
const selectOptions = computed(() =>
    props.items.map((i) => ({
        value: i.key,
        label: i.icon ? `${i.icon}  ${i.label}` : i.label,
        disabled: i.disabled,
    })),
);

/* Mobile select model — mirrors activeKey, and commits on change */
const mobileValue = computed({
    get: () => props.activeKey ?? null,
    set: (v: string | number | Array<string | number> | null) => {
        if (v == null || Array.isArray(v)) return;
        const item = props.items.find((i) => i.key === v);
        if (item) activate(item);
    },
});
</script>

<template>
    <nav :aria-label="label">
        <!-- ══════════ MOBILE — select-based ══════════ -->
        <div v-if="isMobile">
            <UiSelect
                v-model="mobileValue"
                :options="selectOptions"
                :placeholder="mobilePlaceholder"
                size="md"
            />
        </div>

        <!-- ══════════ DESKTOP — buttons ══════════ -->
        <div v-else :class="['flex items-center', gapClass, block && 'w-full']">
            <UiButton
                v-for="item in items"
                :key="item.key"
                :variant="item.key === activeKey ? 'soft' : 'ghost'"
                size="sm"
                :disabled="item.disabled"
                :block="block"
                :aria-current="item.key === activeKey ? 'page' : undefined"
                :href="item.onClick ? undefined : item.to"
                @click="!item.onClick && !item.to ? activate(item) : (item.onClick ? activate(item) : undefined)"
            >
                <template v-if="item.icon" #leading>
                    <span aria-hidden="true">{{ item.icon }}</span>
                </template>
                {{ item.label }}
            </UiButton>
        </div>
    </nav>
</template>