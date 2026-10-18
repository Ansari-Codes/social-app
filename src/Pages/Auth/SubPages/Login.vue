<script setup lang="ts">
import { ref, computed } from 'vue';
import { RouterLink, useRouter, useRoute } from 'vue-router';
import UiLabel from '@/Ui/UiLabel.vue';
import UiButton from '@/Ui/UiButton.vue';
import { ApiError } from '@/Core/api';
import { useMeStore } from '@/Stores/meStore';

const router = useRouter();
const route = useRoute();
const me = useMeStore();

const identifier = ref('');
const password = ref('');
const remember = ref(false);
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');

const canSubmit = computed(
    () => identifier.value.trim() !== '' && password.value.trim() !== '',
);

async function onSubmit() {
    if (!canSubmit.value || loading.value) return;
    error.value = '';
    loading.value = true;

    try {
        const value = identifier.value.trim();
        const payload = value.includes('@')
            ? { email: value, password: password.value }
            : { username: value, password: password.value };

        await me.login(payload, remember.value);
        const requestedRedirect = route.query.redirect;
        const fallback = router.resolve({ name: 'app' }).fullPath;
        let redirect = fallback;
        if (typeof requestedRedirect === 'string' && requestedRedirect.startsWith('/') && !requestedRedirect.startsWith('//')) {
            try {
                const target = new URL(requestedRedirect, window.location.origin);
                if (target.origin === window.location.origin) {
                    const resolved = router.resolve(`${target.pathname}${target.search}${target.hash}`);
                    if (resolved.matched.length) redirect = resolved.fullPath;
                }
            } catch {
                redirect = fallback;
            }
        }
        await router.replace(redirect);
    } catch (e) {
        error.value =
            e instanceof ApiError ? e.message : 'Invalid email or password.';
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="min-h-screen w-full flex flex-col bg-bg text-text">
        <!-- ── HEADER (mirrors TopBar brand block) ─────────────── -->
        <header class="fixed top-0 z-50 w-full bg-accent-bg border-b border-accent-soft shadow-sm">
            <div class="mx-auto flex w-full max-w-6xl items-center h-14 px-3">
                <div class="flex items-center gap-2 shrink-0">
                    <RouterLink :to="{ name: 'app' }" class="flex items-center gap-2 no-underline text-inherit">
                        <span class="grid h-9 w-9 place-items-center rounded-full bg-accent-bg
                                   border border-accent-border text-lg leading-none" aria-hidden="true">🔇</span>
                        <UiLabel label="App" size="lg" class="hidden sm:inline font-bold" />
                    </RouterLink>
                </div>
            </div>
        </header>

        <!-- Spacer for fixed header -->
        <div class="h-14" aria-hidden="true"></div>

        <!-- ── MAIN ─────────────────────────────────────────────── -->
        <main class="flex-1 w-full flex items-center justify-center px-3 py-8">
            <div class="w-full max-w-md">
                <!-- Card -->
                <div class="rounded-lg border border-border bg-bg-elevated p-6 sm:p-8 shadow-sm">
                    <!-- Heading -->
                    <div class="flex flex-col items-center gap-2 mb-6 text-center">
                        <span class="grid h-12 w-12 place-items-center rounded-full
                                   bg-accent-soft border border-accent-border text-2xl leading-none"
                            aria-hidden="true">🔐</span>
                        <h1 class="text-xl font-bold text-text-h">Welcome back</h1>
                        <p class="text-sm text-text-muted">Sign in to continue to your feed.</p>
                    </div>

                    <!-- Error -->
                    <div v-if="error"
                        class="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
                        role="alert">
                        {{ error }}
                    </div>

                    <!-- Form -->
                    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
                        <!-- Username or email -->
                        <div class="flex flex-col gap-1.5">
                            <label for="identifier" class="text-sm font-medium text-text-h">Username or email</label>
                            <input id="identifier" v-model="identifier" type="text" autocomplete="username" required
                                placeholder="alice or you@example.com" class="w-full rounded-md border border-border bg-bg
                                       px-3 py-2 text-sm text-text
                                       placeholder:text-text-muted
                                       focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent" />
                        </div>

                        <!-- Password -->
                        <div class="flex flex-col gap-1.5">
                            <div class="flex items-center justify-between">
                                <label for="password" class="text-sm font-medium text-text-h">Password</label>
                                <a href="#" class="text-xs text-accent hover:underline">Forgot?</a>
                            </div>
                            <div class="relative">
                                <input id="password" v-model="password" :type="showPassword ? 'text' : 'password'"
                                    autocomplete="current-password" required placeholder="••••••••" class="w-full rounded-md border border-border bg-bg
                                           px-3 py-2 pr-10 text-sm text-text
                                           placeholder:text-text-muted
                                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent" />
                                <button type="button" class="absolute inset-y-0 right-0 flex items-center px-3
                                           text-text-muted hover:text-text-h transition-colors"
                                    :aria-label="showPassword ? 'Hide password' : 'Show password'"
                                    @click="showPassword = !showPassword">
                                    <span aria-hidden="true">{{ showPassword ? '🙈' : '👁️' }}</span>
                                </button>
                            </div>
                        </div>

                        <!-- Remember -->
                        <label class="flex items-center gap-2 text-sm text-text-muted select-none cursor-pointer">
                            <input v-model="remember" type="checkbox" class="h-4 w-4 rounded border-border text-accent
                                        focus:ring-accent/40" />
                            Remember me
                        </label>

                        <!-- Submit -->
                        <UiButton variant="soft" block :disabled="!canSubmit || loading" class="mt-1 justify-center" type="submit">
                            <span v-if="loading">Signing in…</span>
                            <span v-else>Sign in</span>
                        </UiButton>
                    </form>
                </div>

                <!-- Footer -->
                <p class="mt-6 text-center text-sm text-text-muted">
                    Don't have an account?
                    <RouterLink :to="{ name: 'signup' }" class="text-accent font-medium hover:underline">
                        Sign up
                    </RouterLink>
                </p>
            </div>
        </main>
    </div>
</template>