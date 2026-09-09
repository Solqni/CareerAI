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
    // 根据用户角色跳转到不同页面
    if (auth.user?.role === 'admin') {
      router.push('/admin')
    } else {
      router.push('/dashboard')
    }
  } catch {
    error.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-side">
      <div class="bg-gradient"></div>
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="brand-content anim-fade-up">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <h1>CareerAI</h1>
        <p>看清自己 · 看懂岗位 · 做好规划 · 持续成长</p>
        <ul class="points">
          <li class="anim-fade-up anim-delay-2">AI 简历解析，能力画像一目了然</li>
          <li class="anim-fade-up anim-delay-3">JD 智能分析，人岗精准匹配</li>
          <li class="anim-fade-up anim-delay-4">模拟面试官，实战演练不怯场</li>
        </ul>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-side">
      <div class="login-card anim-fade-up">
        <h2>欢迎回来</h2>
        <p class="hint">登录你的 CareerAI 账号</p>
        <form @submit.prevent="handleLogin">
          <div class="field">
            <label>用户名</label>
            <input v-model="username" type="text" placeholder="请输入用户名" required />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="password" type="password" placeholder="请输入密码" required />
          </div>
          <Transition name="shake-wrap">
            <p v-if="error" class="error">{{ error }}</p>
          </Transition>
          <button type="submit" class="btn" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>
        <p class="footer-tip">还没有账号？<a href="/register">立即注册</a></p>
        <button class="back" @click="router.push('/')">← 返回首页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page { min-height: 100vh; display: flex; }

/* 左侧品牌区 */
.brand-side {
  flex: 1.1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(-45deg, #667eea, #764ba2, #6b8dd6, #8e6bbf);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  opacity: 0.4;
  animation: float 8s ease-in-out infinite;
}
.blob-1 { width: 300px; height: 300px; background: #f093fb; top: -60px; left: -40px; }
.blob-2 { width: 240px; height: 240px; background: #4facfe; bottom: -50px; right: -30px; animation-delay: -4s; }
.brand-content { position: relative; max-width: 420px; padding: 2rem; }
.logo {
  width: 64px; height: 64px;
  border-radius: 18px;
  background: rgba(255,255,255,0.18);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 1.4rem;
  animation: pulse 3.5s ease-in-out infinite;
}
.logo svg { width: 34px; height: 34px; }
.brand-content h1 { font-size: 2.6rem; margin-bottom: 0.6rem; }
.brand-content > p { opacity: 0.9; margin-bottom: 2rem; }
.points { list-style: none; display: flex; flex-direction: column; gap: 0.8rem; }
.points li {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(6px);
  border-radius: 12px;
  padding: 0.75rem 1.1rem;
  font-size: 0.92rem;
}

/* 右侧表单区 */
.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f8fc;
  padding: 2rem;
}
.login-card {
  background: #fff;
  padding: 2.6rem;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(102,126,234,0.12);
  width: 100%;
  max-width: 400px;
}
.login-card h2 { font-size: 1.6rem; color: #1a202c; }
.hint { color: #a0aec0; font-size: 0.9rem; margin: 0.4rem 0 1.8rem; }
.field { margin-bottom: 1.1rem; }
.field label { display: block; margin-bottom: 0.4rem; font-size: 0.88rem; color: #4a5568; font-weight: 500; }
.field input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.95rem;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
  outline: none;
}
.field input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(102,126,234,0.12);
  transform: translateY(-1px);
}
.error {
  color: #e53e3e;
  font-size: 0.85rem;
  margin-bottom: 0.6rem;
  animation: bubbleIn 0.3s ease;
}
.btn {
  width: 100%;
  padding: 0.85rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  background-size: 200% 100%;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background-position 0.4s ease, transform 0.2s ease, box-shadow 0.25s ease;
}
.btn:hover:not(:disabled) { background-position: 100% 0; transform: translateY(-2px); box-shadow: 0 10px 24px rgba(102,126,234,0.4); }
.btn:disabled { opacity: 0.7; cursor: not-allowed; }
.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.footer-tip { text-align: center; font-size: 0.82rem; color: #a0aec0; margin-top: 1.4rem; }
.back {
  display: block;
  margin: 0.8rem auto 0;
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.85rem;
  transition: transform 0.2s ease;
}
.back:hover { transform: translateX(-3px); }

.shake-wrap-enter-active { animation: bubbleIn 0.3s ease; }

@media (max-width: 860px) {
  .brand-side { display: none; }
}
</style>
