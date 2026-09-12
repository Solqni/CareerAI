<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useJobStore } from '@/stores/job'
import { useResumeStore } from '@/stores/resume'
import {
  categoryMeta,
  createInterviewSession,
  finishInterview,
  getInterviewSession,
  listInterviewSessions,
  submitAnswer,
  type InterviewSession,
  type SessionListItem,
} from '@/api/interview'

const route = useRoute()
const jobStore = useJobStore()
const resumeStore = useResumeStore()

// ---------- 建会话表单 ----------
const jobId = ref<number | null>(null)
const resumeId = ref<number | null>(null)
const questionCount = ref(6)
const starting = ref(false)
const error = ref('')

// ---------- 面试会话 ----------
const session = ref<InterviewSession | null>(null)
const history = ref<SessionListItem[]>([])
const answerText = ref('')
const submitting = ref(false)
const finishing = ref(false)
const chatBody = ref<HTMLElement | null>(null)
const chatInput = ref<HTMLInputElement | null>(null)

const features = [
  { title: '技术题', desc: '岗位相关技术考察', color: '#667eea' },
  { title: '项目题', desc: '深挖简历项目细节', color: '#764ba2' },
  { title: '行为题', desc: '软素质与沟通表达', color: '#f093fb' },
]

const currentQA = computed(
  () => session.value?.qas.find(q => q.answer === null) ?? null
)
// 对话式逐题揭晓：只显示到当前待答题，答完后下一题才出现
const visibleQAs = computed(() => {
  const qas = session.value?.qas ?? []
  if (!qas.length) return []
  const pendingIdx = qas.findIndex(q => q.answer === null)
  if (pendingIdx === -1) return qas
  return qas.slice(0, pendingIdx + 1)
})
const answeredCount = computed(
  () => session.value?.qas.filter(q => q.answer !== null).length ?? 0
)
const averageScore = computed(() => {
  const scores = (session.value?.qas ?? [])
    .map(q => q.score)
    .filter((s): s is number => s !== null && s !== undefined)
  if (!scores.length) return null
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
})
const isFinished = computed(() => session.value?.status === 'finished')

// 每当新问题出现时，自动聚焦底部输入条
watch(
  () => [session.value?.id, currentQA.value?.id],
  async ([, curId]) => {
    if (curId) {
      await nextTick()
      chatInput.value?.focus()
    }
  }
)

function jobTitle(job: any) {
  return job?.parsed_json?.position_title || job?.position_title || `岗位 #${job?.id}`
}
function resumeName(r: any) {
  return r?.name || `简历 #${r?.id}`
}
function catLabel(category: string) {
  return categoryMeta[category]?.label ?? category
}
function catColor(category: string) {
  return categoryMeta[category]?.color ?? '#667eea'
}
function scoreColor(score: number | null) {
  if (score === null) return '#94a3b8'
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}
function fmtDate(iso: string | null | undefined) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

async function scrollToBottom() {
  await nextTick()
  chatBody.value?.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' })
}

async function loadHistory() {
  try {
    history.value = await listInterviewSessions()
  } catch (err) {
    console.error('获取面试历史失败:', err)
  }
}

onMounted(async () => {
  await Promise.all([jobStore.fetchJobs(), resumeStore.fetchResumes(), loadHistory()])
  const qid = Number(route.query.jobId)
  if (qid && jobStore.jobs.some(j => j.id === qid)) jobId.value = qid
})

async function startInterview() {
  if (!jobId.value) {
    error.value = '请选择目标岗位'
    return
  }
  try {
    starting.value = true
    error.value = ''
    session.value = await createInterviewSession({
      job_id: jobId.value,
      resume_id: resumeId.value ?? undefined,
      question_count: questionCount.value,
    })
    answerText.value = ''
    await scrollToBottom()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '创建面试会话失败'
    console.error('创建面试会话失败:', err)
  } finally {
    starting.value = false
  }
}

async function sendAnswer() {
  if (!session.value || !currentQA.value) return
  const text = answerText.value.trim()
  if (!text) return
  try {
    submitting.value = true
    const result = await submitAnswer(session.value.id, currentQA.value.id, text)
    const idx = session.value.qas.findIndex(q => q.id === result.qa.id)
    if (idx !== -1) session.value.qas[idx] = result.qa
    answerText.value = ''
    await scrollToBottom()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '答案评估失败，请重试'
    console.error('答案评估失败:', err)
  } finally {
    submitting.value = false
  }
}

async function finish() {
  if (!session.value) return
  try {
    finishing.value = true
    session.value = await finishInterview(session.value.id)
    await loadHistory()
    await scrollToBottom()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '生成总评报告失败'
    console.error('生成总评失败:', err)
  } finally {
    finishing.value = false
  }
}

async function openHistory(item: SessionListItem) {
  try {
    error.value = ''
    session.value = await getInterviewSession(item.id)
    answerText.value = ''
    await scrollToBottom()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载会话失败'
  }
}

function backToSetup() {
  session.value = null
  answerText.value = ''
  loadHistory()
}
</script>

<template>
  <div class="page">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>
    <div class="page-inner">
    <BackButton class="page-back" />
    <div class="page-header anim-fade-up">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </div>
      <div>
        <h2>面试准备</h2>
        <p>AI 扮演面试官进行多轮对话，每轮从逻辑性、完整性、专业性评估，结束生成总评报告</p>
      </div>
    </div>

    <!-- ============ 准备阶段：建会话 ============ -->
    <template v-if="!session">
      <div class="tips">
        <div v-for="(f, i) in features" :key="f.title" class="tip anim-fade-up" :style="{ '--c': f.color, animationDelay: 0.1 + i * 0.1 + 's' }">
          <strong>{{ f.title }}</strong>
          <span>{{ f.desc }}</span>
        </div>
      </div>

      <div class="setup-card anim-fade-up anim-delay-3">
        <div class="form-row">
          <div class="form-group">
            <label>目标岗位</label>
            <select v-model="jobId">
              <option :value="null" disabled>请选择岗位</option>
              <option v-for="job in jobStore.jobs" :key="job.id" :value="job.id">{{ jobTitle(job) }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>简历（可选）</label>
            <select v-model="resumeId">
              <option :value="null">使用最新简历</option>
              <option v-for="r in resumeStore.resumes" :key="r.id" :value="r.id">{{ resumeName(r) }}</option>
            </select>
          </div>
          <div class="form-group small">
            <label>题目数量</label>
            <select v-model.number="questionCount">
              <option :value="3">3 题（快速体验）</option>
              <option :value="6">6 题（标准）</option>
              <option :value="9">9 题（深度演练）</option>
            </select>
          </div>
        </div>
        <button class="btn" :disabled="starting || !jobId" @click="startInterview">
          {{ starting ? 'AI 正在生成针对性面试题，约 10-30 秒…' : '开始真实模拟面试' }}
        </button>
        <p v-if="error" class="error-text">{{ error }}</p>
        <p class="form-note">题目依据岗位要求与你的简历生成，涵盖技术题 / 项目题 / 行为题三类</p>
      </div>

      <!-- 历史会话 -->
      <div v-if="history.length" class="history-card anim-fade-up anim-delay-4">
        <h3>历史面试（{{ history.length }}）</h3>
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          @click="openHistory(item)"
        >
          <div class="history-main">
            <span class="history-title">{{ item.position_title || `岗位 #${item.job_id}` }}</span>
            <span class="history-meta">
              {{ item.status === 'finished' ? '已结束' : `进行中 ${item.answered_count}/${item.qa_count}` }}
              · {{ fmtDate(item.created_at) }}
            </span>
          </div>
          <div class="history-right">
            <span
              v-if="item.average_score !== null && item.average_score !== undefined"
              class="history-score"
              :style="{ color: scoreColor(Math.round(item.average_score)) }"
            >
              {{ Math.round(item.average_score) }} 分
            </span>
            <span class="history-go">查看 →</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ============ 面试进行 / 报告 ============ -->
    <template v-else>
      <div class="session-bar anim-fade-up">
        <div class="session-info">
          <strong>{{ session.position_title || '模拟面试' }}</strong>
          <span class="progress-chip">
            进度 {{ answeredCount }}/{{ session.qas.length }}
          </span>
          <span v-if="isFinished" class="status-chip finished">已结束</span>
          <span v-else class="status-chip active">进行中</span>
        </div>
        <button class="btn-ghost" @click="backToSetup">返回列表</button>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="chat-window anim-fade-up">
        <div class="chat-titlebar">
          <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
          <span class="chat-title">AI 面试官 · {{ session.position_title || '目标岗位' }}</span>
        </div>
        <div ref="chatBody" class="chat-body">
          <div class="bubble-row ai">
            <div class="bubble">
              <span class="who">AI 面试官</span>
              你好，我是你的 AI 面试官。本场围绕「{{ session.position_title || '目标岗位' }}」共 {{ session.qas.length }} 道题，涵盖技术、项目与行为三类。请尽量结合真实经历作答，开始吧。
            </div>
          </div>

          <template v-for="(qa, idx) in visibleQAs" :key="qa.id">
            <!-- 问题 -->
            <div class="bubble-row ai">
              <div class="bubble">
                <span class="who">AI 面试官 · 第 {{ idx + 1 }} 轮</span>
                <span class="qa-tag" :style="{ background: catColor(qa.category) }">{{ catLabel(qa.category) }}</span>
                <div class="question-text">{{ qa.question }}</div>
              </div>
            </div>

            <!-- 已作答：用户回答 + 评估 -->
            <template v-if="qa.answer !== null">
              <div class="bubble-row user">
                <div class="bubble">
                  <span class="who">我</span>{{ qa.answer }}
                </div>
              </div>
              <div v-if="qa.feedback_json" class="feedback-card">
                <div class="feedback-head">
                  <span class="feedback-title">本轮评估</span>
                  <span class="score-badge" :style="{ color: scoreColor(qa.score) }">{{ qa.score }} 分</span>
                  <span v-if="qa.feedback_json.source === 'fallback'" class="source-tag">规则评估</span>
                </div>
                <div class="dim-list">
                  <div class="dim-row">
                    <span>逻辑性</span>
                    <div class="dim-track"><div class="dim-fill" :style="{ width: qa.feedback_json.scores.logic + '%', background: catColor(qa.category) }"></div></div>
                    <em>{{ qa.feedback_json.scores.logic }}</em>
                  </div>
                  <div class="dim-row">
                    <span>完整性</span>
                    <div class="dim-track"><div class="dim-fill" :style="{ width: qa.feedback_json.scores.completeness + '%', background: catColor(qa.category) }"></div></div>
                    <em>{{ qa.feedback_json.scores.completeness }}</em>
                  </div>
                  <div class="dim-row">
                    <span>专业性</span>
                    <div class="dim-track"><div class="dim-fill" :style="{ width: qa.feedback_json.scores.professionalism + '%', background: catColor(qa.category) }"></div></div>
                    <em>{{ qa.feedback_json.scores.professionalism }}</em>
                  </div>
                </div>
                <div class="feedback-point good"><strong>优点</strong>{{ qa.feedback_json.strengths }}</div>
                <div class="feedback-point bad"><strong>不足</strong>{{ qa.feedback_json.weaknesses }}</div>
                <div class="feedback-point tip"><strong>改进建议</strong>{{ qa.feedback_json.suggestions }}</div>
              </div>
            </template>
          </template>

          <!-- 评估中：AI 打字气泡 -->
          <div v-if="submitting" class="bubble-row ai">
            <div class="bubble typing">
              <span class="who">AI 面试官</span>
              正在评估你的回答<i></i><i></i><i></i>
            </div>
          </div>

          <!-- 总评报告 -->
          <div v-if="isFinished" class="report-card">
            <div class="report-head">
              <div>
                <h3>面试总评报告</h3>
                <p class="report-sub">{{ session.position_title || '目标岗位' }} · 共 {{ answeredCount }} 轮</p>
              </div>
              <div v-if="averageScore !== null" class="report-score" :style="{ color: scoreColor(averageScore) }">
                {{ averageScore }}<small>平均分</small>
              </div>
            </div>
            <p class="report-summary">{{ session.summary }}</p>
          </div>
        </div>

        <!-- 聊天式底部输入条 -->
        <div class="chat-inputbar">
          <template v-if="isFinished">
            <div class="chat-ended">本场面试已结束，可开始一场新的模拟面试</div>
          </template>
          <template v-else-if="currentQA">
            <input
              ref="chatInput"
              v-model="answerText"
              :disabled="submitting"
              placeholder="输入你的回答，回车发送…"
              maxlength="2000"
              @keyup.enter="sendAnswer"
            />
            <button class="btn-send" :disabled="submitting || !answerText.trim()" @click="sendAnswer">
              发送
            </button>
          </template>
          <template v-else>
            <button class="btn-finish" :disabled="finishing" @click="finish">
              {{ finishing ? 'AI 正在生成总评报告…' : '全部题目已完成，生成面试总评报告' }}
            </button>
          </template>
        </div>
      </div>

      <div class="cta">
        <button class="btn-ghost" @click="backToSetup">开始一场新的模拟面试</button>
      </div>
    </template>
    </div>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; position: relative; overflow: hidden; }
.page-bg {
  position: fixed; inset: 0; z-index: -2;
  background: linear-gradient(-45deg, #f0fdf4, #e0f2fe, #eef2ff, #f0fdfa);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
.page-blob {
  position: fixed; border-radius: 50%; filter: blur(70px); z-index: -1;
  animation: float 8s ease-in-out infinite;
}
.blob-a { width: 300px; height: 300px; background: #43e97b; opacity: 0.1; top: -60px; left: -40px; }
.blob-b { width: 260px; height: 260px; background: #4facfe; opacity: 0.09; bottom: -50px; right: -30px; animation-delay: -4s; }

.page-inner { padding: 2rem; max-width: 820px; margin: 0 auto; }
.page-back { margin-bottom: 1.2rem; }

.page-header { display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.6rem; }
.header-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #43e97b, #4facfe);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(67,233,123,0.3);
  animation: pulse 3.5s ease-in-out infinite;
}
.header-icon svg { width: 28px; height: 28px; }
.page-header h2 { font-size: 1.5rem; color: #1a202c; }
.page-header p { font-size: 0.9rem; color: #718096; margin-top: 0.25rem; }

/* 特性提示 */
.tips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin-bottom: 1.4rem; }
.tip {
  --c: var(--primary);
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(226,232,240,0.5);
  border-radius: 12px;
  padding: 0.85rem 1rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.tip:hover { transform: translateY(-3px); border-color: var(--c); box-shadow: 0 8px 20px color-mix(in srgb, var(--c) 18%, transparent); }
.tip strong { display: block; color: var(--c); margin-bottom: 0.2rem; font-size: 0.92rem; }
.tip span { font-size: 0.8rem; color: #718096; }

/* 建会话卡片 */
.setup-card, .history-card {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226,232,240,0.6);
  border-radius: 16px;
  padding: 1.4rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.06);
}
.form-row { display: grid; grid-template-columns: 2fr 2fr 1fr; gap: 0.9rem; margin-bottom: 1.1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: #4a5568; }
.form-group select {
  padding: 0.6rem 0.7rem;
  border: 1px solid #cbd5e0;
  border-radius: 10px;
  background: #fff;
  font-size: 0.88rem;
  color: #2d3748;
  outline: none;
}
.form-group select:focus { border-color: #4facfe; box-shadow: 0 0 0 3px rgba(79,172,254,0.15); }
.form-note { margin-top: 0.7rem; font-size: 0.78rem; color: #a0aec0; text-align: center; }
.error-text { color: #e53e3e; font-size: 0.85rem; margin-top: 0.7rem; text-align: center; }

.btn {
  width: 100%;
  padding: 0.85rem 2.4rem;
  background: linear-gradient(135deg, #43e97b, #4facfe);
  color: #fff;
  border: none;
  border-radius: 999px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.25s ease;
  box-shadow: 0 8px 24px rgba(67,233,123,0.3);
}
.btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(67,233,123,0.4); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* 历史 */
.history-card { margin-top: 1.2rem; }
.history-card h3 { font-size: 1rem; color: #2d3748; margin-bottom: 0.8rem; }
.history-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 0.9rem;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s ease;
}
.history-item:hover { background: rgba(79,172,254,0.08); }
.history-item + .history-item { border-top: 1px solid #edf2f7; }
.history-title { font-size: 0.9rem; font-weight: 600; color: #2d3748; }
.history-meta { display: block; font-size: 0.76rem; color: #a0aec0; margin-top: 0.15rem; }
.history-right { display: flex; align-items: center; gap: 0.8rem; }
.history-score { font-weight: 700; font-size: 0.95rem; }
.history-go { font-size: 0.8rem; color: #4facfe; }

/* 会话状态条 */
.session-bar {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226,232,240,0.6);
  border-radius: 14px;
  padding: 0.8rem 1.2rem;
  margin-bottom: 1rem;
}
.session-info { display: flex; align-items: center; gap: 0.7rem; }
.session-info strong { color: #1a202c; font-size: 0.98rem; }
.progress-chip, .status-chip {
  font-size: 0.74rem; padding: 0.18rem 0.6rem; border-radius: 999px;
}
.progress-chip { background: #edf2f7; color: #4a5568; }
.status-chip.active { background: #c6f6d5; color: #22543d; }
.status-chip.finished { background: #bee3f8; color: #2a4365; }
.btn-ghost {
  padding: 0.5rem 1.1rem;
  border: 1px solid #cbd5e0;
  background: rgba(255,255,255,0.8);
  color: #4a5568;
  border-radius: 999px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-ghost:hover { border-color: #4facfe; color: #2b6cb0; }

/* 对话窗口 */
.chat-window {
  display: flex;
  flex-direction: column;
  height: 72vh;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 36px rgba(0,0,0,0.1);
  border: 1px solid #e2e8f0;
}
.chat-titlebar {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.7rem 1.1rem;
  background: #1a202c;
}
.dot { width: 11px; height: 11px; border-radius: 50%; }
.dot.red { background: #fc8181; }
.dot.yellow { background: #f6e05e; }
.dot.green { background: #68d391; }
.chat-title { margin-left: 0.6rem; color: #a0aec0; font-size: 0.8rem; }
.chat-body {
  flex: 1;
  overflow-y: auto;
  background: rgba(247,250,252,0.6);
  backdrop-filter: blur(10px);
  padding: 1.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}
.bubble-row { display: flex; animation: bubbleIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
.bubble-row.user { justify-content: flex-end; }
.bubble-row.ai { justify-content: flex-start; }
.bubble {
  max-width: 78%;
  padding: 0.75rem 1.05rem;
  border-radius: 14px;
  font-size: 0.9rem;
  line-height: 1.65;
}
.bubble .who { display: block; font-size: 0.7rem; opacity: 0.65; margin-bottom: 0.25rem; }
.bubble-row.ai .bubble { background: rgba(255,255,255,0.85); border: 1px solid rgba(226,232,240,0.6); color: #2d3748; border-top-left-radius: 4px; }
.bubble-row.user .bubble { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border-top-right-radius: 4px; }
.qa-tag {
  display: inline-block;
  font-size: 0.68rem;
  color: #fff;
  padding: 0.1rem 0.55rem;
  border-radius: 999px;
  margin-bottom: 0.45rem;
}
.question-text { white-space: pre-wrap; }

/* 评估卡片 */
.feedback-card {
  align-self: flex-start;
  width: 82%;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #43e97b;
  border-radius: 12px;
  padding: 0.9rem 1.05rem;
  animation: bubbleIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.feedback-head { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.7rem; }
.feedback-title { font-size: 0.82rem; font-weight: 700; color: #2d3748; }
.score-badge { font-size: 1.15rem; font-weight: 800; margin-left: auto; }
.source-tag { font-size: 0.68rem; background: #feebc8; color: #7b341e; padding: 0.1rem 0.5rem; border-radius: 999px; }
.dim-list { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.7rem; }
.dim-row { display: grid; grid-template-columns: 3.2rem 1fr 2rem; align-items: center; gap: 0.6rem; font-size: 0.78rem; color: #4a5568; }
.dim-row em { font-style: normal; font-weight: 700; color: #2d3748; text-align: right; }
.dim-track { height: 7px; background: #edf2f7; border-radius: 999px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
.feedback-point { font-size: 0.82rem; line-height: 1.6; color: #4a5568; margin-top: 0.35rem; }
.feedback-point strong { display: inline-block; margin-right: 0.4rem; font-size: 0.76rem; }
.feedback-point.good strong { color: #22543d; }
.feedback-point.bad strong { color: #742a2a; }
.feedback-point.tip strong { color: #553c9a; }

/* 聊天式底部输入条 */
.chat-inputbar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  border-top: 1px solid #e2e8f0;
  background: rgba(255,255,255,0.92);
}
.chat-inputbar input {
  flex: 1;
  padding: 0.65rem 1.1rem;
  border: 1px solid #cbd5e0;
  border-radius: 999px;
  font-size: 0.9rem;
  outline: none;
  background: #fff;
  color: #2d3748;
}
.chat-inputbar input:focus { border-color: #4facfe; box-shadow: 0 0 0 3px rgba(79,172,254,0.15); }
.chat-inputbar input:disabled { background: #edf2f7; cursor: not-allowed; }
.btn-send {
  padding: 0.6rem 1.4rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}
.btn-send:hover:not(:disabled) { transform: translateY(-2px); }
.btn-send:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-finish {
  width: 100%;
  padding: 0.7rem 1.5rem;
  background: linear-gradient(135deg, #43e97b, #4facfe);
  color: #fff;
  border: none;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.92rem;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(102,126,234,0.3);
  transition: transform 0.2s ease;
}
.btn-finish:hover:not(:disabled) { transform: translateY(-2px); }
.btn-finish:disabled { opacity: 0.6; cursor: not-allowed; }
.chat-ended { width: 100%; text-align: center; color: #a0aec0; font-size: 0.85rem; }

/* 评估中打字气泡 */
.bubble.typing { color: #718096; }
.bubble.typing i {
  display: inline-block;
  width: 5px; height: 5px;
  margin-left: 4px;
  background: #a0aec0;
  border-radius: 50%;
  animation: dotBlink 1.2s infinite;
}
.bubble.typing i:nth-child(2) { animation-delay: 0.2s; }
.bubble.typing i:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBlink {
  0%, 60%, 100% { opacity: 0.25; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-2px); }
}

/* 消息入场：淡入 + 上浮 + 轻微缩放 */
@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(16px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* 总评报告 */
.report-card {
  align-self: stretch;
  background: linear-gradient(135deg, rgba(67,233,123,0.08), rgba(79,172,254,0.08));
  border: 1px solid rgba(67,233,123,0.3);
  border-radius: 14px;
  padding: 1.2rem 1.3rem;
  animation: bubbleIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.report-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }
.report-head h3 { font-size: 1.05rem; color: #1a202c; }
.report-sub { font-size: 0.78rem; color: #718096; margin-top: 0.15rem; }
.report-score { font-size: 2rem; font-weight: 800; line-height: 1; }
.report-score small { display: block; font-size: 0.7rem; font-weight: 500; color: #718096; margin-top: 0.2rem; text-align: center; }
.report-summary { font-size: 0.88rem; line-height: 1.8; color: #2d3748; white-space: pre-wrap; }

.cta { text-align: center; margin-top: 1.4rem; }

@media (max-width: 640px) {
  .tips { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .bubble, .feedback-card { max-width: 100%; }
  .chat-window { height: 78vh; }
}
</style>
