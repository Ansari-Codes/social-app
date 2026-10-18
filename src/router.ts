import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import importPage from "@/Core/importPage";
import { useMeStore } from "@/Stores/meStore";
import { requestAuthPrompt } from "@/Core/authPrompt";

import auth_routes from "./Pages/Auth/routes";
import app_routes from "@/Pages/App/routes";

const history = import.meta.env.PROD
    ? createWebHashHistory(import.meta.env.BASE_URL)
    : createWebHistory(import.meta.env.BASE_URL);

const router = createRouter({
    history,
    routes: [
        {
            path: '/auth',
            component: importPage("Auth"),
            children: auth_routes,
            meta: { requiresGuest: true },
        },
        {
            path: '/',
            component: importPage("App"),
            children: app_routes,
        }
    ]
});

router.beforeEach(async (to) => {
    const me = useMeStore();
    await me.init();

    const requiresAuth = Boolean(to.meta.requiresAuth);
    const requiresGuest = Boolean(to.meta.requiresGuest);
    const requiresAdmin = Boolean(to.meta.requiresAdmin);

    if (requiresAuth && !me.isAuthenticated) {
        requestAuthPrompt();
        return { name: 'app' };
    }

    if (requiresGuest && me.isAuthenticated) {
        return { name: 'app' };
    }

    if (requiresAdmin && !me.isAdmin) {
        return { name: 'app' };
    }

    return true;
});

export default router;
