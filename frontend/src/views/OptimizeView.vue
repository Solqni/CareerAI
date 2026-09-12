<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { optimizeResume, dimensionMeta, type OptimizeResponse } from '@/api/optimize'
import BackButton from '@/components/BackButton.vue'

const router = useRouter()
const route = useRoute()
const jobStore = useJobStore()

const jobId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')
const result = ref<OptimizeResponse | null>(null)

const userJobs = computed(() => jobStore.jobs || [])

// 岗位显示名（列表接口的岗位名在 parsed_json 内）
function jobTitle(job: any) {
  return job?.parsed_json?.position_title || job?.position_title || `岗位 #${job?.id}`
}

onMounted(async () => {
  await jobStore.fetchJobs()
  // 支持从匹配详情页跳转时预选岗位
  const qid = Number(route.query.jobId)
  if (qid && userJobs.value.some(j => j.id === qid)) {
    jobId.value = qid
  }
})

async function generate() {
  if (!jobId.value) {
    error.value = '请选择目标岗位'
    return
  }
  try {
    loading.value = true
    error.value = ''
    result.value = await optimizeResume({ job_id: jobId.value })
  } catch (err: any) {
    error.value = err.response?.data?.detail || '优化建议生成失败'
    console.error('优化建议生成失败:', err)
  } finally {
    loading.value = false
  }
}

function goMatch() {
  const jid = jobId.value
  if (jid) router.push({ path: '/match', query: { jobId: String(jid) } })
  else router.push('/match')
}
</script>

<template>
  <div class="optimize-view">
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
        <button @click="router.push('/dashboard')">返回仪表盘</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <h2>简历优化建议</h2>
        <p class="form-desc">
          选择目标岗位，AI 将结合岗位要求与你的最新简历，从关键词、经历量化、内容增强、结构四个维度给出优化建议。
        </p>

        <!-- 表单 -->
        <div class="form-card">
          <div class="form-group">
            <label>目标岗位</label>
            <select v-model="jobId">
              <option :value="null" disabled>请选择岗位</option>
              <option v-for="job in userJobs" :key="job.id" :value="job.id">
                {{ jobTitle(job) }}
              </option>
            </select>
          </div>
          <button @click="generate" :disabled="loading || !jobId" class="primary-button">
            <span v-if="loading" class="loading">AI 分析中，约需 1-2 分钟...</span>
            <span v-else>生成优化建议</span>
          </button>
          <p v-if="error" class="error-text">{{ error }}</p>
        </div>

        <!-- 结果 -->
        <template v-if="result">
          <div class="result-head">
            <h3>优化建议 <span class="target">· {{ result.position_title }}</span></h3>
            <p v-if="result.summary" class="summary">{{ result.summary }}</p>
          </div>

          <!-- 知识库引用来源（管理员知识库） -->
          <div v-if="result.knowledge_refs?.length" class="knowledge-refs">
            <h4>知识库引用来源 <span class="ref-tag">来自管理员知识库</span></h4>
            <div class="ref-list">
              <div v-for="ref in result.knowledge_refs" :key="ref.doc_id" class="ref-item">
                <span class="ref-title">{{ ref.doc_title }}</span>
                <span class="ref-score">相关度 {{ Math.round(ref.similarity * 100) }}%</span>
              </div>
            </div>
          </div>

          <div class="suggestion-list">
            <div
              v-for="(s, i) in result.suggestions"
              :key="i"
              class="suggestion-item"
              :style="`--color: ${dimensionMeta[s.dimension]?.color || '#8b5cf6'}`"
            >
              <div class="sug-header">
                <span class="dim-tag">{{ dimensionMeta[s.dimension]?.label || s.dimension }}</span>
                <span class="sug-index">#{{ i + 1 }}</span>
              </div>
              <div class="sug-block">
                <span class="block-label">问题定位</span>
                <p>{{ s.issue }}</p>
              </div>
              <div class="sug-block">
                <span class="block-label">修改建议</span>
                <p>{{ s.suggestion }}</p>
              </div>
              <div v-if="s.example" class="sug-block example">
                <span class="block-label">示例改法</span>
                <p>{{ s.example }}</p>
              </div>
            </div>
          </div>

          <div class="bottom-actions">
            <button @click="goMatch" class="secondary-button">前往能力匹配 →</button>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<style scoped>
.optimize-view { min-height: 100vh; position: relative; overflow: hidden; }
.page-bg {
  position: fixed; inset: 0; z-index: -2;
  background: linear-gradient(-45deg, #f0f4ff, #e0e7ff, #f3e8ff, #e0f2fe);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.page-blob {
  position: fixed; border-radius: 50%; filter: blur(70px); z-index: -1;
  animation: float 8s ease-in-out infinite;
}
.blob-a { width: 320px; height: 320px; background: #667eea; opacity: 0.1; top: -60px; left: -40px; }
.blob-b { width: 280px; height: 280px; background: #f093fb; opacity: 0.08; bottom: -40px; right: -30px; animation-delay: -4s; }

.topbar {
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(16px);
  padding: 0.9rem 2rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  position: sticky; top: 0; z-index: 10;
  border-bottom: 1px solid rgba(255,255,255,0.5);
}
.topbar-left { display: flex; align-items: center; gap: 0.9rem; }
.brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 800; font-size: 1.15rem; cursor: pointer; }
.brand-logo { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff; display: flex; align-items: center; justify-content: center; }
.brand-logo svg { width: 20px; height: 20px; }
.topbar nav button {
  padding: 0.5rem 1rem; border: 1px solid #e2e8f0; background: #fff;
  border-radius: 10px; cursor: pointer; font-size: 0.9rem; transition: all 0.25s ease;
}
.topbar nav button:hover {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff; border-color: transparent; transform: translateY(-2px);
}

.content { padding: 2rem; max-width: 1100px; margin: 0 auto; }
.container { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 2rem; box-shadow: 0 2px 16px rgba(0,0,0,0.04); }
h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 0.5rem; }
.form-desc { color: #718096; margin-bottom: 1.5rem; }

.form-card {
  background: rgba(255,255,255,0.7); border-radius: 16px; padding: 1.5rem 2rem; margin-bottom: 2rem;
}
.form-group { margin-bottom: 1.2rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #2d3748; }
.form-group select {
  width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 10px;
  background: #fff; font-size: 1rem; transition: all 0.25s ease;
}
.form-group select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
.primary-button {
  background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff;
  border: none; border-radius: 10px; padding: 0.75rem 2rem; font-size: 1rem;
  font-weight: 600; cursor: pointer; transition: all 0.25s ease; width: 100%;
}
.primary-button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102,126,234,0.3); }
.primary-button:disabled { opacity: 0.6; cursor: not-allowed; }
.loading { display: inline-flex; align-items: center; gap: 0.5rem; }
.loading::before {
  content: ''; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite;
}
.error-text { color: #ef4444; margin-top: 0.8rem; font-size: 0.9rem; }

.result-head h3 { font-size: 1.4rem; color: #1a202c; margin-bottom: 0.5rem; }
.target { color: #7c3aed; font-weight: 700; }
.summary { color: #4a5568; background: rgba(139,92,246,0.08); border-radius: 12px; padding: 1rem 1.2rem; line-height: 1.7; margin-bottom: 1.5rem; }

.knowledge-refs {
  background: rgba(6,182,212,0.06); border-left: 4px solid #06b6d4;
  border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;
}
.knowledge-refs h4 { font-size: 0.95rem; color: #0e7490; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.5rem; }
.ref-tag { font-size: 0.72rem; font-weight: 600; color: #0e7490; background: rgba(6,182,212,0.12); border-radius: 999px; padding: 0.1rem 0.6rem; }
.ref-list { display: flex; flex-direction: column; gap: 0.4rem; }
.ref-item { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.ref-title { color: #164e63; font-size: 0.88rem; }
.ref-score { color: #0e7490; font-size: 0.8rem; white-space: nowrap; }

.suggestion-list { display: flex; flex-direction: column; gap: 1rem; }
.suggestion-item {
  background: rgba(255,255,255,0.75); border-radius: 14px; padding: 1.5rem;
  border-left: 4px solid var(--color); transition: all 0.25s ease;
}
.suggestion-item:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(102,126,234,0.15); }
.sug-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.9rem; }
.dim-tag {
  color: #fff; font-size: 0.8rem; font-weight: 700; padding: 0.25rem 0.8rem;
  border-radius: 999px; background: var(--color);
}
.sug-index { color: #a0aec0; font-size: 0.85rem; font-weight: 600; }
.sug-block { margin-bottom: 0.8rem; }
.sug-block:last-child { margin-bottom: 0; }
.block-label {
  display: inline-block; font-size: 0.78rem; font-weight: 700; color: #718096;
  margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em;
}
.sug-block p { color: #4a5568; line-height: 1.7; font-size: 0.95rem; }
.sug-block.example p {
  color: #2d3748; background: #f7fafc; border-radius: 8px; padding: 0.8rem 1rem;
  font-size: 0.9rem;
}

.bottom-actions { display: flex; gap: 1rem; margin-top: 1.8rem; }
.secondary-button {
  background: #fff; color: var(--primary); border: 1px solid var(--primary);
  border-radius: 10px; padding: 0.7rem 1.5rem; font-size: 0.95rem; font-weight: 600;
  cursor: pointer; transition: all 0.25s ease;
}
.secondary-button:hover {
  background: var(--primary); color: #fff; transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.2);
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; }
}
@keyframes float {
  0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); }
}
@keyframes spin { to { transform: rotate(360deg); } }
.anim-fade { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
