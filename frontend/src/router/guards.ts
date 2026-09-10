import { useAuthStore } from '@/stores/auth'

// 检查用户是否已登录
export function checkAuth(_to: any, _from: any, next: any) {
  const auth = useAuthStore()
  console.log('checkAuth:', { hasToken: !!auth.token, tokenLength: auth.token?.length })
  if (!auth.token) {
    // 未登录，跳转到登录页
    next('/login')
  } else {
    // 确保用户信息已加载
    if (!auth.user) {
      auth.fetchUser().then(() => next()).catch(() => next('/login'))
    } else {
      next()
    }
  }
}

// 检查用户角色
export function checkRole(_to: any, _from: any, next: any) {
  const auth = useAuthStore()
  if (!auth.user) {
    next('/login')
    return
  }

  const requiresAdmin = _to.meta?.requiresAdmin
  if (requiresAdmin && auth.user.role !== 'admin') {
    // 需要管理员权限但用户不是管理员
    next('/dashboard') // 跳转到普通用户仪表板
  } else {
    next()
  }
}

// 初始化时检查用户状态
export async function initializeAuth() {
  const auth = useAuthStore()
  if (auth.token) {
    try {
      await auth.fetchUser()
    } catch (error) {
      console.error('初始化用户状态失败:', error)
      auth.logout()
    }
  }
}