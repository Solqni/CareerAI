<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'

const router = useRouter()

const jobs = ref([])
const loading = ref(true)
const error = ref('')

// 获取岗位列表
const fetchJobs = async () => {
  try {
    // TODO: 实现从后端获取岗位列表的API调用
    loading.value = false
  } catch (err) {
    error.value = '获取岗位列表失败'
    loading.value = false
  }
}

// 上传岗位文档
const handleUpload = () => {
  // TODO: 实现上传功能
  alert('岗位文档上传功能开发中')
}

onMounted(() => {
  fetchJobs()
})
</script>

<template>
  <div class="admin-jobs-page">
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
      <h2 class="page-title anim-fade-up">岗位管理</h2>
      <p class="page-sub anim-fade-up anim-delay-1">上传和管理岗位需求文档</p>

      <!-- 上传区域 -->
      <div class="upload-section anim-fade-up anim-delay-2">
        <div class="upload-card">
          <h3>上传岗位文档</h3>
          <p>支持 PDF、DOC、DOCX 格式的岗位需求文档</p>
          <button class="upload-btn" @click="handleUpload">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            选择文档上传
          </button>
        </div>
      </div>

      <!-- 岗位列表 -->
      <div class="jobs-section anim-fade-up anim-delay-3">
        <div class="section-header">
          <h3>现有岗位</h3>
          <span class="count">{{ jobs.length }} 个岗位</span>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>

        <div v-else class="jobs-list">
          <div v-if="jobs.length === 0" class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            <p>暂无岗位文档</p>
            <p class="hint">请上传岗位需求文档开始构建知识库</p>
          </div>

          <!-- TODO: 实现岗位列表渲染 -->
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-jobs-page { min-height: 100vh; position: relative; overflow: hidden; }
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

/* 上传区域 */
.upload-section {
  margin-bottom: 2rem;
}
.upload-card {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  text-align: center;
}
.upload-card h3 { font-size: 1.2rem; margin-bottom: 0.5rem; color: #2d3748; }
.upload-card p { color: #718096; margin-bottom: 1.5rem; }
.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.5rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}

/* 岗位列表 */
.jobs-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.jobs-section .section-header h3 { font-size: 1.2rem; color: #2d3748; }
.count {
  background: rgba(102,126,234,0.1);
  color: #667eea;
  padding: 0.2rem 0.8rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
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