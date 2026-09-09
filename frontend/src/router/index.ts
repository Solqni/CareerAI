import { createRouter, createWebHistory } from 'vue-router'

import { checkAuth, checkRole } from './guards'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      beforeEnter: checkAuth
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { requiresAdmin: true },
      beforeEnter: [checkAuth, checkRole],
      children: [
        {
          path: 'jobs',
          name: 'admin-jobs',
          component: () => import('@/views/admin/AdminJobs.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'rag',
          name: 'admin-rag',
          component: () => import('@/views/admin/AdminRAG.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: () => import('@/views/admin/AdminSettings.vue'),
          meta: { requiresAdmin: true }
        }
      ]
    },
    { path: '/resume', name: 'resume', component: () => import('@/views/ResumeView.vue') },
    { path: '/jobs', name: 'jobs', component: () => import('@/views/JobsView.vue') },
    { path: '/match', name: 'match', component: () => import('@/views/MatchView.vue') },
    { path: '/interview', name: 'interview', component: () => import('@/views/InterviewView.vue') },
  ],
})

export default router
