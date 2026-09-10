<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useResumeStore } from '@/stores/resume'
import { useJobStore } from '@/stores/job'
import { useMatchStore } from '@/stores/match'
import BackButton from '@/components/BackButton.vue'
import { analyzeMatch } from '@/api/match'

const router = useRouter()
const route = useRoute()
const resumeStore = useResumeStore()
const jobStore = useJobStore()
const matchStore = useMatchStore()

// 表单数据
const resumeId = ref<number | null>(null)
const jobId = ref<number | null>(null)
const selectedResume = ref<any>(null)
const selectedJob = ref<any>(null)

// 状态
const loading = ref(false)
const analyzing = ref(false)
const error = ref('')
const showForm = computed(() => !resumeId.value || !jobId.value)

// 计算属性
const currentMatch = computed(() => matchStore.currentMatch)
const matchLevel = computed(() => matchStore.currentMatchLevel)
const matchProgress = computed(() => matchStore.matchProgress)
const matchBreakdown = computed(() => matchStore.matchBreakdown)

// 获取用户简历列表
const userResumes = computed(() => {
  // 这里应该从API获取用户的简历列表
  return [] // 暂时返回空数组
})

// 获取用户岗位列表
const userJobs = computed(() => {
  return jobStore.jobs || []
})

// 初始化
onMounted(async () => {
  // 从路由参数获取ID
  const { resumeId: paramResumeId, jobId: paramJobId } = route.params

  if (paramResumeId && paramJobId) {
    resumeId.value = Number(paramResumeId)
    jobId.value = Number(paramJobId)

    // 获取匹配详情
    await loadMatchDetail()
  } else {
    // 获取用户数据
    await Promise.all([
      resumeStore.fetchProfile(),
      jobStore.fetchJobs()
    ])
  }
})

// 加载匹配详情
async function loadMatchDetail() {
  if (!resumeId.value || !jobId.value) return

  try {
    loading.value = true
    await matchStore.loadMatchDetail(`match_${resumeId.value}_${jobId.value}`)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载匹配详情失败'
    console.error('加载匹配详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 开始分析匹配度
async function startAnalysis() {
  if (!resumeId.value || !jobId.value) {
    error.value = '请选择简历和岗位'
    return
  }

  try {
    analyzing.value = true
    error.value = ''

    await matchStore.analyzeMatchData({
      resume_id: resumeId.value,
      job_id: jobId.value
    })

    // 跳转到结果页
    router.push(`/match/result/${resumeId.value}/${jobId.value}`)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '分析匹配度失败'
    console.error('分析匹配度失败:', err)
  } finally {
    analyzing.value = false
  }
}

// 选择简历
function selectResume(resume: any) {
  selectedResume.value = resume
  resumeId.value = resume.id
}

// 选择岗位
function selectJob(job: any) {
  selectedJob.value = job
  jobId.value = job.id
}

// 导航到结果页
function viewResult() {
  if (resumeId.value && jobId.value) {
    router.push(`/match/result/${resumeId.value}/${jobId.value}`)
  }
}

// 返回列表
function goBack() {
  router.push('/match')
}

// 获取匹配度总结
function getMatchSummary(score: number) {
  if (score >= 90) return '简历与岗位匹配度很高，建议直接投递'
  if (score >= 70) return '简历与岗位匹配度良好，可以投递'
  if (score >= 50) return '简历与岗位匹配度一般，建议优化后再投递'
  return '简历与岗位匹配度较低，建议大幅优化后再投递'
}

// 获取差距类型标签
function getGapTypeLabel(type: string) {
  switch (type) {
    case 'skill':
      return '技能差距'
    case 'experience':
      return '经验差距'
    case 'education':
      return '教育差距'
    default:
      return '其他差距'
  }
}

// 生成反馈
function generateFeedback() {
  if (currentMatch.value) {
    router.push(`/match/feedback/${currentMatch.value.id}`)
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
        <button @click="goBack">返回列表</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <!-- 表单区域 -->
        <div v-if="showForm" class="form-section anim-fade-up">
          <h2>分析简历与岗位匹配度</h2>
          <p class="form-desc">选择一份简历和一个岗位，系统将分析匹配度并提供改进建议</p>

          <div class="form-group">
            <label>选择简历</label>
            <select v-model="resumeId" @change="selectResume(userResumes.find(r => r.id === resumeId))">
              <option value="">请选择简历</option>
              <option v-for="resume in userResumes" :key="resume.id" :value="resume.id">
                {{ resume.username || '未知' }} - 简历分析
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>选择岗位</label>
            <select v-model="jobId" @change="selectJob(userJobs.find(j => j.id === jobId))">
              <option value="">请选择岗位</option>
              <option v-for="job in userJobs" :key="job.id" :value="job.id">
                {{ job.position_title || '未知' }} - 岗位分析
              </option>
            </select>
          </div>

          <div class="selected-info" v-if="selectedResume || selectedJob">
            <h3>已选择</h3>
            <div class="selected-items">
              <div v-if="selectedResume" class="selected-item">
                <strong>简历：</strong>
                {{ selectedResume.username || '未知' }}
              </div>
              <div v-if="selectedJob" class="selected-item">
                <strong>岗位：</strong>
                {{ selectedJob.position_title || '未知' }}
              </div>
            </div>
          </div>

          <button
            @click="startAnalysis"
            :disabled="analyzing || !resumeId || !jobId"
            class="primary-button"
          >
            <span v-if="analyzing" class="loading">分析中...</span>
            <span v-else>开始分析</span>
          </button>
        </div>

        <!-- 结果展示区域 -->
        <div v-else class="result-section anim-fade-up">
          <h2>匹配度分析结果</h2>

          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>加载匹配数据中...</p>
          </div>

          <div v-else-if="currentMatch" class="match-results">
            <!-- 总体匹配度 -->
            <div class="overall-match">
              <div class="match-score">
                <div class="score-circle" :style="`--color: ${matchLevel?.color || '#8b5cf6'}`">
                  <span class="score-number">{{ currentMatch.overall_score }}</span>
                  <span class="score-label">分</span>
                </div>
                <div class="match-info">
                  <h3>总体匹配度</h3>
                  <div class="match-level" :class="matchLevel?.text">
                    {{ matchLevel?.level }}
                  </div>
                  <p class="match-summary">
                    {{ getMatchSummary(currentMatch.overall_score) }}
                  </p>
                </div>
              </div>

              <!-- 匹配进度 -->
              <div class="match-progress">
                <h4>改进进度</h4>
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="`width: ${matchProgress}%`"
                  ></div>
                </div>
                <div class="progress-text">
                  {{ matchProgress }}% 已完成
                </div>
              </div>
            </div>

            <!-- 各维度匹配度 -->
            <div class="dimensions" v-if="matchBreakdown">
              <h3>各维度匹配度</h3>
              <div class="dimension-cards">
                <div
                  v-for="(dim, key) in matchBreakdown"
                  :key="key"
                  class="dimension-card"
                  :style="`--color: ${dim.color}`"
                >
                  <div class="dim-header">
                    <h4>{{ dim.label }}</h4>
                    <span class="dim-score">{{ dim.score }}%</span>
                  </div>
                  <div class="dim-bar">
                    <div class="dim-fill" :style="`width: ${dim.score}%`"></div>
                  </div>
                  <div class="dim-weight">
                    权重: {{ (dim.weight * 100).toFixed(0) }}%
                  </div>
                </div>
              </div>
            </div>

            <!-- 差距分析 -->
            <div class="gap-analysis" v-if="currentMatch.gaps && currentMatch.gaps.length > 0">
              <h3>差距分析</h3>
              <div class="gap-list">
                <div
                  v-for="gap in currentMatch.gaps"
                  :key="gap.skill_name || gap.experience_type || gap.id"
                  class="gap-item"
                >
                  <div class="gap-header">
                    <div class="gap-type">{{ getGapTypeLabel(gap.type) }}</div>
                    <div class="gap-severity" :class="matchStore.getGapSeverity(gap.severity).text">
                      {{ matchStore.getGapSeverity(gap.severity).level }}优先级
                    </div>
                  </div>
                  <div class="gap-content">
                    <p>{{ gap.description }}</p>
                    <div v-if="gap.skill_name" class="gap-detail">
                      <span class="label">技能：</span>
                      <span>{{ gap.skill_name }}</span>
                    </div>
                    <div v-if="gap.current_level !== undefined && gap.target_level !== undefined" class="gap-detail">
                      <span class="label">当前熟练度：</span>
                      <span>{{ gap.current_level }}</span>
                      <span class="arrow">→</span>
                      <span>目标{{ gap.target_level }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 改进建议 -->
            <div class="recommendations" v-if="currentMatch.recommendations && currentMatch.recommendations.length > 0">
              <h3>改进建议</h3>
              <div class="recommendation-list">
                <div
                  v-for="(rec, index) in currentMatch.recommendations"
                  :key="index"
                  class="recommendation-item"
                >
                  <div class="rec-header">
                    <div class="rec-type">{{ rec.type }}</div>
                    <div class="rec-priority" :class="matchStore.getRecommendationPriority(rec.priority).text">
                      {{ matchStore.getRecommendationPriority(rec.priority).level }}优先级
                    </div>
                  </div>
                  <div class="rec-content">
                    <p>{{ rec.description }}</p>
                    <div v-if="rec.estimated_time" class="rec-time">
                      <span class="label">预估时间：</span>
                      <span>{{ rec.estimated_time }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <button @click="generateFeedback" class="secondary-button">
                生成详细学习计划
              </button>
              <button @click="router.push('/resume')" class="secondary-button">
                查看简历详情
              </button>
              <button @click="router.push('/jobs')" class="secondary-button">
                查看岗位详情
              </button>
            </div>
          </div>

          <div v-else-if="error" class="error-state">
            <div class="error-icon">❌</div>
            <h3>加载失败</h3>
            <p>{{ error }}</p>
            <button @click="loadMatchDetail" class="primary-button">
              重试
            </button>
          </div>
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
.topbar-left { display: flex; align-items: center; gap: 0.9rem; }
.brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 800; font-size: 1.15rem; cursor: pointer; }
.brand-logo { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff; display: flex; align-items: center; justify-content: center; animation: pulse 3s ease-in-out infinite; }
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
.container { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 2rem; box-shadow: 0 2px 16px rgba(0,0,0,0.04); }

/* 表单样式 */
.form-section h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 0.5rem; }
.form-desc { color: #718096; margin-bottom: 2rem; }
.form-group {
  margin-bottom: 1.5rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2d3748;
}
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  font-size: 1rem;
  transition: all 0.25s ease;
}
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

/* 选择信息 */
.selected-info {
  background: rgba(255,255,255,0.5);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}
.selected-info h3 { font-size: 1rem; color: #2d3748; margin-bottom: 0.5rem; }
.selected-item {
  color: #4a5568;
  margin-bottom: 0.5rem;
}
.selected-item strong { color: #2d3748; }

/* 按钮样式 */
.primary-button {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
}
.primary-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}
.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 结果样式 */
.result-section h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 2rem; }

/* 总体匹配度 */
.overall-match {
  background: rgba(255,255,255,0.7);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}
.match-score { display: flex; align-items: center; gap: 1.5rem; }
.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  position: relative;
  box-shadow: 0 4px 20px rgba(139,92,246,0.3);
}
.score-number { font-size: 2.5rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 0.9rem; opacity: 0.9; }
.match-info h3 { font-size: 1.2rem; margin-bottom: 0.5rem; color: #2d3748; }
.match-level {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.match-summary { color: #718096; }

/* 匹配进度 */
.match-progress h4 { font-size: 1rem; color: #2d3748; margin-bottom: 0.5rem; }
.progress-bar {
  height: 8px;
  background: #edf2f7;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}
.progress-fill {
  height: 100%;
  background: var(--color);
  border-radius: 999px;
  transition: width 1s ease;
}
.progress-text { font-size: 0.9rem; color: #4a5568; }

/* 各维度匹配度 */
.dimensions h3 { font-size: 1.3rem; color: #1a202c; margin-bottom: 1rem; }
.dimension-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.dimension-card {
  background: rgba(255,255,255,0.6);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(139,92,246,0.1);
}
.dim-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.dim-header h4 { color: #2d3748; font-size: 1rem; }
.dim-score { font-size: 1.2rem; font-weight: 700; color: var(--color); }
.dim-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}
.dim-fill {
  height: 100%;
  background: var(--color);
  border-radius: 999px;
}
.dim-weight { font-size: 0.8rem; color: #718096; text-align: center; }

/* 差距分析 */
.gap-analysis h3 { font-size: 1.3rem; color: #1a202c; margin-bottom: 1rem; }
.gap-list { display: flex; flex-direction: column; gap: 1rem; }
.gap-item {
  background: rgba(255,255,255,0.5);
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #f59e0b;
}
.gap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.gap-type { font-weight: 600; color: #2d3748; }
.gap-severity { font-size: 0.9rem; font-weight: 600; }
.gap-content p { color: #4a5568; margin-bottom: 0.5rem; line-height: 1.6; }
.gap-detail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #718096;
}
.label { color: #4a5568; font-weight: 500; }
.arrow { color: #a0aec0; }

/* 改进建议 */
.recommendations h3 { font-size: 1.3rem; color: #1a202c; margin-bottom: 1rem; }
.recommendation-list { display: flex; flex-direction: column; gap: 1rem; }
.recommendation-item {
  background: rgba(255,255,255,0.5);
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #10b981;
}
.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.rec-type { font-weight: 600; color: #2d3748; }
.rec-priority { font-size: 0.9rem; font-weight: 600; }
.rec-content p { color: #4a5568; margin-bottom: 0.5rem; line-height: 1.6; }
.rec-time {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #718096;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}
.secondary-button {
  background: #fff;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 10px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}
.secondary-button:hover {
  background: var(--primary);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.2);
}

/* 状态样式 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}
.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid #e2e8f0;
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}
.error-state {
  text-align: center;
  padding: 3rem;
}
.error-icon { font-size: 4rem; margin-bottom: 1rem; color: #ef4444; }

/* 动画 */
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

/* 动画延迟 */
.anim-fade-up {
  animation: fadeInUp 0.6s ease-out;
}
.anim-fade {
  animation: fadeIn 0.6s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.anim-delay-1 { animation-delay: 0.1s; }
.anim-delay-2 { animation-delay: 0.2s; }
.anim-delay-3 { animation-delay: 0.3s; }

/* 响应式 */
@media (max-width: 768px) {
  .overall-match {
    grid-template-columns: 1fr;
  }
  .dimension-cards {
    grid-template-columns: 1fr;
  }
  .action-buttons {
    flex-direction: column;
  }
}
</style>