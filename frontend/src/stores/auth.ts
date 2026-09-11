import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, register as apiRegister, getMe, type User } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const user = ref<User | null>(null)

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    token.value = res.access_token
    localStorage.setItem('access_token', res.access_token)
    await fetchUser()
  }

  async function register(payload: { username: string; password: string; email?: string; role: 'user' | 'admin' }) {
    const res = await apiRegister(payload)
    token.value = res.access_token
    localStorage.setItem('access_token', res.access_token)
    user.value = res.user
  }

  async function fetchUser() {
    try {
      console.log('开始获取用户信息')
      user.value = await getMe()
      console.log('获取用户信息成功:', user.value?.username)
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      console.error('错误详情:', error.message)
      user.value = null
      token.value = ''
      localStorage.removeItem('access_token')
      // 触发重新登录
      window.location.href = '/login'
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { token, user, login, register, logout, fetchUser }
})
