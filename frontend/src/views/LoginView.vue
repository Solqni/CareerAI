<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/dashboard')
  } catch {
    error.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h2>登录 CareerAI</h2>
      <form @submit.prevent="handleLogin">
        <div class="field"><label>用户名</label><input v-model="username" type="text" required /></div>
        <div class="field"><label>密码</label><input v-model="password" type="password" required /></div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f7fa; }
.login-card { background: #fff; padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 360px; }
.login-card h2 { margin-bottom: 1.5rem; text-align: center; }
.field { margin-bottom: 1rem; }
.field label { display: block; margin-bottom: 0.35rem; font-size: 0.9rem; color: #555; }
.field input { width: 100%; padding: 0.6rem 0.8rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }
.btn { width: 100%; padding: 0.7rem; background: #667eea; color: #fff; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 0.5rem; }
.btn:disabled { opacity: 0.6; }
.error { color: #e74c3c; font-size: 0.85rem; margin-bottom: 0.5rem; }
</style>
