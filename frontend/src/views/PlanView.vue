<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMatchStore } from '@/stores/match'
import {
  getTaskStudy,
  refreshTaskStudy,
  submitTaskAnswer,
  type LearningTask,
  type TaskStudy,
  type StudyQuestionItem
} from '@/api/match'
import BackButton from '@/components/BackButton.vue'

const router = useRouter()
const route = useRoute()
const matchStore = useMatchStore()

const matchId = String(route.params.matchId || '')
const loading = ref(false)
const error = ref('')
const updatingId = ref<number | null>(null)

const plan = computed(() => matchStore.currentPlan)
const doneCount = computed(() => plan.value?.tasks.filter(t => t.status === 'done').length ?? 0)
const progress = computed(() =>
  plan.value?.tasks.length ? Math.round((doneCount.value / plan.value.tasks.length) * 100) : 0
)

onMounted(async () => {
  if (!matchId) {
    error.value = '缺少匹配报告 ID'
    return
  }
  try {
    loading.value = true
    await matchStore.loadPlan(matchId)
  } catch {
    error.value = '加载学习计划失败，请先完成匹配分析'
  } finally {
    loading.value = false
  }
})

async function changeStatus(task: LearningTask, status: LearningTask['status']) {
  updatingId.value = task.id
  try {
    await matchStore.setTaskStatus(task.id, status)
  } finally {
    updatingId.value = null
  }
}

// 学习资料：知识点（管理员知识库检索）+ 练习题（首次生成后缓存）
const studyMap = ref<Record<number, TaskStudy>>({})
const studyErrors = ref<Record<number, string>>({})
const expandedIds = ref<Set<number>>(new Set())
const loadingStudyId = ref<number | null>(null)

async function toggleStudy(task: LearningTask) {
  const id = task.id
  if (expandedIds.value.has(id)) {
    const next = new Set(expandedIds.value)
    next.delete(id)
    expandedIds.value = next
    return
  }
  expandedIds.value = new Set(expandedIds.value).add(id)
  if (studyMap.value[id]) return
  // 上次加载失败时清除错误缓存，允许重试
  if (studyErrors.value[id]) {
    const errors = { ...studyErrors.value }
    delete errors[id]
    studyErrors.value = errors
  }
  loadingStudyId.value = id
  try {
    const study = await getTaskStudy(id)
    studyMap.value = { ...studyMap.value, [id]: study }
    // 已有作答记录时预填草稿
    const drafts: Record<string, string> = {}
    for (const [q, a] of Object.entries(study.answers || {})) drafts[q] = a.answer
    if (Object.keys(drafts).length) {
      draftAnswers.value = { ...draftAnswers.value, [id]: drafts }
    }
  } catch (err: any) {
    studyErrors.value = {
      ...studyErrors.value,
      [id]: err.response?.data?.detail || '学习内容加载失败'
    }
    console.error('学习内容加载失败:', err)
  } finally {
    loadingStudyId.value = null
  }
}

// 答题练习：草稿输入 → 提交 AI 点评 → 换一批新题（题库式循环练习）
const draftAnswers = ref<Record<number, Record<string, string>>>({})
const submittingQ = ref<string | null>(null)
const refreshingId = ref<number | null>(null)
const actionErrors = ref<Record<number, string>>({})

function draftAnswer(taskId: number, question: string): string {
  return draftAnswers.value[taskId]?.[question] ?? ''
}

function setDraft(taskId: number, question: string, e: Event) {
  const val = (e.target as HTMLTextAreaElement).value
  draftAnswers.value = {
    ...draftAnswers.value,
    [taskId]: { ...(draftAnswers.value[taskId] || {}), [question]: val }
  }
}

async function submitAnswer(task: LearningTask, q: StudyQuestionItem) {
  const text = draftAnswer(task.id, q.question).trim()
  if (!text || submittingQ.value === q.question) return
  submittingQ.value = q.question
  try {
    const fb = await submitTaskAnswer(task.id, q.question, text)
    const cur = studyMap.value[task.id]
    if (cur) {
      studyMap.value = {
        ...studyMap.value,
        [task.id]: {
          ...cur,
          answers: {
            ...cur.answers,
            [q.question]: { answer: text, feedback: fb.feedback, score: fb.score ?? null }
          }
        }
      }
    }
  } catch (err: any) {
    actionErrors.value = {
      ...actionErrors.value,
      [task.id]: err.response?.data?.detail || '点评生成失败，请稍后重试'
    }
  } finally {
    submittingQ.value = null
  }
}

async function refreshQuestions(task: LearningTask) {
  if (refreshingId.value === task.id) return
  refreshingId.value = task.id
  try {
    const study = await refreshTaskStudy(task.id)
    studyMap.value = { ...studyMap.value, [task.id]: study }
    const drafts = { ...draftAnswers.value }
    delete drafts[task.id]
    draftAnswers.value = drafts
    const errors = { ...actionErrors.value }
    delete errors[task.id]
    actionErrors.value = errors
    const loadErrors = { ...studyErrors.value }
    delete loadErrors[task.id]
    studyErrors.value = loadErrors
  } catch (err: any) {
    actionErrors.value = {
      ...actionErrors.value,
      [task.id]: err.response?.data?.detail || '新题生成失败，请稍后重试'
    }
  } finally {
    refreshingId.value = null
  }
}

function feedbackFor(taskId: number, question: string) {
  return studyMap.value[taskId]?.answers?.[question] ?? null
}

function scoreClass(score?: number | null) {
  if (score == null) return 'mid'
  if (score >= 80) return 'good'
  if (score >= 60) return 'mid'
  return 'bad'
}

function studySourceLabel(source?: string) {
  if (source === 'cache') return '题目来自缓存'
  if (source === 'llm') return 'AI 生成题目'
  return '暂无练习题'
}

const priorityMeta: Record<string, { label: string; color: string }> = {
  high: { label: '高优先级', color: '#ef4444' },
  medium: { label: '中优先级', color: '#f59e0b' },
  low: { label: '低优先级', color: '#10b981' },
}

const statusMeta: Record<string, { label: string; color: string }> = {
  todo: { label: '待开始', color: '#718096' },
  in_progress: { label: '进行中', color: '#3b82f6' },
  done: { label: '已完成', color: '#10b981' },
}
</script>

<template>
  <div class="plan-view">
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
        <button @click="router.push('/match')">返回匹配列表</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <h2>学习计划</h2>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载学习计划中...</p>
        </div>

        <div v-else-if="error && !plan" class="error-state">
          <div class="error-icon">❌</div>
          <h3>加载失败</h3>
          <p>{{ error }}</p>
          <button @click="router.push('/match')" class="primary-button">前往匹配分析</button>
        </div>

        <template v-else-if="plan">
          <!-- 计划概览 -->
          <div class="plan-overview">
            <div class="overview-info">
              <h3>{{ plan.tasks.length }} 项学习任务</h3>
              <p class="plan-source">
                报告 {{ plan.report_id }}
                <span v-if="plan.content_json?.source === 'fallback'" class="source-tag">规则生成</span>
                <span v-else class="source-tag llm">AI 生成</span>
              </p>
            </div>
            <div class="overview-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="`width: ${progress}%`"></div>
              </div>
              <span class="progress-text">{{ doneCount }}/{{ plan.tasks.length }} 已完成（{{ progress }}%）</span>
            </div>
          </div>

          <!-- 任务列表 -->
          <div class="task-list">
            <div
              v-for="task in plan.tasks"
              :key="task.id"
              class="task-item"
              :class="{ done: task.status === 'done' }"
            >
              <div class="task-header">
                <h4 class="task-name">{{ task.task_name }}</h4>
                <div class="task-badges">
                  <span class="badge" :style="{ background: priorityMeta[task.priority]?.color }">
                    {{ priorityMeta[task.priority]?.label }}
                  </span>
                  <span class="badge" :style="{ background: statusMeta[task.status]?.color }">
                    {{ statusMeta[task.status]?.label }}
                  </span>
                </div>
              </div>

              <p v-if="task.description" class="task-desc">{{ task.description }}</p>

              <div class="task-meta">
                <span v-if="task.estimated_days" class="meta-item">⏱ 预估 {{ task.estimated_days }} 天</span>
                <span v-if="task.due_date" class="meta-item">📅 截止 {{ task.due_date }}</span>
                <a
                  v-if="task.resource_url"
                  :href="task.resource_url"
                  target="_blank"
                  rel="noopener"
                  class="meta-item resource"
                >🔗 学习资源</a>
              </div>

              <div class="task-actions">
                <button
                  v-if="task.status === 'todo'"
                  :disabled="updatingId === task.id"
                  class="action-btn start"
                  @click="changeStatus(task, 'in_progress')"
                >开始学习</button>
                <button
                  v-if="task.status === 'in_progress'"
                  :disabled="updatingId === task.id"
                  class="action-btn finish"
                  @click="changeStatus(task, 'done')"
                >标记完成</button>
                <button
                  v-if="task.status !== 'todo'"
                  :disabled="updatingId === task.id"
                  class="action-btn reset"
                  @click="changeStatus(task, 'todo')"
                >重置</button>
                <button
                  :disabled="loadingStudyId === task.id"
                  class="action-btn study-toggle"
                  @click="toggleStudy(task)"
                >{{ loadingStudyId === task.id ? '加载中...' : expandedIds.has(task.id) ? '收起学习资料' : '学习资料' }}</button>
              </div>

              <!-- 学习资料面板 -->
              <div v-if="expandedIds.has(task.id)" class="study-panel">
                <div v-if="studyErrors[task.id]" class="study-error">{{ studyErrors[task.id] }}</div>
                <template v-else-if="studyMap[task.id]">
                  <div class="study-section">
                    <h5>关联知识点 <span class="study-tag">来自管理员知识库</span></h5>
                    <div v-if="studyMap[task.id].knowledge.length" class="knowledge-list">
                      <div v-for="(k, i) in studyMap[task.id].knowledge" :key="i" class="knowledge-item">
                        <p class="knowledge-content">{{ k.content }}</p>
                        <p class="knowledge-meta">{{ k.doc_title }} · 相关度 {{ Math.round(k.similarity * 100) }}%</p>
                      </div>
                    </div>
                    <p v-else class="study-empty">知识库中暂无与该任务相关的内容</p>
                  </div>

                  <div class="study-section">
                    <div class="questions-header">
                      <h5>
                        练习题目
                        <span class="study-tag dim">{{ studySourceLabel(studyMap[task.id].source) }}</span>
                        <span v-if="studyMap[task.id].total_generated" class="study-tag dim">
                          第 {{ studyMap[task.id].batch }} 批 · 累计 {{ studyMap[task.id].total_generated }} 题
                        </span>
                      </h5>
                      <button
                        class="action-btn refresh"
                        :disabled="refreshingId === task.id"
                        @click="refreshQuestions(task)"
                      >{{ refreshingId === task.id ? '正在出题...' : (studyMap[task.id].questions.length ? '换一批新题' : '重试出题') }}</button>
                    </div>
                    <div v-if="actionErrors[task.id]" class="study-error">{{ actionErrors[task.id] }}</div>
                    <ol v-if="studyMap[task.id].questions.length" class="question-list">
                      <li v-for="(q, i) in studyMap[task.id].questions" :key="i" class="question-item">
                        <p class="question-text">{{ i + 1 }}. {{ q.question }}</p>

                        <!-- 作答输入区 -->
                        <div class="answer-input-area">
                          <textarea
                            rows="3"
                            placeholder="输入你的答案，提交后 AI 将给出点评..."
                            :value="draftAnswer(task.id, q.question)"
                            @input="setDraft(task.id, q.question, $event)"
                          ></textarea>
                          <div class="answer-actions">
                            <button
                              class="submit-answer"
                              :disabled="!draftAnswer(task.id, q.question).trim() || submittingQ === q.question"
                              @click="submitAnswer(task, q)"
                            >{{ submittingQ === q.question ? 'AI 点评中...' : feedbackFor(task.id, q.question) ? '重新提交' : '提交答案' }}</button>
                            <details class="answer-box">
                              <summary>查看参考答案</summary>
                              <p>{{ q.reference_answer || '（暂无参考答案）' }}</p>
                            </details>
                          </div>
                        </div>

                        <!-- AI 点评 -->
                        <div v-if="feedbackFor(task.id, q.question)" class="feedback-box">
                          <span class="score" :class="scoreClass(feedbackFor(task.id, q.question)!.score)">
                            {{ feedbackFor(task.id, q.question)!.score != null ? `得分 ${feedbackFor(task.id, q.question)!.score}` : '已点评' }}
                          </span>
                          <p class="feedback-text">{{ feedbackFor(task.id, q.question)!.feedback }}</p>
                        </div>
                      </li>
                    </ol>
                    <p v-else class="study-empty">练习题暂未生成，点击右上角"重试出题"再试一次</p>
                  </div>
                </template>
                <div v-else class="study-loading">
                  <span class="mini-spinner"></span>
                  <span>正在检索知识点并生成练习题（约需 5-20 秒）...</span>
                </div>
              </div>
            </div>
          </div>

          <div class="bottom-actions">
            <button @click="router.push(`/match/detail/${matchId}`)" class="secondary-button">
              查看匹配报告
            </button>
            <button @click="router.push('/optimize')" class="secondary-button">
              简历优化建议 →
            </button>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<style scoped>
.plan-view { min-height: 100vh; position: relative; overflow: hidden; }
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
h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 1.5rem; }

.plan-overview {
  background: rgba(255,255,255,0.7); border-radius: 16px; padding: 1.5rem 2rem;
  margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; gap: 2rem;
}
.overview-info h3 { color: #2d3748; margin-bottom: 0.3rem; }
.plan-source { color: #718096; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; }
.source-tag { padding: 0.1rem 0.6rem; border-radius: 999px; background: #e2e8f0; color: #4a5568; font-size: 0.75rem; }
.source-tag.llm { background: rgba(139,92,246,0.15); color: #7c3aed; }
.overview-progress { flex: 1; max-width: 360px; }
.progress-bar { height: 10px; background: #edf2f7; border-radius: 999px; overflow: hidden; margin-bottom: 0.4rem; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 999px; transition: width 0.5s ease; }
.progress-text { font-size: 0.85rem; color: #4a5568; }

.task-list { display: flex; flex-direction: column; gap: 1rem; }
.task-item {
  background: rgba(255,255,255,0.7); border-radius: 14px; padding: 1.5rem;
  border-left: 4px solid #8b5cf6; transition: all 0.25s ease;
}
.task-item:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(102,126,234,0.15); }
.task-item.done { opacity: 0.75; border-left-color: #10b981; }
.task-item.done .task-name { text-decoration: line-through; }
.task-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.6rem; }
.task-name { color: #1a202c; font-size: 1.05rem; }
.task-badges { display: flex; gap: 0.5rem; flex-shrink: 0; }
.badge { color: #fff; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.7rem; border-radius: 999px; }
.task-desc { color: #4a5568; line-height: 1.7; margin-bottom: 0.8rem; font-size: 0.95rem; }
.task-meta { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.9rem; }
.meta-item { font-size: 0.85rem; color: #718096; }
.meta-item.resource { color: #667eea; text-decoration: none; font-weight: 600; }
.meta-item.resource:hover { text-decoration: underline; }
.task-actions { display: flex; gap: 0.6rem; }
.action-btn {
  padding: 0.45rem 1.1rem; border: none; border-radius: 8px; cursor: pointer;
  font-size: 0.85rem; font-weight: 600; color: #fff; transition: all 0.2s ease;
}
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.action-btn.start { background: #3b82f6; }
.action-btn.finish { background: #10b981; }
.action-btn.reset { background: transparent; color: #718096; border: 1px solid #e2e8f0; }
.action-btn.study-toggle { background: #8b5cf6; }
.action-btn:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(1.08); }

/* 学习资料面板 */
.study-panel {
  margin-top: 1rem; background: rgba(255,255,255,0.85);
  border: 1px solid rgba(139,92,246,0.2); border-radius: 12px; padding: 1.2rem 1.4rem;
}
.study-section { margin-bottom: 1.2rem; }
.study-section:last-child { margin-bottom: 0; }
.study-section h5 { font-size: 0.95rem; color: #2d3748; margin-bottom: 0.7rem; display: flex; align-items: center; gap: 0.5rem; }
.study-tag { font-size: 0.72rem; font-weight: 600; color: #7c3aed; background: rgba(139,92,246,0.12); border-radius: 999px; padding: 0.1rem 0.6rem; }
.study-tag.dim { color: #718096; background: #edf2f7; }
.knowledge-list { display: flex; flex-direction: column; gap: 0.6rem; }
.knowledge-item { background: rgba(6,182,212,0.06); border-left: 3px solid #06b6d4; border-radius: 8px; padding: 0.7rem 0.9rem; }
.knowledge-content { color: #4a5568; font-size: 0.88rem; line-height: 1.7; white-space: pre-wrap; }
.knowledge-meta { color: #0e7490; font-size: 0.78rem; margin-top: 0.3rem; }
.question-list { display: flex; flex-direction: column; gap: 1rem; padding-left: 1.2rem; }
.question-item { color: #2d3748; font-size: 0.92rem; }
.question-text { line-height: 1.6; margin-bottom: 0.5rem; font-weight: 600; }
.questions-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 0.7rem; }
.questions-header h5 { margin-bottom: 0; }
.action-btn.refresh { background: #06b6d4; padding: 0.4rem 0.9rem; font-size: 0.8rem; flex-shrink: 0; }
.answer-input-area textarea {
  width: 100%; box-sizing: border-box; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 0.7rem 0.9rem; font-size: 0.88rem; font-family: inherit; line-height: 1.6;
  resize: vertical; min-height: 72px; transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: #fff;
}
.answer-input-area textarea:focus {
  outline: none; border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(102,126,234,0.12);
}
.answer-actions { display: flex; align-items: center; gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap; }
.submit-answer {
  background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #fff;
  border: none; border-radius: 8px; padding: 0.45rem 1.1rem; font-size: 0.85rem;
  font-weight: 600; cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.submit-answer:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.3); }
.submit-answer:disabled { opacity: 0.5; cursor: not-allowed; }
.answer-box { font-size: 0.85rem; }
.answer-box summary { color: var(--primary); font-size: 0.85rem; cursor: pointer; font-weight: 600; }
.answer-box summary:hover { text-decoration: underline; }
.answer-box p { color: #4a5568; background: #f7fafc; border-radius: 8px; padding: 0.7rem 0.9rem; margin-top: 0.4rem; line-height: 1.7; font-size: 0.88rem; }
.feedback-box {
  margin-top: 0.6rem; background: rgba(102,126,234,0.06);
  border-left: 3px solid var(--primary); border-radius: 8px; padding: 0.7rem 0.9rem;
  display: flex; align-items: flex-start; gap: 0.8rem;
}
.feedback-box .score {
  flex-shrink: 0; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.7rem;
  border-radius: 999px; margin-top: 0.1rem;
}
.feedback-box .score.good { background: rgba(16,185,129,0.15); color: #059669; }
.feedback-box .score.mid { background: rgba(245,158,11,0.15); color: #d97706; }
.feedback-box .score.bad { background: rgba(239,68,68,0.15); color: #dc2626; }
.feedback-text { color: #4a5568; font-size: 0.88rem; line-height: 1.7; }
.study-empty { color: #a0aec0; font-size: 0.88rem; }
.study-error { color: #ef4444; font-size: 0.9rem; }
.study-loading { display: flex; align-items: center; gap: 0.6rem; color: #718096; font-size: 0.9rem; }
.mini-spinner {
  width: 16px; height: 16px; border: 2px solid rgba(102,126,234,0.3);
  border-top-color: var(--primary); border-radius: 50%; display: inline-block;
  animation: spin 0.8s linear infinite;
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
  .plan-overview { flex-direction: column; align-items: stretch; }
  .bottom-actions { flex-direction: column; }
}
</style>
