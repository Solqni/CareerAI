<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { collectKnowledge, type CollectKnowledgeResult } from '@/api/admin'
import { deleteDocument, listDocuments, uploadDocument, type KnowledgeDoc } from '@/api/knowledge'

const collections = ref<KnowledgeDoc[]>([])
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// ===== AI 知识采集 =====
const aiTopic = ref('')
const aiDocCount = ref(1)
const aiCollecting = ref(false)
const aiResult = ref<CollectKnowledgeResult | null>(null)
const aiError = ref('')

const handleAiCollect = async () => {
  const topic = aiTopic.value.trim()
  if (!topic) {
    aiError.value = '请输入知识主题，如：Python 后端面试高频考点'
    return
  }
  try {
    aiCollecting.value = true
    aiError.value = ''
    aiResult.value = null
    aiResult.value = await collectKnowledge({ topic, doc_count: aiDocCount.value })
    await fetchCollections()
  } catch (err: any) {
    aiError.value = err.response?.data?.message || err.response?.data?.detail || 'AI 知识采集失败'
    console.error('AI 知识采集失败:', err)
  } finally {
    aiCollecting.value = false
  }
}

// 文档切片总数（概览卡片用）
const totalChunks = computed(() =>
  collections.value.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0)
)

// 平均每个文档的切片数（无文档时显示 —）
const avgChunks = computed(() =>
  collections.value.length
    ? (totalChunks.value / collections.value.length).toFixed(1)
    : '—'
)

// 获取知识库文档列表
const fetchCollections = async () => {
  try {
    error.value = ''
    collections.value = await listDocuments()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取知识库列表失败'
    console.error('获取知识库列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 触发文件选择
const triggerUpload = () => {
  fileInput.value?.click()
}

// 上传文档
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    uploading.value = true
    error.value = ''
    const doc = await uploadDocument(file)
    showAlert(`文档「${doc.title}」入库成功，切分为 ${doc.chunk_count} 个片段`)
    await fetchCollections()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '文档上传失败'
    console.error('文档上传失败:', err)
  } finally {
    uploading.value = false
    target.value = ''
  }
}

// 删除文档
const handleDelete = async (doc: KnowledgeDoc) => {
  if (!window.confirm(`确定删除文档「${doc.title}」吗？该操作不可恢复。`)) return

  try {
    await deleteDocument(doc.id)
    showAlert('文档已删除')
    await fetchCollections()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '删除失败'
    console.error('删除文档失败:', err)
  }
}

// 显示提示（模板中无法直接访问 window.alert）
const showAlert = (message: string) => {
  alert(message)
}

onMounted(() => {
  fetchCollections()
})
</script>

<template>
  <div class="admin-rag-page">
    <main class="content">
      <h2 class="page-title anim-fade-up">RAG 知识库管理</h2>
      <p class="page-sub anim-fade-up anim-delay-1">管理和监控RAG知识库的构建</p>

      <!-- 概览卡片 -->
      <div class="overview-cards anim-fade-up anim-delay-2">
        <div class="card">
          <div class="card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
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
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <div class="card-content">
            <h3>平均切片数/文档</h3>
            <p class="number">{{ avgChunks }}</p>
          </div>
        </div>

        <div class="card">
          <div class="card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
          </div>
          <div class="card-content">
            <h3>文档切片总数</h3>
            <p class="number">{{ totalChunks }}</p>
          </div>
        </div>
      </div>

      <!-- AI 知识采集 -->
      <div class="ai-collect-card anim-fade-up anim-delay-2">
        <div class="collect-head">
          <h3>AI 采集知识文档</h3>
          <span class="collect-tag">自动生成 → 切分 → 向量化入库</span>
        </div>
        <p>输入知识主题，AI 生成结构化知识文档并自动构建 RAG 索引，标题带【AI采集】前缀</p>
        <div class="collect-form">
          <input
            v-model="aiTopic"
            class="collect-input"
            placeholder="知识主题，如：Python 后端面试高频考点 / 前端学习路线"
            :disabled="aiCollecting"
            @keyup.enter="handleAiCollect"
          />
          <select v-model.number="aiDocCount" class="collect-select" :disabled="aiCollecting">
            <option :value="1">1 篇</option>
            <option :value="2">2 篇</option>
            <option :value="3">3 篇</option>
          </select>
          <button class="collect-btn" :disabled="aiCollecting" @click="handleAiCollect">
            {{ aiCollecting ? 'AI 正在撰写并入库…（约 30-60 秒）' : '开始 AI 采集' }}
          </button>
        </div>
        <p v-if="aiError" class="collect-error">{{ aiError }}</p>
        <div v-if="aiResult" class="collect-result">
          <p class="result-title">已生成 {{ aiResult.generated_count }} 篇文档并入库：</p>
          <ul>
            <li v-for="d in aiResult.documents" :key="d.id">
              {{ d.title }} · {{ d.chunk_count }} 个切片
            </li>
          </ul>
        </div>
      </div>

      <!-- 知识库列表 -->
      <div class="collections-section anim-fade-up anim-delay-3">
        <div class="section-header">
          <h3>知识库文档</h3>
          <button class="add-btn" @click="triggerUpload" :disabled="uploading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            {{ uploading ? '上传解析中...' : '上传文档' }}
          </button>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.doc,.docx,.md,.txt"
            style="display: none"
            @change="handleFileChange"
          />
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
            <p>暂无知识库文档</p>
            <p class="hint">请先上传岗位文档创建知识库</p>
          </div>

          <div v-for="doc in collections" :key="doc.id" class="doc-card">
            <div class="doc-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div class="doc-info">
              <h4>{{ doc.title }}</h4>
              <div class="doc-meta">
                <span class="doc-type">{{ doc.file_type }}</span>
                <span class="doc-chunks">{{ doc.chunk_count }} 个切片</span>
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
.admin-rag-page { position: relative; }

/* 主体 */
.content { padding: 0; max-width: 1100px; margin: 0 auto; }
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

/* AI 采集卡片 */
.ai-collect-card {
  background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
  border: 1px solid rgba(102,126,234,0.25);
  border-radius: 16px;
  padding: 1.5rem 1.8rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  margin-bottom: 2rem;
}
.collect-head { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.4rem; flex-wrap: wrap; }
.ai-collect-card h3 { font-size: 1.15rem; color: #2d3748; }
.collect-tag {
  font-size: 0.72rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.12);
  color: #5a67d8;
  font-weight: 500;
}
.ai-collect-card > p { color: #718096; margin-bottom: 1.1rem; font-size: 0.88rem; }
.collect-form { display: flex; gap: 0.7rem; flex-wrap: wrap; }
.collect-input {
  flex: 1;
  min-width: 220px;
  padding: 0.65rem 0.9rem;
  border: 1px solid #cbd5e0;
  border-radius: 10px;
  font-size: 0.9rem;
  outline: none;
  background: #fff;
}
.collect-input:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
.collect-select {
  padding: 0.65rem 0.7rem;
  border: 1px solid #cbd5e0;
  border-radius: 10px;
  background: #fff;
  font-size: 0.9rem;
  outline: none;
}
.collect-btn {
  padding: 0.65rem 1.6rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}
.collect-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102,126,234,0.3); }
.collect-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.collect-error { color: #e53e3e; font-size: 0.85rem; margin-top: 0.7rem; }
.collect-result {
  margin-top: 1rem;
  background: rgba(72,187,120,0.08);
  border: 1px solid rgba(72,187,120,0.25);
  border-radius: 12px;
  padding: 0.9rem 1.1rem;
}
.result-title { font-size: 0.9rem; font-weight: 600; color: #22543d; margin-bottom: 0.5rem; }
.collect-result ul { list-style: none; }
.collect-result li { font-size: 0.85rem; color: #4a5568; padding: 0.15rem 0; }

/* 知识库列表 */
.collections-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.collections-section .section-header h3 { font-size: 1.2rem; color: #2d3748; }
.add-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

/* 文档卡片 */
.doc-card {
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
.doc-icon {
  width: 46px; height: 46px;
  border-radius: 12px;
  background: rgba(102,126,234,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #667eea;
  flex-shrink: 0;
}
.doc-info { flex: 1; min-width: 0; }
.doc-info h4 {
  font-size: 1rem;
  color: #2d3748;
  margin-bottom: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-meta { display: flex; gap: 0.6rem; }
.doc-type, .doc-chunks {
  font-size: 0.78rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.1);
  color: #5a67d8;
  font-weight: 500;
}
.doc-chunks { background: rgba(72,187,120,0.1); color: #38a169; }
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>