<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { useMatchStore } from '@/stores/match'
import BackButton from '@/components/BackButton.vue'

const router = useRouter()
const route = useRoute()
const matchStore = useMatchStore()

const matchId = String(route.params.matchId || '')
const loading = ref(false)
const error = ref('')

const currentMatch = computed(() => matchStore.currentMatch)
const matchLevel = computed(() => matchStore.currentMatchLevel ?? { level: '', color: '#667eea' })
const matchProgress = computed(() => matchStore.matchProgress)
const matchBreakdown = computed(() => matchStore.matchBreakdown)

onMounted(async () => {
  if (!matchId) {
    error.value = '缺少报告 ID'
    return
  }
  try {
    loading.value = true
    error.value = ''
    await matchStore.loadMatchDetail(matchId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载匹配详情失败'
    console.error('加载匹配详情失败:', err)
  } finally {
    loading.value = false
  }
})

// 差距类型标签
function getGapTypeLabel(type: string) {
  switch (type) {
    case 'skill': return '技能差距'
    case 'experience': return '经验差距'
    case 'education': return '教育差距'
    default: return '其他差距'
  }
}

// AI 综合分析来源（旧报告 detail_json 为空默认显示 AI 生成）
const analysisSourceLabel = computed(() =>
  currentMatch.value?.detail_json?.analysis_source === 'rule' ? '规则生成' : 'AI 生成'
)

// 匹配时间格式化（后端返回无时区的 UTC 时间，补 Z 再转本地时区）
const analyzedAtLabel = computed(() => {
  const raw = currentMatch.value?.analyzed_at
  if (!raw) return ''
  const iso = /[Zz+]/.test(raw.slice(10)) ? raw : `${raw}Z`
  return new Date(iso).toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
})
</script>

<template>
  <div class="match-detail">
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
        <button @click="router.push('/match')">返回列表</button>
        <button @click="router.push('/match/new')">新建分析</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载报告详情中...</p>
        </div>

        <div v-else-if="error && !currentMatch" class="error-state">
          <div class="error-icon">❌</div>
          <h3>加载失败</h3>
          <p>{{ error }}</p>
          <button @click="router.push('/match')" class="primary-button">返回匹配列表</button>
        </div>

        <template v-else-if="currentMatch">
          <!-- 总览 -->
          <div class="overall-match">
            <div class="score-circle" :style="`--color: ${matchLevel.color}`">
              <span class="score-number">{{ currentMatch.overall_score }}</span>
              <span class="score-label">综合匹配度</span>
            </div>
            <div class="match-info">
              <h2>{{ currentMatch.position_title }}</h2>
              <p
                class="job-meta"
                v-if="currentMatch.company || currentMatch.city"
              >
                {{ [currentMatch.company, currentMatch.city].filter(Boolean).join(' · ') }}
              </p>
              <div class="progress-bar">
                <div class="progress-fill" :style="`width: ${matchProgress}%`"></div>
              </div>
              <span class="match-level" :style="`color: ${matchLevel.color}`">{{ matchLevel.level }}</span>
              <p class="report-id">
                报告编号：{{ currentMatch.id }}
                <template v-if="analyzedAtLabel"> · 匹配时间：{{ analyzedAtLabel }}</template>
              </p>
            </div>
          </div>

          <!-- AI 综合分析 -->
          <div class="ai-analysis" v-if="currentMatch.summary">
            <h3>
              AI 综合分析
              <span
                class="source-badge"
                :class="{ rule: currentMatch.detail_json?.analysis_source === 'rule' }"
              >{{ analysisSourceLabel }}</span>
            </h3>
            <p>{{ currentMatch.summary }}</p>
          </div>

          <!-- 分维度得分 -->
          <div class="dimensions" v-if="matchBreakdown">
            <h3>分维度得分</h3>
            <div class="dimension-cards">
              <div
                v-for="(dim, index) in matchBreakdown"
                :key="index"
                class="dimension-card"
              >
                <div class="dim-header">
                  <span class="dim-name">{{ dim.label }}</span>
                  <span class="dim-score" :style="`color: ${dim.color}`">{{ dim.score }}分</span>
                </div>
                <div class="dim-bar">
                  <div class="dim-fill" :style="`width: ${dim.score}%; background: ${dim.color}`"></div>
                </div>
                <p class="dim-basis">权重 {{ Math.round(dim.weight * 100) }}%</p>
              </div>
            </div>
          </div>

          <!-- 差距清单 -->
          <div class="gaps-section">
            <h3>能力差距清单（{{ currentMatch.gaps.length }}）</h3>
            <div class="gap-list">
              <div
                v-for="(gap, index) in currentMatch.gaps"
                :key="index"
                class="gap-item"
                :class="gap.severity"
              >
                <div class="gap-header">
                  <span class="gap-type">{{ getGapTypeLabel(gap.type) }}</span>
                  <span class="gap-severity">{{ gap.severity === 'high' ? '高' : gap.severity === 'medium' ? '中' : '低' }}</span>
                </div>
                <div class="gap-content">
                  <strong v-if="gap.skill_name">{{ gap.skill_name }}</strong>
                  <p>{{ gap.description }}</p>
                  <div class="gap-levels" v-if="gap.current_level !== null && gap.target_level !== null">
                    当前 {{ gap.current_level }}/5 → 目标 {{ gap.target_level }}/5
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 提升建议 -->
          <div class="recommendations" v-if="currentMatch.recommendations.length">
            <h3>提升建议</h3>
            <div class="rec-list">
              <div v-for="(rec, index) in currentMatch.recommendations" :key="index" class="rec-item">
                <div class="rec-header">
                  <span class="rec-priority" :class="rec.priority">{{ rec.priority === 'high' ? '高优先级' : rec.priority === 'medium' ? '中优先级' : '低优先级' }}</span>
                </div>
                <p>{{ rec.description }}</p>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <button @click="router.push(`/match/plan/${currentMatch.id}`)" class="secondary-button">
              查看学习计划
            </button>
            <button @click="router.push({ path: '/optimize', query: { jobId: String(currentMatch.job_id) } })" class="secondary-button">
              简历优化建议
            </button>
            <button @click="router.push('/match')" class="secondary-button">
              返回列表
            </button>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<style scoped>
.match-detail { min-height: 100vh; position: relative; overflow: hidden; }
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
.topbar nav { display: flex; gap: 0.5rem; }
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

.overall-match {
  display: flex; align-items: center; gap: 2.5rem;
  background: rgba(255,255,255,0.7); border-radius: 16px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
}
.score-circle {
  width: 130px; height: 130px; border-radius: 50%; background: var(--color, #667eea);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0;
}
.score-number { font-size: 2.8rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 0.8rem; opacity: 0.9; }
.match-info { flex: 1; }
.match-info h2 { font-size: 1.5rem; color: #1a202c; margin-bottom: 0.4rem; }
.job-meta { color: #718096; font-size: 0.95rem; margin-bottom: 0.6rem; }
.progress-bar { height: 10px; background: #edf2f7; border-radius: 999px; overflow: hidden; margin-bottom: 0.5rem; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 999px; transition: width 0.5s ease; }
.match-level { font-weight: 700; font-size: 1.05rem; }
.report-id { color: #a0aec0; font-size: 0.8rem; margin-top: 0.4rem; }

.ai-analysis {
  background: rgba(139,92,246,0.06);
  border-left: 4px solid #8b5cf6;
  border-radius: 12px;
  padding: 1.2rem 1.5rem;
  margin-bottom: 1.5rem;
}
.ai-analysis h3 { font-size: 1.1rem; color: #6d28d9; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
.source-badge {
  font-size: 0.72rem; font-weight: 600; color: #8b5cf6;
  background: rgba(139,92,246,0.12); border-radius: 999px; padding: 0.1rem 0.6rem;
}
.source-badge.rule { color: #718096; background: #edf2f7; }
.ai-analysis p { color: #4a5568; line-height: 1.8; white-space: pre-wrap; }

.dimensions { margin-bottom: 1.8rem; }
.dimensions h3, .gaps-section h3, .recommendations h3 { font-size: 1.25rem; color: #1a202c; margin-bottom: 1rem; }
.dimension-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.dimension-card {
  background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1.2rem;
}
.dim-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.dim-name { font-weight: 600; color: #2d3748; }
.dim-score { font-weight: 700; font-size: 1.1rem; }
.dim-bar { height: 8px; background: #edf2f7; border-radius: 999px; overflow: hidden; margin-bottom: 0.5rem; }
.dim-fill { height: 100%; border-radius: 999px; transition: width 0.5s ease; }
.dim-basis { color: #718096; font-size: 0.8rem; line-height: 1.5; }

.gaps-section { margin-bottom: 1.8rem; }
.gap-list { display: flex; flex-direction: column; gap: 0.8rem; }
.gap-item {
  background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem 1.2rem;
  border-left: 4px solid #cbd5e0;
}
.gap-item.high { border-left-color: #ef4444; }
.gap-item.medium { border-left-color: #f59e0b; }
.gap-item.low { border-left-color: #10b981; }
.gap-header { display: flex; gap: 0.6rem; margin-bottom: 0.4rem; }
.gap-type { font-size: 0.8rem; font-weight: 600; color: #4a5568; background: #edf2f7; border-radius: 999px; padding: 0.15rem 0.7rem; }
.gap-severity { font-size: 0.8rem; font-weight: 600; color: #718096; }
.gap-content strong { color: #1a202c; }
.gap-content p { color: #4a5568; font-size: 0.92rem; margin: 0.25rem 0; line-height: 1.6; }
.gap-levels { color: #718096; font-size: 0.82rem; }

.rec-list { display: flex; flex-direction: column; gap: 0.8rem; }
.rec-item { background: rgba(255,255,255,0.7); border-radius: 12px; padding: 1rem 1.2rem; }
.rec-header { margin-bottom: 0.4rem; }
.rec-priority { font-size: 0.8rem; font-weight: 600; border-radius: 999px; padding: 0.15rem 0.7rem; }
.rec-priority.high { color: #ef4444; background: rgba(239,68,68,0.1); }
.rec-priority.medium { color: #f59e0b; background: rgba(245,158,11,0.1); }
.rec-priority.low { color: #10b981; background: rgba(16,185,129,0.1); }
.rec-item p { color: #4a5568; font-size: 0.92rem; line-height: 1.6; }

.action-buttons { display: flex; gap: 1rem; margin-top: 2rem; }
.secondary-button {
  background: #fff; color: var(--primary); border: 1px solid var(--primary);
  border-radius: 10px; padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 600;
  cursor: pointer; transition: all 0.25s ease;
}
.secondary-button:hover {
  background: var(--primary); color: #fff; transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.2);
}

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 3rem; }
.spinner {
  width: 50px; height: 50px; border: 3px solid #e2e8f0; border-top-color: var(--primary);
  border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem;
}
.error-state { text-align: center; padding: 3rem; }
.error-icon { font-size: 4rem; margin-bottom: 1rem; }
.error-state .primary-button {
  background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff;
  border: none; border-radius: 10px; padding: 0.75rem 2rem; font-size: 1rem;
  font-weight: 600; cursor: pointer; margin-top: 1rem;
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

@media (max-width: 768px) {
  .overall-match { flex-direction: column; }
  .dimension-cards { grid-template-columns: 1fr; }
  .action-buttons { flex-direction: column; }
}
</style>
