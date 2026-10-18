import type { RouteComponent } from 'vue-router';

const PAGES_ROOT = '/src/Pages';
const pages = import.meta.glob([
  '/src/Pages/*/Index.vue',            // top-level pages
  '/src/Pages/*/SubPages/**/*.vue',    // subpages
]);

/**
 * Lazily import a page by its folder path inside `src/Pages/`.
 *
 * The first segment identifies the page. Any additional segments are
 * treated as subpages nested under `<PageName>/SubPages/`.
 *
 *   importPage('Home')           → src/Pages/Home/Index.vue
 *   importPage('Home/About')     → src/Pages/Home/SubPages/About.vue
 *   importPage('Home', 'About')  → same as above
 *   importPage('Home/About/Team')
 *                                → src/Pages/Home/SubPages/About/Team.vue
 *
 * Returns a thunk compatible with Vue Router's `component` field:
 *
 *   { path: '/home/about', component: importPage('Home', 'About') }
 */
export default function importPage(
    ...segments: string[]
): () => Promise<RouteComponent> {
    const parts = segments
        .flatMap((s) => s.split('/'))
        .map((s) => s.trim().replace(/^\/+|\/+$/g, ''))
        .filter(Boolean);

    if (parts.length === 0) {
        throw new Error('importPage() requires at least one non-empty segment.');
    }

    const [page, ...subPages] = parts;

    const key =
        subPages.length === 0
            ? `${PAGES_ROOT}/${page}/Index.vue`
            : `${PAGES_ROOT}/${page}/SubPages/${subPages.join('/')}.vue`;

    return async () => {
        const loadPage = pages[key];

        if (!loadPage) {
            const available = Object.keys(pages)
                .map((k) => k.slice(PAGES_ROOT.length + 1))
                .sort();

            throw new Error(
                `Page not found: ${parts.join('/')}\n` +
                `  Expected: ${key}\n` +
                `  Available pages:\n` +
                available.map((p) => `    - ${p}`).join('\n'),
            );
        }

        return loadPage() as Promise<RouteComponent>;
    };
}