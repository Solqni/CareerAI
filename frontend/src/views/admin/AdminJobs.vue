<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  collectJobsFromWeb,
  deleteAdminJob,
  listAdminJobs,
  type AdminJob,
  type CollectJobsResult,
} from '@/api/admin'
import { deleteDocument, listDocuments, uploadDocument, type KnowledgeDoc } from '@/api/knowledge'

const jobs = ref<KnowledgeDoc[]>([])
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// ===== AI 招聘网站采集 =====
const collectKeyword = ref('')
const collectCount = ref(3)
const collecting = ref(false)
const collectResult = ref<CollectJobsResult | null>(null)
const collectError = ref('')

// ===== 全平台岗位库 =====
const platformJobs = ref<AdminJob[]>([])
const jobsLoading = ref(true)
const jobsError = ref('')
const sourceMeta: Record<string, { label: string; cls: string }> = {
  web_ncss: { label: '实时采集', cls: 'src-live' },
  ai_fallback: { label: 'AI 模拟', cls: 'src-ai' },
  manual: { label: '手动录入', cls: 'src-manual' },
}

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

const fetchPlatformJobs = async () => {
  try {
    jobsError.value = ''
    platformJobs.value = await listAdminJobs()
  } catch (err: any) {
    jobsError.value = err.response?.data?.detail || '获取岗位库失败'
    console.error('获取岗位库失败:', err)
  } finally {
    jobsLoading.value = false
  }
}

const handleCollect = async () => {
  const kw = collectKeyword.value.trim()
  if (!kw) {
    collectError.value = '请输入岗位关键词，如：Python、前端、数据分析'
    return
  }
  try {
    collecting.value = true
    collectError.value = ''
    collectResult.value = null
    collectResult.value = await collectJobsFromWeb({ keyword: kw, count: collectCount.value })
    await fetchPlatformJobs()
  } catch (err: any) {
    collectError.value = err.response?.data?.message || err.response?.data?.detail || '岗位采集失败'
    console.error('岗位采集失败:', err)
  } finally {
    collecting.value = false
  }
}

const handleDeletePlatformJob = async (job: AdminJob) => {
  if (!window.confirm(`确定删除岗位「${job.position_title || job.id}」吗？其关联的匹配报告将一并删除，不可恢复。`)) return
  try {
    await deleteAdminJob(job.id)
    await fetchPlatformJobs()
  } catch (err: any) {
    jobsError.value = err.response?.data?.message || '删除岗位失败'
    console.error('删除岗位失败:', err)
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
  fetchPlatformJobs()
})
</script>

<template>
  <div class="admin-jobs-page">
    <main class="content">
      <h2 class="page-title anim-fade-up">岗位管理</h2>
      <p class="page-sub anim-fade-up anim-delay-1">AI 招聘网站采集、岗位库与岗位需求文档管理</p>

      <!-- AI 采集区域 -->
      <div class="collect-section anim-fade-up anim-delay-2">
        <div class="collect-card">
          <div class="collect-head">
            <h3>AI 从招聘网站采集岗位</h3>
            <span class="collect-tag">真实数据源：国家大学生就业服务平台</span>
          </div>
          <p>输入岗位关键词，AI 实时抓取在招岗位并解析入库；采集结果全平台共享，所有用户的能力匹配均可选用</p>
          <div class="collect-form">
            <input
              v-model="collectKeyword"
              class="collect-input"
              placeholder="岗位关键词，如：Python / 前端开发 / 数据分析"
              :disabled="collecting"
              @keyup.enter="handleCollect"
            />
            <select v-model.number="collectCount" class="collect-select" :disabled="collecting">
              <option :value="3">3 条</option>
              <option :value="5">5 条</option>
              <option :value="8">8 条</option>
              <option :value="10">10 条</option>
            </select>
            <button class="collect-btn" :disabled="collecting" @click="handleCollect">
              {{ collecting ? '正在抓取并解析岗位…（约 20-60 秒）' : '开始 AI 采集' }}
            </button>
          </div>
          <p v-if="collectError" class="collect-error">{{ collectError }}</p>
          <div v-if="collectResult" class="collect-result">
            <p class="result-title">
              采集完成（{{ collectResult.source_label }}）：新增 {{ collectResult.collected_count }} 条
              <template v-if="collectResult.skipped_count">，去重跳过 {{ collectResult.skipped_count }} 条</template>
              <template v-if="collectResult.failed_count">，失败 {{ collectResult.failed_count }} 条</template>
              <template v-if="!collectResult.collected_count && collectResult.skipped_count">
                ——本次抓取到的岗位均已存在于岗位库
              </template>
            </p>
            <ul v-if="collectResult.collected.length">
              <li v-for="c in collectResult.collected" :key="c.id">
                #{{ c.id }} {{ c.position_title || '未命名岗位' }}
                <template v-if="c.company"> · {{ c.company }}</template>
                <template v-if="c.city"> · {{ c.city }}</template>
              </li>
            </ul>
            <ul v-if="collectResult.skipped?.length">
              <li v-for="(s, i) in collectResult.skipped" :key="`skip-${i}`" class="skipped-item">
                已存在：{{ s.position_title }}
                <template v-if="s.company"> · {{ s.company }}</template>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 全平台岗位库 -->
      <div class="jobs-section anim-fade-up anim-delay-3">
        <div class="section-header">
          <h3>全平台岗位库</h3>
          <span class="count">{{ platformJobs.length }} 个岗位</span>
        </div>

        <div v-if="jobsLoading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="jobsError" class="error">
          <p>{{ jobsError }}</p>
        </div>

        <div v-else class="platform-list">
          <div v-if="platformJobs.length === 0" class="empty-state">
            <p>暂无岗位</p>
            <p class="hint">通过上方 AI 采集或用户上传 JD 产生岗位</p>
          </div>
          <div v-for="job in platformJobs" :key="job.id" class="job-card">
            <div class="job-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2"></rect>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
              </svg>
            </div>
            <div class="job-info">
              <h4>{{ job.position_title || `岗位 #${job.id}` }}</h4>
              <div class="job-meta">
                <span class="job-type" :class="sourceMeta[job.source]?.cls || 'src-manual'">
                  {{ job.source_label }}
                </span>
                <span v-if="job.company" class="job-chunks">{{ job.company }}</span>
                <span v-if="job.city" class="job-chunks">{{ job.city }}</span>
                <span v-if="job.is_shared" class="job-shared">共享</span>
                <span class="job-owner">@{{ job.owner_username }}</span>
              </div>
            </div>
            <button class="delete-btn" @click="handleDeletePlatformJob(job)">删除</button>
          </div>
        </div>
      </div>

      <!-- 岗位文档（知识库） -->
      <div class="jobs-section anim-fade-up anim-delay-4">
        <div class="section-header">
          <h3>岗位需求文档</h3>
          <span class="count">{{ jobs.length }} 个文档</span>
        </div>

        <div class="upload-inline">
          <button class="upload-btn" @click="handleUpload" :disabled="uploading">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            {{ uploading ? '上传解析中...' : '上传岗位文档' }}
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

        <div v-else class="platform-list">
          <div v-if="jobs.length === 0" class="empty-state">
            <p>暂无岗位文档</p>
            <p class="hint">请上传岗位需求文档开始构建知识库</p>
          </div>

          <div v-for="doc in jobs" :key="doc.id" class="job-card">
            <div class="job-icon doc">
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

/* AI 采集卡片 */
.collect-section { margin-bottom: 2rem; }
.collect-card {
  background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
  border: 1px solid rgba(102,126,234,0.25);
  border-radius: 16px;
  padding: 1.5rem 1.8rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}
.collect-head { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.4rem; flex-wrap: wrap; }
.collect-card h3 { font-size: 1.15rem; color: #2d3748; }
.collect-tag {
  font-size: 0.72rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.12);
  color: #5a67d8;
  font-weight: 500;
}
.collect-card > p { color: #718096; margin-bottom: 1.1rem; font-size: 0.88rem; }
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
.collect-result li.skipped-item { color: #a0aec0; }

/* 岗位列表 */
.jobs-section { margin-bottom: 2rem; }
.jobs-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
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
.upload-inline { margin-bottom: 1rem; }
.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 1.2rem;
  background: #fff;
  color: #5a67d8;
  border: 1px solid #cbd5e0;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.upload-btn:hover:not(:disabled) { border-color: #667eea; box-shadow: 0 4px 14px rgba(102,126,234,0.2); }
.upload-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.platform-list { display: flex; flex-direction: column; gap: 0.7rem; }
.job-card {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1rem 1.3rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  display: flex;
  align-items: center;
  gap: 1rem;
}
.job-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: rgba(102,126,234,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #667eea;
  flex-shrink: 0;
}
.job-icon.doc { background: rgba(72,187,120,0.1); color: #38a169; }
.job-info { flex: 1; min-width: 0; }
.job-info h4 {
  font-size: 0.98rem;
  color: #2d3748;
  margin-bottom: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.job-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
.job-type, .job-chunks {
  font-size: 0.75rem;
  padding: 0.12rem 0.55rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.1);
  color: #5a67d8;
  font-weight: 500;
}
.job-chunks { background: #edf2f7; color: #4a5568; }
.src-live { background: rgba(72,187,120,0.12) !important; color: #22543d !important; }
.src-ai { background: rgba(237,137,54,0.12) !important; color: #7b341e !important; }
.src-manual { background: #edf2f7 !important; color: #4a5568 !important; }
.job-shared {
  font-size: 0.75rem;
  padding: 0.12rem 0.55rem;
  border-radius: 999px;
  background: rgba(102,126,234,0.12);
  color: #5a67d8;
  font-weight: 600;
}
.job-owner { font-size: 0.75rem; color: #a0aec0; }
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

.loading, .error, .empty-state {
  text-align: center;
  padding: 2.5rem;
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
.empty-state p { color: #718096; margin-bottom: 0.5rem; }
.empty-state .hint { font-size: 0.9rem; color: #a0aec0; }

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
