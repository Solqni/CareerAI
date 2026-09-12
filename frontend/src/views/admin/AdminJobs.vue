<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { deleteDocument, listDocuments, uploadDocument, type KnowledgeDoc } from '@/api/knowledge'

const jobs = ref<KnowledgeDoc[]>([])
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 获取岗位文档列表（与知识库同一数据源）
const fetchJobs = async () => {
  try {
    error.value = ''
    jobs.value = await listDocuments()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取岗位文档列表失败'
    console.error('获取岗位文档列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 触发文件选择
const handleUpload = () => {
  fileInput.value?.click()
}

// 上传岗位文档
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    uploading.value = true
    error.value = ''
    const doc = await uploadDocument(file)
    alert(`岗位文档「${doc.title}」入库成功，切分为 ${doc.chunk_count} 个片段`)
    await fetchJobs()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '岗位文档上传失败'
    console.error('岗位文档上传失败:', err)
  } finally {
    uploading.value = false
    target.value = ''
  }
}

// 删除岗位文档
const handleDelete = async (doc: KnowledgeDoc) => {
  if (!window.confirm(`确定删除岗位文档「${doc.title}」吗？该操作不可恢复。`)) return

  try {
    await deleteDocument(doc.id)
    alert('岗位文档已删除')
    await fetchJobs()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '删除失败'
    console.error('删除岗位文档失败:', err)
  }
}

onMounted(() => {
  fetchJobs()
})
</script>

<template>
  <div class="admin-jobs-page">
    <main class="content">
      <h2 class="page-title anim-fade-up">岗位管理</h2>
      <p class="page-sub anim-fade-up anim-delay-1">上传和管理岗位需求文档</p>

      <!-- 上传区域 -->
      <div class="upload-section anim-fade-up anim-delay-2">
        <div class="upload-card">
          <h3>上传岗位文档</h3>
          <p>支持 PDF、DOC、DOCX、Markdown、TXT 格式的岗位需求文档</p>
          <button class="upload-btn" @click="handleUpload" :disabled="uploading">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            {{ uploading ? '上传解析中...' : '选择文档上传' }}
          </button>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.doc,.docx,.md,.txt"
            style="display: none"
            @change="handleFileChange"
          />
        </div>
      </div>

      <!-- 岗位列表 -->
      <div class="jobs-section anim-fade-up anim-delay-3">
        <div class="section-header">
          <h3>现有岗位文档</h3>
          <span class="count">{{ jobs.length }} 个文档</span>
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

          <div v-for="doc in jobs" :key="doc.id" class="job-card">
            <div class="job-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div class="job-info">
              <h4>{{ doc.title }}</h4>
              <div class="job-meta">
                <span class="job-type">{{ doc.file_type }}</span>
                <span class="job-chunks">{{ doc.chunk_count }} 个切片</span>
              </div>
            </div>
            <button class="delete-btn" @click="handleDelete(doc)">删除</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-jobs-page { position: relative; }

/* 主体 */
.content { padding: 0; max-width: 1100px; margin: 0 auto; }
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
.upload-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

/* 岗位文档卡片 */
.job-card {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.2rem 1.4rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  display: flex;
  align-items: center;
  gap: 1rem;
}
.job-icon {
  width: 46px; height: 46px;
  border-radius: 12px;
  background: rgba(102,126,234,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #667eea;
  flex-shrink: 0;
}
.job-info { flex: 1; min-width: 0; }
.job-info h4 {
  font-size: 1rem;
  color: #2d3748;
  margin-bottom: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.job-meta { display: flex; gap: 0.6rem; }
.job-type, .job-chunks {
  font-size: 0.78rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.1);
  color: #5a67d8;
  font-weight: 500;
}
.job-chunks { background: rgba(72,187,120,0.1); color: #38a169; }
.delete-btn {
  padding: 0.4rem 0.9rem;
  border: 1px solid #fc8181;
  background: #fff;
  color: #e53e3e;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}
.delete-btn:hover { background: #e53e3e; color: #fff; border-color: transparent; }

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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>