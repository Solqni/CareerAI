<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const user = ref({
  username: '',
  email: '',
  role: ''
})

onMounted(async () => {
  try {
    await auth.fetchUser()
    if (auth.user) {
      user.value = {
        username: auth.user.username,
        email: auth.user.email || '',
        role: auth.user.role
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="admin-page">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>
    <div class="page-blob blob-c"></div>
    <header class="topbar anim-fade">
      <div class="topbar-left">
        <BackButton class="topbar-back" />
        <div class="brand" @click="router.push('/')">
          <div class="brand-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <span>CareerAI</span>
        </div>
      </div>
      <nav>
        <button v-if="route.name !== 'admin'" @click="router.push('/admin')">控制台</button>
        <button @click="router.push('/admin/jobs')">岗位管理</button>
        <button @click="router.push('/admin/rag')">RAG 知识库</button>
        <button @click="router.push('/admin/settings')">系统设置</button>
        <button @click="handleLogout">退出登录</button>
      </nav>
    </header>

    <main class="content">
      <!-- 控制台首页内容（仅 /admin 显示，子页面走 router-view） -->
      <template v-if="route.name === 'admin'">
      <h2 class="page-title anim-fade-up">管理员控制台</h2>
      <p class="page-sub anim-fade-up anim-delay-1">管理岗位文档和 RAG 知识库</p>

      <!-- 用户信息卡片 -->
      <div class="user-card anim-fade-up anim-delay-2">
        <div class="card-header">
          <h3>当前用户</h3>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">用户名:</span>
            <span class="value">{{ user.username }}</span>
          </div>
          <div class="info-item">
            <span class="label">邮箱:</span>
            <span class="value">{{ user.email || '未设置' }}</span>
          </div>
          <div class="info-item">
            <span class="label">角色:</span>
            <span class="value admin-badge">管理员</span>
          </div>
        </div>
      </div>

      <!-- 功能面板 -->
      <div class="panels">
        <!-- 岗位管理 -->
        <div class="panel anim-fade-up anim-delay-3">
          <h3>岗位管理</h3>
          <p class="panel-desc">上传和管理岗位需求文档</p>
          <button class="panel-btn" @click="router.push('/admin/jobs')">
            管理岗位
          </button>
        </div>

        <!-- RAG 知识库 -->
        <div class="panel anim-fade-up anim-delay-4">
          <h3>RAG 知识库</h3>
          <p class="panel-desc">构建和管理 RAG 知识库（阶段二功能）</p>
          <button class="panel-btn" @click="router.push('/admin/rag')">
            管理知识库
          </button>
        </div>

        <!-- 系统设置 -->
        <div class="panel anim-fade-up anim-delay-5">
          <h3>系统设置</h3>
          <p class="panel-desc">系统配置和用户管理</p>
          <button class="panel-btn" @click="router.push('/admin/settings')">
            系统设置
          </button>
        </div>
      </div>
      </template>

      <!-- 子页面挂载点：/admin/jobs、/admin/rag、/admin/settings -->
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-page { min-height: 100vh; position: relative; overflow: hidden; }
.page-bg {
  position: fixed; inset: 0; z-index: -2;
  background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.page-blob {
  position: fixed; border-radius: 50%; filter: blur(70px); z-index: -1;
  animation: float 8s ease-in-out infinite;
}
.blob-a { width: 320px; height: 320px; background: #667eea; opacity: 0.1; top: -60px; left: -40px; }
.blob-b { width: 280px; height: 280px; background: #f093fb; opacity: 0.08; bottom: -40px; right: -30px; animation-delay: -4s; }
.blob-c { width: 200px; height: 200px; background: #4facfe; opacity: 0.08; top: 40%; left: 60%; animation-delay: -6s; }

/* 顶栏 */
.topbar {
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(16px);
  padding: 0.9rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid rgba(255,255,255,0.5);
}
.brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 800; font-size: 1.15rem; cursor: pointer; }
.topbar-left { display: flex; align-items: center; gap: 0.9rem; }
.brand-logo {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  animation: pulse 3s ease-in-out infinite;
}
.brand-logo svg { width: 20px; height: 20px; }
.topbar nav { display: flex; gap: 0.5rem; }
.topbar nav button {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.25s ease;
}
.topbar nav button svg { width: 15px; height: 15px; }
.topbar nav button:hover {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.35);
}

/* 主体 */
.content { padding: 2rem; max-width: 1100px; margin: 0 auto; }
.page-title { font-size: 1.5rem; color: #1a202c; }
.page-sub { color: #718096; margin: 0.3rem 0 1.8rem; }

/* 用户信息卡片 */
.user-card {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  margin-bottom: 2rem;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.card-header h3 { font-size: 1.1rem; color: #2d3748; }
.card-body { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.info-item { display: flex; justify-content: space-between; align-items: center; }
.label { font-weight: 500; color: #4a5568; }
.value { font-weight: 600; color: #2d3748; }
.admin-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
}

/* 功能面板 */
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.2rem;
}
.panel {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}
.panel h3 { font-size: 1.05rem; margin-bottom: 0.8rem; color: #2d3748; }
.panel-desc { color: #718096; font-size: 0.88rem; margin-bottom: 1.2rem; }
.panel-btn {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.panel-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}

/* 动画 */
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>