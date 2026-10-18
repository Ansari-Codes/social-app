import { ref, computed, watchEffect } from 'vue';

export type Theme = 'auto' | 'light' | 'dark';
const KEY = 'theme';

const theme = ref<Theme>((localStorage.getItem(KEY) as Theme) ?? 'auto');

watchEffect(() => {
    const root = document.documentElement;
    if (theme.value === 'auto') {
        root.removeAttribute('data-theme');
        localStorage.removeItem(KEY);
    } else {
        root.setAttribute('data-theme', theme.value);
        localStorage.setItem(KEY, theme.value);
    }
});

const systemPrefersDark = ref(
    window.matchMedia('(prefers-color-scheme: dark)').matches,
);
window
    .matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', (e) => (systemPrefersDark.value = e.matches));

const resolvedTheme = computed<'light' | 'dark'>(() =>
    theme.value === 'auto'
        ? (systemPrefersDark.value ? 'dark' : 'light')
        : theme.value,
);

export function useTheme() {
    return {
        theme,                 // 'auto' | 'light' | 'dark'  (user choice)
        resolvedTheme,         // 'light' | 'dark'           (what's shown)
        systemPrefersDark,     // boolean                    (OS setting)
        setTheme: (t: Theme) => (theme.value = t),
        toggle: () => {
            theme.value =
                theme.value === 'light' ? 'dark'
                : theme.value === 'dark' ? 'auto'
                : 'light';
        },
    };
}