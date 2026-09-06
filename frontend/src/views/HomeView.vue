<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="home">
    <div class="hero">
      <h1>CareerAI</h1>
      <p class="subtitle">AI求职与职业成长智能体</p>
      <p class="desc">简历解析 · 岗位分析 · 能力匹配 · 学习规划 · 面试准备</p>
      <div class="actions">
        <button class="btn primary" @click="router.push('/login')">立即开始</button>
        <button class="btn" @click="router.push('/dashboard')">查看仪表盘</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.hero { text-align: center; color: #fff; padding: 2rem; }
.hero h1 { font-size: 3.5rem; margin-bottom: 0.5rem; }
.subtitle { font-size: 1.5rem; opacity: 0.95; margin-bottom: 1rem; }
.desc { font-size: 1.1rem; opacity: 0.85; margin-bottom: 2rem; }
.actions { display: flex; gap: 1rem; justify-content: center; }
.btn { padding: 0.75rem 2rem; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; background: rgba(255,255,255,0.2); color: #fff; transition: all 0.2s; }
.btn.primary { background: #fff; color: #667eea; font-weight: 600; }
.btn:hover { transform: translateY(-2px); }
</style>
