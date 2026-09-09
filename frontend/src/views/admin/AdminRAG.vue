<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const collections = ref([])
const loading = ref(true)
const error = ref('')

// 获取RAG知识库列表
const fetchCollections = async () => {
  try {
    // TODO: 实现从后端获取RAG知识库列表的API调用
    loading.value = false
  } catch (err) {
    error.value = '获取知识库列表失败'
    loading.value = false
  }
}

// 重新构建知识库
const rebuildKnowledge = (collectionId: string) => {
  // TODO: 实现知识库重建功能
  alert(`知识库重建功能开发中`)
}

// 删除知识库
const deleteCollection = (collectionId: string) => {
  // TODO: 实现知识库删除功能
  if (confirm('确定要删除这个知识库吗？')) {
    alert('知识库删除功能开发中')
  }
}

onMounted(() => {
  fetchCollections()
})
</script>

<template>
  <div class="admin-rag-page">
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
      <h2 class="page-title anim-fade-up">RAG 知识库管理</h2>
      <p class="page-sub anim-fade-up anim-delay-1">管理和监控RAG知识库的构建</p>

      <!-- 概览卡片 -->
      <div class="overview-cards anim-fade-up anim-delay-2">
        <div class="card">
          <div class="card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
          </div>
          <div class="card-content">
            <h3>知识库总数</h3>
            <p class="number">{{ collections.length }}</p>
          </div>
        </div>

        <div class="card">
          <div class="card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <div class="card-content">
            <h3>处理状态</h3>
            <p class="status">运行中</p>
          </div>
        </div>

        <div class="card">
          <div class="card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </div>
          <div class="card-content">
            <h3>文档总数</h3>
            <p class="number">{{ collections.reduce((sum, col) => sum + (col.docCount || 0), 0) }}</p>
          </div>
        </div>
      </div>

      <!-- 知识库列表 -->
      <div class="collections-section anim-fade-up anim-delay-3">
        <div class="section-header">
          <h3>知识库列表</h3>
          <button class="add-btn" @click="alert('添加新知识库功能开发中')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加知识库
          </button>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>

        <div v-else class="collections-grid">
          <div v-if="collections.length === 0" class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <p>暂无知识库</p>
            <p class="hint">请先上传岗位文档创建知识库</p>
          </div>

          <!-- TODO: 实现知识库列表渲染 -->
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-rag-page { min-height: 100vh; position: relative; overflow: hidden; }
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

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.card {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  display: flex;
  align-items: center;
  gap: 1rem;
}
.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(102,126,234,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
}
.card-content h3 {
  font-size: 0.95rem;
  color: #718096;
  margin-bottom: 0.3rem;
}
.card-content .number {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2d3748;
}
.card-content .status {
  display: inline-block;
  padding: 0.2rem 0.8rem;
  background: rgba(72, 187, 120, 0.1);
  color: #48bb78;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
}

/* 知识库列表 */
.collections-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.collections-section .section-header h3 { font-size: 1.2rem; color: #2d3748; }
.add-btn {
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
.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}
.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
  grid-column: 1 / -1;
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