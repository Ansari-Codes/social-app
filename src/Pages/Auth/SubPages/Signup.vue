<script setup lang="ts">
import { ref, computed } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import UiLabel from '@/Ui/UiLabel.vue';
import UiButton from '@/Ui/UiButton.vue';
import { ApiError } from '@/Core/api';
import { useMeStore } from '@/Stores/meStore';

const router = useRouter();
const me = useMeStore();

const username = ref('');
const email = ref('');
const password = ref('');
const confirm = ref('');
const agree = ref(false);
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');

/* ── Validation ──────────────────────────────────────────────────── */
const usernameError = computed(() => {
    if (!username.value) return '';
    if (username.value.length < 3) return 'Username must be at least 3 characters.';
    if (!/^[a-zA-Z0-9_]+$/.test(username.value))
        return 'Only letters, numbers, and underscores.';
    return '';
});

const emailError = computed(() => {
    if (!email.value) return '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return 'Enter a valid email.';
    return '';
});

const passwordError = computed(() => {
    if (!password.value) return '';
    if (password.value.length < 8) return 'Password must be at least 8 characters.';
    return '';
});

const confirmError = computed(() => {
    if (!confirm.value) return '';
    if (confirm.value !== password.value) return 'Passwords do not match.';
    return '';
});

const canSubmit = computed(
    () =>
        username.value.trim() !== '' &&
        email.value.trim() !== '' &&
        password.value.trim() !== '' &&
        confirm.value.trim() !== '' &&
        agree.value &&
        !usernameError.value &&
        !emailError.value &&
        !passwordError.value &&
        !confirmError.value,
);

/* Simple strength meter (0–4) */
const strength = computed(() => {
    const p = password.value;
    if (!p) return 0;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
});

const strengthLabel = computed(
    () => ['', 'Weak', 'Fair', 'Good', 'Strong'][strength.value] ?? '',
);

const strengthColor = computed(
    () =>
        ['', 'bg-red-400', 'bg-amber-400', 'bg-yellow-400', 'bg-emerald-500'][
            strength.value
        ] ?? '',
);

/* ── Submit ──────────────────────────────────────────────────────── */
async function onSubmit() {
    if (!canSubmit.value || loading.value) return;
    error.value = '';
    loading.value = true;

    try {
        await me.signup({
            username: username.value.trim(),
            email: email.value.trim(),
            password: password.value,
            display_name: null,
        });
        // signup() already logs the user in.
        router.push({ name: 'app' });
    } catch (e) {
        error.value =
            e instanceof ApiError
                ? e.message
                : 'Could not create your account. Try again.';
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="min-h-screen w-full flex flex-col bg-bg text-text">
        <!-- ── HEADER (same brand block as TopBar / Login) ─────── -->
        <header class="fixed top-0 z-50 w-full bg-accent-bg border-b border-accent-soft shadow-sm">
            <div class="mx-auto flex w-full max-w-6xl items-center h-14 px-3">
                <div class="flex items-center gap-2 shrink-0">
                    <RouterLink :to="{ name: 'app' }"
                        class="flex items-center gap-2 no-underline text-inherit">
                        <span class="grid h-9 w-9 place-items-center rounded-full bg-accent-bg
                                   border border-accent-border text-lg leading-none"
                            aria-hidden="true">🔇</span>
                        <UiLabel label="App" size="lg" class="hidden sm:inline font-bold" />
                    </RouterLink>
                </div>
            </div>
        </header>

        <div class="h-14" aria-hidden="true"></div>

        <!-- ── MAIN ─────────────────────────────────────────────── -->
        <main class="flex-1 w-full flex items-center justify-center px-3 py-8">
            <div class="w-full max-w-md">
                <div class="rounded-lg border border-border bg-bg-elevated p-6 sm:p-8 shadow-sm">
                    <!-- Heading -->
                    <div class="flex flex-col items-center gap-2 mb-6 text-center">
                        <span class="grid h-12 w-12 place-items-center rounded-full
                                   bg-accent-soft border border-accent-border text-2xl leading-none"
                            aria-hidden="true">✨</span>
                        <h1 class="text-xl font-bold text-text-h">Create your account</h1>
                        <p class="text-sm text-text-muted">
                            Join the feed in less than a minute.
                        </p>
                    </div>

                    <!-- Error -->
                    <div v-if="error"
                        class="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
                        role="alert">
                        {{ error }}
                    </div>

                    <!-- Form -->
                    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
                        <!-- Username -->
                        <div class="flex flex-col gap-1.5">
                            <label for="username" class="text-sm font-medium text-text-h">Username</label>
                            <input id="username" v-model="username" type="text" autocomplete="username" required
                                placeholder="alice" class="w-full rounded-md border bg-bg px-3 py-2 text-sm text-text
                                       placeholder:text-text-muted
                                       focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
                                :class="usernameError ? 'border-red-300' : 'border-border'" />
                            <p v-if="usernameError" class="text-xs text-red-500">{{ usernameError }}</p>
                        </div>

                        <!-- Email -->
                        <div class="flex flex-col gap-1.5">
                            <label for="email" class="text-sm font-medium text-text-h">Email</label>
                            <input id="email" v-model="email" type="email" autocomplete="email" required
                                placeholder="you@example.com" class="w-full rounded-md border bg-bg px-3 py-2 text-sm text-text
                                       placeholder:text-text-muted
                                       focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
                                :class="emailError ? 'border-red-300' : 'border-border'" />
                            <p v-if="emailError" class="text-xs text-red-500">{{ emailError }}</p>
                        </div>

                        <!-- Password -->
                        <div class="flex flex-col gap-1.5">
                            <label for="password" class="text-sm font-medium text-text-h">Password</label>
                            <div class="relative">
                                <input id="password" v-model="password"
                                    :type="showPassword ? 'text' : 'password'"
                                    autocomplete="new-password" required placeholder="At least 8 characters" class="w-full rounded-md border bg-bg px-3 py-2 pr-10 text-sm text-text
                                           placeholder:text-text-muted
                                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
                                    :class="passwordError ? 'border-red-300' : 'border-border'" />
                                <button type="button"
                                    class="absolute inset-y-0 right-0 flex items-center px-3
                                           text-text-muted hover:text-text-h transition-colors"
                                    :aria-label="showPassword ? 'Hide password' : 'Show password'"
                                    @click="showPassword = !showPassword">
                                    <span aria-hidden="true">{{ showPassword ? '🙈' : '👁️' }}</span>
                                </button>
                            </div>

                            <!-- Strength meter -->
                            <div v-if="password" class="flex items-center gap-2">
                                <div class="flex h-1.5 flex-1 gap-1" aria-hidden="true">
                                    <span v-for="i in 4" :key="i" class="h-full flex-1 rounded-full transition-colors"
                                        :class="i <= strength ? strengthColor : 'bg-bg-hover'" />
                                </div>
                                <span class="text-xs text-text-muted w-12 text-right">{{ strengthLabel }}</span>
                            </div>
                            <p v-if="passwordError" class="text-xs text-red-500">{{ passwordError }}</p>
                        </div>

                        <!-- Confirm password -->
                        <div class="flex flex-col gap-1.5">
                            <label for="confirm" class="text-sm font-medium text-text-h">Confirm password</label>
                            <input id="confirm" v-model="confirm" :type="showPassword ? 'text' : 'password'"
                                autocomplete="new-password" required placeholder="Repeat your password" class="w-full rounded-md border bg-bg px-3 py-2 text-sm text-text
                                       placeholder:text-text-muted
                                       focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
                                :class="confirmError ? 'border-red-300' : 'border-border'" />
                            <p v-if="confirmError" class="text-xs text-red-500">{{ confirmError }}</p>
                        </div>

                        <!-- Terms -->
                        <label class="flex items-start gap-2 text-sm text-text-muted select-none cursor-pointer">
                            <input v-model="agree" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-border text-accent
                                        focus:ring-accent/40" />
                            <span>
                                I agree to the
                                <a href="#" class="text-accent hover:underline">Terms</a>
                                and
                                <a href="#" class="text-accent hover:underline">Privacy Policy</a>.
                            </span>
                        </label>

                        <!-- Submit -->
                        <UiButton variant="soft" block :disabled="!canSubmit || loading" class="mt-1 justify-center" type="submit">
                            <span v-if="loading">Creating account…</span>
                            <span v-else>Create account</span>
                        </UiButton>
                    </form>
                </div>

                <!-- Footer -->
                <p class="mt-6 text-center text-sm text-text-muted">
                    Already have an account?
                    <RouterLink :to="{ name: 'login' }" class="text-accent font-medium hover:underline">
                        Sign in
                    </RouterLink>
                </p>
            </div>
        </main>
    </div>
</template>