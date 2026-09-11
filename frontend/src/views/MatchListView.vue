<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import { useMatchStore } from '@/stores/match'

const router = useRouter()
const matchStore = useMatchStore()

// 状态
const loading = ref(false)

// 计算属性
const matches = computed(() => matchStore.matches)
const hasMatches = computed(() => matchStore.hasMatches)

// 加载匹配列表
async function loadMatches() {
  try {
    loading.value = true
    await matchStore.fetchMatches()
  } catch (err) {
    console.error('加载匹配列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 查看匹配详情
function viewMatchDetail(matchId: string) {
  router.push(`/match/detail/${matchId}`)
}

// 分析新的匹配
function analyzeNewMatch() {
  router.push('/match')
}

// 初始化
onMounted(() => {
  loadMatches()
})

// 获取匹配度等级
function getMatchLevel(score: number) {
  if (score >= 90) return { level: '优秀', color: '#10b981', text: 'text-green-600' }
  if (score >= 70) return { level: '良好', color: '#3b82f6', text: 'text-blue-600' }
  if (score >= 50) return { level: '一般', color: '#f59e0b', text: 'text-yellow-600' }
  return { level: '较差', color: '#ef4444', text: 'text-red-600' }
}

// 获取匹配颜色
function getMatchColor(score: number) {
  const level = getMatchLevel(score)
  return level.color
}

// 格式化日期
function formatDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now.getTime() - date.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 1) return '今天'
  if (diffDays === 2) return '昨天'
  if (diffDays <= 7) return `${diffDays}天前`
  if (diffDays <= 30) return `${Math.floor(diffDays / 7)}周前`
  if (diffDays <= 365) return `${Math.floor(diffDays / 30)}个月前`
  return `${Math.floor(diffDays / 365)}年前`
}
</script>

<template>
  <div class="match-list">
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
        <button @click="analyzeNewMatch" class="new-match-btn">新建分析</button>
      </nav>
    </header>

    <main class="content">
      <div class="container">
        <div class="page-header anim-fade-up">
          <h1>匹配度分析</h1>
          <p>查看简历与岗位的匹配度分析结果</p>
        </div>

        <!-- 统计信息 -->
        <div v-if="hasMatches" class="stats-section anim-fade-up anim-delay-1">
          <div class="stat-card">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div class="stat-info">
              <strong>{{ matches.length }}</strong>
              <span>匹配分析</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div class="stat-info">
              <strong>{{ matches.filter(m => m.overall_score >= 70).length }}</strong>
              <span>优秀匹配</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div class="stat-info">
              <strong>{{ matches.filter(m => m.overall_score < 70).length }}</strong>
              <span>待优化</span>
            </div>
          </div>
        </div>

        <!-- 匹配列表 -->
        <div v-if="hasMatches" class="matches-list anim-fade-up anim-delay-2">
          <h2>历史分析</h2>
          <div class="match-cards">
            <div
              v-for="match in matches"
              :key="match.id"
              class="match-card"
              @click="viewMatchDetail(match.id)"
            >
              <div class="match-header">
                <div class="match-title">{{ match.position_title }}</div>
                <div class="match-date">{{ formatDate(match.analyzed_at) }}</div>
              </div>

              <div class="match-score">
                <div class="score-circle" :style="`--color: ${getMatchColor(match.overall_score)}`">
                  <span class="score-number">{{ match.overall_score }}</span>
                  <span class="score-label">分</span>
                </div>
                <div class="score-details">
                  <div class="score-item">
                    <span class="label">技能</span>
                    <span class="value">{{ match.skill_match }}%</span>
                  </div>
                  <div class="score-item">
                    <span class="label">经验</span>
                    <span class="value">{{ match.experience_match }}%</span>
                  </div>
                  <div class="score-item">
                    <span class="label">教育</span>
                    <span class="value">{{ match.education_match }}%</span>
                  </div>
                </div>
              </div>

              <div class="match-level" :class="getMatchLevel(match.overall_score).text">
                {{ getMatchLevel(match.overall_score).level }}
              </div>

              <div class="match-actions">
                <button class="detail-btn">查看详情</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state anim-fade-up">
          <div class="empty-icon">📊</div>
          <h2>暂无匹配分析</h2>
          <p>开始分析您的简历与岗位的匹配度吧</p>
          <button @click="analyzeNewMatch" class="primary-button">
            开始分析
          </button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载匹配列表中...</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.match-list { min-height: 100vh; position: relative; overflow: hidden; }
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
.new-match-btn {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.5rem 1.2rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}
.new-match-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.35);
}

/* 主体 */
.content { padding: 2rem; max-width: 1100px; margin: 0 auto; }
.container { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 2rem; box-shadow: 0 2px 16px rgba(0,0,0,0.04); }

/* 页面标题 */
.page-header { text-align: center; margin-bottom: 3rem; }
.page-header h1 { font-size: 2.5rem; color: #1a202c; margin-bottom: 0.5rem; }
.page-header p { font-size: 1.1rem; color: #718096; }

/* 统计信息 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 3rem;
}
.stat-card {
  background: rgba(255,255,255,0.7);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}
.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}
.stat-icon svg { width: 30px; height: 30px; }
.stat-info strong { font-size: 2rem; color: #1a202c; display: block; margin-bottom: 0.5rem; }
.stat-info span { color: #718096; font-size: 0.9rem; }

/* 匹配列表 */
.matches-list h2 { font-size: 1.8rem; color: #1a202c; margin-bottom: 2rem; }
.match-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}
.match-card {
  background: rgba(255,255,255,0.7);
  border-radius: 16px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1px solid transparent;
}
.match-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  border-color: var(--primary);
}
.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.match-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1a202c;
  flex: 1;
}
.match-date {
  font-size: 0.9rem;
  color: #718096;
}

.match-score {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1rem;
}
.score-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  position: relative;
}
.score-number { font-size: 1.8rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 0.8rem; opacity: 0.9; }
.score-details { flex: 1; }
.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.score-item:last-child { margin-bottom: 0; }
.score-item .label { color: #718096; font-size: 0.9rem; }
.score-item .value { font-weight: 600; color: #1a202c; }

.match-level {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background: rgba(255,255,255,0.5);
}

.match-actions {
  display: flex;
  justify-content: center;
}
.detail-btn {
  background: #fff;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.detail-btn:hover {
  background: var(--primary);
  color: #fff;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}
.empty-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}
.empty-state h2 {
  font-size: 1.8rem;
  color: #1a202c;
  margin-bottom: 1rem;
}
.empty-state p {
  color: #718096;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}
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
}
.primary-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102,126,234,0.3);
}

/* 加载状态 */
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
.anim-delay-1 { animation-delay: 0.1s; }
.anim-delay-2 { animation-delay: 0.2s; }
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

/* 响应式 */
@media (max-width: 768px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
  .match-cards {
    grid-template-columns: 1fr;
  }
}
</style>