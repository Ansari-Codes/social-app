export const APP_NAME = import.meta.env.APP_NAME || 'DotMuted'
export const BASE_URL = import.meta.env.BASE_URL

export const BACKEND_URL = (
    import.meta.env.BACKEND_URL ||
    (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')
).replace(/\/+$/, '')