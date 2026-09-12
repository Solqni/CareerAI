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
    // 能力匹配：/match 历史列表，/match/new 新建分析，/match/detail 报告详情
    { path: '/match', name: 'match-list', component: () => import('@/views/MatchListView.vue') },
    {
      path: '/match/new',
      name: 'match-new',
      component: () => import('@/views/MatchView.vue'),
      props: route => ({
        resumeId: route.query.resumeId ? Number(route.query.resumeId) : null,
        jobId: route.query.jobId ? Number(route.query.jobId) : null
      })
    },
    {
      path: '/match/detail/:matchId',
      name: 'match-detail',
      component: () => import('@/views/MatchDetailView.vue'),
      props: route => ({ matchId: route.params.matchId })
    },
    {
      path: '/match/plan/:matchId',
      name: 'match-plan',
      component: () => import('@/views/PlanView.vue'),
      props: route => ({ matchId: route.params.matchId })
    },
    { path: '/optimize', name: 'optimize', component: () => import('@/views/OptimizeView.vue') },
    { path: '/interview', name: 'interview', component: () => import('@/views/InterviewView.vue') },
  ],
})

export default router
