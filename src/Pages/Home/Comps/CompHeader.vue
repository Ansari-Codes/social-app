<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import UiNav, { type NavItem } from '@/Ui/UiNav.vue';
import UiLink from '@/Ui/UiLink.vue';
import UiLabel from '@/Ui/UiLabel.vue';
import { APP_NAME } from '@/Core/config';

const props = withDefaults(defineProps<{
    brand?: string;
    logo?: string;
}>(), {
    brand: APP_NAME,
    logo: '🔇',
});

const router = useRouter();

const links: NavItem[] = [
    { key: 'home', label: 'Home', to: '/' },
    { key: 'about', label: 'About', to: '/about' },
    { key: 'terms', label: 'Terms', to: '/tos' },
];

const activeKey = ref(
    links.find((l) => l.to === router.currentRoute.value.path)?.key ?? 'home',
);

function onNavigate(item: NavItem) {
    if (item.to) router.push(item.to);
}
</script>
<template>
    <header class="fixed top-0 z-999 w-full border-b border-border bg-bg-elevated">
        <div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">

            <!-- Left — logo -->
            <UiLink href="/" variant="inherit" underline="none"
                class="flex shrink-0 items-center gap-2 text-text-h hover:text-accent">
                <span class="grid h-7 w-7 place-items-center rounded-md bg-accent-bg
                            border border-accent-border text-base leading-none" aria-hidden="true">
                    {{ logo }}
                </span>
                <UiLabel :label="brand" size="lg" />
            </UiLink>

            <!-- Right — nav (shrink-0 so it hugs its content) -->
            <div class="shrink-0">
                <UiNav v-model:active-key="activeKey" :items="links" label="Primary" @navigate="onNavigate" />
            </div>
        </div>
    </header>
    <div class="h-14" aria-hidden="true"></div>

</template>