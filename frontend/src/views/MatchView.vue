<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { useMatchStore } from '@/stores/match'
import { useResumeStore } from '@/stores/resume'
import BackButton from '@/components/BackButton.vue'

const props = defineProps<{
  resumeId?: number | null
  jobId?: number | null
}>()

const router = useRouter()
const jobStore = useJobStore()
const matchStore = useMatchStore()
const resumeStore = useResumeStore()

// 表单数据
const resumeId = ref<number | null>(null)
const jobId = ref<number | null>(null)

// 状态
const initializing = ref(true)
const analyzing = ref(false)
const error = ref('')

// 用户简历列表（真实数据，来自 /resume/list）
const userResumes = computed(() => resumeStore.resumes || [])
// 简历显示名
function resumeName(resume: { id: number; name?: string | null }) {
  return resume?.name || `简历 #${resume?.id}`
}
// 用户岗位列表
const userJobs = computed(() => jobStore.jobs || [])
// 岗位显示名
function jobTitle(job: any) {
  return job?.position_title || `岗位 #${job?.id}`
}
// 已选中的岗位
const selectedJob = computed(() => userJobs.value.find(j => j.id === jobId.value))

// 初始化：并行拉取简历列表 + 岗位列表
onMounted(async () => {
  try {
    await Promise.all([resumeStore.fetchResumes(), jobStore.fetchJobs()])

    // 简历：优先用跳转链接指定的，否则默认选最新一份（列表按 id 倒序，第一份即最新）
    if (props.resumeId && userResumes.value.some(r => r.id === props.resumeId)) {
      resumeId.value = props.resumeId
    } else {
      resumeId.value = userResumes.value[0]?.id ?? null
    }

    // 岗位：支持从岗位分析页跳转时预选
    if (props.jobId && userJobs.value.some(j => j.id === props.jobId)) {
      jobId.value = props.jobId
    }
  } finally {
    initializing.value = false
  }
})

// 开始分析：成功后跳转报告详情页
async function startAnalysis() {
  if (!resumeId.value || !jobId.value) {
    error.value = '请先上传解析简历并完成岗位分析'
    return
  }

  try {
    analyzing.value = true
    error.value = ''

    const report = await matchStore.analyzeMatchData({
      resume_id: resumeId.value,
      job_id: jobId.value
    })

    // 跳转到详情页（使用真实报告 ID）
    router.push(`/match/detail/${report.id}`)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '分析匹配度失败'
    console.error('分析匹配度失败:', err)
  } finally {
    analyzing.value = false
  }
}
</script>

<template>
  <div class="match-analysis">
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
        <button @click="router.push('/match')">历史分析</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <div v-if="initializing" class="loading-state">
          <div class="spinner"></div>
          <p>加载数据中...</p>
        </div>

        <!-- 表单区域 -->
        <div v-else class="form-section anim-fade-up">
          <h2>分析简历与岗位匹配度</h2>
          <p class="form-desc">系统将对比简历技能与岗位要求，生成可解释的匹配报告与学习计划</p>

          <!-- 简历选择（真实简历列表） -->
          <div class="form-group">
            <label>简历</label>
            <select v-if="userResumes.length" v-model="resumeId">
              <option :value="null" disabled>请选择简历</option>
              <option v-for="resume in userResumes" :key="resume.id" :value="resume.id">
                {{ resumeName(resume) }}
              </option>
            </select>
            <div v-else class="resume-card missing">
              <div class="resume-info">
                <strong>暂无简历</strong>
                <span>请先上传并解析简历，才能进行匹配分析</span>
              </div>
              <button class="primary-btn small" @click="router.push('/resume')">去上传简历</button>
            </div>
          </div>

          <!-- 岗位选择 -->
          <div class="form-group">
            <label>选择岗位</label>
            <select v-if="userJobs.length" v-model="jobId">
              <option :value="null" disabled>请选择已分析的岗位</option>
              <option v-for="job in userJobs" :key="job.id" :value="job.id">
                {{ jobTitle(job) }}
              </option>
            </select>
            <div v-else class="resume-card missing">
              <div class="resume-info">
                <strong>暂无已分析的岗位</strong>
                <span>请先粘贴 JD 完成岗位解析</span>
              </div>
              <button class="primary-btn small" @click="router.push('/jobs')">去分析岗位</button>
            </div>
          </div>

          <!-- 已选岗位信息 -->
          <div class="selected-info" v-if="selectedJob">
            <h3>目标岗位</h3>
            <div class="selected-items">
              <div class="selected-item">
                <strong>岗位：</strong>{{ selectedJob ? jobTitle(selectedJob) : '' }}
              </div>
            </div>
          </div>

          <button
            @click="startAnalysis"
            :disabled="analyzing || !resumeId || !jobId"
            class="primary-button"
          >
            <span v-if="analyzing" class="loading">AI 分析中（含学习计划生成，约需 10-60 秒）...</span>
            <span v-else>开始分析</span>
          </button>
          <p v-if="error" class="error-text">{{ error }}</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.match-analysis { min-height: 100vh; position: relative; overflow: hidden; }
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

.content { padding: 2rem; max-width: 860px; margin: 0 auto; }
.container { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 2rem; box-shadow: 0 2px 16px rgba(0,0,0,0.04); }
h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 0.5rem; }
.form-desc { color: #718096; margin-bottom: 1.8rem; }

.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.6rem; font-weight: 600; color: #2d3748; }
.form-group select {
  width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 10px;
  background: #fff; font-size: 1rem; transition: all 0.25s ease;
}
.form-group select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }

.resume-card {
  display: flex; justify-content: space-between; align-items: center; gap: 1rem;
  border-radius: 12px; padding: 1rem 1.2rem; border: 1px solid #e2e8f0; background: #fff;
}
.resume-card.selected { border-color: rgba(102,126,234,0.5); background: rgba(102,126,234,0.06); }
.resume-card.missing { border-style: dashed; }
.resume-info { display: flex; flex-direction: column; gap: 0.25rem; }
.resume-info strong { color: #1a202c; }
.resume-info span { color: #718096; font-size: 0.85rem; }
.link-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 0.9rem; font-weight: 600; }
.link-btn:hover { text-decoration: underline; }
.primary-btn.small {
  background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff;
  border: none; border-radius: 8px; padding: 0.5rem 1.1rem; font-size: 0.9rem;
  font-weight: 600; cursor: pointer; white-space: nowrap;
}
.primary-btn.small:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.3); }

.selected-info {
  background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;
}
.selected-info h3 { font-size: 1rem; color: #2d3748; margin-bottom: 0.5rem; }
.selected-item { color: #4a5568; font-size: 0.95rem; }

.primary-button {
  background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff;
  border: none; border-radius: 10px; padding: 0.85rem 2rem; font-size: 1rem;
  font-weight: 600; cursor: pointer; transition: all 0.25s ease; width: 100%;
}
.primary-button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102,126,234,0.3); }
.primary-button:disabled { opacity: 0.6; cursor: not-allowed; }
.loading { display: inline-flex; align-items: center; gap: 0.5rem; }
.loading::before {
  content: ''; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite;
}
.error-text { color: #ef4444; margin-top: 0.8rem; font-size: 0.9rem; text-align: center; }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 3rem; }
.spinner {
  width: 50px; height: 50px; border: 3px solid #e2e8f0; border-top-color: var(--primary);
  border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; }
}
@keyframes float {
  0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); }
}
@keyframes spin { to { transform: rotate(360deg); } }
.anim-fade { animation: fadeIn 0.6s ease-out; }
.anim-fade-up { animation: fadeInUp 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
</style>
