import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
    { path: '/resume', name: 'resume', component: () => import('@/views/ResumeView.vue') },
    { path: '/jobs', name: 'jobs', component: () => import('@/views/JobsView.vue') },
    { path: '/match', name: 'match', component: () => import('@/views/MatchView.vue') },
    { path: '/interview', name: 'interview', component: () => import('@/views/InterviewView.vue') },
  ],
})

export default router
