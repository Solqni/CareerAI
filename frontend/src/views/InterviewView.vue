<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import BackButton from '@/components/BackButton.vue'

// 模拟面试对话演示气泡
const demoScript = [
  { role: 'ai', text: '你好，我是你的 AI 面试官。我们开始今天 Python 后端岗位的模拟面试吧。' },
  { role: 'user', text: '好的，我准备好了！' },
  { role: 'ai', text: '请介绍一下你在项目中使用过的最复杂的技术方案，以及你解决的核心难点。' },
  { role: 'user', text: '我在课设中设计了基于 LangGraph 的 Agent 工作流……' },
  { role: 'ai', text: '不错，能展开讲讲 Tool 调用失败时的降级策略吗？' },
]

const visibleCount = ref(0)
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => {
    if (visibleCount.value < demoScript.length) {
      visibleCount.value++
    } else {
      visibleCount.value = 0 // 循环播放
    }
  }, 1400)
})
onUnmounted(() => window.clearInterval(timer))

const features = [
  { title: '技术题', desc: '岗位相关技术考察', color: '#667eea' },
  { title: '项目题', desc: '深挖简历项目细节', color: '#764ba2' },
  { title: '行为题', desc: '软素质与沟通表达', color: '#f093fb' },
]
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
        <p>AI 扮演面试官进行多轮对话，结束后生成多维度评估反馈报告</p>
      </div>
    </div>

    <div class="tips">
      <div v-for="(f, i) in features" :key="f.title" class="tip anim-fade-up" :style="{ '--c': f.color, animationDelay: 0.1 + i * 0.1 + 's' }">
        <strong>{{ f.title }}</strong>
        <span>{{ f.desc }}</span>
      </div>
    </div>

    <!-- 对话演示窗口 -->
    <div class="chat-window anim-fade-up anim-delay-3">
      <div class="chat-titlebar">
        <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
        <span class="chat-title">AI 面试官 · 模拟对话演示</span>
      </div>
      <div class="chat-body">
        <div
          v-for="(m, i) in demoScript.slice(0, visibleCount)"
          :key="i"
          class="bubble-row"
          :class="m.role"
        >
          <div class="bubble">
            <span class="who">{{ m.role === 'ai' ? 'AI 面试官' : '我' }}</span>
            {{ m.text }}
          </div>
        </div>
      </div>
    </div>

    <div class="cta anim-fade-up anim-delay-4">
      <button class="btn">开始真实模拟面试</button>
      <p class="cta-note">评估维度：逻辑性 · 完整性 · 专业性</p>
    </div>
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

.page-inner { padding: 2rem; max-width: 760px; margin: 0 auto; }
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
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease, background 0.25s ease;
}
.tip:hover { transform: translateY(-3px); border-color: var(--c); background: rgba(255,255,255,0.8); box-shadow: 0 8px 20px color-mix(in srgb, var(--c) 18%, transparent); }
.tip strong { display: block; color: var(--c); margin-bottom: 0.2rem; font-size: 0.92rem; }
.tip span { font-size: 0.8rem; color: #718096; }

/* 对话窗口 */
.chat-window {
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
  background: rgba(247,250,252,0.6);
  backdrop-filter: blur(10px);
  padding: 1.3rem;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}
.bubble-row { display: flex; animation: bubbleIn 0.45s ease both; }
.bubble-row.user { justify-content: flex-end; }
.bubble-row.ai { justify-content: flex-start; }
.bubble {
  max-width: 75%;
  padding: 0.75rem 1.05rem;
  border-radius: 14px;
  font-size: 0.9rem;
  line-height: 1.6;
}
.bubble .who { display: block; font-size: 0.7rem; opacity: 0.65; margin-bottom: 0.2rem; }
.bubble-row.ai .bubble { background: rgba(255,255,255,0.7); backdrop-filter: blur(8px); border: 1px solid rgba(226,232,240,0.5); color: #2d3748; border-top-left-radius: 4px; }
.bubble-row.user .bubble { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border-top-right-radius: 4px; }

/* CTA */
.cta { text-align: center; margin-top: 1.6rem; }
.btn {
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
.btn:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 14px 32px rgba(67,233,123,0.42); }
.cta-note { margin-top: 0.7rem; font-size: 0.8rem; color: #a0aec0; }

@media (max-width: 640px) {
  .tips { grid-template-columns: 1fr; }
}
</style>
