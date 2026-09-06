<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="dashboard">
    <header class="topbar">
      <h2>仪表盘</h2>
      <nav>
        <button @click="router.push('/resume')">我的简历</button>
        <button @click="router.push('/jobs')">岗位分析</button>
        <button @click="router.push('/match')">能力匹配</button>
        <button @click="router.push('/interview')">面试准备</button>
      </nav>
    </header>
    <main class="content">
      <div class="card"><h3>能力画像概览</h3><p>展示技能、经验、教育背景等关键指标（占位）</p></div>
      <div class="card"><h3>匹配度趋势</h3><p>可视化匹配报告（占位）</p></div>
      <div class="card"><h3>学习进度</h3><p>学习计划与任务完成情况（占位）</p></div>
    </main>
  </div>
</template>

<style scoped>
.dashboard { min-height: 100vh; }
.topbar { background: #fff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.topbar nav { display: flex; gap: 0.5rem; }
.topbar button { padding: 0.5rem 1rem; border: 1px solid #ddd; background: #fff; border-radius: 6px; cursor: pointer; }
.topbar button:hover { background: #f0f2ff; }
.content { padding: 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
.card { background: #fff; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card h3 { margin-bottom: 0.5rem; color: #333; }
</style>
