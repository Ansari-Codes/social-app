// src/Pages/Auth/Types/auth.type.ts

/** Shape returned by POST /sessions/login. */
export interface LoginResponse {
    token: string;
    expires_at: string;
    session: SessionPublic;
}

/** Public session representation. */
export interface SessionPublic {
    id: number;
    user_id: number;
    user_agent: string | null;
    ip_address: string | null;
    created_at: string;
    expires_at: string;
    revoked: boolean;
}

/** Public user representation (never includes password_hash). */
export interface UserPublic {
    id: number;
    username: string;
    email: string;
    display_name: string | null;
    is_active: boolean;
    is_admin: boolean;
    created_at: string;
    updated_at: string;
    last_login: string | null;
}

/** Request bodies. */
export interface LoginRequest {
    username?: string;
    email?: string;
    password: string;
}

export interface SignupRequest {
    username: string;
    email: string;
    password: string;
    display_name?: string | null;
}

export interface LogoutRequest {
    all_devices?: boolean;
}

export interface LogoutResponse {
    revoked: number;
    all_devices: boolean;
}

/** Wrappers returned by the envelope unwrapping inside callAPI. */
export interface DataLogin   { /* already unwrapped to LoginResponse */ }
export interface DataUser    { user: UserPublic }
export interface DataSession { session: SessionPublic }