<script setup lang="ts">
import { computed } from 'vue';

import UiLink from '@/Ui/UiLink.vue';
import UiLabel from '@/Ui/UiLabel.vue';
import { APP_NAME } from '@/Core/config';

/* ── Props ───────────────────────────────────────────────────────── */

interface FooterLink {
    label: string;
    href: string;

    /** Open in a new tab; auto-detected for external URLs when omitted. */
    external?: boolean;
}

const props = withDefaults(defineProps<{
    /** Brand name shown in the copyright line. */
    brand?: string;

    /** Directory-style links (Privacy, Terms, …). */
    links?: FooterLink[];

    /** Optional secondary line under the copyright. */
    tagline?: string;
}>(), {
    brand: APP_NAME,

    links: () => [
        { label: 'Privacy', href: '/privacy' },
        { label: 'Terms', href: '/tos' },
        { label: 'GitHub', href: 'https://github.com' },
        { label: 'Contact', href: 'mailto:hi@dotmuted.com' },
    ],

    tagline: undefined,
});

/* ── Year ────────────────────────────────────────────────────────── */

const year = computed(() => new Date().getFullYear());
</script>

<template>
    <!-- Spacer: reserves the footer's space in normal document flow -->
    <div class="h-20" aria-hidden="true" />

    <!-- Actual fixed footer -->
    <footer class="fixed bottom-0 left-0 z-50 w-full border-t border-border bg-bg">
        <div class="mx-auto flex max-w-6xl flex-col items-center gap-3 px-4 py-6
                    sm:flex-row sm:justify-between sm:gap-4 sm:px-6">
            <!-- Left — copyright -->
            <p class="text-xs text-text-muted">
                <span aria-hidden="true">©</span>

                <span class="ml-1">
                    {{ year }}
                </span>

                <UiLabel :label="props.brand" size="sm" class="ml-1! inline! font-semibold! text-text-h!" />

                <span v-if="props.tagline" class="ml-2 text-text-faint">
                    · {{ props.tagline }}
                </span>
            </p>

            <!-- Right — links -->
            <nav aria-label="Footer" class="flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
                <UiLink v-for="link in props.links" :key="link.href" :href="link.href" :external="link.external"
                    variant="muted" size="sm" underline="hover">
                    {{ link.label }}
                </UiLink>
            </nav>
        </div>
    </footer>
</template>
