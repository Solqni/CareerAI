<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const dims = [
  { name: '技能匹配', value: 78 },
  { name: '经验匹配', value: 64 },
  { name: '学历匹配', value: 90 },
  { name: '项目相关', value: 55 },
  { name: '软实力', value: 72 },
]

const gapList = [
  { skill: 'Docker 容器化', priority: '高', color: '#fc8181' },
  { skill: '系统设计经验', priority: '高', color: '#fc8181' },
  { skill: 'Redis 缓存实战', priority: '中', color: '#f6ad55' },
  { skill: '单元测试', priority: '低', color: '#68d391' },
]

const shown = ref(false)
onMounted(() => setTimeout(() => (shown.value = true), 400))
</script>

<template>
  <div class="page">
    <div class="page-header anim-fade-up">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </div>
      <div>
        <h2>能力匹配</h2>
        <p>Agent 自动对比能力画像与岗位要求，计算匹配度并生成差距报告</p>
      </div>
    </div>

    <!-- 总分卡 -->
    <div class="score-card anim-fade-up anim-delay-1">
      <div class="score-ring">
        <svg viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="52" fill="none" stroke="#edf2f7" stroke-width="10" />
          <circle
            class="ring-progress"
            cx="60" cy="60" r="52"
            fill="none"
            stroke="url(#grad)"
            stroke-width="10"
            stroke-linecap="round"
            :stroke-dasharray="2 * Math.PI * 52"
            :stroke-dashoffset="shown ? 2 * Math.PI * 52 * (1 - 0.72) : 2 * Math.PI * 52"
          />
          <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#667eea" />
              <stop offset="100%" stop-color="#f093fb" />
            </linearGradient>
          </defs>
        </svg>
        <div class="score-num">
          <strong>72</strong>
          <span>综合匹配度</span>
        </div>
      </div>
      <div class="score-summary">
        <h3>匹配诊断摘要</h3>
        <p>你的技能基础与该岗位总体契合度较好，学历完全达标。主要差距集中在<strong>容器化部署</strong>与<strong>系统设计经验</strong>两方面，建议优先补齐。</p>
        <button class="btn" @click="router.push('/interview')">生成学习计划 →</button>
      </div>
    </div>

    <div class="panels">
      <!-- 维度条形图 -->
      <div class="panel anim-fade-up anim-delay-2">
        <h3>维度分析</h3>
        <div class="bars">
          <div v-for="(d, i) in dims" :key="d.name" class="bar-row">
            <span class="bar-label">{{ d.name }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{
                  width: shown ? d.value + '%' : '0%',
                  transitionDelay: i * 0.12 + 's',
                  background: `linear-gradient(90deg, #667eea, #f093fb)`,
                }"
              ></div>
            </div>
            <strong class="bar-val">{{ d.value }}</strong>
          </div>
        </div>
      </div>

      <!-- 差距清单 -->
      <div class="panel anim-fade-up anim-delay-3">
        <h3>差距清单</h3>
        <div class="gaps">
          <div v-for="(g, i) in gapList" :key="g.skill" class="gap-item" :style="{ animationDelay: 0.5 + i * 0.1 + 's' }">
            <span class="prio" :style="{ background: g.color }">{{ g.priority }}</span>
            <span class="skill">{{ g.skill }}</span>
            <span class="go">补齐 →</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 2rem; max-width: 860px; margin: 0 auto; }

.page-header { display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.6rem; }
.header-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f093fb, #667eea);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(240,147,251,0.3);
  animation: pulse 3.5s ease-in-out infinite;
}
.header-icon svg { width: 28px; height: 28px; }
.page-header h2 { font-size: 1.5rem; color: #1a202c; }
.page-header p { font-size: 0.9rem; color: #718096; margin-top: 0.25rem; }

/* 总分卡 */
.score-card {
  display: flex;
  align-items: center;
  gap: 2rem;
  background: #fff;
  border-radius: 18px;
  padding: 1.8rem;
  box-shadow: 0 4px 20px rgba(102,126,234,0.08);
  margin-bottom: 1.4rem;
}
.score-ring { position: relative; width: 150px; height: 150px; flex-shrink: 0; }
.ring-progress { transition: stroke-dashoffset 1.6s cubic-bezier(0.22, 1, 0.36, 1); transform: rotate(-90deg); transform-origin: center; }
.score-num {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-num strong { font-size: 2.4rem; background: linear-gradient(135deg, #667eea, #f093fb); -webkit-background-clip: text; background-clip: text; color: transparent; }
.score-num span { font-size: 0.75rem; color: #a0aec0; }
.score-summary h3 { margin-bottom: 0.5rem; color: #2d3748; }
.score-summary p { font-size: 0.92rem; color: #718096; line-height: 1.7; margin-bottom: 1rem; }
.score-summary strong { color: #e53e3e; }
.btn {
  padding: 0.65rem 1.6rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.25s ease;
}
.btn:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(102,126,234,0.35); }

/* 面板 */
.panels { display: grid; grid-template-columns: 1.2fr 1fr; gap: 1.2rem; }
.panel { background: #fff; border-radius: 16px; padding: 1.5rem; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.panel h3 { font-size: 1.02rem; margin-bottom: 1.2rem; color: #2d3748; }

/* 条形图 */
.bars { display: flex; flex-direction: column; gap: 0.9rem; }
.bar-row { display: flex; align-items: center; gap: 0.8rem; }
.bar-label { width: 72px; font-size: 0.85rem; color: #4a5568; flex-shrink: 0; }
.bar-track { flex: 1; height: 10px; background: #edf2f7; border-radius: 999px; overflow: hidden; }
.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 1.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.bar-val { width: 32px; text-align: right; font-size: 0.85rem; color: #667eea; }

/* 差距清单 */
.gaps { display: flex; flex-direction: column; gap: 0.7rem; }
.gap-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.9rem;
  background: #f7fafc;
  border-radius: 10px;
  font-size: 0.88rem;
  animation: bubbleIn 0.5s ease both;
  transition: transform 0.2s ease, background 0.2s ease;
}
.gap-item:hover { transform: translateX(4px); background: #edf2f7; }
.prio {
  font-size: 0.7rem;
  color: #fff;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  flex-shrink: 0;
}
.skill { color: #2d3748; font-weight: 500; }
.go { margin-left: auto; font-size: 0.78rem; color: #a0aec0; }
.gap-item:hover .go { color: var(--primary); }

@media (max-width: 760px) {
  .score-card { flex-direction: column; text-align: center; }
  .panels { grid-template-columns: 1fr; }
}
</style>
