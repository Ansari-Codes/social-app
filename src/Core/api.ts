// src/Core/api.ts

import { BACKEND_URL } from '@/Core/config'

/** Shape of the envelope every endpoint returns (mirrors Models/core.py). */
export interface ApiEnvelope<T> {
    success: boolean;
    errors: Record<string, string>;
    status_code: number;
    data: T | null;
}

export class ApiError extends Error {
    status: number;
    payload: unknown;

    constructor(status: number, message: string, payload?: unknown) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.payload = payload;
    }
}

const BASE_URL = BACKEND_URL

/** Token storage key — kept in one place so stores/services agree. */
export const TOKEN_KEY = 'silence.auth.token';
const SESSION_TOKEN_KEY = `${TOKEN_KEY}.session`;

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(SESSION_TOKEN_KEY);
}

export function setToken(token: string | null, remember = true): void {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
    if (!token) return;
    if (remember) localStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.setItem(SESSION_TOKEN_KEY, token);
}

/** Options for a single callAPI invocation. */
export interface CallOptions {
    method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
    /** Query params appended to the URL. */
    params?: Record<string, string | number | boolean | undefined | null>;
    /** JSON body — serialised automatically. */
    body?: unknown;
    /** Extra headers to merge on top of defaults. */
    headers?: Record<string, string>;
    /** Skip the Authorization header even if a token exists. */
    noAuth?: boolean;
    /** AbortSignal for cancellation. */
    signal?: AbortSignal;
}

function buildQuery(
    params?: Record<string, string | number | boolean | undefined | null>,
): string {
    if (!params) return '';
    const usp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
        if (v === undefined || v === null) continue;
        usp.append(k, String(v));
    }
    const s = usp.toString();
    return s ? `?${s}` : '';
}

/**
 * Call an API endpoint. Returns the unwrapped `data` on success.
 *
 * Throws `ApiError` on any non-2xx response, with the FastAPI `detail`
 * message extracted when available.
 */
export async function callAPI<T>(
    path: string,
    options: CallOptions = {},
): Promise<T> {
    const {
        method = 'GET',
        params,
        body,
        headers = {},
        noAuth = false,
        signal,
    } = options;

    const url = `${BASE_URL}${path}${buildQuery(params)}`;

    const finalHeaders: Record<string, string> = {
        Accept: 'application/json',
        ...headers,
    };

    if (body !== undefined && !('Content-Type' in finalHeaders)) {
        finalHeaders['Content-Type'] = 'application/json';
    }

    if (!noAuth) {
        const token = getToken();
        if (token) finalHeaders['Authorization'] = `Bearer ${token}`;
    }

    let res: Response;
    try {
        res = await fetch(url, {
            method,
            headers: finalHeaders,
            body: body === undefined ? undefined : JSON.stringify(body),
            signal,
        });
    } catch (err) {
        // Network failure — no response at all.
        throw new ApiError(0, 'Network error. Please check your connection.');
    }

    // Try to parse JSON regardless of status.
    let json: unknown = null;
    const text = await res.text();
    if (text) {
        try {
            json = JSON.parse(text);
        } catch {
            json = { detail: text };
        }
    }

    if (!res.ok) {
        // FastAPI puts errors under `detail`.
        const detail =
            (json as any)?.detail ??
            (json as any)?.errors?.msg ??
            (json as any)?.message ??
            res.statusText ??
            'Request failed';
        const message = Array.isArray(detail)
            ? detail.map((d: any) => d.msg ?? String(d)).join(', ')
            : String(detail);
        throw new ApiError(res.status, message, json);
    }

    // Unwrap the envelope if it looks like one; otherwise return raw.
    if (json && typeof json === 'object' && 'success' in json && 'data' in json) {
        const env = json as ApiEnvelope<T>;
        if (!env.success) {
            const msg =
                env.errors?.msg ??
                Object.values(env.errors ?? {})[0] ??
                'Request failed';
            throw new ApiError(env.status_code || 400, msg, env);
        }
        return env.data as T;
    }

    return json as T;
}