import { copyFileSync } from 'node:fs'
import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'
import { defineConfig, loadEnv } from 'vite'

function escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    })[character]!)
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    const frontendEnv = loadEnv(mode, process.cwd(), 'F_')
    const appName = frontendEnv.F_APP_NAME || 'DotMuted'
    const backendUrl = (frontendEnv.F_BACKEND_URL || '').replace(/\/+$/, '')
    const configuredBasePath = (frontendEnv.F_BASE_PATH || '/').replace(/^\/+|\/+$/g, '')
    const basePath = configuredBasePath ? `/${configuredBasePath}/` : '/'

    if (mode === 'production' && !backendUrl) {
        throw new Error('F_BACKEND_URL must point to the deployed API when building for production.')
    }

    return {
        base: basePath,
        plugins: [
            {
                name: 'frontend-config',
                transformIndexHtml(html) {
                    return html.replaceAll('%APP_NAME%', escapeHtml(appName))
                }
            },
            vue(),
            tailwindcss(),
            {
                name: 'github-pages-spa-fallback',
                apply: 'build',
                closeBundle() {
                    const distDirectory = resolve(process.cwd(), 'dist')
                    copyFileSync(
                        resolve(distDirectory, 'index.html'),
                        resolve(distDirectory, '404.html'),
                    )
                },
            },
        ],
        define: {
            'import.meta.env.APP_NAME': JSON.stringify(appName),
            'import.meta.env.BACKEND_URL': JSON.stringify(backendUrl),
        },
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url))
            }
        },
    }
})
