<script setup lang="ts">
import { computed } from 'vue';

type Padding = 'none' | 'sm' | 'md' | 'lg';
type Radius = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';

const props = withDefaults(defineProps<{
    /** Section heading text (or use the `title` slot). */
    title?: string;
    /** Optional description below the title. */
    description?: string;
    /** Icon shown before the title (emoji, or use the `icon` slot). */
    icon?: string;
    /** Show a hairline border around the section. */
    bordered?: boolean;
    /** Show a stronger outline (thicker ring). Wins over `bordered`. */
    outlined?: boolean;
    /** Show the soft card shadow. */
    shadow?: boolean;
    /** Show a bottom divider under the header. */
    headerDivider?: boolean;
    /** Inner padding preset. */
    padding?: Padding;
    /** Corner radius preset. */
    radius?: Radius;
    /** Background surface. */
    surface?: 'default' | 'elevated' | 'sunken' | 'transparent';
    /** Render as an <article> instead of <section> (SEO / semantics). */
    as?: 'section' | 'article' | 'div' | 'aside';
}>(), {
    bordered: false,
    outlined: false,
    shadow: false,
    headerDivider: true,
    padding: 'sm',
    radius: 'xs',
    surface: 'elevated',
    as: 'section',
});

const paddingClass = computed(() => ({
    none: '',
    sm:   'p-3',
    md:   'p-4 sm:p-5',
    lg:   'p-6 sm:p-7',
}[props.padding]));

const headerPaddingClass = computed(() => ({
    none: '',
    sm:   'px-3 py-2',
    md:   'px-4 py-3 sm:px-5',
    lg:   'px-6 py-4 sm:px-7',
}[props.padding]));

const bodyPaddingClass = computed(() => paddingClass.value);

const radiusClass = computed(() => ({
    none: '',
    xs:   'rounded-xs',
    sm:   'rounded-sm',
    md:   'rounded-md',
    lg:   'rounded-lg',
    xl:   'rounded-xl',
}[props.radius]));

const surfaceClass = computed(() => ({
    default:     'bg-bg',
    elevated:    'bg-bg-elevated',
    sunken:      'bg-bg-sunken',
    transparent: 'bg-transparent',
}[props.surface]));

const borderClass = computed(() => {
    if (props.outlined) return 'border-2 border-border-strong';
    if (props.bordered) return 'border border-border';
    return '';
});

const shadowClass = computed(() => (props.shadow ? 'shadow-card' : ''));

const hasHeader = computed(
    () => !!(props.title || props.description || props.icon || useSlots().title || useSlots().icon || useSlots().actions),
);

// useSlots needs to be imported explicitly for the hasHeader computed
import { useSlots } from 'vue';
</script>

<template>
    <component
        :is="as"
        :class="[
            'flex flex-col overflow-hidden',
            surfaceClass,
            borderClass,
            shadowClass,
            radiusClass,
        ]"
    >
        <!-- Header -->
        <header
            v-if="hasHeader"
            :class="[
                'flex items-start justify-between gap-3',
                headerPaddingClass,
                headerDivider && 'border-b border-border',
            ]"
        >
            <div class="flex min-w-0 items-start gap-2.5">
                <!-- Icon -->
                <span
                    v-if="icon || $slots.icon"
                    class="mt-0.5 shrink-0 text-text-muted"
                    aria-hidden="true"
                >
                    <slot name="icon">{{ icon }}</slot>
                </span>

                <div class="min-w-0">
                    <!-- Title -->
                    <h2
                        v-if="title || $slots.title"
                        class="text-base font-semibold text-text-h leading-tight truncate"
                    >
                        <slot name="title">{{ title }}</slot>
                    </h2>

                    <!-- Description -->
                    <p
                        v-if="description || $slots.description"
                        class="mt-0.5 text-xs text-text-muted leading-relaxed"
                    >
                        <slot name="description">{{ description }}</slot>
                    </p>
                </div>
            </div>

            <!-- Actions -->
            <div
                v-if="$slots.actions"
                class="flex shrink-0 items-center gap-1"
            >
                <slot name="actions" />
            </div>
        </header>

        <!-- Body -->
        <div :class="['flex-1', bodyPaddingClass]">
            <slot />
        </div>

        <!-- Footer -->
        <footer
            v-if="$slots.footer"
            :class="[
                'border-t border-border',
                headerPaddingClass,
            ]"
        >
            <slot name="footer" />
        </footer>
    </component>
</template>