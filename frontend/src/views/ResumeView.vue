<script setup lang="ts">
import { ref } from 'vue'
const resumeText = ref('')
const loading = ref(false)
async function handleParse() {
  if (!resumeText.value.trim()) return
  loading.value = true
  setTimeout(() => { loading.value = false; alert('简历解析占位：请接入后端 API') }, 800)
}
</script>

<template>
  <div class="page">
    <h2>简历解析</h2>
    <textarea v-model="resumeText" placeholder="粘贴简历文本，或上传 PDF/Word 文件..."></textarea>
    <button class="btn" :disabled="loading" @click="handleParse">{{ loading ? '解析中...' : '开始解析' }}</button>
  </div>
</template>

<style scoped>
.page { padding: 2rem; max-width: 800px; margin: 0 auto; }
textarea { width: 100%; min-height: 300px; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; font-family: inherit; margin: 1rem 0; }
.btn { padding: 0.7rem 1.5rem; background: #667eea; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
</style>
