<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const settings = ref({
  system: {
    name: 'CareerAI',
    version: '1.0.0',
    status: '运行中'
  },
  database: {
    type: 'PostgreSQL',
    status: '连接正常',
    size: '128MB'
  },
  llm: {
    provider: 'DeepSeek',
    model: 'deepseek-chat',
    temperature: 0.3
  },
  rag: {
    chunkSize: 800,
    chunkOverlap: 80,
    topK: 5,
    similarityThreshold: 0.5
  }
})

const users = ref([])
const loading = ref(true)
const error = ref('')

// 获取系统信息
const fetchSystemInfo = async () => {
  try {
    // TODO: 实现从后端获取系统信息的API调用
    loading.value = false
  } catch (err) {
    error.value = '获取系统信息失败'
    loading.value = false
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    // TODO: 实现从后端获取用户列表的API调用
    loading.value = false
  } catch (err) {
    error.value = '获取用户列表失败'
    loading.value = false
  }
}

// 修改用户角色
const changeUserRole = (userId: string, newRole: string) => {
  // TODO: 实现修改用户角色功能
  alert('修改用户角色功能开发中')
}

// 删除用户
const deleteUser = (userId: string) => {
  // TODO: 实现删除用户功能
  if (confirm('确定要删除这个用户吗？')) {
    alert('删除用户功能开发中')
  }
}

onMounted(() => {
  fetchSystemInfo()
  fetchUsers()
})
</script>

<template>
  <div class="admin-settings-page">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>

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
        <button @click="router.push('/admin')">管理员控制台</button>
        <button @click="router.push('/admin/jobs')">岗位管理</button>
        <button @click="router.push('/admin/rag')">RAG 知识库</button>
        <button @click="router.push('/logout')">退出登录</button>
      </nav>
    </header>

    <main class="content">
      <h2 class="page-title anim-fade-up">系统设置</h2>
      <p class="page-sub anim-fade-up anim-delay-1">配置系统和管理用户</p>

      <!-- 系统信息 -->
      <div class="settings-section anim-fade-up anim-delay-2">
        <h3>系统信息</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>系统名称</label>
            <p>{{ settings.system.name }}</p>
          </div>
          <div class="setting-item">
            <label>版本</label>
            <p>{{ settings.system.version }}</p>
          </div>
          <div class="setting-item">
            <label>状态</label>
            <span class="status-badge success">{{ settings.system.status }}</span>
          </div>
        </div>
      </div>

      <!-- 数据库信息 -->
      <div class="settings-section anim-fade-up anim-delay-3">
        <h3>数据库</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>类型</label>
            <p>{{ settings.database.type }}</p>
          </div>
          <div class="setting-item">
            <label>状态</label>
            <span class="status-badge success">{{ settings.database.status }}</span>
          </div>
          <div class="setting-item">
            <label>存储大小</label>
            <p>{{ settings.database.size }}</p>
          </div>
        </div>
      </div>

      <!-- LLM配置 -->
      <div class="settings-section anim-fade-up anim-delay-4">
        <h3>大语言模型配置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>提供商</label>
            <p>{{ settings.llm.provider }}</p>
          </div>
          <div class="setting-item">
            <label>模型</label>
            <p>{{ settings.llm.model }}</p>
          </div>
          <div class="setting-item">
            <label>温度</label>
            <p>{{ settings.llm.temperature }}</p>
          </div>
        </div>
      </div>

      <!-- RAG配置 -->
      <div class="settings-section anim-fade-up anim-delay-5">
        <h3>RAG配置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label>块大小</label>
            <p>{{ settings.rag.chunkSize }}</p>
          </div>
          <div class="setting-item">
            <label>块重叠</label>
            <p>{{ settings.rag.chunkOverlap }}</p>
          </div>
          <div class="setting-item">
            <label>Top-K</label>
            <p>{{ settings.rag.topK }}</p>
          </div>
          <div class="setting-item">
            <label>相似度阈值</label>
            <p>{{ settings.rag.similarityThreshold }}</p>
          </div>
        </div>
      </div>

      <!-- 用户管理 -->
      <div class="settings-section anim-fade-up anim-delay-6">
        <div class="section-header">
          <h3>用户管理</h3>
          <button class="add-user-btn" @click="alert('添加新用户功能开发中')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加用户
          </button>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>

        <div v-else class="users-table">
          <div v-if="users.length === 0" class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="8.5" cy="7" r="4"></circle>
              <line x1="20" y1="8" x2="20" y2="14"></line>
              <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
            <p>暂无用户</p>
            <p class="hint">添加第一个用户开始使用系统</p>
          </div>

          <!-- TODO: 实现用户表格渲染 -->
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-settings-page { min-height: 100vh; position: relative; overflow: hidden; }
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

/* 设置区域 */
.settings-section {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  margin-bottom: 1.5rem;
}
.settings-section h3 { font-size: 1.1rem; margin-bottom: 1rem; color: #2d3748; }
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.setting-item label {
  font-weight: 500;
  color: #4a5568;
  font-size: 0.85rem;
}
.setting-item p {
  font-weight: 600;
  color: #2d3748;
}
.status-badge {
  display: inline-block;
  padding: 0.2rem 0.8rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
}
.status-badge.success {
  background: rgba(72, 187, 120, 0.1);
  color: #48bb78;
}

/* 用户管理 */
.settings-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.add-user-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.add-user-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}
.users-table {
  overflow-x: auto;
}
.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(102,126,234,0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}
.error p { color: #e53e3e; }
.empty-state svg { margin: 0 auto 1rem; opacity: 0.3; }
.empty-state p { color: #718096; margin-bottom: 0.5rem; }
.empty-state .hint { font-size: 0.9rem; color: #a0aec0; }

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
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>