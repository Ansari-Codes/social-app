import importPage from "@/Core/importPage";

const auth_routes = [
    {
        name: 'login',
        path: 'login',
        props: true,
        component: importPage("Auth/Login"),
        meta: { requiresGuest: true },
    },
    {
        name: 'signup',
        path: 'signup',
        props: true,
        component: importPage("Auth/Signup"),
        meta: { requiresGuest: true },
    },
]

export default auth_routes
