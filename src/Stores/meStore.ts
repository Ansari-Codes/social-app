// src/Stores/meStore.ts

import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

import { getToken, setToken, ApiError } from '@/Core/api';
import { publishDataChange } from './dataChanges';
import {
    login as apiLogin,
    logout as apiLogout,
    registerUser as apiRegister,
    getMe as apiGetMe,
} from '@/Pages/Auth/Services/Auth.serve';
import type {
    LoginRequest,
    SignupRequest,
    UserPublic,
} from '@/Pages/Auth/Types/auth.type';

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function toMessage(err: unknown): string {
    if (err instanceof ApiError) return err.message;
    if (err instanceof Error) return err.message;
    return 'Something went wrong.';
}

/* ------------------------------------------------------------------ */
/* Store                                                              */
/* ------------------------------------------------------------------ */

export const useMeStore = defineStore('me', () => {
    /* ---------------------------------------------------------- */
    /* State                                                      */
    /* ---------------------------------------------------------- */

    const user = ref<UserPublic | null>(null);
    const token = ref<string | null>(getToken());
    const loading = ref(false);
    const initialized = ref(false);
    const error = ref<string | null>(null);

    /* ---------------------------------------------------------- */
    /* Getters                                                    */
    /* ---------------------------------------------------------- */

    const isAuthenticated = computed(() => !!token.value && !!user.value);
    const isAdmin = computed(() => user.value?.is_admin === true);
    const displayName = computed(
        () =>
            user.value?.display_name?.trim() ||
            user.value?.username ||
            '',
    );

    /* ---------------------------------------------------------- */
    /* Internal actions                                           */
    /* ---------------------------------------------------------- */

    function _setToken(next: string | null, remember = true) {
        const changed = token.value !== next;
        token.value = next;
        setToken(next, remember);
        if (changed) publishDataChange({ type: 'viewer-changed' });
    }

    function updateAccountDetails(username: string, email: string) {
        if (!user.value) return;
        user.value = { ...user.value, username, email };
        publishDataChange({
            type: 'account-updated',
            userId: user.value.id,
            username,
            email,
        });
    }

    function _clear() {
        _setToken(null);
        user.value = null;
        error.value = null;
    }

    /* ---------------------------------------------------------- */
    /* Public actions                                             */
    /* ---------------------------------------------------------- */

    /**
     * Restore session from a stored token on app startup.
     * Idempotent — subsequent calls are a no-op.
     */
    async function init(): Promise<void> {
        if (initialized.value) return;

        if (!token.value) {
            initialized.value = true;
            return;
        }

        loading.value = true;
        error.value = null;
        try {
            user.value = await apiGetMe();
        } catch (err) {
            if (
                err instanceof ApiError &&
                (err.status === 401 || err.status === 403)
            ) {
                // Stale token — clear quietly.
                _clear();
            } else {
                error.value = toMessage(err);
            }
        } finally {
            loading.value = false;
            initialized.value = true;
        }
    }

    /**
     * Exchange credentials for a token, then fetch the profile.
     */
    async function login(payload: LoginRequest, remember = false): Promise<UserPublic> {
        loading.value = true;
        error.value = null;
        try {
            const res = await apiLogin(payload);
            _setToken(res.token, remember);

            const me = await apiGetMe();
            user.value = me;
            initialized.value = true;
            return me;
        } catch (err) {
            _clear();
            error.value = toMessage(err);
            throw err;
        } finally {
            loading.value = false;
        }
    }

    /**
     * Register, then immediately log in with the same credentials.
     */
    async function signup(payload: SignupRequest): Promise<UserPublic> {
        loading.value = true;
        error.value = null;
        try {
            const created = await apiRegister(payload);
            // Auto-login using the credentials just provided.
            return await login({
                username: created.username,
                password: payload.password,
            });
        } catch (err) {
            error.value = toMessage(err);
            throw err;
        } finally {
            loading.value = false;
        }
    }

    /**
     * Revoke server-side session(s), then clear locally.
     * Always clears local state, even if the network call fails.
     */
    async function logout(allDevices = false): Promise<void> {
        loading.value = true;
        try {
            if (token.value) {
                await apiLogout(allDevices);
            }
        } catch {
            // Swallow — we still want local state cleared.
        } finally {
            _clear();
            loading.value = false;
            initialized.value = true;
        }
    }

    /* ---------------------------------------------------------- */
    /* Returned surface                                           */
    /* ---------------------------------------------------------- */

    return {
        // state (as refs)
        user,
        token,
        loading,
        initialized,
        error,

        // getters
        isAuthenticated,
        isAdmin,
        displayName,

        // actions
        init,
        login,
        signup,
        logout,
        updateAccountDetails,
    };
});