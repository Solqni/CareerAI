<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  { title: '简历解析', desc: '上传 PDF/Word，AI 自动提取技能与经历', path: '/resume', color: '#667eea', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM8 13h8M8 17h8M8 9h2' },
  { title: '岗位分析', desc: '粘贴 JD，秒级提取岗位要求与关键词', path: '/jobs', color: '#764ba2', icon: 'M21 13.255A23.9 23.9 0 0 1 12 15a23.9 23.9 0 0 1-9-1.745V16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2.745zM16 3v2a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V3' },
  { title: '能力匹配', desc: '雷达图呈现匹配度，精准定位差距', path: '/match', color: '#f093fb', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
  { title: '学习规划', desc: 'AI 定制学习计划，追踪每一步成长', path: '/dashboard', color: '#4facfe', icon: 'M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z' },
  { title: '面试准备', desc: '模拟面试官多轮对话，实时评估反馈', path: '/interview', color: '#43e97b', icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
]

// 打字机效果
const phrases = ['看清自己', '看懂岗位', '做好规划', '持续成长']
const typed = ref('')
let phraseIdx = 0
let charIdx = 0
let deleting = false
let timer: number | undefined

function typeLoop() {
  const current = phrases[phraseIdx]
  if (!deleting) {
    typed.value = current.slice(0, ++charIdx)
    if (charIdx === current.length) {
      deleting = true
      timer = window.setTimeout(typeLoop, 1600)
      return
    }
  } else {
    typed.value = current.slice(0, --charIdx)
    if (charIdx === 0) {
      deleting = false
      phraseIdx = (phraseIdx + 1) % phrases.length
    }
  }
  timer = window.setTimeout(typeLoop, deleting ? 60 : 140)
}

onMounted(() => { timer = window.setTimeout(typeLoop, 500) })
onUnmounted(() => window.clearTimeout(timer))
</script>

<template>
  <div class="home">
    <!-- 动态渐变背景 -->
    <div class="bg-gradient"></div>
    <!-- 浮动装饰形状 -->
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>

    <div class="container">
      <div class="hero">
        <span class="badge anim-fade-up">AI 求职与职业成长智能体</span>
        <h1 class="anim-fade-up anim-delay-1">CareerAI</h1>
        <p class="subtitle anim-fade-up anim-delay-2">
          帮助你 <span class="typed">{{ typed }}</span><span class="caret"></span>
        </p>
        <p class="desc anim-fade-up anim-delay-3">
          从简历解析到面试模拟，一站式 AI 求职助手，伴你走完求职每一步
        </p>
        <div class="actions anim-fade-up anim-delay-4">
          <button class="btn primary" @click="router.push('/login')">立即开始</button>
          <button class="btn ghost" @click="router.push('/dashboard')">查看仪表盘</button>
        </div>
      </div>

      <!-- 功能流程 -->
      <section class="flow-section">
        <div class="flow-header anim-fade-up">
          <span class="flow-label">FIVE CORE MODULES</span>
          <h2>一站式求职工作流</h2>
        </div>

        <div class="flow-track">
          <!-- 连接线 -->
          <div class="flow-line"></div>
          <div class="flow-line-fill"></div>

          <!-- 步骤节点 -->
          <div
            v-for="(f, i) in features"
            :key="f.title"
            class="flow-step anim-fade-up"
            :style="{ animationDelay: `${0.5 + i * 0.12}s`, '--step-color': f.color }"
            @click="router.push(f.path)"
          >
            <div class="step-node">
              <span class="step-num">{{ String(i + 1).padStart(2, '0') }}</span>
              <div class="step-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="f.icon" />
                </svg>
              </div>
              <div class="step-ring"></div>
            </div>
            <div class="step-info">
              <h3>{{ f.title }}</h3>
              <p>{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  padding: 4rem 2rem;
}
.bg-gradient {
  position: fixed;
  inset: 0;
  z-index: -2;
  background: linear-gradient(-45deg, #667eea, #764ba2, #6b8dd6, #8e6bbf);
  background-size: 400% 400%;
  animation: gradientShift 14s ease infinite;
}
/* 浮动装饰 */
.blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.45;
  z-index: -1;
  animation: float 9s ease-in-out infinite;
}
.blob-1 { width: 340px; height: 340px; background: #f093fb; top: -80px; left: -60px; }
.blob-2 { width: 280px; height: 280px; background: #4facfe; bottom: -60px; right: -40px; animation-delay: -3s; }
.blob-3 { width: 180px; height: 180px; background: #43e97b; top: 55%; left: 8%; animation-delay: -5s; opacity: 0.3; }
.blob-4 { width: 220px; height: 220px; background: #ffd86f; top: 12%; right: 12%; animation-delay: -7s; opacity: 0.28; }

.container { max-width: 1100px; margin: 0 auto; }

/* Hero 区 */
.hero { text-align: center; color: #fff; padding: 3rem 0 4rem; }
.badge {
  display: inline-block;
  padding: 0.4rem 1.1rem;
  border: 1px solid rgba(255,255,255,0.35);
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(6px);
  border-radius: 999px;
  font-size: 0.85rem;
  letter-spacing: 2px;
  margin-bottom: 1.4rem;
}
.hero h1 {
  font-size: 4.2rem;
  letter-spacing: 2px;
  margin-bottom: 1rem;
  text-shadow: 0 4px 24px rgba(0,0,0,0.18);
}
.subtitle { font-size: 1.6rem; margin-bottom: 1rem; min-height: 2.2em; }
.typed { font-weight: 700; border-bottom: 3px solid rgba(255,255,255,0.7); padding-bottom: 2px; }
.caret {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: #fff;
  margin-left: 3px;
  vertical-align: text-bottom;
  animation: blink 0.9s step-end infinite;
}
.desc { font-size: 1.08rem; opacity: 0.9; margin-bottom: 2.2rem; }

.actions { display: flex; gap: 1rem; justify-content: center; }
.btn {
  padding: 0.85rem 2.4rem;
  border: none;
  border-radius: 999px;
  font-size: 1.05rem;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.btn.primary {
  background: #fff;
  color: var(--primary);
  font-weight: 700;
  box-shadow: 0 8px 24px rgba(255,255,255,0.25);
}
.btn.primary:hover { transform: translateY(-3px) scale(1.03); box-shadow: 0 12px 32px rgba(255,255,255,0.35); }
.btn.ghost {
  background: rgba(255,255,255,0.15);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.45);
  backdrop-filter: blur(6px);
}
.btn.ghost:hover { background: rgba(255,255,255,0.28); transform: translateY(-3px); }

/* 功能流程 */
.flow-section { margin-top: 1rem; }
.flow-header { text-align: center; color: #fff; margin-bottom: 3rem; }
.flow-label {
  font-size: 0.75rem;
  letter-spacing: 4px;
  opacity: 0.7;
  display: block;
  margin-bottom: 0.5rem;
}
.flow-header h2 { font-size: 1.8rem; font-weight: 700; }

.flow-track {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0 1rem;
}
/* 连接线 */
.flow-line {
  position: absolute;
  top: 32px;
  left: 8%;
  right: 8%;
  height: 3px;
  background: rgba(255,255,255,0.15);
  border-radius: 2px;
  z-index: 0;
}
.flow-line-fill {
  position: absolute;
  top: 32px;
  left: 8%;
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #4facfe, #43e97b);
  border-radius: 2px;
  z-index: 1;
  animation: drawLine 2s ease 0.3s forwards;
}
@keyframes drawLine { to { width: 84%; } }

/* 步骤节点 */
.flow-step {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  text-align: center;
}
.step-node {
  position: relative;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.1rem;
}
.step-num {
  position: absolute;
  top: -8px;
  right: -8px;
  font-size: 0.65rem;
  font-weight: 800;
  color: #fff;
  background: var(--step-color);
  padding: 2px 6px;
  border-radius: 8px;
  z-index: 3;
}
.step-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.18);
  border: 2px solid var(--step-color);
  color: #fff;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(8px);
  z-index: 2;
}
.step-icon svg { width: 22px; height: 22px; }
.step-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid var(--step-color);
  opacity: 0;
  transition: opacity 0.3s ease;
  animation: ringPulse 2.5s ease-in-out infinite;
}
@keyframes ringPulse {
  0%, 100% { transform: scale(1); opacity: 0; }
  50% { transform: scale(1.3); opacity: 0.3; }
}
/* hover 效果 */
.flow-step:hover .step-icon {
  background: var(--step-color);
  transform: scale(1.18);
  box-shadow: 0 0 24px var(--step-color);
}
.flow-step:hover .step-ring { opacity: 0.5; animation: ringPulse 1s ease-in-out infinite; }
.step-info { max-width: 150px; }
.step-info h3 {
  font-size: 1rem;
  color: #fff;
  margin-bottom: 0.3rem;
  transition: color 0.3s ease;
}
.flow-step:hover .step-info h3 { color: var(--step-color); }
.step-info p {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.6);
  line-height: 1.5;
  transition: color 0.3s ease;
}
.flow-step:hover .step-info p { color: rgba(255,255,255,0.85); }

/* 响应式 */
@media (max-width: 768px) {
  .flow-track {
    flex-direction: column;
    gap: 0;
    align-items: stretch;
  }
  .flow-line, .flow-line-fill {
    top: 32px;
    bottom: auto;
    left: 32px;
    right: auto;
    width: 3px;
    height: auto;
  }
  .flow-line { height: 100%; background: rgba(255,255,255,0.12); }
  .flow-line-fill {
    width: 3px;
    height: 0;
    animation: drawLineV 2s ease 0.3s forwards;
  }
  @keyframes drawLineV { to { height: calc(100% - 64px); } }
  .flow-step {
    flex-direction: row;
    align-items: center;
    text-align: left;
    padding: 0.5rem 0 0.5rem 5rem;
  }
  .step-node { margin-bottom: 0; }
  .step-info { max-width: none; }
}
</style>
