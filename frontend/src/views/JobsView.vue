<script setup lang="ts">
import { ref } from 'vue'
const jdText = ref('')
const loading = ref(false)
async function handleParse() {
  if (!jdText.value.trim()) return
  loading.value = true
  setTimeout(() => { loading.value = false; alert('JD 解析占位：请接入后端 API') }, 800)
}
</script>

<template>
  <div class="page">
    <h2>岗位分析</h2>
    <textarea v-model="jdText" placeholder="粘贴目标岗位 JD 文本..."></textarea>
    <button class="btn" :disabled="loading" @click="handleParse">{{ loading ? '解析中...' : '解析 JD' }}</button>
  </div>
</template>

<style scoped>
.page { padding: 2rem; max-width: 800px; margin: 0 auto; }
textarea { width: 100%; min-height: 300px; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; margin: 1rem 0; font-family: inherit; }
.btn { padding: 0.7rem 1.5rem; background: #667eea; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
</style>
