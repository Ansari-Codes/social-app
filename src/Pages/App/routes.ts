import importPage from "@/Core/importPage";
import type { RouteRecordRaw } from 'vue-router';

const app_routes: RouteRecordRaw[] = [
    {
        name: 'app',
        path: '',
        component: importPage('App/Feed'),
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
        name: 'terms',
        path: 'terms',
        component: importPage('Home/Terms'),
    },
    {
        name: 'about',
        path: 'about',
        component: importPage('Home/About'),
    },
    {
        name: 'settings',
        path: 'settings',
        component: importPage('App/Settings'),
        meta: { requiresAuth: true },
    },
    {
        name: 'post-detail',
        path: 'post/:id',
        component: importPage('App/Post'),
        props: true,
    },
    {
        name: 'profile',
        path: '@:profile',
        component: importPage('App/Profile'),
        props: true,
        meta: { requiresAuth: true },
    },
    {
        path: 'tos',
        redirect: { name: 'terms' },
    },
];

export default app_routes;