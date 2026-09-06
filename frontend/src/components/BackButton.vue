<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  // 有浏览历史则返回上一页，否则回到首页
  if (window.history.state && window.history.state.back) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<template>
  <button class="back-btn" aria-label="返回" @click="goBack">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
    <span class="back-text">返回</span>
  </button>
</template>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  height: 40px;
  padding: 0 0.9rem 0 0.7rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(12px);
  color: #4a5568;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.25s ease;
}
.back-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.25s ease;
}
.back-btn:hover {
  background: rgba(255, 255, 255, 0.85);
  color: var(--primary, #667eea);
  border-color: var(--primary, #667eea);
  box-shadow: 0 6px 18px rgba(102, 126, 234, 0.2);
  transform: translateX(-2px);
}
.back-btn:hover svg { transform: translateX(-3px); }
.back-btn:active { transform: scale(0.96); }
</style>
