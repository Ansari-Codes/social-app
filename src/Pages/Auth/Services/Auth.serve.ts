// src/Pages/Auth/Service/AuthService.ts

import { callAPI } from '@/Core/api';
import type {
    DataSession,
    DataUser,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    SessionPublic,
    SignupRequest,
    UserPublic,
} from '../Types/auth.type';

/* ------------------------------------------------------------------ */
/* Users                                                              */
/* ------------------------------------------------------------------ */

export async function registerUser(payload: SignupRequest): Promise<UserPublic> {
    const res = await callAPI<DataUser>('/users/', {
        method: 'POST',
        body: {
            username: payload.username,
            email: payload.email,
            password: payload.password,
            display_name: payload.display_name ?? null,
        },
        noAuth: true,
    });
    return res.user;
}

export async function getMe(): Promise<UserPublic> {
    const res = await callAPI<DataUser>('/users/me');
    return res.user;
}

/* ------------------------------------------------------------------ */
/* Sessions                                                           */
/* ------------------------------------------------------------------ */

export async function login(payload: LoginRequest): Promise<LoginResponse> {
    return await callAPI<LoginResponse>('/sessions/login', {
        method: 'POST',
        body: payload,
        noAuth: true,
    });
}

export async function logout(allDevices = false): Promise<LogoutResponse> {
    const body: LogoutRequest = { all_devices: allDevices };
    return await callAPI<LogoutResponse>('/sessions/logout', {
        method: 'POST',
        body,
    });
}

export async function getMySession(): Promise<SessionPublic> {
    const res = await callAPI<DataSession>('/sessions/me');
    return res.session;
}