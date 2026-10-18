import importPage from "@/Core/importPage";

const home_routes = [
    {
        name: 'home',
        path: '',
        component: importPage('App/Feed')
    },
    {
        path: 'about',
        component: importPage('Home/About')
    },
    {
        name: 'post-detail',
        path: 'post/:id',
        component: importPage('App/Post'),
        props: true,
    },
    {
        path: 'tos',
        component: importPage('Home/Terms'),
    }
]

export default home_routes
