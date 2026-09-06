<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BackButton from '@/components/BackButton.vue'

const router = useRouter()

const navs = [
  { label: '我的简历', path: '/resume', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z' },
  { label: '岗位分析', path: '/jobs', icon: 'M21 13.255A23.9 23.9 0 0 1 12 15a23.9 23.9 0 0 1-9-1.745V16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2.745z' },
  { label: '能力匹配', path: '/match', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
  { label: '面试准备', path: '/interview', icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
]

// 统计数据（数字滚动）
const stats = ref([
  { label: '技能数量', target: 12, suffix: '项', current: 0, color: '#667eea', icon: 'M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5' },
  { label: '平均匹配度', target: 78, suffix: '%', current: 0, color: '#f093fb', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
  { label: '学习任务', target: 8, suffix: '个', current: 0, color: '#4facfe', icon: 'M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' },
  { label: '模拟面试', target: 3, suffix: '场', current: 0, color: '#43e97b', icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87' },
])

const progress = ref(0)

function animateNumbers() {
  stats.value.forEach((s, idx) => {
    const duration = 1200
    const start = performance.now() + idx * 120
    function step(now: number) {
      const t = Math.min(Math.max((now - start) / duration, 0), 1)
      const eased = 1 - Math.pow(1 - t, 3)
      s.current = Math.round(s.target * eased)
      if (t < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  })
  // 进度条动画
  setTimeout(() => { progress.value = 64 }, 300)
}

onMounted(animateNumbers)
</script>

<template>
  <div class="dashboard">
    <div class="page-bg"></div>
    <div class="page-blob blob-a"></div>
    <div class="page-blob blob-b"></div>
    <div class="page-blob blob-c"></div>
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
        <button v-for="n in navs" :key="n.path" @click="router.push(n.path)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="n.icon" />
          </svg>
          {{ n.label }}
        </button>
      </nav>
    </header>

    <main class="content">
      <h2 class="page-title anim-fade-up">早上好，求职者 👋</h2>
      <p class="page-sub anim-fade-up anim-delay-1">这是你的求职成长概览</p>

      <!-- 统计卡片 -->
      <div class="stats">
        <div
          v-for="(s, i) in stats"
          :key="s.label"
          class="stat-card anim-fade-up"
          :style="{ animationDelay: `${0.1 + i * 0.08}s`, '--c': s.color }"
        >
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path :d="s.icon" />
            </svg>
          </div>
          <div class="stat-info">
            <strong>{{ s.current }}<span class="suffix">{{ s.suffix }}</span></strong>
            <span class="stat-label">{{ s.label }}</span>
          </div>
        </div>
      </div>

      <div class="panels">
        <!-- 学习进度 -->
        <div class="panel anim-fade-up anim-delay-3">
          <h3>学习进度</h3>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="progress-meta">
            <span>Python 基础强化</span>
            <strong>{{ progress }}%</strong>
          </div>
          <div class="task-list">
            <div class="task done"><span class="dot"></span>复习 Python 装饰器<span class="tag">已完成</span></div>
            <div class="task doing"><span class="dot"></span>LeetCode 链表专项<span class="tag">进行中</span></div>
            <div class="task todo"><span class="dot"></span>八股文：HTTP 缓存<span class="tag">待开始</span></div>
          </div>
        </div>

        <!-- 能力雷达占位 -->
        <div class="panel anim-fade-up anim-delay-4">
          <h3>能力画像概览</h3>
          <div class="radar">
            <div class="radar-ring r1"></div>
            <div class="radar-ring r2"></div>
            <div class="radar-ring r3"></div>
            <svg class="radar-shape" viewBox="0 0 100 100">
              <polygon points="50,12 82,32 74,72 50,88 26,72 18,32" fill="rgba(102,126,234,0.25)" stroke="#667eea" stroke-width="2" />
            </svg>
          </div>
          <p class="radar-note">技能 · 经验 · 学历 · 项目 · 软实力</p>
        </div>

        <!-- 快捷入口 -->
        <div class="panel anim-fade-up anim-delay-5">
          <h3>快捷入口</h3>
          <div class="quick-grid">
            <button class="quick" style="--c:#667eea" @click="router.push('/resume')">
              <span>上传简历</span><small>AI 解析能力画像</small>
            </button>
            <button class="quick" style="--c:#764ba2" @click="router.push('/jobs')">
              <span>解析 JD</span><small>提取岗位要求</small>
            </button>
            <button class="quick" style="--c:#f093fb" @click="router.push('/match')">
              <span>匹配诊断</span><small>生成差距报告</small>
            </button>
            <button class="quick" style="--c:#43e97b" @click="router.push('/interview')">
              <span>模拟面试</span><small>AI 面试官陪练</small>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard { min-height: 100vh; position: relative; overflow: hidden; }
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
.blob-c { width: 200px; height: 200px; background: #4facfe; opacity: 0.08; top: 40%; left: 60%; animation-delay: -6s; }

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
.brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 800; font-size: 1.15rem; cursor: pointer; }
.topbar-left { display: flex; align-items: center; gap: 0.9rem; }
.brand-logo {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  animation: pulse 3s ease-in-out infinite;
}
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
.topbar nav button svg { width: 15px; height: 15px; }
.topbar nav button:hover {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102,126,234,0.35);
}

/* 主体 */
.content { padding: 2rem; max-width: 1100px; margin: 0 auto; }
.page-title { font-size: 1.5rem; color: #1a202c; }
.page-sub { color: #718096; margin: 0.3rem 0 1.8rem; }

/* 统计卡片 */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.2rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  --c: var(--primary);
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.3rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  border-bottom: 3px solid transparent;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease, background 0.3s ease;
}
.stat-card:hover { transform: translateY(-5px); background: rgba(255,255,255,0.8); box-shadow: 0 14px 30px rgba(0,0,0,0.1); border-bottom-color: var(--c); }
.stat-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--c) 15%, white);
  color: var(--c);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon svg { width: 24px; height: 24px; }
.stat-info strong { font-size: 1.7rem; color: #1a202c; display: block; line-height: 1.1; }
.suffix { font-size: 0.85rem; font-weight: 500; color: #a0aec0; margin-left: 2px; }
.stat-label { font-size: 0.85rem; color: #718096; }

/* 面板 */
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.2rem;
}
.panel {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}
.panel h3 { font-size: 1.05rem; margin-bottom: 1.1rem; color: #2d3748; }

/* 进度条 */
.progress-track { height: 10px; background: #edf2f7; border-radius: 999px; overflow: hidden; }
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  background-size: 200% 100%;
  animation: gradientShift 3s ease infinite;
  transition: width 1.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.progress-meta { display: flex; justify-content: space-between; margin: 0.5rem 0 1rem; font-size: 0.88rem; color: #4a5568; }
.task-list { display: flex; flex-direction: column; gap: 0.6rem; }
.task {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.55rem 0.8rem;
  background: rgba(255,255,255,0.5);
  border-radius: 10px;
  font-size: 0.88rem;
  color: #4a5568;
  transition: transform 0.2s ease, background 0.2s ease;
}
.task:hover { transform: translateX(4px); background: rgba(255,255,255,0.7); }
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.task.done .dot { background: #43e97b; }
.task.doing .dot { background: #4facfe; animation: pulse 1.6s ease infinite; }
.task.todo .dot { background: #cbd5e0; }
.tag { margin-left: auto; font-size: 0.72rem; padding: 0.15rem 0.55rem; border-radius: 999px; background: #fff; border: 1px solid #e2e8f0; color: #718096; }

/* 雷达占位 */
.radar {
  position: relative;
  width: 180px; height: 180px;
  margin: 0.5rem auto 0.8rem;
}
.radar-ring {
  position: absolute;
  border: 1px dashed #cbd5e0;
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
.r1 { width: 60px; height: 60px; }
.r2 { width: 115px; height: 115px; }
.r3 { width: 170px; height: 170px; }
.radar-shape {
  position: absolute;
  inset: 0;
  animation: pulse 4s ease-in-out infinite;
}
.radar-note { text-align: center; font-size: 0.8rem; color: #a0aec0; }

/* 快捷入口 */
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
.quick {
  --c: var(--primary);
  border: 1px solid rgba(226,232,240,0.6);
  background: rgba(255,255,255,0.5);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 0.9rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}
.quick::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--c);
  opacity: 0;
  transition: opacity 0.25s ease;
}
.quick:hover { transform: translateY(-3px); box-shadow: 0 10px 24px color-mix(in srgb, var(--c) 30%, transparent); border-color: var(--c); }
.quick:hover::after { opacity: 0.08; }
.quick span { display: block; font-weight: 700; color: #2d3748; font-size: 0.95rem; position: relative; }
.quick small { color: #a0aec0; font-size: 0.75rem; position: relative; }
</style>
