import importPage from "@/Core/importPage";
import type { RouteRecordRaw } from 'vue-router';

const app_routes: RouteRecordRaw[] = [
    {
        name: 'app',
        path: '',
        component: importPage('App/Feed'),
        meta: { requiresAuth: true },
    },
    {
        name: 'feed',
        path: 'feed',
        redirect: { name: 'app' },
    },
    {
        name: 'dashboard',
        path: 'dashboard',
        component: importPage('App/Dashboard'),
        meta: { requiresAuth: true },
    },
    {
        name: 'posts',
        path: 'posts',
        redirect: { name: 'dashboard' },
        meta: { requiresAuth: true },
    },
    {
        name: 'notifications',
        path: 'notifications',
        component: importPage('App/Notifications'),
        meta: { requiresAuth: true },
    },
    {
        name: 'analytics',
        path: 'analytics',
        redirect: { name: 'notifications' },
        meta: { requiresAuth: true },
    },
    {
        name: 'settings',
        path: 'settings',
        component: importPage('App/Settings'),
        meta: { requiresAuth: true },
    },
    {
        name: 'app-post-detail',
        path: 'post/:id',
        redirect: to => ({ name: 'post-detail', params: { id: to.params.id } }),
    },
    {
        name: 'profile',
        path: '@:profile',
        component: importPage('App/Profile'),
        props: true,
        meta: { requiresAuth: true },
    },
];

export default app_routes;